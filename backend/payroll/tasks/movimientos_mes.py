# backend/payroll/tasks/movimientos_mes.py
# Tareas Celery para procesar archivos de movimientos del mes (Altas/Bajas y Ausentismo)

from celery import shared_task
from django.utils import timezone
from decimal import Decimal, InvalidOperation
import pandas as pd
import logging
import traceback
from datetime import datetime

from ..models.models_fase_1 import ArchivoSubido
from ..models.models_staging import AltasBajas_stg, Ausencias_stg

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def procesar_movimientos_mes(self, archivo_id):
    """
    Task principal que coordina el procesamiento de archivos de movimientos del mes.
    
    Proceso:
    1. Validar archivo Excel
    2. Procesar hoja "Altas y Bajas" → AltasBajas_stg
    3. Procesar hoja "Ausentismo" → Ausencias_stg
    4. Finalizar procesamiento
    
    Args:
        archivo_id (int): ID del archivo a procesar
        
    Returns:
        dict: Resultado del procesamiento
    """
    
    try:
        # Obtener el archivo
        archivo = ArchivoSubido.objects.get(id=archivo_id)
        
        logger.info(f"🚀 Iniciando procesamiento de movimientos del mes - Archivo {archivo_id}")
        
        # Actualizar estado a procesando
        archivo.estado_procesamiento = 'parseando'
        archivo.save()
        
        # Ejecutar tareas secuencialmente
        logger.info(f"🔍 Paso 1: Validando archivo - {archivo_id}")
        resultado_validacion = validar_archivo_movimientos(archivo_id)
        if not resultado_validacion.get('success', False):
            return resultado_validacion
        
        logger.info(f"👥 Paso 2: Procesando altas y bajas - {archivo_id}")
        resultado_altas_bajas = procesar_altas_bajas(archivo_id)
        if not resultado_altas_bajas.get('success', False):
            return resultado_altas_bajas
        
        logger.info(f"🏥 Paso 3: Procesando ausentismo - {archivo_id}")
        resultado_ausentismo = procesar_ausentismo(archivo_id)
        if not resultado_ausentismo.get('success', False):
            return resultado_ausentismo
        
        logger.info(f"🏁 Paso 4: Finalizando procesamiento - {archivo_id}")
        resultado_final = finalizar_procesamiento_movimientos(archivo_id)
        
        logger.info(f"✅ Procesamiento de movimientos completado - Archivo {archivo_id}")
        
        return resultado_final
        
    except ArchivoSubido.DoesNotExist:
        error_msg = f"Archivo {archivo_id} no encontrado"
        logger.error(f"❌ {error_msg}")
        return {'success': False, 'error': error_msg}
        
    except Exception as e:
        error_msg = f"Error en procesamiento de movimientos: {str(e)}"
        logger.error(f"❌ {error_msg}")
        logger.error(traceback.format_exc())
        
        # Actualizar estado de error
        try:
            archivo = ArchivoSubido.objects.get(id=archivo_id)
            archivo.estado_procesamiento = 'error'
            archivo.save()
        except:
            pass
            
        return {'success': False, 'error': error_msg}


@shared_task(bind=True)
def validar_archivo_movimientos(self, archivo_id):
    """
    Valida que el archivo Excel tenga las hojas necesarias y estructura correcta.
    
    Args:
        archivo_id (int): ID del archivo a validar
        
    Returns:
        dict: Resultado de la validación
    """
    
    try:
        archivo = ArchivoSubido.objects.get(id=archivo_id)
        
        logger.info(f"🔍 Validando archivo de movimientos - {archivo_id}")
        
        # Leer el Excel y verificar hojas
        excel_file = pd.ExcelFile(archivo.archivo.path)
        hojas_disponibles = excel_file.sheet_names
        
        logger.info(f"📋 Hojas encontradas: {hojas_disponibles}")
        
        # Verificar que existan las hojas necesarias
        hojas_requeridas = ['Altas y Bajas', 'Ausentismo']
        hojas_faltantes = []
        
        for hoja in hojas_requeridas:
            if hoja not in hojas_disponibles:
                # Buscar variaciones del nombre
                hoja_encontrada = False
                for hoja_disponible in hojas_disponibles:
                    if hoja.lower().replace(' ', '') in hoja_disponible.lower().replace(' ', ''):
                        logger.info(f"✅ Hoja '{hoja}' encontrada como '{hoja_disponible}'")
                        hoja_encontrada = True
                        break
                
                if not hoja_encontrada:
                    hojas_faltantes.append(hoja)
        
        if hojas_faltantes:
            error_msg = f"Hojas faltantes en el Excel: {hojas_faltantes}"
            logger.error(f"❌ {error_msg}")
            
            archivo.estado_procesamiento = 'error'
            archivo.errores_detectados = archivo.errores_detectados or []
            archivo.errores_detectados.append(error_msg)
            archivo.save()
            
            return {'success': False, 'error': error_msg}
        
        logger.info(f"✅ Validación exitosa - Archivo {archivo_id}")
        
        return {
            'success': True,
            'archivo_id': archivo_id,
            'hojas_encontradas': hojas_disponibles,
            'mensaje': 'Archivo validado correctamente'
        }
        
    except Exception as e:
        error_msg = f"Error validando archivo: {str(e)}"
        logger.error(f"❌ {error_msg}")
        return {'success': False, 'error': error_msg}


@shared_task(bind=True)
def procesar_altas_bajas(self, archivo_id):
    """
    Procesa la hoja "Altas y Bajas" del Excel y crea registros en AltasBajas_stg.
    
    Args:
        resultado_anterior (dict): Resultado de la tarea anterior
        archivo_id (int): ID del archivo a procesar
        
    Returns:
        dict: Resultado del procesamiento
    """
    
    try:
        archivo = ArchivoSubido.objects.get(id=archivo_id)
        
        logger.info(f"📊 Procesando hoja 'Altas y Bajas' - Archivo {archivo_id}")
        
        # Leer la hoja específica (headers en fila 3, índice 2)
        df = pd.read_excel(archivo.archivo.path, sheet_name='Altas y Bajas', header=2)
        
        logger.info(f"📋 Columnas encontradas: {list(df.columns)}")
        logger.info(f"📊 Filas a procesar: {len(df)}")
        
        # Limpiar el DataFrame
        df = df.dropna(how='all')  # Eliminar filas completamente vacías
        
        registros_creados = 0
        errores = []
        
        for index, row in df.iterrows():
            try:
                fila_excel = index + 4  # +4 porque: +1 para base 1, +3 para header en fila 3
                
                # Validar que tenga al menos RUT y nombre
                if pd.isna(row.get('Rut')) or pd.isna(row.get('Nombre')):
                    continue
                
                # Debug: verificar valor de Alta/Baja antes de crear el registro
                alta_baja_valor = str(row.get('Alta / Baja', '')).strip()
                logger.info(f"🔍 Fila {fila_excel}: Alta/Baja = '{alta_baja_valor}' (tipo: {type(row.get('Alta / Baja'))})")
                
                # Crear registro en staging
                alta_baja = AltasBajas_stg.objects.create(
                    archivo_subido=archivo,
                    fila_excel=fila_excel,
                    
                    # Datos principales
                    nombre=str(row.get('Nombre', '')).strip(),
                    rut=str(row.get('Rut', '')).strip(),
                    empresa=str(row.get('Empresa', '')).strip(),
                    cargo=str(row.get('Cargo', '')).strip(),
                    centro_de_costo=str(row.get('Centro de Costo', '')).strip(),
                    sucursal=str(row.get('Sucursal', '')).strip(),
                    
                    # Fechas
                    fecha_ingreso=_parsear_fecha(row.get('Fecha Ingreso')),
                    fecha_retiro=_parsear_fecha(row.get('Fecha Retiro')),
                    
                    # Datos laborales
                    tipo_contrato=str(row.get('Tipo Contrato', '')).strip(),
                    dias_trabajados=_parsear_entero(row.get('Dias Trabajados')),
                    sueldo_base=_parsear_decimal(row.get('Sueldo Base')),
                    alta_baja=alta_baja_valor,  # Usar la variable ya procesada
                    motivo=str(row.get('Motivo', '')).strip(),
                    
                    # Datos raw para debugging
                    fecha_ingreso_raw=str(row.get('Fecha Ingreso', '')),
                    fecha_retiro_raw=str(row.get('Fecha Retiro', '')),
                    dias_trabajados_raw=str(row.get('Dias Trabajados', '')),
                    sueldo_base_raw=str(row.get('Sueldo Base', ''))
                )
                
                registros_creados += 1
                
            except Exception as e:
                error_msg = f"Error en fila {fila_excel}: {str(e)}"
                errores.append(error_msg)
                logger.warning(f"⚠️ {error_msg}")
        
        logger.info(f"✅ Procesamiento de Altas y Bajas completado:")
        logger.info(f"   - Registros creados: {registros_creados}")
        logger.info(f"   - Errores: {len(errores)}")
        
        return {
            'success': True,
            'archivo_id': archivo_id,
            'tipo': 'altas_bajas',
            'registros_creados': registros_creados,
            'errores': errores,
            'mensaje': f'Procesadas {registros_creados} altas/bajas'
        }
        
    except Exception as e:
        error_msg = f"Error procesando Altas y Bajas: {str(e)}"
        logger.error(f"❌ {error_msg}")
        logger.error(traceback.format_exc())
        return {'success': False, 'error': error_msg}


@shared_task(bind=True) 
def procesar_ausentismo(self, archivo_id):
    """
    Procesa la hoja "Ausentismo" del Excel y crea registros en Ausencias_stg.
    
    Args:
        archivo_id (int): ID del archivo a procesar
        
    Returns:
        dict: Resultado del procesamiento
    """
    
    try:
        archivo = ArchivoSubido.objects.get(id=archivo_id)
        
        logger.info(f"📊 Procesando hoja 'Ausentismo' - Archivo {archivo_id}")
        
        # Leer la hoja específica (headers en fila 3, índice 2)
        df = pd.read_excel(archivo.archivo.path, sheet_name='Ausentismo', header=2)
        
        logger.info(f"📋 Columnas encontradas: {list(df.columns)}")
        logger.info(f"📊 Filas a procesar: {len(df)}")
        
        # Limpiar el DataFrame
        df = df.dropna(how='all')  # Eliminar filas completamente vacías
        
        registros_creados = 0
        errores = []
        
        for index, row in df.iterrows():
            try:
                fila_excel = index + 4  # +4 porque: +1 para base 1, +3 para header en fila 3
                
                # Validar que tenga al menos RUT y nombre
                if pd.isna(row.get('Rut')) or pd.isna(row.get('Nombre')):
                    continue
                
                # Crear registro en staging
                ausencia = Ausencias_stg.objects.create(
                    archivo_subido=archivo,
                    fila_excel=fila_excel,
                    
                    # Datos principales
                    nombre=str(row.get('Nombre', '')).strip(),
                    rut=str(row.get('Rut', '')).strip(),
                    empresa=str(row.get('Empresa', '')).strip(),
                    cargo=str(row.get('Cargo', '')).strip(),
                    centro_de_costo=str(row.get('Centro de Costo', '')).strip(),
                    sucursal=str(row.get('Sucursal', '')).strip(),
                    
                    # Datos de ausencia
                    fecha_inicio_ausencia=_parsear_fecha(row.get('Fecha Inicio Ausencia')),
                    fecha_fin_ausencia=_parsear_fecha(row.get('Fecha Fin Ausencia')),
                    dias=_parsear_entero(row.get('Dias')),
                    tipo_de_ausentismo=str(row.get('Tipo de Ausentismo', '')).strip(),
                    motivo=str(row.get('Motivo', '')).strip(),
                    observaciones=str(row.get('Observaciones', '')).strip(),
                    
                    # Datos raw para debugging
                    fecha_inicio_ausencia_raw=str(row.get('Fecha Inicio Ausencia', '')),
                    fecha_fin_ausencia_raw=str(row.get('Fecha Fin Ausencia', '')),
                    dias_raw=str(row.get('Dias', ''))
                )
                
                registros_creados += 1
                
            except Exception as e:
                error_msg = f"Error en fila {fila_excel}: {str(e)}"
                errores.append(error_msg)
                logger.warning(f"⚠️ {error_msg}")
        
        logger.info(f"✅ Procesamiento de Ausentismo completado:")
        logger.info(f"   - Registros creados: {registros_creados}")
        logger.info(f"   - Errores: {len(errores)}")
        
        return {
            'success': True,
            'archivo_id': archivo_id,
            'tipo': 'ausentismo',
            'registros_creados': registros_creados,
            'errores': errores,
            'mensaje': f'Procesadas {registros_creados} ausencias'
        }
        
    except Exception as e:
        error_msg = f"Error procesando Ausentismo: {str(e)}"
        logger.error(f"❌ {error_msg}")
        logger.error(traceback.format_exc())
        return {'success': False, 'error': error_msg}


@shared_task(bind=True)
def finalizar_procesamiento_movimientos(self, archivo_id):
    """
    Finaliza el procesamiento actualizando el estado del archivo.
    
    Args:
        archivo_id (int): ID del archivo procesado
        
    Returns:
        dict: Resultado final
    """
    
    try:
        archivo = ArchivoSubido.objects.get(id=archivo_id)
        
        # Contar registros creados
        total_altas_bajas = AltasBajas_stg.objects.filter(archivo_subido=archivo).count()
        total_ausencias = Ausencias_stg.objects.filter(archivo_subido=archivo).count()
        total_registros = total_altas_bajas + total_ausencias
        
        # Actualizar archivo
        archivo.estado_procesamiento = 'parsing_completo'
        archivo.registros_procesados = total_registros
        archivo.fecha_proceso = timezone.now()
        archivo.save()
        
        logger.info(f"🎉 Procesamiento finalizado - Archivo {archivo_id}")
        logger.info(f"   - Altas/Bajas: {total_altas_bajas}")
        logger.info(f"   - Ausencias: {total_ausencias}")
        logger.info(f"   - Total: {total_registros}")
        
        return {
            'success': True,
            'archivo_id': archivo_id,
            'estadisticas': {
                'altas_bajas': total_altas_bajas,
                'ausencias': total_ausencias,
                'total': total_registros
            },
            'mensaje': 'Procesamiento de movimientos del mes finalizado exitosamente'
        }
        
    except Exception as e:
        error_msg = f"Error finalizando procesamiento: {str(e)}"
        logger.error(f"❌ {error_msg}")
        return {'success': False, 'error': error_msg}


# =============================================================================
# FUNCIONES AUXILIARES
# =============================================================================

def _parsear_fecha(valor):
    """Parsea una fecha desde diferentes formatos"""
    if pd.isna(valor):
        return None
    
    if isinstance(valor, datetime):
        return valor.date()
    
    try:
        # Intentar parsear como string
        fecha_str = str(valor).strip()
        if not fecha_str or fecha_str.lower() in ['nan', 'nat', '']:
            return None
        
        # Intentar diferentes formatos
        formatos = ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d']
        
        for formato in formatos:
            try:
                return datetime.strptime(fecha_str, formato).date()
            except ValueError:
                continue
        
        logger.warning(f"⚠️ No se pudo parsear fecha: {valor}")
        return None
        
    except Exception as e:
        logger.warning(f"⚠️ Error parseando fecha {valor}: {e}")
        return None


def _parsear_entero(valor):
    """Parsea un valor entero"""
    if pd.isna(valor):
        return None
    
    try:
        return int(float(valor))
    except (ValueError, TypeError):
        logger.warning(f"⚠️ No se pudo parsear entero: {valor}")
        return None


def _parsear_decimal(valor):
    """Parsea un valor decimal/monetario"""
    if pd.isna(valor):
        return None
    
    try:
        # Limpiar el valor (quitar símbolos de moneda, comas, etc.)
        valor_str = str(valor).replace('$', '').replace(',', '').replace(' ', '').strip()
        
        if not valor_str or valor_str.lower() in ['nan', '']:
            return None
        
        return Decimal(valor_str)
        
    except (ValueError, TypeError, InvalidOperation):
        logger.warning(f"⚠️ No se pudo parsear decimal: {valor}")
        return None
