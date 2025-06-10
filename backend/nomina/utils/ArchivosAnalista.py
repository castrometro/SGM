import pandas as pd
import logging
from datetime import datetime

from nomina.models import (
    ArchivoAnalistaUpload, 
    EmpleadoCierre,
    AnalistaFiniquito,
    AnalistaIncidencia, 
    AnalistaIngreso
)

logger = logging.getLogger(__name__)

def validar_headers_finiquitos(df):
    """Valida que el archivo de finiquitos tenga los headers correctos"""
    expected_headers = ['Rut', 'Nombre', 'Fecha Retiro', 'Motivo']
    headers = list(df.columns)
    
    missing = [h for h in expected_headers if h not in headers]
    if missing:
        raise ValueError(f"Faltan columnas requeridas: {', '.join(missing)}")
    
    return True

def validar_headers_incidencias(df):
    """Valida que el archivo de incidencias tenga los headers correctos"""
    expected_headers = ['Rut', 'Nombre', 'Fecha Inicio Ausencia', 'Fecha Fin Ausencia', 'Dias', 'Tipo de Ausentismo']
    headers = list(df.columns)
    
    missing = [h for h in expected_headers if h not in headers]
    if missing:
        raise ValueError(f"Faltan columnas requeridas: {', '.join(missing)}")
    
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
    """Limpia y normaliza el RUT"""
    if pd.isna(rut_str):
        return ""
    
    rut = str(rut_str).strip().replace('.', '').replace('-', '').upper()
    return rut

def parsear_fecha(fecha_str):
    """Convierte string de fecha a objeto date"""
    if pd.isna(fecha_str):
        return None
    
    # Si ya es datetime, extraer solo la fecha
    if isinstance(fecha_str, pd.Timestamp):
        return fecha_str.date()
    
    # Si es string, intentar parsear
    if isinstance(fecha_str, str):
        # Intentar varios formatos
        formatos = ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d']
        for formato in formatos:
            try:
                return datetime.strptime(fecha_str.strip(), formato).date()
            except ValueError:
                continue
        raise ValueError(f"No se pudo parsear la fecha: {fecha_str}")
    
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
                
                # Buscar empleado asociado
                empleado = EmpleadoCierre.objects.filter(
                    cierre=cierre, 
                    rut=rut
                ).first()
                
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
        validar_headers_incidencias(df)
        
        cierre = archivo.cierre
        count = 0
        errores = []
        
        # Limpiar registros anteriores para este archivo
        AnalistaIncidencia.objects.filter(archivo_origen=archivo).delete()
        
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
                
                fecha_inicio = parsear_fecha(row.get('Fecha Inicio Ausencia'))
                if not fecha_inicio:
                    errores.append(f"Fila {index + 2}: Fecha Inicio Ausencia inválida")
                    continue
                
                fecha_fin = parsear_fecha(row.get('Fecha Fin Ausencia'))
                if not fecha_fin:
                    errores.append(f"Fila {index + 2}: Fecha Fin Ausencia inválida")
                    continue
                
                # Validar días
                try:
                    dias = int(row.get('Dias', 0))
                except (ValueError, TypeError):
                    errores.append(f"Fila {index + 2}: Días debe ser un número entero")
                    continue
                
                tipo_ausentismo = str(row.get('Tipo de Ausentismo', '')).strip()
                if not tipo_ausentismo:
                    errores.append(f"Fila {index + 2}: Tipo de Ausentismo vacío")
                    continue
                
                # Buscar empleado asociado
                empleado = EmpleadoCierre.objects.filter(
                    cierre=cierre, 
                    rut=rut
                ).first()
                
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
                
                # Buscar empleado asociado
                empleado = EmpleadoCierre.objects.filter(
                    cierre=cierre, 
                    rut=rut
                ).first()
                
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
    tipo = archivo.tipo_archivo
    
    if tipo == 'finiquitos':
        return procesar_archivo_finiquitos_util(archivo)
    elif tipo == 'incidencias':
        return procesar_archivo_incidencias_util(archivo)
    elif tipo == 'ingresos':
        return procesar_archivo_ingresos_util(archivo)
    else:
        raise ValueError(f"Tipo de archivo no soportado: {tipo}")
