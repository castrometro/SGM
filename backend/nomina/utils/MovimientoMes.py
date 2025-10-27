import pandas as pd
import logging
from datetime import datetime
from datetime import datetime
from typing import Dict, List, Tuple, Any
from django.utils.dateparse import parse_date
from ..models import (
    MovimientosMesUpload,
    MovimientoAltaBaja,
    MovimientoAusentismo,
    MovimientoVacaciones,
    MovimientoVariacionSueldo,
    MovimientoVariacionContrato,
    EmpleadoCierre,
)

logger = logging.getLogger(__name__)

# Definición de headers esperados para cada hoja
HEADERS_ESPERADOS = {
    'altas_bajas': [
        'NOMBRE', 'RUT', 'EMPRESA', 'CARGO', 'CENTRO DE COSTO', 'SUCURSAL', 'FECHA INGRESO',
        'FECHA RETIRO', 'TIPO CONTRATO', 'DIAS TRABAJADOS', 'SUELDO BASE', 'ALTA / BAJA', 'MOTIVO'
    ],
    'ausentismos': [
        'NOMBRE', 'RUT', 'EMPRESA', 'CARGO', 'CENTRO DE COSTO',
        'SUCURSAL', 'FECHA INICIO AUSENCIA', 'FECHA FIN AUSENCIA',
        'DIAS', 'TIPO DE AUSENTISMO', 'MOTIVO', 'OBSERVACIONES'
    ],
    'vacaciones': [
        'NOMBRE', 'RUT', 'EMPRESA', 'CARGO', 'CENTRO DE COSTO',
        'SUCURSAL', 'FECHA INGRESO', 'FECHA INICIAL', 'FECHA FIN VACACIONES',
        'FECHA RETORNO', 'CANTIDAD DE DIAS'
    ],
    'variaciones_sueldo': [
        'NOMBRE', 'RUT', 'EMPRESA', 'CARGO', 'CENTRO DE COSTO',
        'SUCURSAL', 'FECHA INGRESO', 'TIPO CONTRATO', 'SUELDO BASE ANTERIOR',
        'SUELDO BASE ACTUAL', '% DE REAJUSTE', 'VARIACIÓN ($)'
    ],
    'variaciones_contrato': [
        'NOMBRE', 'RUT', 'EMPRESA', 'CARGO', 'CENTRO DE COSTO',
        'SUCURSAL', 'FECHA INGRESO', 'TIPO CONTRATO ANTERIOR', 'TIPO CONTRATO ACTUAL'
    ]
}

def leer_archivo_movimientos_mes(archivo_path: str) -> Dict[str, pd.DataFrame]:
    """
    Lee el archivo Excel de movimientos del mes y retorna un diccionario con DataFrames
    para cada hoja. Los headers están siempre en la fila 3 (índice 2).
    """
    try:
        # Leer todas las hojas del archivo Excel con headers en fila 3 (índice 2)
        hojas = pd.read_excel(archivo_path, sheet_name=None, engine='openpyxl', header=2)
        
        logger.info(f"Hojas encontradas en el archivo: {list(hojas.keys())}")
        
        hojas_procesadas = {}
        
        for nombre_hoja, df in hojas.items():
            # Limpiar solo filas completamente vacías, pero ser más cuidadoso con columnas
            df = df.dropna(how='all')  # Eliminar filas completamente vacías
            
            if not df.empty:
                # Normalizar headers sin eliminar columnas aún
                headers_limpios = []
                for col in df.columns:
                    if pd.notna(col):
                        header_limpio = str(col).strip().upper()
                        # Limpiar caracteres especiales como "|"
                        header_limpio = header_limpio.replace("|", "").replace("Unnamed:", "COLUMNA")
                        headers_limpios.append(header_limpio)
                    else:
                        headers_limpios.append(f"COLUMNA_{len(headers_limpios)}")
                
                df.columns = headers_limpios
                
                # Solo eliminar columnas que son completamente NaN Y no tienen header válido
                columnas_a_mantener = []
                for col in df.columns:
                    if col.startswith('COLUMNA_') and df[col].isna().all():
                        continue  # Eliminar columnas sin header válido que están vacías
                    else:
                        columnas_a_mantener.append(col)
                
                df = df[columnas_a_mantener]
                df = df.reset_index(drop=True)  # Resetear índices
                
                hojas_procesadas[nombre_hoja.strip().lower()] = df
                logger.info(f"Hoja '{nombre_hoja}' procesada con {len(df.columns)} columnas: {df.columns.tolist()}")
        
        return hojas_procesadas
        
    except Exception as e:
        logger.error(f"Error leyendo archivo de movimientos: {e}")
        raise

def validar_headers_hoja(df: pd.DataFrame, headers_esperados: List[str], nombre_hoja: str) -> Tuple[bool, List[str]]:
    """
    Valida que una hoja tenga los headers esperados.
    Retorna (es_valida, headers_faltantes)
    """
    headers_actuales = list(df.columns)
    headers_faltantes = []
    
    for header in headers_esperados:
        if header not in headers_actuales:
            headers_faltantes.append(header)
    
    es_valida = len(headers_faltantes) == 0
    
    if not es_valida:
        logger.warning(f"Hoja '{nombre_hoja}' - Headers faltantes: {headers_faltantes}")
    
    return es_valida, headers_faltantes

def limpiar_rut(rut: str) -> str:
    """Limpia y normaliza un RUT"""
    if pd.isna(rut) or rut is None:
        return ""
    
    rut_str = str(rut).strip().replace(".", "").replace("-", "").upper()
    # Asegurar que el dígito verificador esté separado
    if len(rut_str) > 1 and rut_str[-1].isalpha():
        return f"{rut_str[:-1]}-{rut_str[-1]}"
    elif len(rut_str) > 1:
        return f"{rut_str[:-1]}-{rut_str[-1]}"
    return rut_str

def convertir_fecha(fecha_valor: Any) -> Any:
    """Convierte un valor a fecha, manejando diferentes formatos"""
    if pd.isna(fecha_valor) or fecha_valor is None:
        return None
    
    if isinstance(fecha_valor, datetime):
        return fecha_valor.date()
    
    # Manejar pandas Timestamp (que viene de Excel)
    if hasattr(fecha_valor, 'to_pydatetime'):
        # Convertir Timestamp a datetime y luego a date
        # Esto evita problemas de timezone que causan el bug de "un día menos"
        return fecha_valor.to_pydatetime().date()
    
    if isinstance(fecha_valor, str):
        try:
            return parse_date(fecha_valor)
        except:
            return None
    
    return None

def convertir_decimal(valor: Any) -> float:
    """Convierte un valor a decimal/float"""
    if pd.isna(valor) or valor is None:
        return 0.0
    
    try:
        # Limpiar el valor si es string
        if isinstance(valor, str):
            valor = valor.replace(",", "").replace("$", "").replace("%", "").strip()
        return float(valor)
    except:
        return 0.0

def convertir_entero(valor: Any) -> int:
    """Convierte un valor a entero"""
    if pd.isna(valor) or valor is None:
        return 0
    
    try:
        return int(float(valor))
    except:
        return 0

def buscar_empleado_por_rut(rut: str, cierre) -> EmpleadoCierre:
    """Busca un empleado en el cierre por RUT"""
    try:
        return EmpleadoCierre.objects.get(cierre=cierre, rut=rut)
    except EmpleadoCierre.DoesNotExist:
        return None

def procesar_altas_bajas(df: pd.DataFrame, cierre) -> int:
    """Procesa la hoja de Altas y Bajas"""
    contador = 0
    
    # Limpiar registros anteriores de este cierre
    MovimientoAltaBaja.objects.filter(cierre=cierre).delete()
    
    for index, row in df.iterrows():
        try:
            rut_limpio = limpiar_rut(row.get('RUT', ''))
            if not rut_limpio:
                logger.warning(f"Fila {index}: RUT vacío o inválido")
                continue
            
            empleado = buscar_empleado_por_rut(rut_limpio, cierre)
            
            MovimientoAltaBaja.objects.create(
                cierre=cierre,
                empleado=empleado,
                nombres_apellidos=str(row.get('NOMBRE', '')).strip(),
                rut=rut_limpio,
                empresa_nombre=str(row.get('EMPRESA', '')).strip(),
                cargo=str(row.get('CARGO', '')).strip(),
                centro_de_costo=str(row.get('CENTRO DE COSTO', '')).strip(),
                sucursal=str(row.get('SUCURSAL', '')).strip(),
                fecha_ingreso=convertir_fecha(row.get('FECHA INGRESO')),
                fecha_retiro=convertir_fecha(row.get('FECHA RETIRO')),
                tipo_contrato=str(row.get('TIPO CONTRATO', '')).strip(),
                dias_trabajados=convertir_entero(row.get('DIAS TRABAJADOS')),
                sueldo_base=convertir_decimal(row.get('SUELDO BASE')),
                alta_o_baja=str(row.get('ALTA / BAJA', '')).strip().upper(),
                motivo=str(row.get('MOTIVO', '')).strip()  # Campo opcional
            )
            contador += 1
            
        except Exception as e:
            logger.error(f"Error procesando fila {index} de Altas/Bajas: {e}")
            continue
    
    logger.info(f"Procesados {contador} registros de Altas/Bajas")
    return contador

def procesar_ausentismos(df: pd.DataFrame, cierre) -> int:
    """Procesa la hoja de Ausentismos"""
    contador = 0
    
    # Limpiar registros anteriores de este cierre
    MovimientoAusentismo.objects.filter(cierre=cierre).delete()
    
    for index, row in df.iterrows():
        try:
            rut_limpio = limpiar_rut(row.get('RUT', ''))
            if not rut_limpio:
                logger.warning(f"Fila {index}: RUT vacío o inválido")
                continue
            
            empleado = buscar_empleado_por_rut(rut_limpio, cierre)
            
            MovimientoAusentismo.objects.create(
                cierre=cierre,
                empleado=empleado,
                nombres_apellidos=str(row.get('NOMBRE', '')).strip(),
                rut=rut_limpio,
                empresa_nombre=str(row.get('EMPRESA', '')).strip(),
                cargo=str(row.get('CARGO', '')).strip(),
                centro_de_costo=str(row.get('CENTRO DE COSTO', '')).strip(),
                sucursal=str(row.get('SUCURSAL', '')).strip(),
                fecha_inicio_ausencia=convertir_fecha(row.get('FECHA INICIO AUSENCIA')),
                fecha_fin_ausencia=convertir_fecha(row.get('FECHA FIN AUSENCIA')),
                dias=convertir_entero(row.get('DIAS')),
                tipo=str(row.get('TIPO DE AUSENTISMO', '')).strip(),
                motivo=str(row.get('MOTIVO', '')).strip(),
                observaciones=str(row.get('OBSERVACIONES', '')).strip()
            )
            contador += 1
            
        except Exception as e:
            logger.error(f"Error procesando fila {index} de Ausentismos: {e}")
            continue
    
    logger.info(f"Procesados {contador} registros de Ausentismos")
    return contador

def procesar_vacaciones(df: pd.DataFrame, cierre) -> int:
    """Procesa la hoja de Vacaciones"""
    contador = 0
    
    # Limpiar registros anteriores de este cierre
    MovimientoVacaciones.objects.filter(cierre=cierre).delete()
    
    for index, row in df.iterrows():
        try:
            rut_limpio = limpiar_rut(row.get('RUT', ''))
            if not rut_limpio:
                logger.warning(f"Fila {index}: RUT vacío o inválido")
                continue
            
            empleado = buscar_empleado_por_rut(rut_limpio, cierre)
            
            MovimientoVacaciones.objects.create(
                cierre=cierre,
                empleado=empleado,
                nombres_apellidos=str(row.get('NOMBRE', '')).strip(),
                rut=rut_limpio,
                empresa_nombre=str(row.get('EMPRESA', '')).strip(),
                cargo=str(row.get('CARGO', '')).strip(),
                centro_de_costo=str(row.get('CENTRO DE COSTO', '')).strip(),
                sucursal=str(row.get('SUCURSAL', '')).strip(),
                fecha_ingreso=convertir_fecha(row.get('FECHA INGRESO')),
                fecha_inicio=convertir_fecha(row.get('FECHA INICIAL')),
                fecha_fin_vacaciones=convertir_fecha(row.get('FECHA FIN VACACIONES')),
                fecha_retorno=convertir_fecha(row.get('FECHA RETORNO')),
                cantidad_dias=convertir_entero(row.get('CANTIDAD DE DIAS'))
            )
            contador += 1
            
        except Exception as e:
            logger.error(f"Error procesando fila {index} de Vacaciones: {e}")
            continue
    
    logger.info(f"Procesados {contador} registros de Vacaciones")
    return contador

def procesar_variaciones_sueldo(df: pd.DataFrame, cierre) -> int:
    """Procesa la hoja de Variaciones Sueldo Base"""
    contador = 0
    
    # Limpiar registros anteriores de este cierre
    MovimientoVariacionSueldo.objects.filter(cierre=cierre).delete()
    
    for index, row in df.iterrows():
        try:
            rut_limpio = limpiar_rut(row.get('RUT', ''))
            if not rut_limpio:
                logger.warning(f"Fila {index}: RUT vacío o inválido")
                continue
            
            empleado = buscar_empleado_por_rut(rut_limpio, cierre)
            
            MovimientoVariacionSueldo.objects.create(
                cierre=cierre,
                empleado=empleado,
                nombres_apellidos=str(row.get('NOMBRE', '')).strip(),
                rut=rut_limpio,
                empresa_nombre=str(row.get('EMPRESA', '')).strip(),
                cargo=str(row.get('CARGO', '')).strip(),
                centro_de_costo=str(row.get('CENTRO DE COSTO', '')).strip(),
                sucursal=str(row.get('SUCURSAL', '')).strip(),
                fecha_ingreso=convertir_fecha(row.get('FECHA INGRESO')),
                tipo_contrato=str(row.get('TIPO CONTRATO', '')).strip(),
                sueldo_base_anterior=convertir_decimal(row.get('SUELDO BASE ANTERIOR')),
                sueldo_base_actual=convertir_decimal(row.get('SUELDO BASE ACTUAL')),
                porcentaje_reajuste=convertir_decimal(row.get('% DE REAJUSTE')),
                variacion_pesos=convertir_decimal(row.get('VARIACIÓN ($)'))
            )
            contador += 1
            
        except Exception as e:
            logger.error(f"Error procesando fila {index} de Variaciones Sueldo: {e}")
            continue
    
    logger.info(f"Procesados {contador} registros de Variaciones Sueldo")
    return contador

def procesar_variaciones_contrato(df: pd.DataFrame, cierre) -> int:
    """Procesa la hoja de Variaciones Tipo Contrato"""
    contador = 0
    
    # Limpiar registros anteriores de este cierre
    MovimientoVariacionContrato.objects.filter(cierre=cierre).delete()
    
    for index, row in df.iterrows():
        try:
            rut_limpio = limpiar_rut(row.get('RUT', ''))
            if not rut_limpio:
                logger.warning(f"Fila {index}: RUT vacío o inválido")
                continue
            
            empleado = buscar_empleado_por_rut(rut_limpio, cierre)
            
            MovimientoVariacionContrato.objects.create(
                cierre=cierre,
                empleado=empleado,
                nombres_apellidos=str(row.get('NOMBRE', '')).strip(),
                rut=rut_limpio,
                empresa_nombre=str(row.get('EMPRESA', '')).strip(),
                cargo=str(row.get('CARGO', '')).strip(),
                centro_de_costo=str(row.get('CENTRO DE COSTO', '')).strip(),
                sucursal=str(row.get('SUCURSAL', '')).strip(),
                fecha_ingreso=convertir_fecha(row.get('FECHA INGRESO')),
                tipo_contrato_anterior=str(row.get('TIPO CONTRATO ANTERIOR', '')).strip(),
                tipo_contrato_actual=str(row.get('TIPO CONTRATO ACTUAL', '')).strip()
            )
            contador += 1
            
        except Exception as e:
            logger.error(f"Error procesando fila {index} de Variaciones Contrato: {e}")
            continue
    
    logger.info(f"Procesados {contador} registros de Variaciones Contrato")
    return contador

def procesar_archivo_movimientos_mes_util(movimiento_upload: MovimientosMesUpload) -> Dict[str, int]:
    """
    Función principal para procesar un archivo de movimientos del mes.
    Retorna un diccionario con el conteo de registros procesados por tipo.
    """
    archivo_path = movimiento_upload.archivo.path
    cierre = movimiento_upload.cierre
    
    logger.info(f"Iniciando procesamiento de archivo de movimientos: {archivo_path}")
    
    # Leer todas las hojas del archivo
    hojas = leer_archivo_movimientos_mes(archivo_path)
    
    resultados = {
        'altas_bajas': 0,
        'ausentismos': 0,
        'vacaciones': 0,
        'variaciones_sueldo': 0,
        'variaciones_contrato': 0,
        'errores': []
    }
    
    # Mapeo de nombres de hojas posibles a funciones de procesamiento
    mapeo_hojas = {
        'altas_bajas': ('altas_bajas', procesar_altas_bajas),
        'altasbajas': ('altas_bajas', procesar_altas_bajas),
        'altas y bajas': ('altas_bajas', procesar_altas_bajas),
        'ausentismos': ('ausentismos', procesar_ausentismos),
        'ausentismo': ('ausentismos', procesar_ausentismos),
        'vacaciones': ('vacaciones', procesar_vacaciones),
        'variaciones_sueldo': ('variaciones_sueldo', procesar_variaciones_sueldo),
        'variaciones sueldo': ('variaciones_sueldo', procesar_variaciones_sueldo),
        'variaciones de sueldo base': ('variaciones_sueldo', procesar_variaciones_sueldo),
        'variaciones_contrato': ('variaciones_contrato', procesar_variaciones_contrato),
        'variaciones contrato': ('variaciones_contrato', procesar_variaciones_contrato),
        'variaciones de tipo contrato': ('variaciones_contrato', procesar_variaciones_contrato),
    }
    
    # Procesar cada hoja encontrada
    for nombre_hoja, df in hojas.items():
        if df.empty:
            logger.warning(f"Hoja '{nombre_hoja}' está vacía, omitiendo...")
            continue
        
        # Buscar el mapeo correspondiente
        # FIX: Normalizar ambos lados de la comparación para evitar problemas con '_' vs ' '
        clave_encontrada = None
        nombre_hoja_normalizado = nombre_hoja.lower().replace('_', ' ').replace('-', ' ')
        
        for posible_nombre, (tipo, funcion) in mapeo_hojas.items():
            posible_nombre_normalizado = posible_nombre.replace('_', ' ').replace('-', ' ')
            if posible_nombre_normalizado in nombre_hoja_normalizado:
                clave_encontrada = (tipo, funcion)
                break
        
        if not clave_encontrada:
            logger.warning(f"Hoja '{nombre_hoja}' no reconocida, omitiendo...")
            continue
        
        tipo, funcion_procesamiento = clave_encontrada
        
        # Validar headers
        headers_esperados = HEADERS_ESPERADOS[tipo]
        es_valida, headers_faltantes = validar_headers_hoja(df, headers_esperados, nombre_hoja)
        
        if not es_valida:
            error_msg = f"Hoja '{nombre_hoja}' - Headers faltantes: {headers_faltantes}"
            resultados['errores'].append(error_msg)
            logger.error(error_msg)
            continue
        
        # Procesar la hoja
        try:
            count = funcion_procesamiento(df, cierre)
            resultados[tipo] = count
            logger.info(f"Hoja '{nombre_hoja}' procesada exitosamente: {count} registros")
        except Exception as e:
            error_msg = f"Error procesando hoja '{nombre_hoja}': {str(e)}"
            resultados['errores'].append(error_msg)
            logger.error(error_msg)
    
    total_procesados = sum([v for k, v in resultados.items() if k != 'errores'])
    logger.info(f"Procesamiento completado. Total de registros: {total_procesados}")
    
    return resultados