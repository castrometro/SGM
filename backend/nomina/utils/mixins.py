# backend/nomina/utils/mixins.py

import os
import hashlib
from datetime import datetime
from django.utils import timezone
from django.core.files.storage import default_storage

from ..models_logging import UploadLogNomina, TarjetaActivityLogNomina, registrar_actividad_tarjeta_nomina


class UploadLogNominaMixin:
    """
    Mixin para manejar el logging de uploads en nómina
    """
    
    def __init__(self):
        self.tipo_upload = None
        self.cliente = None
        self.usuario = None
        self.ip_usuario = None
    
    def crear_upload_log(self, cliente, archivo, tipo_upload=None):
        """
        Crea un nuevo registro de UploadLogNomina
        """
        # Calcular hash del archivo
        hash_archivo = self._calcular_hash_archivo(archivo)
        
        # Crear log básico
        upload_log = UploadLogNomina.objects.create(
            cliente=cliente,
            tipo_upload=tipo_upload or self.tipo_upload,
            nombre_archivo_original=archivo.name,
            tamaño_archivo=archivo.size,
            hash_archivo=hash_archivo,
            estado='procesando',
            fecha_subida=timezone.now(),
            usuario=self.usuario,
            ip_usuario=self.ip_usuario,
        )
        
        return upload_log
    
    def actualizar_upload_log(self, upload_log_id, **kwargs):
        """
        Actualiza un registro de UploadLogNomina
        """
        try:
            upload_log = UploadLogNomina.objects.get(id=upload_log_id)
            
            for key, value in kwargs.items():
                setattr(upload_log, key, value)
            
            upload_log.save()
            return upload_log
            
        except UploadLogNomina.DoesNotExist:
            raise ValueError(f"UploadLogNomina con id {upload_log_id} no encontrado")
    
    def marcar_como_completado(self, upload_log_id, resumen=None):
        """
        Marca un upload como completado
        """
        return self.actualizar_upload_log(
            upload_log_id,
            estado='completado',
            fecha_procesamiento=timezone.now(),
            resumen=resumen
        )
    
    def marcar_como_error(self, upload_log_id, errores):
        """
        Marca un upload como error
        """
        return self.actualizar_upload_log(
            upload_log_id,
            estado='error',
            fecha_procesamiento=timezone.now(),
            errores=errores
        )
    
    def _calcular_hash_archivo(self, archivo):
        """
        Calcula el hash MD5 del archivo
        """
        hash_md5 = hashlib.md5()
        
        # Leer el archivo en chunks para archivos grandes
        for chunk in archivo.chunks():
            hash_md5.update(chunk)
        
        # Resetear el puntero del archivo
        archivo.seek(0)
        
        return hash_md5.hexdigest()
    
    def validar_archivo_duplicado(self, cliente, hash_archivo, tipo_upload=None):
        """
        Valida si ya existe un archivo con el mismo hash
        """
        tipo = tipo_upload or self.tipo_upload
        
        return UploadLogNomina.objects.filter(
            cliente=cliente,
            tipo_upload=tipo,
            hash_archivo=hash_archivo,
            estado='completado'
        ).exists()
    
    def registrar_actividad(self, tarjeta_tipo, tarjeta_id, accion, descripcion, usuario=None, datos_adicionales=None):
        """
        Registra una actividad en el log de actividades
        """
        # Necesitamos obtener el cierre_id desde el tarjeta_id dependiendo del tipo
        cierre_id = self._obtener_cierre_id_desde_tarjeta(tarjeta_tipo, tarjeta_id)
        
        return registrar_actividad_tarjeta_nomina(
            cierre_id=cierre_id,
            tarjeta=tarjeta_tipo,
            accion=accion,
            descripcion=descripcion,
            usuario=usuario or self.usuario,
            detalles=datos_adicionales,
            ip_address=self.ip_usuario
        )
    
    def _obtener_cierre_id_desde_tarjeta(self, tarjeta_tipo, tarjeta_id):
        """
        Obtiene el cierre_id desde el tarjeta_id dependiendo del tipo
        """
        try:
            if tarjeta_tipo == "libro_remuneraciones":
                from ..models import LibroRemuneracionesUpload
                obj = LibroRemuneracionesUpload.objects.get(id=tarjeta_id)
                return obj.cierre_id
            elif tarjeta_tipo == "movimientos_mes":
                from ..models import MovimientosMesUpload
                obj = MovimientosMesUpload.objects.get(id=tarjeta_id)
                return obj.cierre_id
            elif tarjeta_tipo == "archivo_analista":
                from ..models import ArchivoAnalistaUpload
                obj = ArchivoAnalistaUpload.objects.get(id=tarjeta_id)
                return obj.cierre_id
            elif tarjeta_tipo == "archivo_novedades":
                from ..models import ArchivoNovedadesUpload
                obj = ArchivoNovedadesUpload.objects.get(id=tarjeta_id)
                return obj.cierre_id
            else:
                return None
        except Exception:
            return None


class ValidacionArchivoCRUDMixin:
    """
    Mixin para validaciones comunes de archivos en nómina
    """
    
    EXTENSIONES_PERMITIDAS = {'.xlsx', '.xls', '.csv'}
    TAMAÑO_MAXIMO = 50 * 1024 * 1024  # 50MB
    
    def validar_archivo(self, archivo):
        """
        Valida el archivo subido
        """
        errores = []
        
        # Validar extensión
        if not self._validar_extension(archivo.name):
            errores.append(f"Extensión no permitida. Permitidas: {', '.join(self.EXTENSIONES_PERMITIDAS)}")
        
        # Validar tamaño
        if archivo.size > self.TAMAÑO_MAXIMO:
            errores.append(f"Archivo demasiado grande. Máximo: {self.TAMAÑO_MAXIMO / (1024*1024):.1f}MB")
        
        # Validar que no esté vacío
        if archivo.size == 0:
            errores.append("El archivo está vacío")
        
        if errores:
            raise ValueError("; ".join(errores))
        
        return True
    
    def _validar_extension(self, nombre_archivo):
        """
        Valida que la extensión del archivo sea permitida
        """
        _, ext = os.path.splitext(nombre_archivo.lower())
        return ext in self.EXTENSIONES_PERMITIDAS
    
    def validar_nombre_archivo(self, nombre_archivo, patron_esperado=None):
        """
        Valida el nombre del archivo contra un patrón esperado
        """
        if patron_esperado:
            import re
            if not re.match(patron_esperado, nombre_archivo, re.IGNORECASE):
                # Mensaje más claro para el usuario
                if "libro_remuneraciones" in patron_esperado:
                    raise ValueError(
                        f"El nombre del archivo debe seguir el formato: "
                        f"AAAAMM_libro_remuneraciones_RUT.xlsx "
                        f"(ej: 202508_libro_remuneraciones_12345678.xlsx). "
                        f"Archivo recibido: {nombre_archivo}"
                    )
                else:
                    raise ValueError(f"Nombre de archivo no válido. Patrón esperado: {patron_esperado}")
        
        return True
        
        return True


class CeleryTaskMixin:
    """
    Mixin para manejar tareas de Celery en nómina
    """
    
    def ejecutar_con_logging(self, upload_log_id, funcion_procesamiento, *args, **kwargs):
        """
        Ejecuta una función de procesamiento con logging automático
        """
        mixin = UploadLogNominaMixin()
        
        try:
            # Marcar como procesando
            mixin.actualizar_upload_log(upload_log_id, estado='procesando')
            
            # Ejecutar procesamiento
            resultado = funcion_procesamiento(*args, **kwargs)
            
            # Marcar como completado
            mixin.marcar_como_completado(upload_log_id, resumen=resultado)
            
            return resultado
            
        except Exception as e:
            # Marcar como error
            mixin.marcar_como_error(upload_log_id, errores=str(e))
            raise
    
    def actualizar_progreso(self, upload_log_id, registros_procesados, registros_totales=None):
        """
        Actualiza el progreso del procesamiento
        """
        mixin = UploadLogNominaMixin()
        
        datos_actualizacion = {
            'registros_procesados': registros_procesados
        }
        
        if registros_totales:
            datos_actualizacion['registros_totales'] = registros_totales
        
        mixin.actualizar_upload_log(upload_log_id, **datos_actualizacion)
