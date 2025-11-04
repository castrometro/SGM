from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from django.conf import settings
from django.contrib.auth import get_user_model
import hashlib
import logging
from ..models import IncidenciaCierre, CierreNomina, ResolucionIncidencia, ConceptoConsolidado

logger = logging.getLogger(__name__)


def _elegir_usuario_para_nota(cierre: CierreNomina):
    # Preferir supervisor asignado, luego analista; si ninguno, retornar None
    return cierre.supervisor_asignado or cierre.usuario_analista or None


def _obtener_usuario_sistema():
    """Obtiene o crea un usuario especial 'Sistema' para comentarios automáticos."""
    User = get_user_model()
    correo = getattr(settings, 'SYSTEM_USER_EMAIL', 'sistema@sgm.local')
    defaults = {
        'nombre': 'Sistema',
        'apellido': 'Automático',
        'cargo_bdo': 'SGM',
        'tipo_usuario': 'gerente',
        'is_staff': True,
        'is_superuser': True,
    }
    usuario, _ = User.objects.get_or_create(correo_bdo=correo, defaults=defaults)
    return usuario


def _variacion_pct(actual, anterior):
    if not anterior or float(anterior) == 0:
        return 100.0 if (actual or 0) > 0 else 0.0
    try:
        return float(((actual or 0) - (anterior or 0)) / anterior * 100)
    except Exception:
        return 0.0


def _hash_incidencia_suma_total(nombre_concepto: str, tipo_concepto: str) -> str:
    """Hash estable por concepto/tipo para identificar la misma incidencia a través de recalculos.

    No incluye montos, de modo que una misma incidencia (mismo concepto/tipo) conserve el hash
    aunque cambien los valores, permitiendo actualizarla en lugar de duplicarla.
    """
    base = f"suma_total|{(tipo_concepto or '').strip().lower()}|{(nombre_concepto or '').strip().lower()}"
    return hashlib.sha1(base.encode('utf-8')).hexdigest()


def verificar_y_actualizar_estado_cierre(cierre_id: int) -> dict:
    """
    Verifica el estado de todas las incidencias de un cierre y actualiza automáticamente
    el estado del cierre según corresponda.
    
    Lógica:
    - Si NO hay incidencias vigentes → 'incidencias_resueltas' / 'resueltas'
    - Si TODAS las incidencias están en estado 'aprobada_supervisor' → 'incidencias_resueltas' / 'resueltas'
    - Si hay incidencias pendientes → 'con_incidencias' / 'detectadas' o 'en_revision'
    
    Args:
        cierre_id: ID del cierre a verificar
        
    Returns:
        dict: Información del estado actualizado
    """
    try:
        cierre = CierreNomina.objects.get(id=cierre_id)
        
        # Contar incidencias por estado
        total_incidencias = cierre.incidencias.count()
        incidencias_aprobadas = cierre.incidencias.filter(estado='aprobada_supervisor').count()
        incidencias_resueltas = cierre.incidencias.filter(estado__in=['resuelta_analista', 'aprobada_supervisor']).count()
        incidencias_pendientes = cierre.incidencias.filter(estado='pendiente').count()
        
        estado_anterior = cierre.estado
        estado_incidencias_anterior = cierre.estado_incidencias
        
        # CASO 1: No hay incidencias → Estado resuelto
        if total_incidencias == 0:
            cierre.estado = 'incidencias_resueltas'
            cierre.estado_incidencias = 'resueltas'
            cierre.total_incidencias = 0
            cierre.save(update_fields=['estado', 'estado_incidencias', 'total_incidencias'])
            logger.info(f"✅ Cierre {cierre_id}: Sin incidencias → 'incidencias_resueltas'")
            
        # CASO 2: Todas las incidencias están aprobadas → Estado resuelto
        elif incidencias_aprobadas == total_incidencias:
            # Solo actualizar si el cierre está en estados de incidencias
            if cierre.estado in ['con_incidencias', 'datos_consolidados']:
                cierre.estado = 'incidencias_resueltas'
            cierre.estado_incidencias = 'resueltas'
            cierre.total_incidencias = 0  # Todas resueltas
            cierre.save(update_fields=['estado', 'estado_incidencias', 'total_incidencias'])
            logger.info(f"✅ Cierre {cierre_id}: {incidencias_aprobadas}/{total_incidencias} aprobadas → 'incidencias_resueltas'")
            
        # CASO 3: Hay incidencias pendientes → Estado con incidencias
        else:
            if cierre.estado not in ['con_incidencias']:
                cierre.estado = 'con_incidencias'
            
            # Determinar sub-estado según cantidad de resueltas
            if incidencias_resueltas > 0:
                cierre.estado_incidencias = 'en_revision'
            else:
                cierre.estado_incidencias = 'detectadas'
            
            cierre.total_incidencias = total_incidencias - incidencias_aprobadas
            cierre.save(update_fields=['estado', 'estado_incidencias', 'total_incidencias'])
            logger.info(f"⚠️ Cierre {cierre_id}: {cierre.total_incidencias} pendientes → '{cierre.estado}' / '{cierre.estado_incidencias}'")
        
        return {
            'success': True,
            'cierre_id': cierre_id,
            'estado_anterior': estado_anterior,
            'estado_nuevo': cierre.estado,
            'estado_incidencias_anterior': estado_incidencias_anterior,
            'estado_incidencias_nuevo': cierre.estado_incidencias,
            'total_incidencias': total_incidencias,
            'incidencias_aprobadas': incidencias_aprobadas,
            'incidencias_pendientes': incidencias_pendientes,
            'cambio_realizado': estado_anterior != cierre.estado or estado_incidencias_anterior != cierre.estado_incidencias
        }
        
    except CierreNomina.DoesNotExist:
        logger.error(f"❌ Cierre {cierre_id} no existe")
        return {'success': False, 'error': 'Cierre no encontrado'}
    except Exception as e:
        logger.error(f"❌ Error verificando estado del cierre {cierre_id}: {e}", exc_info=True)
        return {'success': False, 'error': str(e)}



def reconciliar_cierre_suma_total(cierre_id: int, umbral_pct: float = 30.0) -> dict:
    """
    Reconciliación para el modelo simplificado (suma_total):
    - Recalcula variaciones por concepto (todas las categorías, agregado por ítem)
    - Upsert: crea nuevas o actualiza existentes (descripcion, datos, impacto, version_ultima)
    - Marca como resuelta_analista las incidencias que ya no superan el umbral
    Retorna resumen con conteos y versión utilizada.
    """
    with transaction.atomic():
        cierre = CierreNomina.objects.select_for_update().get(id=cierre_id)
        vN = cierre.version_datos or 1

        # Determinar cierre anterior finalizado (si no hay, no se generan variaciones)
        cierre_anterior = (
            CierreNomina.objects
            .filter(cliente=cierre.cliente, periodo__lt=cierre.periodo, estado='finalizado')
            .order_by('-periodo')
            .first()
        )

        # Mapa de totales por (nombre_concepto, tipo_concepto)
        # ✅ Excluir conceptos informativos (no generan incidencias)
        EXCLUIR_TIPOS = {'informativo'}  # No comparar categoría informativa
        def totales_por_concepto(cierre_obj):
            if not cierre_obj:
                return {}
            qs = ConceptoConsolidado.objects.filter(nomina_consolidada__cierre=cierre_obj)
            if EXCLUIR_TIPOS:
                qs = qs.exclude(tipo_concepto__in=EXCLUIR_TIPOS)
            datos = (
                qs.values('nombre_concepto', 'tipo_concepto')
                .annotate(total=Sum('monto_total'))
            )
            return { (d['nombre_concepto'], d['tipo_concepto']) : d['total'] for d in datos }

        mapa_act = totales_por_concepto(cierre)
        mapa_ant = totales_por_concepto(cierre_anterior)
        claves = set(mapa_act.keys()) | set(mapa_ant.keys())

        existentes_qs = IncidenciaCierre.objects.select_for_update().filter(
            cierre_id=cierre_id,
            tipo_comparacion='suma_total'
        )
        # Mapear existentes por hash estable si está, y por clave de concepto como respaldo
        existentes_por_hash = {i.hash_deteccion: i for i in existentes_qs if getattr(i, 'hash_deteccion', None)}
        existentes_por_concepto = {(i.concepto_afectado, i.tipo_incidencia): i for i in existentes_qs}

        creadas = 0
        actualizadas = 0
        marcadas_resueltas = 0
        # Preferir analista para comentarios automáticos; si no existe, usar usuario de Sistema
        usuario_sistema = _obtener_usuario_sistema()
        usuario_para_comentario = cierre.usuario_analista or usuario_sistema

        # Upsert para las que superan umbral
        vigentes_hashes = set()
        vigentes_keys = set()
        for (nombre, tipo) in claves:
            # Saltar categorías informativas
            if tipo in EXCLUIR_TIPOS:
                continue
            suma_act = float(mapa_act.get((nombre, tipo), 0) or 0)
            suma_ant = float(mapa_ant.get((nombre, tipo), 0) or 0)
            variacion = _variacion_pct(suma_act, suma_ant)
            if abs(variacion) < umbral_pct:
                continue

            key = (nombre, 'variacion_suma_total')
            hash_estable = _hash_incidencia_suma_total(nombre, tipo)
            vigentes_keys.add(key)
            vigentes_hashes.add(hash_estable)

            # Incluir ambas nomenclaturas para compatibilidad (monto_* y suma_*)
            delta_abs = suma_act - suma_ant
            datos = {
                'alcance': 'item',
                'categoria_concepto': tipo,
                'concepto': nombre,
                'tipo_concepto': tipo,
                'suma_actual': suma_act,
                'suma_anterior': suma_ant,
                'monto_actual': suma_act,
                'monto_anterior': suma_ant,
                'variacion_porcentual': round(variacion, 2),
                'variacion_absoluta': abs(delta_abs),
                'delta_abs': delta_abs,
                'delta_pct': round(variacion, 2),
                'tipo_comparacion': 'suma_total'
            }
            descripcion = f"Variación {variacion:.1f}% en suma total de {nombre}"
            impacto = abs(delta_abs)

            # Buscar por hash estable primero; si no, por clave concepto/tipo
            existente = existentes_por_hash.get(hash_estable) or existentes_por_concepto.get(key)
            if existente:
                campos = []
                if existente.descripcion != descripcion:
                    existente.descripcion = descripcion; campos.append('descripcion')
                if existente.clasificacion_concepto != tipo:
                    existente.clasificacion_concepto = tipo; campos.append('clasificacion_concepto')
                if existente.datos_adicionales != datos:
                    existente.datos_adicionales = datos; campos.append('datos_adicionales')
                if float(existente.impacto_monetario or 0) != impacto:
                    existente.impacto_monetario = impacto; campos.append('impacto_monetario')
                if (existente.version_detectada_ultima or 0) != vN:
                    existente.version_detectada_ultima = vN; campos.append('version_detectada_ultima')
                if existente.version_detectada_primera is None:
                    existente.version_detectada_primera = vN; campos.append('version_detectada_primera')
                if existente.hash_deteccion != hash_estable:
                    existente.hash_deteccion = hash_estable; campos.append('hash_deteccion')
                if campos:
                    existente.save(update_fields=campos)
                    actualizadas += 1
            else:
                IncidenciaCierre.objects.create(
                    cierre_id=cierre_id,
                    tipo_incidencia='variacion_suma_total',
                    tipo_comparacion='suma_total',
                    concepto_afectado=nombre,
                    clasificacion_concepto=tipo,
                    descripcion=descripcion,
                    impacto_monetario=impacto,
                    datos_adicionales=datos,
                    version_detectada_primera=vN,
                    version_detectada_ultima=vN,
                    hash_deteccion=hash_estable,
                    asignado_a=cierre.usuario_analista,  # Asignar automáticamente al analista del cierre
                )
                creadas += 1

        # Marcar como resueltas las que ya no superan el umbral
        for obj in existentes_qs:
            if obj.tipo_incidencia != 'variacion_suma_total':
                continue
            clave = (obj.concepto_afectado, obj.tipo_incidencia)
            if (obj.hash_deteccion and obj.hash_deteccion in vigentes_hashes) or clave in vigentes_keys:
                continue
            # Dejar comentario informando valores vigentes, pero SIN actualizar los valores almacenados en la incidencia
            tipo_concepto = obj.clasificacion_concepto
            nombre = obj.concepto_afectado
            suma_act_res = float(mapa_act.get((nombre, tipo_concepto), 0) or 0)
            suma_ant_res = float(mapa_ant.get((nombre, tipo_concepto), 0) or 0)
            variacion_res = _variacion_pct(suma_act_res, suma_ant_res)

            # Formatear comentario solicitado
            fecha_str = timezone.now().strftime('%Y-%m-%d')
            comentario = (
                f"Incidencia Resuelta el día {fecha_str} en resubida de libro. "
                f"Monto Mes Anterior: ${suma_ant_res:,.0f}, "
                f"Monto Mes Actual: ${suma_act_res:,.0f}, "
                f"Nueva variación: {round(variacion_res, 2)}%."
            )

            campos_update = []
            if obj.estado != 'resuelta_analista':
                obj.estado = 'resuelta_analista'; campos_update.append('estado')
            if obj.asignado_a != cierre.usuario_analista:
                obj.asignado_a = cierre.usuario_analista; campos_update.append('asignado_a')
            if (obj.version_detectada_ultima or 0) != vN:
                obj.version_detectada_ultima = vN; campos_update.append('version_detectada_ultima')
            if obj.version_detectada_primera is None:
                obj.version_detectada_primera = vN; campos_update.append('version_detectada_primera')
            if campos_update:
                obj.save(update_fields=campos_update)
            marcadas_resueltas += 1

            ResolucionIncidencia.objects.create(
                incidencia=obj,
                usuario=usuario_para_comentario,
                tipo_resolucion='justificacion',
                comentario=comentario
            )

        # ✅ ACTUALIZAR ESTADO DEL CIERRE según incidencias detectadas
        total_vigentes = creadas + actualizadas
        if total_vigentes > 0:
            cierre.estado = 'con_incidencias'
            cierre.estado_incidencias = 'detectadas'
            cierre.total_incidencias = total_vigentes
            cierre.save(update_fields=['estado', 'estado_incidencias', 'total_incidencias'])
            logger.info(f"📌 Estado del cierre actualizado a 'con_incidencias' / 'detectadas' ({total_vigentes} incidencias)")
        else:
            cierre.estado = 'incidencias_resueltas'
            cierre.estado_incidencias = 'resueltas'
            cierre.total_incidencias = 0
            cierre.save(update_fields=['estado', 'estado_incidencias', 'total_incidencias'])
            logger.info(f"✅ Estado del cierre actualizado a 'incidencias_resueltas' / 'resueltas' (0 incidencias)")

        return {
            'creadas': creadas,
            'actualizadas': actualizadas,
            'marcadas_resueltas': marcadas_resueltas,
            'version': vN,
        }
