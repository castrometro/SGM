from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db import transaction
from .models import CierreNomina, ConceptoConsolidado, IncidenciaCierre

TIPO_VALIDO_SET = {
    'haber_imponible', 'haber_no_imponible', 'descuento_legal', 'otro_descuento', 'aporte_patronal', 'impuesto', 'informativo'
}

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def reclasificar_concepto_consolidado(request, cierre_id: int):
    """🔄 Reclasifica un concepto consolidado (post datos_consolidados).

    Body JSON esperado:
      {
        "nombre_concepto": "Sueldo Base",
        "tipo_concepto_nuevo": "haber_imponible",
        "motivo": "Corrección manual" (opcional)
      }

        Reglas:
            - Estados permitidos del cierre: datos_consolidados, con_incidencias, incidencias_resueltas
            - Aplica a TODOS los registros ConceptoConsolidado con ese nombre dentro del cierre.
            - Actualiza (si existe y el cierre NO está finalizado) el bloque libro_resumen_v2 del InformeNomina para mantener consistencia.
            - Invalida (elimina) cache Redis de datos consolidados para forzar regeneración ligera en próxima consulta.
            - Actualiza incidencias existentes del concepto:
                    * Si pasa a 'informativo' => se eliminan incidencias del concepto (ya no deberían existir).
                    * Si pasa a otra categoría => se actualiza campo 'clasificacion_concepto' y datos_adicionales.tipo_concepto.
    """
    cierre = get_object_or_404(CierreNomina, pk=cierre_id)

    estados_permitidos = {"datos_consolidados", "con_incidencias", "incidencias_resueltas"}
    if cierre.estado not in estados_permitidos:
        return Response({
            'error': 'Cierre no admite reclasificación en su estado actual',
            'estado': cierre.estado
        }, status=status.HTTP_400_BAD_REQUEST)

    nombre = (request.data.get('nombre_concepto') or '').strip()
    tipo_nuevo = (request.data.get('tipo_concepto_nuevo') or '').strip()
    motivo = (request.data.get('motivo') or '').strip() or None

    if not nombre or not tipo_nuevo:
        return Response({'error': 'nombre_concepto y tipo_concepto_nuevo son requeridos'}, status=400)
    if tipo_nuevo not in TIPO_VALIDO_SET:
        return Response({'error': f'tipo_concepto_nuevo inválido. Valores permitidos: {sorted(TIPO_VALIDO_SET)}'}, status=400)

    # Query base de conceptos del cierre (todas las nóminas asociadas)
    conceptos_qs = ConceptoConsolidado.objects.filter(nomina_consolidada__cierre_id=cierre.id, nombre_concepto=nombre)
    total_registros = conceptos_qs.count()
    if total_registros == 0:
        return Response({'error': 'Concepto no encontrado en este cierre'}, status=404)

    # Si ya está en el tipo solicitado, retornar early
    tipos_distintos = conceptos_qs.exclude(tipo_concepto=tipo_nuevo).exists()
    if not tipos_distintos:
        return Response({
            'mensaje': 'Concepto ya tenía el tipo solicitado. Sin cambios.',
            'nombre_concepto': nombre,
            'tipo_concepto': tipo_nuevo,
            'registros_afectados': 0
        }, status=200)

    # Mapeo a la clasificación usada en incidencias/front
    mapeo_clasificaciones = {
        'haber_imponible': 'haberes_imponibles',
        'haber_no_imponible': 'haberes_no_imponibles',
        'descuento_legal': 'descuentos_legales',
        'otro_descuento': 'otros_descuentos',
        'aporte_patronal': 'aportes_patronales',
        'impuesto': 'impuestos',
        'informativo': 'informacion_adicional'
    }
    nueva_clasificacion_ext = mapeo_clasificaciones.get(tipo_nuevo)

    with transaction.atomic():
        conceptos_qs.update(tipo_concepto=tipo_nuevo)
        incidencias_actualizadas = 0
        incidencias_eliminadas = 0
        # Procesar incidencias del concepto
        incidencias_qs = IncidenciaCierre.objects.filter(cierre=cierre, concepto_afectado=nombre)
        if incidencias_qs.exists():
            if nueva_clasificacion_ext == 'informacion_adicional':
                incidencias_eliminadas = incidencias_qs.count()
                incidencias_qs.delete()
                # Ajustar conteo del cierre
                try:
                    cierre.total_incidencias = max(0, (cierre.total_incidencias or 0) - incidencias_eliminadas)
                    if cierre.total_incidencias == 0:
                        cierre.estado_incidencias = 'resueltas'
                        if cierre.estado == 'con_incidencias':
                            cierre.estado = 'incidencias_resueltas'
                    cierre.save(update_fields=['total_incidencias', 'estado_incidencias', 'estado'])
                except Exception:
                    pass
            else:
                # Actualizar clasificación en bloque
                for inc in incidencias_qs.iterator():
                    dirty = False
                    if inc.clasificacion_concepto != nueva_clasificacion_ext:
                        inc.clasificacion_concepto = nueva_clasificacion_ext
                        dirty = True
                    try:
                        if isinstance(inc.datos_adicionales, dict):
                            if inc.datos_adicionales.get('tipo_concepto') != nueva_clasificacion_ext:
                                inc.datos_adicionales['tipo_concepto'] = nueva_clasificacion_ext
                                dirty = True
                    except Exception:
                        pass
                    if dirty:
                        inc.save(update_fields=['clasificacion_concepto', 'datos_adicionales'])
                        incidencias_actualizadas += 1

        # Intentar actualizar informe JSON si existe (y no finalizado)
        informe_actualizado = False
        try:
            informe = getattr(cierre, 'informe', None)
            if informe and isinstance(informe.datos_cierre, dict) and cierre.estado != 'finalizado':
                bloque = informe.datos_cierre.get('libro_resumen_v2')
                if isinstance(bloque, dict):
                    conceptos_lista = bloque.get('conceptos') or []
                    cambiado = False
                    for c in conceptos_lista:
                        if c.get('nombre') == nombre:
                            # Ajustar totales categorias: restar de vieja, sumar a nueva
                            old_cat = c.get('categoria')
                            if old_cat and old_cat != tipo_nuevo:
                                tot_cat = bloque.get('totales_categorias') or {}
                                try:
                                    if old_cat in tot_cat:
                                        tot_cat[old_cat] = float(tot_cat.get(old_cat, 0.0)) - float(c.get('total', 0.0))
                                    if tipo_nuevo in tot_cat:
                                        tot_cat[tipo_nuevo] = float(tot_cat.get(tipo_nuevo, 0.0)) + float(c.get('total', 0.0))
                                except Exception:
                                    pass
                            c['categoria'] = tipo_nuevo
                            cambiado = True
                    if cambiado:
                        informe.datos_cierre['libro_resumen_v2'] = bloque
                        # Marcar metadato simple
                        meta = bloque.get('meta') or {}
                        meta['reclasificado_en'] = meta.get('reclasificado_en', []) + [request.user.correo_bdo]
                        informe.datos_cierre['libro_resumen_v2']['meta'] = meta
                        informe.save(update_fields=['datos_cierre'])
                        informe_actualizado = True
        except Exception:
            pass

        # Limpiar cache Redis de datos consolidados (TTL corto) para este cierre
        try:
            from .cache_redis import get_cache_system_nomina
            cache = get_cache_system_nomina()
            # La clase no tiene delete explícito; sobreescribimos con dict vacío TTL muy corto para invalidar
            cache.set_datos_consolidados(cierre.cliente_id, cierre.periodo, {'invalidado_por_reclasificacion': True}, ttl=5)
        except Exception:
            pass

    return Response({
        'mensaje': 'Reclasificación aplicada',
        'nombre_concepto': nombre,
        'tipo_concepto_nuevo': tipo_nuevo,
        'nueva_clasificacion_ext': nueva_clasificacion_ext,
        'registros_afectados': total_registros,
        'motivo': motivo,
        'informe_actualizado': informe_actualizado,
        'incidencias_actualizadas': locals().get('incidencias_actualizadas', 0),
        'incidencias_eliminadas': locals().get('incidencias_eliminadas', 0)
    }, status=200)
