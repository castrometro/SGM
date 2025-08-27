# backend/payroll/tasks/archivos_analista.py
# Tareas Celery para procesar archivos del analista (Finiquitos, Ausentismos, Ingresos)

from celery import shared_task
from django.utils import timezone
from decimal import Decimal, InvalidOperation
import pandas as pd
import logging
import traceback
from datetime import datetime

from ..models.models_fase_1 import ArchivoSubido
from ..models.models_staging import Finiquitos_analista_stg, Ausentismos_analista_stg, Ingresos_analista_stg

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def procesar_finiquitos_analista(self, archivo_id):
    """
    Procesa el archivo de Finiquitos del Analista.
    Estructura esperada: Rut, Nombre, Fecha Retiro, Motivo
    Headers en la primera fila.
    
    Args:
        archivo_id (int): ID del archivo a procesar
        
    Returns:
        dict: Resultado del procesamiento
    """
    
    try:
        archivo = ArchivoSubido.objects.get(id=archivo_id)
        
        logger.info(f"🏢 Iniciando procesamiento de Finiquitos Analista - Archivo {archivo_id}")
        
        # Actualizar estado
        archivo.estado_procesamiento = 'parseando'
        archivo.save()
        
        # Leer Excel
        df = pd.read_excel(archivo.archivo.path, header=0)  # Headers en fila 1 (índice 0)
        
        logger.info(f"📋 Columnas encontradas en Finiquitos: {list(df.columns)}")
        logger.info(f"📊 Total de filas en Finiquitos: {len(df)}")
        
        # Mapeo de columnas (flexible para diferentes variaciones)
        column_mapping = {
            'rut': ['Rut', 'RUT', 'rut'],
            'nombre': ['Nombre', 'nombre', 'NOMBRE'],
            'fecha_retiro': ['Fecha Retiro', 'Fecha de Retiro', 'fecha_retiro', 'FECHA RETIRO'],
            'motivo': ['Motivo', 'motivo', 'MOTIVO', 'Motivo Retiro']
        }
        
        # Encontrar las columnas correctas
        columns_found = {}
        for field, possible_names in column_mapping.items():
            for name in possible_names:
                if name in df.columns:
                    columns_found[field] = name
                    break
            
            if field not in columns_found:
                logger.warning(f"⚠️ No se encontró columna para {field}. Columnas disponibles: {list(df.columns)}")
        
        # Limpiar DataFrame
        df = df.dropna(how='all')  # Eliminar filas completamente vacías
        
        registros_creados = 0
        errores = []
        
        for index, row in df.iterrows():
            try:
                fila_excel = index + 2  # +2 porque: +1 para base 1, +1 para header en fila 1
                
                # Extraer datos usando el mapeo
                rut_valor = row.get(columns_found.get('rut')) if 'rut' in columns_found else None
                nombre_valor = row.get(columns_found.get('nombre')) if 'nombre' in columns_found else None
                
                # Validar que tenga al menos RUT y nombre
                if pd.isna(rut_valor) or pd.isna(nombre_valor):
                    continue
                
                # Procesar fecha de retiro
                fecha_retiro_valor = None
                if 'fecha_retiro' in columns_found:
                    fecha_raw = row.get(columns_found['fecha_retiro'])
                    if pd.notna(fecha_raw):
                        try:
                            if isinstance(fecha_raw, str):
                                fecha_retiro_valor = pd.to_datetime(fecha_raw).date()
                            else:
                                fecha_retiro_valor = fecha_raw.date() if hasattr(fecha_raw, 'date') else fecha_raw
                        except:
                            logger.warning(f"⚠️ Error parseando fecha retiro en fila {fila_excel}: {fecha_raw}")
                
                # Crear registro en staging
                finiquito = Finiquitos_analista_stg.objects.create(
                    archivo_subido=archivo,
                    fila_excel=fila_excel,
                    
                    # Datos principales
                    rut=str(rut_valor).strip(),
                    nombre=str(nombre_valor).strip(),
                    fecha_retiro=fecha_retiro_valor,
                    motivo=str(row.get(columns_found.get('motivo'), '')).strip() if 'motivo' in columns_found else ''
                )
                
                registros_creados += 1
                logger.debug(f"✅ Finiquito creado: {finiquito.rut} - {finiquito.nombre}")
                
            except Exception as e:
                error_msg = f"Error en fila {fila_excel}: {str(e)}"
                errores.append(error_msg)
                logger.error(f"❌ {error_msg}")
        
        # Actualizar archivo con resultados
        archivo.estado_procesamiento = 'completado'
        archivo.registros_procesados = registros_creados
        archivo.errores_detectados = len(errores)
        archivo.fecha_procesamiento = timezone.now()
        archivo.save()
        
        logger.info(f"✅ Finiquitos Analista completado - {registros_creados} registros, {len(errores)} errores")
        
        return {
            'success': True,
            'archivo_id': archivo_id,
            'registros_creados': registros_creados,
            'errores': errores,
            'mensaje': f'Procesamiento de finiquitos completado: {registros_creados} registros creados'
        }
        
    except ArchivoSubido.DoesNotExist:
        error_msg = f"Archivo {archivo_id} no encontrado"
        logger.error(f"❌ {error_msg}")
        return {'success': False, 'error': error_msg}
        
    except Exception as e:
        error_msg = f"Error procesando finiquitos analista: {str(e)}"
        logger.error(f"❌ {error_msg}")
        logger.error(traceback.format_exc())
        
        try:
            archivo = ArchivoSubido.objects.get(id=archivo_id)
            archivo.estado_procesamiento = 'error'
            archivo.save()
        except:
            pass
            
        return {'success': False, 'error': error_msg}


@shared_task(bind=True)
def procesar_ausentismos_analista(self, archivo_id):
    """
    Procesa el archivo de Ausentismos del Analista.
    Estructura esperada: Rut, Nombre, Fecha Inicio Ausencia, Fecha Fin Ausencia, Dias, Tipo de Ausentismo
    Headers en la primera fila.
    
    Args:
        archivo_id (int): ID del archivo a procesar
        
    Returns:
        dict: Resultado del procesamiento
    """
    
    try:
        archivo = ArchivoSubido.objects.get(id=archivo_id)
        
        logger.info(f"🏥 Iniciando procesamiento de Ausentismos Analista - Archivo {archivo_id}")
        
        # Actualizar estado
        archivo.estado_procesamiento = 'parseando'
        archivo.save()
        
        # Leer Excel
        df = pd.read_excel(archivo.archivo.path, header=0)  # Headers en fila 1
        
        logger.info(f"📋 Columnas encontradas en Ausentismos: {list(df.columns)}")
        logger.info(f"📊 Total de filas en Ausentismos: {len(df)}")
        
        # Mapeo de columnas
        column_mapping = {
            'rut': ['Rut', 'RUT', 'rut'],
            'nombre': ['Nombre', 'nombre', 'NOMBRE'],
            'fecha_inicio': ['Fecha Inicio Ausencia', 'Fecha Inicio', 'fecha_inicio_ausencia', 'FECHA INICIO'],
            'fecha_fin': ['Fecha Fin Ausencia', 'Fecha Fin', 'fecha_fin_ausencia', 'FECHA FIN'],
            'dias': ['Dias', 'Días', 'dias', 'DIAS'],
            'tipo': ['Tipo de Ausentismo', 'Tipo Ausentismo', 'tipo_ausentismo', 'TIPO']
        }
        
        # Encontrar columnas correctas
        columns_found = {}
        for field, possible_names in column_mapping.items():
            for name in possible_names:
                if name in df.columns:
                    columns_found[field] = name
                    break
            
            if field not in columns_found:
                logger.warning(f"⚠️ No se encontró columna para {field}. Columnas disponibles: {list(df.columns)}")
        
        # Limpiar DataFrame
        df = df.dropna(how='all')
        
        registros_creados = 0
        errores = []
        
        for index, row in df.iterrows():
            try:
                fila_excel = index + 2  # +2 para header en fila 1
                
                # Extraer datos usando el mapeo
                rut_valor = row.get(columns_found.get('rut')) if 'rut' in columns_found else None
                nombre_valor = row.get(columns_found.get('nombre')) if 'nombre' in columns_found else None
                
                # Validar que tenga al menos RUT y nombre
                if pd.isna(rut_valor) or pd.isna(nombre_valor):
                    continue
                
                # Procesar fechas
                fecha_inicio_valor = None
                fecha_fin_valor = None
                
                if 'fecha_inicio' in columns_found:
                    fecha_raw = row.get(columns_found['fecha_inicio'])
                    if pd.notna(fecha_raw):
                        try:
                            if isinstance(fecha_raw, str):
                                fecha_inicio_valor = pd.to_datetime(fecha_raw).date()
                            else:
                                fecha_inicio_valor = fecha_raw.date() if hasattr(fecha_raw, 'date') else fecha_raw
                        except:
                            logger.warning(f"⚠️ Error parseando fecha inicio en fila {fila_excel}: {fecha_raw}")
                
                if 'fecha_fin' in columns_found:
                    fecha_raw = row.get(columns_found['fecha_fin'])
                    if pd.notna(fecha_raw):
                        try:
                            if isinstance(fecha_raw, str):
                                fecha_fin_valor = pd.to_datetime(fecha_raw).date()
                            else:
                                fecha_fin_valor = fecha_raw.date() if hasattr(fecha_raw, 'date') else fecha_raw
                        except:
                            logger.warning(f"⚠️ Error parseando fecha fin en fila {fila_excel}: {fecha_raw}")
                
                # Procesar días
                dias_valor = None
                if 'dias' in columns_found:
                    dias_raw = row.get(columns_found['dias'])
                    if pd.notna(dias_raw):
                        try:
                            dias_valor = int(float(dias_raw))
                        except:
                            logger.warning(f"⚠️ Error parseando días en fila {fila_excel}: {dias_raw}")
                
                # Crear registro en staging
                ausentismo = Ausentismos_analista_stg.objects.create(
                    archivo_subido=archivo,
                    fila_excel=fila_excel,
                    
                    # Datos principales
                    rut=str(rut_valor).strip(),
                    nombre=str(nombre_valor).strip(),
                    fecha_inicio_ausencia=fecha_inicio_valor,
                    fecha_fin_ausencia=fecha_fin_valor,
                    dias=dias_valor,
                    tipo_ausentismo=str(row.get(columns_found.get('tipo'), '')).strip() if 'tipo' in columns_found else ''
                )
                
                registros_creados += 1
                logger.debug(f"✅ Ausentismo creado: {ausentismo.rut} - {ausentismo.nombre}")
                
            except Exception as e:
                error_msg = f"Error en fila {fila_excel}: {str(e)}"
                errores.append(error_msg)
                logger.error(f"❌ {error_msg}")
        
        # Actualizar archivo con resultados
        archivo.estado_procesamiento = 'completado'
        archivo.registros_procesados = registros_creados
        archivo.errores_detectados = len(errores)
        archivo.fecha_procesamiento = timezone.now()
        archivo.save()
        
        logger.info(f"✅ Ausentismos Analista completado - {registros_creados} registros, {len(errores)} errores")
        
        return {
            'success': True,
            'archivo_id': archivo_id,
            'registros_creados': registros_creados,
            'errores': errores,
            'mensaje': f'Procesamiento de ausentismos completado: {registros_creados} registros creados'
        }
        
    except ArchivoSubido.DoesNotExist:
        error_msg = f"Archivo {archivo_id} no encontrado"
        logger.error(f"❌ {error_msg}")
        return {'success': False, 'error': error_msg}
        
    except Exception as e:
        error_msg = f"Error procesando ausentismos analista: {str(e)}"
        logger.error(f"❌ {error_msg}")
        logger.error(traceback.format_exc())
        
        try:
            archivo = ArchivoSubido.objects.get(id=archivo_id)
            archivo.estado_procesamiento = 'error'
            archivo.save()
        except:
            pass
            
        return {'success': False, 'error': error_msg}


@shared_task(bind=True)
def procesar_ingresos_analista(self, archivo_id):
    """
    Procesa el archivo de Ingresos del Analista.
    Estructura esperada: Rut, Nombre, Fecha Ingreso
    Headers en la primera fila.
    
    Args:
        archivo_id (int): ID del archivo a procesar
        
    Returns:
        dict: Resultado del procesamiento
    """
    
    try:
        archivo = ArchivoSubido.objects.get(id=archivo_id)
        
        logger.info(f"👋 Iniciando procesamiento de Ingresos Analista - Archivo {archivo_id}")
        
        # Actualizar estado
        archivo.estado_procesamiento = 'parseando'
        archivo.save()
        
        # Leer Excel
        df = pd.read_excel(archivo.archivo.path, header=0)  # Headers en fila 1
        
        logger.info(f"📋 Columnas encontradas en Ingresos: {list(df.columns)}")
        logger.info(f"📊 Total de filas en Ingresos: {len(df)}")
        
        # Mapeo de columnas
        column_mapping = {
            'rut': ['Rut', 'RUT', 'rut'],
            'nombre': ['Nombre', 'nombre', 'NOMBRE'],
            'fecha_ingreso': ['Fecha Ingreso', 'Fecha de Ingreso', 'fecha_ingreso', 'FECHA INGRESO']
        }
        
        # Encontrar columnas correctas
        columns_found = {}
        for field, possible_names in column_mapping.items():
            for name in possible_names:
                if name in df.columns:
                    columns_found[field] = name
                    break
            
            if field not in columns_found:
                logger.warning(f"⚠️ No se encontró columna para {field}. Columnas disponibles: {list(df.columns)}")
        
        # Limpiar DataFrame
        df = df.dropna(how='all')
        
        registros_creados = 0
        errores = []
        
        for index, row in df.iterrows():
            try:
                fila_excel = index + 2  # +2 para header en fila 1
                
                # Extraer datos usando el mapeo
                rut_valor = row.get(columns_found.get('rut')) if 'rut' in columns_found else None
                nombre_valor = row.get(columns_found.get('nombre')) if 'nombre' in columns_found else None
                
                # Validar que tenga al menos RUT y nombre
                if pd.isna(rut_valor) or pd.isna(nombre_valor):
                    continue
                
                # Procesar fecha de ingreso
                fecha_ingreso_valor = None
                if 'fecha_ingreso' in columns_found:
                    fecha_raw = row.get(columns_found['fecha_ingreso'])
                    if pd.notna(fecha_raw):
                        try:
                            if isinstance(fecha_raw, str):
                                fecha_ingreso_valor = pd.to_datetime(fecha_raw).date()
                            else:
                                fecha_ingreso_valor = fecha_raw.date() if hasattr(fecha_raw, 'date') else fecha_raw
                        except:
                            logger.warning(f"⚠️ Error parseando fecha ingreso en fila {fila_excel}: {fecha_raw}")
                
                # Crear registro en staging
                ingreso = Ingresos_analista_stg.objects.create(
                    archivo_subido=archivo,
                    fila_excel=fila_excel,
                    
                    # Datos principales
                    rut=str(rut_valor).strip(),
                    nombre=str(nombre_valor).strip(),
                    fecha_ingreso=fecha_ingreso_valor
                )
                
                registros_creados += 1
                logger.debug(f"✅ Ingreso creado: {ingreso.rut} - {ingreso.nombre}")
                
            except Exception as e:
                error_msg = f"Error en fila {fila_excel}: {str(e)}"
                errores.append(error_msg)
                logger.error(f"❌ {error_msg}")
        
        # Actualizar archivo con resultados
        archivo.estado_procesamiento = 'completado'
        archivo.registros_procesados = registros_creados
        archivo.errores_detectados = len(errores)
        archivo.fecha_procesamiento = timezone.now()
        archivo.save()
        
        logger.info(f"✅ Ingresos Analista completado - {registros_creados} registros, {len(errores)} errores")
        
        return {
            'success': True,
            'archivo_id': archivo_id,
            'registros_creados': registros_creados,
            'errores': errores,
            'mensaje': f'Procesamiento de ingresos completado: {registros_creados} registros creados'
        }
        
    except ArchivoSubido.DoesNotExist:
        error_msg = f"Archivo {archivo_id} no encontrado"
        logger.error(f"❌ {error_msg}")
        return {'success': False, 'error': error_msg}
        
    except Exception as e:
        error_msg = f"Error procesando ingresos analista: {str(e)}"
        logger.error(f"❌ {error_msg}")
        logger.error(traceback.format_exc())
        
        try:
            archivo = ArchivoSubido.objects.get(id=archivo_id)
            archivo.estado_procesamiento = 'error'
            archivo.save()
        except:
            pass
            
        return {'success': False, 'error': error_msg}
