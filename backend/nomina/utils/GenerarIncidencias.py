# backend/nomina/utils/GenerarIncidencias.py

import logging
import unicodedata
import re
from django.utils import timezone
from ..models import (
    CierreNomina, EmpleadoCierre, RegistroConceptoEmpleado,
    EmpleadoCierreNovedades, RegistroConceptoEmpleadoNovedades,
    MovimientoAltaBaja, MovimientoAusentismo, MovimientoVacaciones,
    AnalistaFiniquito, AnalistaIncidencia, AnalistaIngreso,
    IncidenciaCierre, TipoIncidencia, ResolucionIncidencia
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
    Ejemplos:
    - '12.345.678-9' -> '123456789'
    - '12345678-9' -> '123456789'
    - ' 12.345.678-9 ' -> '123456789'
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

def formatear_rut_con_guion(rut):
    """
    Formatea RUT agregando guión antes del dígito verificador
    Ejemplos:
    - '123456789' -> '12345678-9'
    - '12345678K' -> '12345678-K'
    - '12.345.678-9' -> '12345678-9' (primero normaliza, luego formatea)
    """
    if not rut:
        return ""
    
    # Primero normalizar para limpiar formato
    rut_limpio = normalizar_rut(rut)
    
    # Validar que tenga al menos 2 caracteres (número + dígito verificador)
    if len(rut_limpio) < 2:
        return rut_limpio
    
    # Separar número del dígito verificador
    numero = rut_limpio[:-1]
    digito_verificador = rut_limpio[-1]
    
    # Formatear con guión
    return f"{numero}-{digito_verificador}"

def ruts_son_equivalentes(rut1, rut2):
    """Compara si dos RUTs son equivalentes después de normalización"""
    return normalizar_rut(rut1) == normalizar_rut(rut2)

def generar_todas_incidencias(cierre):
    """Función principal para generar todas las incidencias de un cierre"""
    logger.info(f"Iniciando generación de incidencias para cierre {cierre.id}")
    
    # Limpiar incidencias anteriores si existen
    IncidenciaCierre.objects.filter(cierre=cierre).delete()
    
    incidencias_generadas = []
    
    try:
        # Grupo 1: Libro vs Novedades
        incidencias_libro_novedades = generar_incidencias_libro_vs_novedades(cierre)
        incidencias_generadas.extend(incidencias_libro_novedades)
        
        # Grupo 2: MovimientosMes vs Archivos Analista
        incidencias_movimientos_analista = generar_incidencias_movimientos_vs_analista(cierre)
        incidencias_generadas.extend(incidencias_movimientos_analista)
        
        # Guardar todas las incidencias
        if incidencias_generadas:
            IncidenciaCierre.objects.bulk_create(incidencias_generadas)
            logger.info(f"Generadas {len(incidencias_generadas)} incidencias para cierre {cierre.id}")
        else:
            logger.info(f"No se encontraron incidencias para cierre {cierre.id}")
        
        # Actualizar estado del cierre
        cierre.estado_incidencias = 'incidencias_generadas' if incidencias_generadas else 'aprobado'
        cierre.save(update_fields=['estado_incidencias'])
        
        return {
            'total_incidencias': len(incidencias_generadas),
            'libro_vs_novedades': len(incidencias_libro_novedades),
            'movimientos_vs_analista': len(incidencias_movimientos_analista),
            'cierre_id': cierre.id
        }
        
    except Exception as e:
        logger.error(f"Error generando incidencias para cierre {cierre.id}: {e}")
        raise

def generar_incidencias_libro_vs_novedades(cierre):
    """Compara Libro de Remuneraciones vs Novedades"""
    incidencias = []
    
    try:
        # 1. Obtener empleados de ambos lados con RUTs normalizados
        empleados_libro_raw = EmpleadoCierre.objects.filter(cierre=cierre)
        empleados_novedades_raw = EmpleadoCierreNovedades.objects.filter(cierre=cierre)
        
        # Crear diccionarios RUT_normalizado -> empleado original
        empleados_libro_dict = {}
        empleados_libro_normalizados = set()
        for emp in empleados_libro_raw:
            rut_norm = normalizar_rut(emp.rut)
            empleados_libro_dict[rut_norm] = emp
            empleados_libro_normalizados.add(rut_norm)
        
        empleados_novedades_dict = {}
        empleados_novedades_normalizados = set()
        for emp in empleados_novedades_raw:
            rut_norm = normalizar_rut(emp.rut)
            empleados_novedades_dict[rut_norm] = emp
            empleados_novedades_normalizados.add(rut_norm)
        
        # 2. Empleados solo en Libro - NO es incidencia, es normal
        # Los empleados pueden estar en el libro sin tener novedades
        solo_libro = empleados_libro_normalizados - empleados_novedades_normalizados
        logger.info(f"Empleados solo en Libro (normal): {len(solo_libro)}")
        # No se crean incidencias para empleados solo en libro
        
        # 3. Empleados solo en Novedades - SÍ es incidencia crítica
        # No deberían existir novedades para empleados que no están en el libro
        solo_novedades = empleados_novedades_normalizados - empleados_libro_normalizados
        for rut_normalizado in solo_novedades:
            empleado = empleados_novedades_dict[rut_normalizado]
            incidencias.append(IncidenciaCierre(
                cierre=cierre,
                tipo_incidencia=TipoIncidencia.EMPLEADO_SOLO_NOVEDADES,
                empleado_novedades=empleado,
                rut_empleado=empleado.rut,  # Usar RUT original
                descripcion=f"Empleado {empleado.nombre} {empleado.apellido_paterno} (RUT: {empleado.rut}) tiene novedades pero no existe en el Libro de Remuneraciones. Esto indica una inconsistencia crítica.",
                prioridad='critica',  # Crítico porque indica datos inconsistentes
                impacto_monetario=0  # Se puede calcular después si es necesario
            ))
        
        # 4. Comparar empleados comunes
        empleados_comunes = empleados_libro_normalizados & empleados_novedades_normalizados
        for rut_normalizado in empleados_comunes:
            emp_libro = empleados_libro_dict[rut_normalizado]
            emp_novedades = empleados_novedades_dict[rut_normalizado]
            incidencias.extend(_comparar_empleado_comun(cierre, rut_normalizado, emp_libro, emp_novedades))
        
        logger.info(f"Generadas {len(incidencias)} incidencias Libro vs Novedades")
        return incidencias
        
    except Exception as e:
        logger.error(f"Error en comparación Libro vs Novedades: {e}")
        return []

def _comparar_empleado_comun(cierre, rut_normalizado, emp_libro, emp_novedades):
    """Compara un empleado que existe en ambos lados"""
    incidencias = []
    
    try:
        # Comparar datos personales con normalización
        nombre_libro_norm = f"{emp_libro.nombre} {emp_libro.apellido_paterno}".strip()
        nombre_novedades_norm = f"{emp_novedades.nombre} {emp_novedades.apellido_paterno}".strip()
        
        if not textos_son_equivalentes(nombre_libro_norm, nombre_novedades_norm):
            incidencias.append(IncidenciaCierre(
                cierre=cierre,
                tipo_incidencia=TipoIncidencia.DIFERENCIA_DATOS_PERSONALES,
                empleado_libro=emp_libro,
                empleado_novedades=emp_novedades,
                rut_empleado=emp_libro.rut,  # Usar RUT original del libro
                descripcion=f"Diferencia en datos personales para {emp_libro.rut}",
                valor_libro=nombre_libro_norm,
                valor_novedades=nombre_novedades_norm,
                prioridad='baja'
            ))
        
        # Comparar sueldo base si ambos lo tienen
        if hasattr(emp_libro, 'sueldo_base') and hasattr(emp_novedades, 'sueldo_base'):
            if emp_libro.sueldo_base and emp_novedades.sueldo_base:
                if abs(float(emp_libro.sueldo_base) - float(emp_novedades.sueldo_base)) > 0.01:
                    incidencias.append(IncidenciaCierre(
                        cierre=cierre,
                        tipo_incidencia=TipoIncidencia.DIFERENCIA_SUELDO_BASE,
                        empleado_libro=emp_libro,
                        empleado_novedades=emp_novedades,
                        rut_empleado=emp_libro.rut,  # Usar RUT original del libro
                        descripcion=f"Diferencia en sueldo base para {emp_libro.nombre}",
                        valor_libro=str(emp_libro.sueldo_base),
                        valor_novedades=str(emp_novedades.sueldo_base),
                        prioridad='alta'
                    ))
        
        # Comparar conceptos por empleado
        incidencias.extend(_comparar_conceptos_empleado(cierre, emp_libro.rut, emp_libro, emp_novedades))
        
    except Exception as e:
        logger.error(f"Error comparando empleado {emp_libro.rut}: {e}")
    
    return incidencias

def _comparar_conceptos_empleado(cierre, rut, emp_libro, emp_novedades):
    """Compara conceptos de un empleado específico entre Libro y Novedades"""
    incidencias = []
    
    try:
        # Obtener registros de conceptos
        registros_libro = RegistroConceptoEmpleado.objects.filter(empleado=emp_libro)
        registros_novedades = RegistroConceptoEmpleadoNovedades.objects.filter(empleado=emp_novedades)
        
        # Crear diccionario de conceptos libro por concepto_id
        conceptos_libro = {}
        for registro in registros_libro:
            if registro.concepto:
                conceptos_libro[registro.concepto.id] = registro
        
        # Crear diccionario de conceptos novedades por concepto_libro_equivalente_id
        conceptos_novedades = {}
        for registro in registros_novedades:
            if hasattr(registro, 'concepto_libro_equivalente') and registro.concepto_libro_equivalente:
                conceptos_novedades[registro.concepto_libro_equivalente.id] = registro
        
        # Conceptos solo en libro - NO es incidencia, es normal
        # Los empleados pueden tener conceptos en el libro sin novedades
        solo_libro = set(conceptos_libro.keys()) - set(conceptos_novedades.keys())
        logger.debug(f"Conceptos solo en Libro para {rut} (normal): {len(solo_libro)}")
        # No se crean incidencias para conceptos solo en libro
        
        # Conceptos solo en novedades - SÍ es incidencia crítica
        # No deberían existir novedades para conceptos que no están en el libro
        solo_novedades = set(conceptos_novedades.keys()) - set(conceptos_libro.keys())
        for concepto_id in solo_novedades:
            registro = conceptos_novedades[concepto_id]
            incidencias.append(IncidenciaCierre(
                cierre=cierre,
                tipo_incidencia=TipoIncidencia.CONCEPTO_SOLO_NOVEDADES,
                empleado_novedades=emp_novedades,
                rut_empleado=rut,
                concepto_afectado=registro.concepto_libro_equivalente.nombre_concepto,
                descripcion=f"Concepto {registro.concepto_libro_equivalente.nombre_concepto} existe en Novedades pero no en Libro para {emp_novedades.nombre}. Esto indica una inconsistencia crítica.",
                valor_novedades=registro.monto,
                prioridad='critica'  # Crítico porque indica datos inconsistentes
            ))
        
        # Comparar conceptos comunes
        conceptos_comunes = set(conceptos_libro.keys()) & set(conceptos_novedades.keys())
        for concepto_id in conceptos_comunes:
            reg_libro = conceptos_libro[concepto_id]
            reg_novedades = conceptos_novedades[concepto_id]
            
            # Convertir montos a float para comparar
            try:
                if reg_libro.monto and reg_novedades.monto:
                    monto_libro = float(str(reg_libro.monto).replace(',', '').replace('$', '').strip())
                    monto_novedades = float(str(reg_novedades.monto).replace(',', '').replace('$', '').strip())
                    
                    if abs(monto_libro - monto_novedades) > 0.01:  # Tolerancia de 1 centavo
                        # Determinar prioridad basada en magnitud de diferencia
                        diferencia = abs(monto_libro - monto_novedades)
                        if diferencia > 100000:  # Más de $100k
                            prioridad = 'critica'
                        elif diferencia > 50000:  # Más de $50k
                            prioridad = 'alta'
                        elif diferencia > 10000:  # Más de $10k
                            prioridad = 'media'
                        else:
                            prioridad = 'baja'
                        
                        incidencias.append(IncidenciaCierre(
                            cierre=cierre,
                            tipo_incidencia=TipoIncidencia.DIFERENCIA_CONCEPTO_MONTO,
                            empleado_libro=emp_libro,
                            empleado_novedades=emp_novedades,
                            rut_empleado=rut,
                            concepto_afectado=reg_libro.concepto.nombre_concepto,
                            descripcion=f"Diferencia en {reg_libro.concepto.nombre_concepto} para {emp_libro.nombre}: ${diferencia:,.0f}",
                            valor_libro=reg_libro.monto,
                            valor_novedades=reg_novedades.monto,
                            prioridad=prioridad
                        ))
            except (ValueError, AttributeError, TypeError):
                # Error en conversión de montos - crear incidencia de formato
                incidencias.append(IncidenciaCierre(
                    cierre=cierre,
                    tipo_incidencia=TipoIncidencia.DIFERENCIA_CONCEPTO_MONTO,
                    empleado_libro=emp_libro,
                    empleado_novedades=emp_novedades,
                    rut_empleado=rut,
                    concepto_afectado=reg_libro.concepto.nombre_concepto,
                    descripcion=f"Error en formato de montos para {reg_libro.concepto.nombre_concepto} - {emp_libro.nombre}",
                    valor_libro=str(reg_libro.monto) if reg_libro.monto else 'N/A',
                    valor_novedades=str(reg_novedades.monto) if reg_novedades.monto else 'N/A',
                    prioridad='media'
                ))
    
    except Exception as e:
        logger.error(f"Error comparando conceptos para empleado {rut}: {e}")
    
    return incidencias

def generar_incidencias_movimientos_vs_analista(cierre):
    """Compara MovimientosMes vs Archivos del Analista"""
    incidencias = []
    
    try:
        # 1. Comparar Altas/Bajas vs Ingresos/Finiquitos
        incidencias.extend(_comparar_altas_bajas_vs_ingresos_finiquitos(cierre))
        
        # 2. Comparar Ausentismos vs Incidencias
        incidencias.extend(_comparar_ausentismos_vs_incidencias(cierre))
        
        logger.info(f"Generadas {len(incidencias)} incidencias Movimientos vs Analista")
        return incidencias
        
    except Exception as e:
        logger.error(f"Error en comparación Movimientos vs Analista: {e}")
        return []

def _comparar_altas_bajas_vs_ingresos_finiquitos(cierre):
    """Compara MovimientoAltaBaja vs AnalistaIngreso/AnalistaFiniquito"""
    incidencias = []
    
    try:
        # Obtener movimientos de altas y bajas
        altas_bajas = MovimientoAltaBaja.objects.filter(cierre=cierre)
        ingresos_analista = AnalistaIngreso.objects.filter(cierre=cierre)
        finiquitos_analista = AnalistaFiniquito.objects.filter(cierre=cierre)
        
        # Crear sets de RUTs normalizados por tipo
        ruts_ingresos_mov = set()
        for movimiento in altas_bajas.filter(alta_o_baja__iexact='ALTA'):
            ruts_ingresos_mov.add(normalizar_rut(movimiento.rut))
        
        ruts_finiquitos_mov = set()
        for movimiento in altas_bajas.filter(alta_o_baja__iexact='BAJA'):
            ruts_finiquitos_mov.add(normalizar_rut(movimiento.rut))
        
        ruts_ingresos_analista = set()
        for ingreso in ingresos_analista:
            ruts_ingresos_analista.add(normalizar_rut(ingreso.rut))
        
        ruts_finiquitos_analista = set()
        for finiquito in finiquitos_analista:
            ruts_finiquitos_analista.add(normalizar_rut(finiquito.rut))
        
        # Ingresos no reportados por analista
        ingresos_no_reportados = ruts_ingresos_mov - ruts_ingresos_analista
        for rut_normalizado in ingresos_no_reportados:
            # Buscar el movimiento que corresponde a este RUT normalizado
            movimiento = None
            for mov in altas_bajas.filter(alta_o_baja__iexact='ALTA'):
                if normalizar_rut(mov.rut) == rut_normalizado:
                    movimiento = mov
                    break
            
            if movimiento:
                incidencias.append(IncidenciaCierre(
                    cierre=cierre,
                    tipo_incidencia=TipoIncidencia.INGRESO_NO_REPORTADO,
                    rut_empleado=movimiento.rut,  # Usar RUT original
                    descripcion=f"Ingreso en MovimientosMes no reportado por Analista: {movimiento.nombres_apellidos}",
                    valor_movimientos=str(movimiento.fecha_ingreso),
                    prioridad='alta'
                ))
        
        # Finiquitos no reportados por analista
        finiquitos_no_reportados = ruts_finiquitos_mov - ruts_finiquitos_analista
        for rut_normalizado in finiquitos_no_reportados:
            # Buscar el movimiento que corresponde a este RUT normalizado
            movimiento = None
            for mov in altas_bajas.filter(alta_o_baja__iexact='BAJA'):
                if normalizar_rut(mov.rut) == rut_normalizado:
                    movimiento = mov
                    break
            
            if movimiento:
                incidencias.append(IncidenciaCierre(
                    cierre=cierre,
                    tipo_incidencia=TipoIncidencia.FINIQUITO_NO_REPORTADO,
                    rut_empleado=movimiento.rut,  # Usar RUT original
                    descripcion=f"Finiquito en MovimientosMes no reportado por Analista: {movimiento.nombres_apellidos}",
                    valor_movimientos=str(movimiento.fecha_retiro) if movimiento.fecha_retiro else 'N/A',
                    prioridad='critica'  # Finiquitos son críticos
                ))
        
    except Exception as e:
        logger.error(f"Error comparando altas/bajas vs ingresos/finiquitos: {e}")
    
    return incidencias

def _comparar_ausentismos_vs_incidencias(cierre):
    """Compara MovimientoAusentismo vs AnalistaIncidencia"""
    incidencias = []
    
    try:
        ausentismos_mov = MovimientoAusentismo.objects.filter(cierre=cierre)
        incidencias_analista = AnalistaIncidencia.objects.filter(cierre=cierre)
        
        # Crear diccionario de incidencias del analista por RUT normalizado
        incidencias_por_rut = {}
        for inc in incidencias_analista:
            rut_normalizado = normalizar_rut(inc.rut)
            if rut_normalizado not in incidencias_por_rut:
                incidencias_por_rut[rut_normalizado] = []
            incidencias_por_rut[rut_normalizado].append(inc)
        
        for ausentismo in ausentismos_mov:
            rut_ausentismo_normalizado = normalizar_rut(ausentismo.rut)
            incidencias_empleado = incidencias_por_rut.get(rut_ausentismo_normalizado, [])
            
            # Buscar coincidencia por fechas
            coincidencia_encontrada = False
            for inc_analista in incidencias_empleado:
                if (ausentismo.fecha_inicio_ausencia == inc_analista.fecha_inicio_ausencia and
                    ausentismo.fecha_fin_ausencia == inc_analista.fecha_fin_ausencia):
                    coincidencia_encontrada = True
                    
                    # Comparar días
                    if ausentismo.dias != inc_analista.dias:
                        incidencias.append(IncidenciaCierre(
                            cierre=cierre,
                            tipo_incidencia=TipoIncidencia.DIFERENCIA_DIAS_AUSENCIA,
                            rut_empleado=ausentismo.rut,
                            descripcion=f"Diferencia en días de ausencia para {ausentismo.nombres_apellidos}",
                            valor_movimientos=str(ausentismo.dias),
                            valor_analista=str(inc_analista.dias),
                            prioridad='media'
                        ))
                    
                    # Comparar tipo de ausentismo con normalización
                    if not textos_son_equivalentes(ausentismo.tipo, inc_analista.tipo_ausentismo):
                        incidencias.append(IncidenciaCierre(
                            cierre=cierre,
                            tipo_incidencia=TipoIncidencia.DIFERENCIA_TIPO_AUSENCIA,
                            rut_empleado=ausentismo.rut,
                            descripcion=f"Diferencia en tipo de ausencia para {ausentismo.nombres_apellidos}",
                            valor_movimientos=ausentismo.tipo,
                            valor_analista=inc_analista.tipo_ausentismo,
                            prioridad='baja'
                        ))
                    break
            
            # Si no se encontró coincidencia
            if not coincidencia_encontrada:
                incidencias.append(IncidenciaCierre(
                    cierre=cierre,
                    tipo_incidencia=TipoIncidencia.AUSENCIA_NO_REPORTADA,
                    rut_empleado=ausentismo.rut,
                    descripcion=f"Ausencia en MovimientosMes no reportada por Analista: {ausentismo.nombres_apellidos}",
                    valor_movimientos=f"{ausentismo.fecha_inicio_ausencia} - {ausentismo.fecha_fin_ausencia} ({ausentismo.tipo})",
                    prioridad='alta'
                ))
    
    except Exception as e:
        logger.error(f"Error comparando ausentismos vs incidencias: {e}")
    
    return incidencias

def obtener_resumen_incidencias(cierre):
    """Obtiene un resumen de incidencias por prioridad y estado"""
    incidencias = IncidenciaCierre.objects.filter(cierre=cierre)
    
    resumen = {
        'total': incidencias.count(),
        'por_prioridad': {
            'critica': incidencias.filter(prioridad='critica').count(),
            'alta': incidencias.filter(prioridad='alta').count(),
            'media': incidencias.filter(prioridad='media').count(),
            'baja': incidencias.filter(prioridad='baja').count(),
        },
        'por_estado': {
            'pendiente': incidencias.filter(estado='pendiente').count(),
            'resuelta_analista': incidencias.filter(estado='resuelta_analista').count(),
            'aprobada_supervisor': incidencias.filter(estado='aprobada_supervisor').count(),
            'rechazada_supervisor': incidencias.filter(estado='rechazada_supervisor').count(),
        },
        'impacto_monetario_total': sum(
            inc.impacto_monetario for inc in incidencias 
            if inc.impacto_monetario
        ) or 0
    }
    
    return resumen
