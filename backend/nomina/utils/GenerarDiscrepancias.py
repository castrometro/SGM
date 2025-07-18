# backend/nomina/utils/GenerarDiscrepancias.py

import logging
import unicodedata
import re
from django.utils import timezone
from ..models import (
    CierreNomina, EmpleadoCierre, RegistroConceptoEmpleado,
    EmpleadoCierreNovedades, RegistroConceptoEmpleadoNovedades,
    MovimientoAltaBaja, MovimientoAusentismo, MovimientoVacaciones,
    AnalistaFiniquito, AnalistaIncidencia, AnalistaIngreso,
    DiscrepanciaCierre, TipoDiscrepancia
)

logger = logging.getLogger(__name__)

def normalizar_texto(texto):
    """
    Normaliza texto para comparaciones ignorando:
    - Mayúsculas/minúsculas
    - Tildes y acentos
    - Guiones, puntos, espacios extra
    - Caracteres especiales
    """
    if not texto:
        return ""
    
    # Convertir a string y minúsculas
    texto = str(texto).lower().strip()
    
    # Quitar acentos/tildes usando unicodedata
    texto = unicodedata.normalize('NFD', texto)
    texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')
    
    # Quitar guiones, puntos, comas y caracteres especiales
    texto = re.sub(r'[-.,;:()\'\"]+', ' ', texto)
    
    # Normalizar espacios múltiples a uno solo
    texto = re.sub(r'\s+', ' ', texto).strip()
    
    return texto

def textos_son_equivalentes(texto1, texto2):
    """Compara si dos textos son equivalentes después de normalización"""
    return normalizar_texto(texto1) == normalizar_texto(texto2)

def normalizar_rut(rut):
    """
    Normaliza RUT para comparaciones removiendo puntos, guiones y espacios
    """
    if not rut:
        return ""
    
    # Convertir a string y limpiar
    rut_limpio = str(rut).strip()
    
    # Remover puntos, guiones, espacios
    rut_limpio = re.sub(r'[.\-\s]', '', rut_limpio)
    
    # Convertir a mayúsculas (por si el dígito verificador es 'k')
    rut_limpio = rut_limpio.upper()
    
    return rut_limpio

def ruts_son_equivalentes(rut1, rut2):
    """Compara si dos RUTs son equivalentes después de normalización"""
    return normalizar_rut(rut1) == normalizar_rut(rut2)

def generar_todas_discrepancias(cierre):
    """Función principal para generar todas las discrepancias de un cierre"""
    logger.info(f"Iniciando generación de discrepancias para cierre {cierre.id}")
    
    discrepancias_generadas = []
    
    try:
        # Grupo 1: Libro vs Novedades
        discrepancias_libro_novedades = generar_discrepancias_libro_vs_novedades(cierre)
        discrepancias_generadas.extend(discrepancias_libro_novedades)
        
        # Grupo 2: MovimientosMes vs Archivos Analista
        discrepancias_movimientos_analista = generar_discrepancias_movimientos_vs_analista(cierre)
        discrepancias_generadas.extend(discrepancias_movimientos_analista)
        
        # Guardar todas las discrepancias
        if discrepancias_generadas:
            DiscrepanciaCierre.objects.bulk_create(discrepancias_generadas)
            logger.info(f"Generadas {len(discrepancias_generadas)} discrepancias para cierre {cierre.id}")
        else:
            logger.info(f"No se encontraron discrepancias para cierre {cierre.id}")
        
        return {
            'cierre_id': cierre.id,
            'total_discrepancias': len(discrepancias_generadas),
            'libro_vs_novedades': len(discrepancias_libro_novedades),
            'movimientos_vs_analista': len(discrepancias_movimientos_analista),
            'estado': 'completado'
        }
        
    except Exception as e:
        logger.error(f"Error generando discrepancias para cierre {cierre.id}: {e}")
        raise

def generar_discrepancias_libro_vs_novedades(cierre):
    """Genera discrepancias comparando Libro de Remuneraciones vs Novedades"""
    discrepancias = []
    
    logger.info(f"Generando discrepancias Libro vs Novedades para cierre {cierre.id}")
    
    # Obtener empleados de ambos archivos
    empleados_libro = EmpleadoCierre.objects.filter(cierre=cierre).prefetch_related('registroconceptoempleado_set')
    empleados_novedades = EmpleadoCierreNovedades.objects.filter(cierre=cierre).prefetch_related('registroconceptoempleadonovedades_set')
    
    # Crear diccionarios por RUT normalizado
    dict_libro = {normalizar_rut(emp.rut): emp for emp in empleados_libro}
    dict_novedades = {normalizar_rut(emp.rut): emp for emp in empleados_novedades}
    
    # 1. Empleados solo en Libro
    for rut_norm, emp_libro in dict_libro.items():
        if rut_norm not in dict_novedades:
            discrepancias.append(DiscrepanciaCierre(
                cierre=cierre,
                tipo_discrepancia=TipoDiscrepancia.EMPLEADO_SOLO_LIBRO,
                empleado_libro=emp_libro,
                rut_empleado=emp_libro.rut,
                descripcion=f"Empleado {emp_libro.nombre} {emp_libro.apellido_paterno} (RUT: {emp_libro.rut}) aparece solo en Libro de Remuneraciones",
                valor_libro=f"{emp_libro.nombre} {emp_libro.apellido_paterno}",
                valor_novedades="No encontrado"
            ))
    
    # 2. Empleados solo en Novedades
    for rut_norm, emp_novedades in dict_novedades.items():
        if rut_norm not in dict_libro:
            discrepancias.append(DiscrepanciaCierre(
                cierre=cierre,
                tipo_discrepancia=TipoDiscrepancia.EMPLEADO_SOLO_NOVEDADES,
                empleado_novedades=emp_novedades,
                rut_empleado=emp_novedades.rut,
                descripcion=f"Empleado {emp_novedades.nombre} {emp_novedades.apellido_paterno} (RUT: {emp_novedades.rut}) aparece solo en Novedades",
                valor_libro="No encontrado",
                valor_novedades=f"{emp_novedades.nombre} {emp_novedades.apellido_paterno}"
            ))
    
    # 3. Empleados en ambos - comparar datos
    for rut_norm in dict_libro.keys() & dict_novedades.keys():
        emp_libro = dict_libro[rut_norm]
        emp_novedades = dict_novedades[rut_norm]
        
        # Comparar datos personales
        discrepancias.extend(_comparar_datos_personales(cierre, emp_libro, emp_novedades))
        
        # Comparar conceptos y montos
        discrepancias.extend(_comparar_conceptos_empleado(cierre, emp_libro, emp_novedades))
    
    logger.info(f"Generadas {len(discrepancias)} discrepancias Libro vs Novedades")
    return discrepancias

def _comparar_datos_personales(cierre, emp_libro, emp_novedades):
    """Compara datos personales entre empleados del libro y novedades"""
    discrepancias = []
    
    # Comparar nombres y apellidos
    nombre_libro = f"{emp_libro.nombre} {emp_libro.apellido_paterno} {emp_libro.apellido_materno}".strip()
    nombre_novedades = f"{emp_novedades.nombre} {emp_novedades.apellido_paterno} {emp_novedades.apellido_materno}".strip()
    
    if not textos_son_equivalentes(nombre_libro, nombre_novedades):
        discrepancias.append(DiscrepanciaCierre(
            cierre=cierre,
            tipo_discrepancia=TipoDiscrepancia.DIFERENCIA_DATOS_PERSONALES,
            empleado_libro=emp_libro,
            empleado_novedades=emp_novedades,
            rut_empleado=emp_libro.rut,
            descripcion=f"Diferencia en datos personales para RUT {emp_libro.rut}",
            valor_libro=nombre_libro,
            valor_novedades=nombre_novedades
        ))
    
    return discrepancias

def _comparar_conceptos_empleado(cierre, emp_libro, emp_novedades):
    """Compara conceptos y montos entre empleados del libro y novedades"""
    discrepancias = []
    
    # Obtener registros de conceptos
    registros_libro = RegistroConceptoEmpleado.objects.filter(empleado=emp_libro)
    registros_novedades = RegistroConceptoEmpleadoNovedades.objects.filter(empleado=emp_novedades)
    
    # Crear diccionarios por concepto normalizado
    dict_libro = {normalizar_texto(reg.nombre_concepto_original): reg for reg in registros_libro}
    dict_novedades = {normalizar_texto(reg.nombre_concepto_original): reg for reg in registros_novedades}
    
    # Conceptos solo en Libro
    for concepto_norm, reg_libro in dict_libro.items():
        if concepto_norm not in dict_novedades:
            discrepancias.append(DiscrepanciaCierre(
                cierre=cierre,
                tipo_discrepancia=TipoDiscrepancia.CONCEPTO_SOLO_LIBRO,
                empleado_libro=emp_libro,
                empleado_novedades=emp_novedades,
                rut_empleado=emp_libro.rut,
                descripcion=f"Concepto '{reg_libro.nombre_concepto_original}' aparece solo en Libro para RUT {emp_libro.rut}",
                valor_libro=f"{reg_libro.nombre_concepto_original}: {reg_libro.monto}",
                valor_novedades="No encontrado",
                concepto_afectado=reg_libro.nombre_concepto_original
            ))
    
    # Conceptos solo en Novedades
    for concepto_norm, reg_novedades in dict_novedades.items():
        if concepto_norm not in dict_libro:
            discrepancias.append(DiscrepanciaCierre(
                cierre=cierre,
                tipo_discrepancia=TipoDiscrepancia.CONCEPTO_SOLO_NOVEDADES,
                empleado_libro=emp_libro,
                empleado_novedades=emp_novedades,
                rut_empleado=emp_libro.rut,
                descripcion=f"Concepto '{reg_novedades.nombre_concepto_original}' aparece solo en Novedades para RUT {emp_libro.rut}",
                valor_libro="No encontrado",
                valor_novedades=f"{reg_novedades.nombre_concepto_original}: {reg_novedades.monto}",
                concepto_afectado=reg_novedades.nombre_concepto_original
            ))
    
    # Conceptos en ambos - comparar montos
    for concepto_norm in dict_libro.keys() & dict_novedades.keys():
        reg_libro = dict_libro[concepto_norm]
        reg_novedades = dict_novedades[concepto_norm]
        
        # Comparar montos si ambos son numéricos
        if reg_libro.es_numerico and reg_novedades.es_numerico:
            if abs(reg_libro.monto_numerico - reg_novedades.monto_numerico) > 0.01:  # Tolerancia de 1 centavo
                discrepancias.append(DiscrepanciaCierre(
                    cierre=cierre,
                    tipo_discrepancia=TipoDiscrepancia.DIFERENCIA_CONCEPTO_MONTO,
                    empleado_libro=emp_libro,
                    empleado_novedades=emp_novedades,
                    rut_empleado=emp_libro.rut,
                    descripcion=f"Diferencia en monto del concepto '{reg_libro.nombre_concepto_original}' para RUT {emp_libro.rut}",
                    valor_libro=str(reg_libro.monto),
                    valor_novedades=str(reg_novedades.monto),
                    concepto_afectado=reg_libro.nombre_concepto_original
                ))
        elif str(reg_libro.monto) != str(reg_novedades.monto):
            # Si no son numéricos, comparar como texto
            discrepancias.append(DiscrepanciaCierre(
                cierre=cierre,
                tipo_discrepancia=TipoDiscrepancia.DIFERENCIA_CONCEPTO_MONTO,
                empleado_libro=emp_libro,
                empleado_novedades=emp_novedades,
                rut_empleado=emp_libro.rut,
                descripcion=f"Diferencia en valor del concepto '{reg_libro.nombre_concepto_original}' para RUT {emp_libro.rut}",
                valor_libro=str(reg_libro.monto),
                valor_novedades=str(reg_novedades.monto),
                concepto_afectado=reg_libro.nombre_concepto_original
            ))
    
    return discrepancias

def generar_discrepancias_movimientos_vs_analista(cierre):
    """Genera discrepancias comparando MovimientosMes vs Archivos del Analista"""
    discrepancias = []
    
    logger.info(f"Generando discrepancias MovimientosMes vs Analista para cierre {cierre.id}")
    
    try:
        # Comparar Ingresos
        discrepancias.extend(_comparar_ingresos(cierre))
        
        # Comparar Finiquitos
        discrepancias.extend(_comparar_finiquitos(cierre))
        
        # Comparar Ausentismos
        discrepancias.extend(_comparar_ausentismos(cierre))
        
    except Exception as e:
        logger.error(f"Error comparando MovimientosMes vs Analista: {e}")
        raise
    
    logger.info(f"Generadas {len(discrepancias)} discrepancias MovimientosMes vs Analista")
    return discrepancias

def _comparar_ingresos(cierre):
    """Compara ingresos entre MovimientosMes y Archivos del Analista"""
    discrepancias = []
    
    # Obtener ingresos de MovimientosMes (altas)
    movimientos_alta = MovimientoAltaBaja.objects.filter(cierre=cierre, alta_o_baja='ALTA')
    
    # Obtener ingresos reportados por el analista
    ingresos_analista = AnalistaIngreso.objects.filter(cierre=cierre)
    
    # Crear diccionarios por RUT normalizado
    dict_movimientos = {normalizar_rut(mov.rut): mov for mov in movimientos_alta}
    dict_analista = {normalizar_rut(ing.rut): ing for ing in ingresos_analista}
    
    # Ingresos en MovimientosMes no reportados por Analista
    for rut_norm, mov_alta in dict_movimientos.items():
        if rut_norm not in dict_analista:
            discrepancias.append(DiscrepanciaCierre(
                cierre=cierre,
                tipo_discrepancia=TipoDiscrepancia.INGRESO_NO_REPORTADO,
                rut_empleado=mov_alta.rut,
                descripcion=f"Ingreso de {mov_alta.nombres_apellidos} (RUT: {mov_alta.rut}) en MovimientosMes no reportado por Analista",
                valor_movimientos=f"Ingreso {mov_alta.fecha_ingreso}",
                valor_analista="No reportado"
            ))
    
    return discrepancias

def _comparar_finiquitos(cierre):
    """Compara finiquitos entre MovimientosMes y Archivos del Analista"""
    discrepancias = []
    
    # Obtener finiquitos de MovimientosMes (bajas)
    movimientos_baja = MovimientoAltaBaja.objects.filter(cierre=cierre, alta_o_baja='BAJA')
    
    # Obtener finiquitos reportados por el analista
    finiquitos_analista = AnalistaFiniquito.objects.filter(cierre=cierre)
    
    # Crear diccionarios por RUT normalizado
    dict_movimientos = {normalizar_rut(mov.rut): mov for mov in movimientos_baja}
    dict_analista = {normalizar_rut(fin.rut): fin for fin in finiquitos_analista}
    
    # Finiquitos en MovimientosMes no reportados por Analista
    for rut_norm, mov_baja in dict_movimientos.items():
        if rut_norm not in dict_analista:
            discrepancias.append(DiscrepanciaCierre(
                cierre=cierre,
                tipo_discrepancia=TipoDiscrepancia.FINIQUITO_NO_REPORTADO,
                rut_empleado=mov_baja.rut,
                descripcion=f"Finiquito de {mov_baja.nombres_apellidos} (RUT: {mov_baja.rut}) en MovimientosMes no reportado por Analista",
                valor_movimientos=f"Retiro {mov_baja.fecha_retiro}",
                valor_analista="No reportado"
            ))
    
    return discrepancias

def _comparar_ausentismos(cierre):
    """Compara ausentismos entre MovimientosMes y Archivos del Analista"""
    discrepancias = []
    
    # Obtener ausentismos de MovimientosMes
    movimientos_ausentismo = MovimientoAusentismo.objects.filter(cierre=cierre)
    
    # Obtener incidencias reportadas por el analista
    incidencias_analista = AnalistaIncidencia.objects.filter(cierre=cierre)
    
    # Crear diccionarios por RUT normalizado
    dict_movimientos = {normalizar_rut(mov.rut): mov for mov in movimientos_ausentismo}
    dict_analista = {normalizar_rut(inc.rut): inc for inc in incidencias_analista}
    
    # Ausentismos en MovimientosMes no reportados por Analista
    for rut_norm, mov_ausencia in dict_movimientos.items():
        if rut_norm not in dict_analista:
            discrepancias.append(DiscrepanciaCierre(
                cierre=cierre,
                tipo_discrepancia=TipoDiscrepancia.AUSENCIA_NO_REPORTADA,
                rut_empleado=mov_ausencia.rut,
                descripcion=f"Ausencia de {mov_ausencia.nombres_apellidos} (RUT: {mov_ausencia.rut}) en MovimientosMes no reportada por Analista",
                valor_movimientos=f"{mov_ausencia.tipo} ({mov_ausencia.fecha_inicio_ausencia} - {mov_ausencia.fecha_fin_ausencia})",
                valor_analista="No reportado"
            ))
        else:
            # Comparar detalles de ausentismo reportado
            inc_analista = dict_analista[rut_norm]
            
            # Comparar fechas
            if mov_ausencia.fecha_inicio_ausencia != inc_analista.fecha_inicio_ausencia or \
               mov_ausencia.fecha_fin_ausencia != inc_analista.fecha_fin_ausencia:
                discrepancias.append(DiscrepanciaCierre(
                    cierre=cierre,
                    tipo_discrepancia=TipoDiscrepancia.DIFERENCIA_FECHAS_AUSENCIA,
                    rut_empleado=mov_ausencia.rut,
                    descripcion=f"Diferencia en fechas de ausencia para {mov_ausencia.nombres_apellidos} (RUT: {mov_ausencia.rut})",
                    valor_movimientos=f"{mov_ausencia.fecha_inicio_ausencia} - {mov_ausencia.fecha_fin_ausencia}",
                    valor_analista=f"{inc_analista.fecha_inicio_ausencia} - {inc_analista.fecha_fin_ausencia}"
                ))
            
            # Comparar días
            if mov_ausencia.dias != inc_analista.dias:
                discrepancias.append(DiscrepanciaCierre(
                    cierre=cierre,
                    tipo_discrepancia=TipoDiscrepancia.DIFERENCIA_DIAS_AUSENCIA,
                    rut_empleado=mov_ausencia.rut,
                    descripcion=f"Diferencia en días de ausencia para {mov_ausencia.nombres_apellidos} (RUT: {mov_ausencia.rut})",
                    valor_movimientos=str(mov_ausencia.dias),
                    valor_analista=str(inc_analista.dias)
                ))
            
            # Comparar tipo de ausentismo
            if not textos_son_equivalentes(mov_ausencia.tipo, inc_analista.tipo_ausentismo):
                discrepancias.append(DiscrepanciaCierre(
                    cierre=cierre,
                    tipo_discrepancia=TipoDiscrepancia.DIFERENCIA_TIPO_AUSENCIA,
                    rut_empleado=mov_ausencia.rut,
                    descripcion=f"Diferencia en tipo de ausencia para {mov_ausencia.nombres_apellidos} (RUT: {mov_ausencia.rut})",
                    valor_movimientos=mov_ausencia.tipo,
                    valor_analista=inc_analista.tipo_ausentismo
                ))
    
    return discrepancias

def obtener_resumen_discrepancias(cierre):
    """Genera un resumen estadístico de las discrepancias de un cierre"""
    discrepancias = DiscrepanciaCierre.objects.filter(cierre=cierre)
    
    # Conteo total
    total_discrepancias = discrepancias.count()
    
    # Conteo por tipo
    discrepancias_por_tipo = {}
    for tipo in TipoDiscrepancia:
        count = discrepancias.filter(tipo_discrepancia=tipo.value).count()
        if count > 0:
            discrepancias_por_tipo[tipo.value] = {
                'count': count,
                'label': tipo.label
            }
    
    # Conteo por grupo
    libro_vs_novedades = [
        'empleado_solo_libro', 'empleado_solo_novedades', 'diff_datos_personales',
        'diff_sueldo_base', 'diff_concepto_monto', 'concepto_solo_libro', 'concepto_solo_novedades'
    ]
    
    total_libro_vs_novedades = discrepancias.filter(tipo_discrepancia__in=libro_vs_novedades).count()
    total_movimientos_vs_analista = total_discrepancias - total_libro_vs_novedades
    
    # Empleados únicos afectados
    empleados_afectados = discrepancias.values('rut_empleado').distinct().count()
    
    # Conceptos únicos afectados
    conceptos_afectados = list(
        discrepancias.exclude(concepto_afectado__isnull=True)
        .exclude(concepto_afectado='')
        .values_list('concepto_afectado', flat=True)
        .distinct()
    )
    
    # Top tipos de discrepancia
    top_tipos = []
    for tipo, info in sorted(discrepancias_por_tipo.items(), key=lambda x: x[1]['count'], reverse=True)[:5]:
        top_tipos.append({
            'tipo': tipo,
            'label': info['label'],
            'count': info['count']
        })
    
    return {
        'total_discrepancias': total_discrepancias,
        'discrepancias_por_tipo': discrepancias_por_tipo,
        'discrepancias_por_grupo': {
            'libro_vs_novedades': total_libro_vs_novedades,
            'movimientos_vs_analista': total_movimientos_vs_analista
        },
        'total_libro_vs_novedades': total_libro_vs_novedades,
        'total_movimientos_vs_analista': total_movimientos_vs_analista,
        'empleados_afectados': empleados_afectados,
        'conceptos_afectados': conceptos_afectados,
        'fecha_ultimo_analisis': timezone.now(),
        'top_tipos_discrepancia': top_tipos
    }
