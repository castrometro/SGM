# backend/payroll/config/archivo_config.py

import os
import re
from datetime import datetime

class ArchivoConfig:
    """
    Configuración centralizada para el manejo de archivos de payroll.
    Define formatos, validaciones y nomenclatura para cada tipo de archivo.
    """
    
    # Configuración por tipo de archivo
    TIPOS_ARCHIVO_CONFIG = {
        'libro_remuneraciones': {
            'formato_nombre': lambda cierre: f"{cierre.periodo.replace('-', '')}_libro_remuneraciones_{cierre.cliente.rut}",
            'extensiones_permitidas': ['.xlsx', '.xls'],
            'tamaño_maximo_mb': 10,
            'columnas_esperadas': [
                'rut', 'nombre', 'cargo', 'sueldo_base', 'gratificacion', 
                'comisiones', 'descuentos', 'liquido_a_pagar'
            ],
            'descripcion': 'Talana - Libro de Remuneraciones'
        },
        'movimientos_mes': {
            'formato_nombre': lambda cierre: f"{cierre.periodo.replace('-', '')}_movimientos_mes_{cierre.cliente.rut}",
            'extensiones_permitidas': ['.xlsx', '.xls'],
            'tamaño_maximo_mb': 15,
            'columnas_esperadas': [
                'fecha', 'tipo_movimiento', 'rut_empleado', 'concepto', 'monto'
            ],
            'descripcion': 'Talana - Movimientos del Mes'
        },
        'ausentismos': {
            'formato_nombre': lambda cierre: f"{cierre.periodo.replace('-', '')}_ausentismos_{cierre.cliente.rut}",
            'extensiones_permitidas': ['.xlsx', '.xls', '.csv'],
            'tamaño_maximo_mb': 5,
            'columnas_esperadas': [
                'rut_empleado', 'fecha_inicio', 'fecha_fin', 'tipo_ausentismo', 'dias'
            ],
            'descripcion': 'Analista - Ausentismos'
        },
        'ingresos': {
            'formato_nombre': lambda cierre: f"{cierre.periodo.replace('-', '')}_ingresos_{cierre.cliente.rut}",
            'extensiones_permitidas': ['.xlsx', '.xls', '.csv'],
            'tamaño_maximo_mb': 5,
            'columnas_esperadas': [
                'rut_empleado', 'fecha_ingreso', 'cargo', 'sueldo_base'
            ],
            'descripcion': 'Analista - Ingresos'
        },
        'finiquitos': {
            'formato_nombre': lambda cierre: f"{cierre.periodo.replace('-', '')}_finiquitos_{cierre.cliente.rut}",
            'extensiones_permitidas': ['.xlsx', '.xls', '.csv'],
            'tamaño_maximo_mb': 5,
            'columnas_esperadas': [
                'rut_empleado', 'fecha_termino', 'motivo', 'indemnizacion', 'vacaciones'
            ],
            'descripcion': 'Analista - Finiquitos'
        },
        'novedades': {
            'formato_nombre': lambda cierre: f"{cierre.periodo.replace('-', '')}_novedades_{cierre.cliente.rut}",
            'extensiones_permitidas': ['.xlsx', '.xls', '.csv'],
            'tamaño_maximo_mb': 5,
            'columnas_esperadas': [
                'rut_empleado', 'tipo_novedad', 'descripcion', 'monto', 'fecha'
            ],
            'descripcion': 'Analista - Novedades'
        }
    }
    
    @classmethod
    def get_config(cls, tipo_archivo):
        """Obtiene la configuración para un tipo específico de archivo"""
        return cls.TIPOS_ARCHIVO_CONFIG.get(tipo_archivo, {})
    
    @classmethod
    def generate_filename(cls, cierre, tipo_archivo, extension):
        """
        Genera el nombre de archivo según el formato establecido
        
        Args:
            cierre: Instancia del modelo CierrePayroll
            tipo_archivo: Tipo de archivo (string)
            extension: Extensión del archivo (incluye el punto)
        
        Returns:
            str: Nombre del archivo formateado
        """
        config = cls.get_config(tipo_archivo)
        if not config or 'formato_nombre' not in config:
            # Formato por defecto si no está configurado
            periodo_sin_guion = cierre.periodo.replace('-', '')
            return f"{periodo_sin_guion}_{tipo_archivo}_{cierre.cliente.rut}{extension}"
        
        base_name = config['formato_nombre'](cierre)
        return f"{base_name}{extension}"
    
    @classmethod
    def validate_filename_format(cls, filename, cierre, tipo_archivo):
        """
        Valida que el nombre del archivo tenga el formato correcto según el tipo
        
        Args:
            filename: Nombre del archivo (string)
            cierre: Instancia del modelo CierrePayroll
            tipo_archivo: Tipo de archivo (string)
        
        Returns:
            tuple: (is_valid: bool, error_message: str)
        """
        # Remover extensión del filename
        name_without_ext = os.path.splitext(filename)[0]
        
        # Obtener datos del cierre
        periodo_sin_guion = cierre.periodo.replace('-', '')  # "2025-08" -> "202508"
        # Limpiar RUT: sin puntos ni guión
        rut_limpio = cierre.cliente.rut.replace('.', '').replace('-', '')  # "96.540.690-5" -> "965406905"
        
        if tipo_archivo == 'libro_remuneraciones':
            # Formato esperado: "AAAAMM_libro_remuneraciones_RUTCLIENTESINGUION"
            formato_esperado = f"{periodo_sin_guion}_libro_remuneraciones_{rut_limpio}"
            
            if name_without_ext != formato_esperado:
                return False, (
                    f"Formato de nombre incorrecto. "
                    f"Esperado: '{formato_esperado}.xlsx' "
                    f"Recibido: '{filename}'"
                )
        
        elif tipo_archivo == 'movimientos_mes':
            # Formato esperado: "AAAAMM_movimientos_mes_RUTCLIENTESINGUION"
            formato_esperado = f"{periodo_sin_guion}_movimientos_mes_{rut_limpio}"
            
            if name_without_ext != formato_esperado:
                return False, (
                    f"Formato de nombre incorrecto. "
                    f"Esperado: '{formato_esperado}.xlsx' "
                    f"Recibido: '{filename}'"
                )
        
        elif tipo_archivo in ['ausentismos', 'ingresos', 'finiquitos', 'novedades']:
            # Formato esperado: "AAAAMM_TIPOARCHIVO_RUTCLIENTESINGUION"
            formato_esperado = f"{periodo_sin_guion}_{tipo_archivo}_{rut_limpio}"
            
            if name_without_ext != formato_esperado:
                return False, (
                    f"Formato de nombre incorrecto. "
                    f"Esperado: '{formato_esperado}.xlsx' "
                    f"Recibido: '{filename}'"
                )
        
        else:
            return False, f"Tipo de archivo '{tipo_archivo}' no reconocido"
        
        return True, ""
    
    @classmethod
    def validate_file(cls, archivo, tipo_archivo, cierre=None):
        """
        Valida un archivo según su tipo
        
        Args:
            archivo: Archivo subido (UploadedFile)
            tipo_archivo: Tipo de archivo (string)
            cierre: Instancia del modelo CierrePayroll (requerido para validar nombre)
        
        Returns:
            tuple: (is_valid: bool, errors: list)
        """
        config = cls.get_config(tipo_archivo)
        errors = []
        
        if not config:
            errors.append(f"Tipo de archivo '{tipo_archivo}' no configurado")
            return False, errors
        
        # Validar extensión
        file_ext = os.path.splitext(archivo.name)[1].lower()
        if file_ext not in config.get('extensiones_permitidas', []):
            errors.append(f"Extensión '{file_ext}' no permitida. Extensiones válidas: {config.get('extensiones_permitidas', [])}")
        
        # Validar tamaño
        max_size = config.get('tamaño_maximo_mb', 10) * 1024 * 1024  # Convertir a bytes
        if archivo.size > max_size:
            errors.append(f"Archivo demasiado grande. Máximo permitido: {config.get('tamaño_maximo_mb', 10)}MB")
        
        # VALIDAR FORMATO DEL NOMBRE DEL ARCHIVO
        if cierre:
            is_valid_name, name_error = cls.validate_filename_format(archivo.name, cierre, tipo_archivo)
            if not is_valid_name:
                errors.append(name_error)
        
        return len(errors) == 0, errors
    
    @classmethod
    def get_upload_path(cls, cierre, tipo_archivo, extension):
        """
        Genera la ruta completa donde se guardará el archivo
        
        Estructura: media/payroll/id_cliente/año/mes/archivo.ext
        
        Args:
            cierre: Instancia del modelo CierrePayroll
            tipo_archivo: Tipo de archivo (string)
            extension: Extensión del archivo
        
        Returns:
            str: Ruta completa del archivo
        """
        # Extraer año y mes del periodo (formato "YYYY-MM")
        año, mes = cierre.periodo.split('-')
        
        filename = cls.generate_filename(cierre, tipo_archivo, extension)
        return f"payroll/{cierre.cliente.id}/{año}/{mes}/{filename}"
