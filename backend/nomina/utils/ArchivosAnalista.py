import pandas as pd
import logging
from datetime import datetime, date

from nomina.models import (
    ArchivoAnalistaUpload, 
    EmpleadoCierre,
    AnalistaFiniquito,
    AnalistaIncidencia, 
    AnalistaIngreso
)
from .GenerarIncidencias import formatear_rut_con_guion, normalizar_rut

logger = logging.getLogger(__name__)

def validar_headers_finiquitos(df):
    """Valida que el archivo de finiquitos tenga los headers correctos"""
    expected_headers = ['Rut', 'Nombre', 'Fecha Retiro', 'Motivo']
    headers = list(df.columns)
    
    missing = [h for h in expected_headers if h not in headers]
    if missing:
        raise ValueError(f"Faltan columnas requeridas: {', '.join(missing)}")
    
    return True

def _normalizar_texto(s: str) -> str:
    """Normaliza texto para comparar headers (lower, sin tildes, colapsa espacios)."""
    import re
    import unicodedata
    if s is None:
        return ""
    s = str(s).strip().lower()
    s = ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
    s = re.sub(r"\s+", " ", s)
    return s


def _construir_mapeo_headers_incidencias(df):
    """
    Construye un mapeo de headers del archivo -> nombres canónicos esperados para incidencias.
    Acepta sinónimos y variaciones frecuentes.

    Retorna un dict con claves canónicas y valores de la columna real en el DataFrame.
    { 'Rut': <col_rut>, 'Nombre': <col_nombre>, 'Fecha Inicio Ausencia': <col_fi>, ... }
    """
    # Definir sinónimos por header canónico
    sinonimos = {
        'Rut': [
            'rut', 'r.u.t', 'r u t', 'identificador', 'id trabajador'
        ],
        'Nombre': [
            'nombre', 'nombres', 'nombres y apellidos', 'nombre completo'
        ],
        'Fecha Inicio Ausencia': [
            'fecha inicio ausencia', 'fecha inicio', 'inicio ausencia', 'fecha de inicio de ausencia',
            'fecha inicio ausentismo', 'fecha inicio de ausentismo', 'f. inicio'
        ],
        'Fecha Fin Ausencia': [
            'fecha fin ausencia', 'fecha fin', 'fin ausencia', 'fecha de fin de ausencia',
            'fecha fin ausentismo', 'fecha fin de ausentismo', 'f. fin'
        ],
        'Dias': [
            'dias', 'días', 'n dias', 'n días', 'cantidad dias', 'cant dias', 'cantidad de dias'
        ],
        'Tipo de Ausentismo': [
            'tipo de ausentismo', 'tipo ausentismo', 'ausentismo', 'motivo ausentismo', 'clase de ausentismo'
        ],
    }

    # Construir índice normalizado de columnas reales
    headers_reales = list(df.columns)
    normalizados = { _normalizar_texto(h): h for h in headers_reales }

    mapeo = {}
    faltantes = []

    for canonico, lista in sinonimos.items():
        # Asegurar que el canónico está incluido como su propio sinónimo
        candidatos = set(lista + [_normalizar_texto(canonico)])
        col_encontrada = None
        for cand in candidatos:
            if cand in normalizados:
                col_encontrada = normalizados[cand]
                break
        if col_encontrada:
            mapeo[canonico] = col_encontrada
        else:
            faltantes.append(canonico)

    if faltantes:
        raise ValueError(
            "Faltan columnas requeridas para incidencias: " + ", ".join(faltantes)
        )

    return mapeo


def validar_headers_incidencias(df):
    """Valida headers de incidencias de forma tolerante y retorna True si el mapeo es posible."""
    _ = _construir_mapeo_headers_incidencias(df)
    return True

def validar_headers_ingresos(df):
    """Valida que el archivo de ingresos tenga los headers correctos"""
    expected_headers = ['Rut', 'Nombre', 'Fecha Ingreso']
    headers = list(df.columns)
    
    missing = [h for h in expected_headers if h not in headers]
    if missing:
        raise ValueError(f"Faltan columnas requeridas: {', '.join(missing)}")
    
    return True

def limpiar_rut(rut_str):
    """Limpia y normaliza el RUT agregando guión si es necesario"""
    if pd.isna(rut_str):
        return ""
    
    # Usar la función de formateo para agregar guión
    rut_formateado = formatear_rut_con_guion(rut_str)
    return rut_formateado

def buscar_empleado_por_rut(cierre, rut):
    """Busca empleado por RUT considerando diferentes formatos"""
    # Normalizar el RUT de búsqueda
    rut_normalizado = normalizar_rut(rut)
    
    # Buscar empleados cuyo RUT normalizado coincida
    empleados = EmpleadoCierre.objects.filter(cierre=cierre)
    for empleado in empleados:
        if normalizar_rut(empleado.rut) == rut_normalizado:
            return empleado
    
    return None

def parsear_fecha(valor):
    """Convierte un valor de celda a date. Soporta Timestamp, datetime/date, string y serial Excel."""
    # NaN/None (manejo amplio con pd.isna)
    try:
        if valor is None or pd.isna(valor):
            return None
    except Exception:
        if valor is None:
            return None

    # Pandas Timestamp
    if isinstance(valor, pd.Timestamp):
        return valor.date()

    # datetime.datetime o datetime.date
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor

    # Números (posible serial de Excel)
    if isinstance(valor, (int, float)):
        try:
            # Excel usa 1899-12-30 como origin (en la mayoría de casos)
            return pd.to_datetime(valor, unit='d', origin='1899-12-30').date()
        except Exception:
            pass

    # Strings
    if isinstance(valor, str):
        s = valor.strip()
        if not s:
            return None
        # Intentar varios formatos comunes
        formatos = ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d', '%m/%d/%Y']
        for formato in formatos:
            try:
                return datetime.strptime(s, formato).date()
            except ValueError:
                continue
        # Último intento con pandas
        try:
            return pd.to_datetime(s, dayfirst=True, errors='raise').date()
        except Exception:
            raise ValueError(f"No se pudo parsear la fecha: {valor}")

    return None

def procesar_archivo_finiquitos_util(archivo):
    """Procesa un archivo de finiquitos y guarda los registros"""
    try:
        df = pd.read_excel(archivo.archivo.path, engine="openpyxl")
        validar_headers_finiquitos(df)
        
        cierre = archivo.cierre
        count = 0
        errores = []
        
        # Limpiar registros anteriores para este archivo
        AnalistaFiniquito.objects.filter(archivo_origen=archivo).delete()
        
        for index, row in df.iterrows():
            try:
                # Validar datos obligatorios
                rut = limpiar_rut(row.get('Rut', ''))
                if not rut:
                    errores.append(f"Fila {index + 2}: RUT vacío")
                    continue
                
                nombre = str(row.get('Nombre', '')).strip()
                if not nombre:
                    errores.append(f"Fila {index + 2}: Nombre vacío")
                    continue
                
                fecha_retiro = parsear_fecha(row.get('Fecha Retiro'))
                if not fecha_retiro:
                    errores.append(f"Fila {index + 2}: Fecha Retiro inválida")
                    continue
                
                motivo = str(row.get('Motivo', '')).strip()
                
                # Buscar empleado asociado usando normalización de RUT
                empleado = buscar_empleado_por_rut(cierre, rut)
                
                # Crear registro
                AnalistaFiniquito.objects.create(
                    cierre=cierre,
                    empleado=empleado,
                    archivo_origen=archivo,
                    rut=rut,
                    nombre=nombre,
                    fecha_retiro=fecha_retiro,
                    motivo=motivo
                )
                count += 1
                
            except Exception as e:
                errores.append(f"Fila {index + 2}: {str(e)}")
                continue
        
        logger.info(f"Procesados {count} finiquitos desde archivo {archivo.id}")
        
        if errores:
            logger.warning(f"Errores en procesamiento: {errores}")
            return {"procesados": count, "errores": errores}
        
        return {"procesados": count, "errores": []}
        
    except Exception as e:
        logger.error(f"Error procesando archivo de finiquitos {archivo.id}: {e}")
        raise

def procesar_archivo_incidencias_util(archivo):
    """Procesa un archivo de incidencias y guarda los registros"""
    try:
        df = pd.read_excel(archivo.archivo.path, engine="openpyxl")
        # Construir mapeo tolerante de headers
        mapeo = _construir_mapeo_headers_incidencias(df)
        
        cierre = archivo.cierre
        count = 0
        errores = []
        
        # Limpiar registros anteriores para este archivo
        AnalistaIncidencia.objects.filter(archivo_origen=archivo).delete()
        
        for index, row in df.iterrows():
            try:
                # Validar datos obligatorios
                rut = limpiar_rut(row.get(mapeo['Rut'], ''))
                if not rut:
                    errores.append(f"Fila {index + 2}: RUT vacío")
                    continue
                
                nombre = str(row.get(mapeo['Nombre'], '')).strip()
                if not nombre:
                    errores.append(f"Fila {index + 2}: Nombre vacío")
                    continue
                
                fecha_inicio = parsear_fecha(row.get(mapeo['Fecha Inicio Ausencia']))
                if not fecha_inicio:
                    errores.append(f"Fila {index + 2}: Fecha Inicio Ausencia inválida")
                    continue
                
                fecha_fin = parsear_fecha(row.get(mapeo['Fecha Fin Ausencia']))
                if not fecha_fin:
                    errores.append(f"Fila {index + 2}: Fecha Fin Ausencia inválida")
                    continue
                
                # Validar días
                try:
                    dias_raw = row.get(mapeo['Dias'], 0)
                    if pd.isna(dias_raw) or dias_raw == "":
                        raise ValueError("vacío")
                    # Si viene como float/str con decimales, castear con cuidado
                    if isinstance(dias_raw, float):
                        dias = int(round(dias_raw))
                    else:
                        dias = int(str(dias_raw).strip())
                except (ValueError, TypeError):
                    errores.append(f"Fila {index + 2}: Días debe ser un número entero")
                    continue
                
                tipo_ausentismo = str(row.get(mapeo['Tipo de Ausentismo'], '')).strip()
                if not tipo_ausentismo:
                    errores.append(f"Fila {index + 2}: Tipo de Ausentismo vacío")
                    continue
                
                # Buscar empleado asociado usando normalización de RUT
                empleado = buscar_empleado_por_rut(cierre, rut)
                
                # Crear registro
                AnalistaIncidencia.objects.create(
                    cierre=cierre,
                    empleado=empleado,
                    archivo_origen=archivo,
                    rut=rut,
                    nombre=nombre,
                    fecha_inicio_ausencia=fecha_inicio,
                    fecha_fin_ausencia=fecha_fin,
                    dias=dias,
                    tipo_ausentismo=tipo_ausentismo
                )
                count += 1
                
            except Exception as e:
                errores.append(f"Fila {index + 2}: {str(e)}")
                continue
        
        logger.info(f"Procesadas {count} incidencias desde archivo {archivo.id}")
        
        if errores:
            logger.warning(f"Errores en procesamiento: {errores}")
            return {"procesados": count, "errores": errores}
        
        return {"procesados": count, "errores": []}
        
    except Exception as e:
        logger.error(f"Error procesando archivo de incidencias {archivo.id}: {e}")
        raise

def procesar_archivo_ingresos_util(archivo):
    """Procesa un archivo de ingresos y guarda los registros"""
    try:
        df = pd.read_excel(archivo.archivo.path, engine="openpyxl")
        validar_headers_ingresos(df)
        
        cierre = archivo.cierre
        count = 0
        errores = []
        
        # Limpiar registros anteriores para este archivo
        AnalistaIngreso.objects.filter(archivo_origen=archivo).delete()
        
        for index, row in df.iterrows():
            try:
                # Validar datos obligatorios
                rut = limpiar_rut(row.get('Rut', ''))
                if not rut:
                    errores.append(f"Fila {index + 2}: RUT vacío")
                    continue
                
                nombre = str(row.get('Nombre', '')).strip()
                if not nombre:
                    errores.append(f"Fila {index + 2}: Nombre vacío")
                    continue
                
                fecha_ingreso = parsear_fecha(row.get('Fecha Ingreso'))
                if not fecha_ingreso:
                    errores.append(f"Fila {index + 2}: Fecha Ingreso inválida")
                    continue
                
                # Buscar empleado asociado usando normalización de RUT
                empleado = buscar_empleado_por_rut(cierre, rut)
                
                # Crear registro
                AnalistaIngreso.objects.create(
                    cierre=cierre,
                    empleado=empleado,
                    archivo_origen=archivo,
                    rut=rut,
                    nombre=nombre,
                    fecha_ingreso=fecha_ingreso
                )
                count += 1
                
            except Exception as e:
                errores.append(f"Fila {index + 2}: {str(e)}")
                continue
        
        logger.info(f"Procesados {count} ingresos desde archivo {archivo.id}")
        
        if errores:
            logger.warning(f"Errores en procesamiento: {errores}")
            return {"procesados": count, "errores": errores}
        
        return {"procesados": count, "errores": []}
        
    except Exception as e:
        logger.error(f"Error procesando archivo de ingresos {archivo.id}: {e}")
        raise

def procesar_archivo_analista_util(archivo):
    """Función principal que procesa cualquier tipo de archivo del analista"""
    # Normalizar tipo y aceptar alias comunes
    tipo = (archivo.tipo_archivo or '').strip().lower()
    if tipo == 'ausentismos':
        tipo = 'incidencias'
    
    if tipo == 'finiquitos':
        return procesar_archivo_finiquitos_util(archivo)
    elif tipo == 'incidencias':
        return procesar_archivo_incidencias_util(archivo)
    elif tipo == 'ingresos':
        return procesar_archivo_ingresos_util(archivo)
    else:
        raise ValueError(f"Tipo de archivo no soportado: {tipo}")
