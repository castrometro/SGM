from django.db import transaction
from django.db.models import Count
from ..models import IncidenciaCierre, CierreNomina, ResolucionIncidencia


def _elegir_usuario_para_nota(cierre: CierreNomina):
    # Preferir supervisor asignado, luego analista; si ninguno, retornar None
    return cierre.supervisor_asignado or cierre.usuario_analista or None


def reconciliar_cierre_por_firma(cierre_id: int) -> dict:
    """
    Reconciliación vN: unifica incidencias por firma dentro de un cierre,
    actualiza versiones y marca desapariciones como 'resolucion_supervisor_pendiente'.
    Retorna resumen con conteos.
    """
    with transaction.atomic():
        cierre = CierreNomina.objects.select_for_update().get(id=cierre_id)
        vN = cierre.version_datos or 1

        # No usar select_related('cierre') aquí porque más abajo se usa only(...) y se difiere el campo
        # 'cierre', lo que provoca: "Field IncidenciaCierre.cierre cannot be both deferred and traversed"
        # Además, en este flujo no accedemos a inc.cierre, por lo que el join no aporta.
        qs = IncidenciaCierre.objects.filter(
            cierre_id=cierre_id,
            tipo_comparacion__in=['individual', 'suma_total']
        )

        # Asegurar firma y versiones en vacíos (por bulk_create no pasa por save)
        faltantes = []
        for inc in qs.only('id', 'tipo_comparacion', 'concepto_afectado', 'rut_empleado', 'firma_clave', 'firma_hash', 'version_detectada_primera', 'version_detectada_ultima'):
            mod = False
            if not inc.firma_clave or not inc.firma_hash:
                clave, h = inc.generar_firma()
                inc.firma_clave = clave
                inc.firma_hash = h
                mod = True
            if not inc.version_detectada_primera:
                inc.version_detectada_primera = vN
                inc.version_detectada_ultima = vN
                mod = True
            if mod:
                faltantes.append(inc)
        if faltantes:
            IncidenciaCierre.objects.bulk_update(faltantes, ['firma_clave', 'firma_hash', 'version_detectada_primera', 'version_detectada_ultima'])

        # Agrupar por firma_hash para detectar duplicados (múltiples versiones)
        todas = list(qs)
        grupos = {}
        for inc in todas:
            if not inc.firma_hash:
                # si no hay firma, saltar (informativas, etc.)
                continue
            grupos.setdefault(inc.firma_hash, []).append(inc)

        vigentes_actualizadas = 0
        unificadas = 0
        desaparecidas_pendientes = 0
        usuario_nota = _elegir_usuario_para_nota(cierre)

        for firma, lista in grupos.items():
            if len(lista) == 1:
                # Solo una versión; si es vN, cuenta como vigente actualizada
                inc = lista[0]
                if inc.version_detectada_ultima == vN:
                    vigentes_actualizadas += 1
                continue

            # Elegir incidencia canónica: la con resoluciones o la de menor version_detectada_primera
            lista_sorted = sorted(
                lista,
                key=lambda x: (
                    -(getattr(x, 'resoluciones_count', 0)),
                    x.version_detectada_primera or 10**9,
                    x.id
                )
            )

            # Prefetch conteo de resoluciones si no existe
            if not hasattr(lista_sorted[0], 'resoluciones_count'):
                ids = [i.id for i in lista_sorted]
                counts = dict(
                    IncidenciaCierre.objects.filter(id__in=ids)
                    .annotate(c=Count('resoluciones')).values_list('id', 'c')
                )
                for i in lista_sorted:
                    i.resoluciones_count = counts.get(i.id, 0)

            lista_sorted = sorted(
                lista,
                key=lambda x: (-x.resoluciones_count, x.version_detectada_primera or 10**9, x.id)
            )
            canon = lista_sorted[0]
            otros = [x for x in lista_sorted[1:]]

            # Tomar el más reciente (si existe) para copiar valores
            mas_reciente = max(lista, key=lambda x: (x.version_detectada_ultima or 0, x.id))

            # Actualizar canónica con datos de la versión más reciente
            campos_update = []
            for campo in ['impacto_monetario', 'descripcion', 'prioridad', 'concepto_afectado', 'datos_adicionales', 'tipo_incidencia']:
                nuevo_valor = getattr(mas_reciente, campo)
                if getattr(canon, campo) != nuevo_valor:
                    setattr(canon, campo, nuevo_valor)
                    campos_update.append(campo)
            # Actualizar tracking de versión
            if (canon.version_detectada_ultima or 0) != (mas_reciente.version_detectada_ultima or vN):
                canon.version_detectada_ultima = mas_reciente.version_detectada_ultima or vN
                campos_update.append('version_detectada_ultima')
            if campos_update:
                canon.save(update_fields=campos_update)
                vigentes_actualizadas += 1
                unificadas += len(otros)

            # Mover resoluciones de duplicados (por seguridad) y eliminar duplicados
            for dup in otros:
                if dup.id == canon.id:
                    continue
                # Reasignar resoluciones si existieran
                dup.resoluciones.update(incidencia=canon)
                dup.delete()

            # Nota del sistema (opcional) — solo si tenemos un usuario para asociar la nota
            if usuario_nota and mas_reciente.id != canon.id:
                ResolucionIncidencia.objects.create(
                    incidencia=canon,
                    usuario=usuario_nota,
                    tipo_resolucion='consulta',  # neutral
                    comentario=f"Recalculada con v{vN}. Valores actualizados desde ID {mas_reciente.id}"
                )

        # Marcar desapariciones: incidencias cuya version_detectada_ultima < vN
        desaparecidas = IncidenciaCierre.objects.filter(
            cierre_id=cierre_id,
            tipo_comparacion__in=['individual', 'suma_total'],
            version_detectada_ultima__lt=vN
        )
        count_desap = 0
        for inc in desaparecidas:
            if inc.estado != 'resolucion_supervisor_pendiente':
                inc.estado = 'resolucion_supervisor_pendiente'
                inc.save(update_fields=['estado'])
                count_desap += 1
                if usuario_nota:
                    ResolucionIncidencia.objects.create(
                        incidencia=inc,
                        usuario=usuario_nota,
                        tipo_resolucion='consulta',
                        comentario=f"Incidencia no presente en v{vN}; requiere confirmación del supervisor"
                    )
        desaparecidas_pendientes = count_desap

        return {
            'vigentes_actualizadas': vigentes_actualizadas,
            'unificadas': unificadas,
            'supervisor_pendiente': desaparecidas_pendientes,
            'version': vN,
        }
