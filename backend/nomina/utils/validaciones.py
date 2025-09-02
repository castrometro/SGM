import os
import re
import pandas as pd
import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

def validar_archivo_libro_remuneraciones_excel(ruta_archivo: str) -> Dict[str, Any]:
    """
    Valida exhaustivamente un archivo Excel de libro de remuneraciones antes de procesarlo.
    
    Args:
        ruta_archivo (str): Ruta completa al archivo Excel
        
    Returns:
        dict: Resultado de validación con estructura:
            - es_valido (bool): True si el archivo pasa todas las validaciones
            - errores (list): Lista de errores críticos que impiden el procesamiento
            - advertencias (list): Lista de advertencias que no impiden el procesamiento
            - estadisticas (dict): Estadísticas del archivo validado
    """
    errores = []
    advertencias = []
    estadisticas = {}
    
    try:
        # 1. VALIDACIONES BÁSICAS DEL ARCHIVO
        if not os.path.exists(ruta_archivo):
            errores.append("El archivo no existe en la ruta especificada")
            return _build_validation_result(False, errores, advertencias, estadisticas)
        
        # Verificar que el archivo no esté vacío
        if os.path.getsize(ruta_archivo) == 0:
            errores.append("El archivo está vacío (0 bytes)")
            return _build_validation_result(False, errores, advertencias, estadisticas)
        
        # 2. LEER Y VALIDAR ESTRUCTURA DEL EXCEL
        try:
            df = pd.read_excel(ruta_archivo, engine="openpyxl")
        except Exception as e:
            errores.append(f"Error leyendo el archivo Excel: {str(e)}")
            return _build_validation_result(False, errores, advertencias, estadisticas)
        
        # Verificar que tenga al menos una fila de datos (además del header)
        if len(df) == 0:
            errores.append("El archivo no contiene filas de datos (solo headers o completamente vacío)")
            return _build_validation_result(False, errores, advertencias, estadisticas)
        
        # Verificar que tenga al menos las columnas mínimas requeridas
        if len(df.columns) < 8:  # Mínimo: Año, Mes, RUT Empresa, RUT Trabajador, Nombre, Apellidos + al menos 1 concepto
            errores.append(f"El archivo debe tener al menos 8 columnas (encontradas: {len(df.columns)})")
            return _build_validation_result(False, errores, advertencias, estadisticas)
        
        # 3. VALIDAR COLUMNAS OBLIGATORIAS DE EMPLEADO
        headers = list(df.columns)
        columnas_obligatorias = {
            "Año": "Año",
            "Mes": "Mes", 
            "Rut de la Empresa": "Rut de la Empresa",
            "Rut del Trabajador": "Rut del Trabajador",
            "Nombre": "Nombre",
            "Apellido Paterno": "Apellido Paterno",
            "Apellido Materno": "Apellido Materno"
        }
        
        columnas_faltantes = []
        for key, col_name in columnas_obligatorias.items():
            if col_name not in headers:
                columnas_faltantes.append(col_name)
        
        if columnas_faltantes:
            errores.append(f"Faltan columnas obligatorias: {', '.join(columnas_faltantes)}")
            return _build_validation_result(False, errores, advertencias, estadisticas)
        
        # 4. VALIDAR CONTENIDO DE DATOS OBLIGATORIOS
        filas_con_errores = []
        ruts_vacios = 0
        ruts_invalidos = []
        nombres_vacios = 0
        anos_invalidos = []
        meses_invalidos = []
        
        # Patrón para validar RUT (números con puntos y guión opcional)
        patron_rut = r'^\d{1,2}\.?\d{3}\.?\d{3}-?[\dkK]$|^\d{7,8}-?[\dkK]$'
        
        for index, row in df.iterrows():
            fila = index + 2  # +2 para número de fila real en Excel
            
            # Validar RUT del Trabajador
            rut_trabajador = row.get("Rut del Trabajador")
            if pd.isna(rut_trabajador) or str(rut_trabajador).strip() == '':
                ruts_vacios += 1
                filas_con_errores.append(f"Fila {fila}: RUT del trabajador vacío")
            else:
                rut_str = str(rut_trabajador).strip()
                if not re.match(patron_rut, rut_str):
                    ruts_invalidos.append(f"Fila {fila}: RUT inválido '{rut_str}'")
            
            # Validar Nombre
            nombre = row.get("Nombre")
            if pd.isna(nombre) or str(nombre).strip() == '':
                nombres_vacios += 1
                filas_con_errores.append(f"Fila {fila}: Nombre vacío")
            
            # Validar Año
            ano = row.get("Año")
            if pd.isna(ano):
                anos_invalidos.append(f"Fila {fila}: Año vacío")
            else:
                try:
                    ano_int = int(ano)
                    if ano_int < 2020 or ano_int > 2030:  # Rango razonable
                        anos_invalidos.append(f"Fila {fila}: Año fuera de rango '{ano_int}'")
                except (ValueError, TypeError):
                    anos_invalidos.append(f"Fila {fila}: Año inválido '{ano}'")
            
            # Validar Mes
            mes = row.get("Mes")
            if pd.isna(mes):
                meses_invalidos.append(f"Fila {fila}: Mes vacío")
            else:
                try:
                    mes_int = int(mes)
                    if mes_int < 1 or mes_int > 12:
                        meses_invalidos.append(f"Fila {fila}: Mes fuera de rango '{mes_int}'")
                except (ValueError, TypeError):
                    meses_invalidos.append(f"Fila {fila}: Mes inválido '{mes}'")
        
        # 5. IDENTIFICAR Y VALIDAR COLUMNAS DE CONCEPTOS
        columnas_empleado = set(columnas_obligatorias.values())
        
        # Detectar columnas adicionales que podrían ser conceptos usando heurística
        columnas_conceptos = []
        for header in headers:
            if header not in columnas_empleado:
                # Aplicar heurística para filtrar posibles columnas no-concepto
                header_lower = header.lower()
                
                # Saltar columnas que parecen ser de empleado pero no están en obligatorias
                if any(keyword in header_lower for keyword in ['rut', 'dv', 'ingreso', 'fecha']):
                    continue
                    
                columnas_conceptos.append(header)
        
        # Validar que existan conceptos
        if len(columnas_conceptos) == 0:
            errores.append("No se encontraron columnas de conceptos de remuneración")
            return _build_validation_result(False, errores, advertencias, estadisticas)
        
        # 6. GENERAR ERRORES CRÍTICOS
        if ruts_invalidos:
            errores.extend(ruts_invalidos[:5])  # Mostrar máximo 5 ejemplos
            if len(ruts_invalidos) > 5:
                errores.append(f"... y {len(ruts_invalidos) - 5} RUTs inválidos más")
        
        if anos_invalidos:
            errores.extend(anos_invalidos[:3])
            if len(anos_invalidos) > 3:
                errores.append(f"... y {len(anos_invalidos) - 3} años inválidos más")
        
        if meses_invalidos:
            errores.extend(meses_invalidos[:3])
            if len(meses_invalidos) > 3:
                errores.append(f"... y {len(meses_invalidos) - 3} meses inválidos más")
        
        # 7. GENERAR ADVERTENCIAS
        if ruts_vacios > 0:
            porcentaje_vacios = (ruts_vacios / len(df)) * 100
            if porcentaje_vacios > 10:  # Si más del 10% tienen RUT vacío
                advertencias.append(f"Alto porcentaje de RUTs vacíos: {ruts_vacios} filas ({porcentaje_vacios:.1f}%)")
            else:
                advertencias.append(f"Se encontraron {ruts_vacios} filas con RUT del trabajador vacío")
        
        if nombres_vacios > 0:
            advertencias.append(f"Se encontraron {nombres_vacios} filas con nombre vacío")
        
        # Advertir sobre conceptos que parecen extraños
        conceptos_sospechosos = []
        for concepto in columnas_conceptos:
            concepto_lower = concepto.lower()
            if any(keyword in concepto_lower for keyword in ['fecha', 'telefono', 'direccion', 'email']):
                conceptos_sospechosos.append(concepto)
        
        if conceptos_sospechosos:
            advertencias.append(f"Conceptos con nombres sospechosos (verificar si son realmente conceptos de remuneración): {', '.join(conceptos_sospechosos[:3])}")
        
        # 8. ESTADÍSTICAS
        estadisticas = {
            'total_filas': len(df),
            'total_columnas': len(df.columns),
            'columnas_empleado': len(columnas_empleado),
            'columnas_conceptos': len(columnas_conceptos),
            'conceptos_detectados': columnas_conceptos,
            'ruts_vacios': ruts_vacios,
            'ruts_invalidos': len(ruts_invalidos),
            'nombres_vacios': nombres_vacios,
            'anos_invalidos': len(anos_invalidos),
            'meses_invalidos': len(meses_invalidos),
            'filas_con_errores': len(filas_con_errores)
        }
        
        # 9. DETERMINAR SI ES VÁLIDO
        es_valido = len(errores) == 0 and len(columnas_conceptos) > 0
        
        return _build_validation_result(es_valido, errores, advertencias, estadisticas)
        
    except Exception as e:
        errores.append(f"Error inesperado validando archivo: {str(e)}")
        logger.exception(f"Error validando libro de remuneraciones: {e}")
        return _build_validation_result(False, errores, advertencias, estadisticas)


def _build_validation_result(es_valido: bool, errores: List[str], advertencias: List[str], estadisticas: Dict[str, Any]) -> Dict[str, Any]:
    """Construye el resultado estándar de validación"""
    return {
        'es_valido': es_valido,
        'errores': errores,
        'advertencias': advertencias,
        'estadisticas': estadisticas
    }


def validar_nombre_archivo_libro_remuneraciones(nombre_archivo: str, rut_cliente: str = None, periodo_cierre: str = None) -> Dict[str, Any]:
    """
    Valida el nombre de archivo del libro de remuneraciones.
    
    Formatos aceptados:
    - {RUT_SIN_PUNTOS}_LibroRemuneraciones.xlsx
    - {RUT_SIN_PUNTOS}_LibroRemuneraciones_MMAAAA.xlsx
    - {MMAAAA}_libro_remuneraciones_completo.xlsx
    
    Ejemplos: 
    - 12345678_LibroRemuneraciones.xlsx
    - 12345678_LibroRemuneraciones_122024.xlsx
    - 202503_libro_remuneraciones_completo.xlsx
    
    Args:
        nombre_archivo (str): Nombre del archivo a validar
        rut_cliente (str, optional): RUT del cliente para validación específica
        periodo_cierre (str, optional): Período del cierre en formato MMAAAA (ej: "032024")
        
    Returns:
        dict: Resultado de validación
    """
    errores = []
    advertencias = []
    
    # Validar extensión
    if not nombre_archivo.lower().endswith(('.xlsx', '.xls')):
        errores.append(f"Formato de archivo no soportado: {nombre_archivo}. Solo se aceptan archivos Excel (.xlsx, .xls)")
        return _build_validation_result(False, errores, advertencias, {})
    
    # Validar caracteres problemáticos
    caracteres_problematicos = ['<', '>', ':', '"', '|', '?', '*']
    if any(char in nombre_archivo for char in caracteres_problematicos):
        errores.append(f"El nombre del archivo contiene caracteres no permitidos: {nombre_archivo}")
        return _build_validation_result(False, errores, advertencias, {})
    
    # Patrones de validación (en orden de prioridad)
    patrones_validos = [
        # Formato 1: {RUT}_LibroRemuneraciones.xlsx
        (r'^(\d{7,9})_LibroRemuneraciones\.xlsx?$', 'rut_formato_1'),
        # Formato 2: {RUT}_LibroRemuneraciones_MMAAAA.xlsx
        (r'^(\d{7,9})_LibroRemuneraciones_(\d{6})\.xlsx?$', 'rut_formato_2'),
        # Formato 3: {MMAAAA}_libro_remuneraciones_completo.xlsx
        (r'^(\d{6})_libro_remuneraciones_completo\.xlsx?$', 'fecha_formato'),
    ]
    
    rut_extraido = None
    fecha_extraida = None
    formato_detectado = None
    
    # Probar cada patrón
    for patron, tipo_formato in patrones_validos:
        match = re.match(patron, nombre_archivo, re.IGNORECASE)
        if match:
            formato_detectado = tipo_formato
            if tipo_formato == 'rut_formato_1':
                rut_extraido = match.group(1)
            elif tipo_formato == 'rut_formato_2':
                rut_extraido = match.group(1)
                fecha_extraida = match.group(2)
            elif tipo_formato == 'fecha_formato':
                fecha_extraida = match.group(1)
            break
    
    # Si no coincide con ningún patrón, es inválido
    if not formato_detectado:
        errores.append(
            f"Nombre de archivo incorrecto: {nombre_archivo}. "
            f"Formatos esperados:\n"
            f"- {{RUT_SIN_PUNTOS}}_LibroRemuneraciones.xlsx\n"
            f"- {{RUT_SIN_PUNTOS}}_LibroRemuneraciones_MMAAAA.xlsx\n"
            f"- {{MMAAAA}}_libro_remuneraciones_completo.xlsx"
        )
        return _build_validation_result(False, errores, advertencias, {})
    
    # Si se proporciona RUT del cliente, validar que coincida (solo para formatos con RUT)
    if rut_cliente and rut_extraido:
        rut_clean = rut_cliente.replace('.', '').replace('-', '')
        # Remover dígito verificador si existe
        if len(rut_clean) > 8:
            rut_clean = rut_clean[:-1]
        
        if rut_extraido != rut_clean:
            errores.append(
                f"El RUT en el nombre del archivo no coincide con el cliente. "
                f"Esperado: {rut_clean}, "
                f"Encontrado: {rut_extraido}"
            )
            return _build_validation_result(False, errores, advertencias, {})
    
    # Validar formato de fecha si está presente
    if fecha_extraida:
        try:
            mes = int(fecha_extraida[2:4])
            ano = int(fecha_extraida[4:6])
            # Convertir año de 2 dígitos a 4 dígitos (asumiendo 20xx)
            if ano < 50:
                ano_completo = 2000 + ano
            else:
                ano_completo = 1900 + ano
            
            if mes < 1 or mes > 12:
                advertencias.append(f"Mes en el nombre del archivo parece incorrecto: {mes:02d}")
            if ano_completo < 2020 or ano_completo > 2030:
                advertencias.append(f"Año en el nombre del archivo parece incorrecto: {ano_completo}")
                
        except ValueError:
            advertencias.append(f"Formato de fecha en el nombre del archivo no es válido: {fecha_extraida}")
    
    # Validar período del cierre si se proporciona
    if periodo_cierre and fecha_extraida:
        # Normalizar el período del cierre para comparar
        periodo_normalizado = periodo_cierre.replace('/', '').replace('-', '')
        
        # Si el período del cierre tiene 6 dígitos (MMAAAA), comparar directamente
        if len(periodo_normalizado) == 6:
            if fecha_extraida != periodo_normalizado:
                errores.append(
                    f"El período en el nombre del archivo ({fecha_extraida}) no coincide "
                    f"con el período del cierre ({periodo_normalizado})"
                )
                return _build_validation_result(False, errores, advertencias, {})
        else:
            # Si el período del cierre tiene otro formato, tratar de extraer mes y año
            try:
                # Ejemplo: si viene "03/2024" o "2024-03"
                if '/' in periodo_cierre:
                    partes = periodo_cierre.split('/')
                    if len(partes) == 2:
                        mes_cierre = int(partes[0])
                        ano_cierre = int(partes[1])
                elif '-' in periodo_cierre:
                    partes = periodo_cierre.split('-')
                    if len(partes) == 2:
                        ano_cierre = int(partes[0])
                        mes_cierre = int(partes[1])
                else:
                    # Formato AAAAMM
                    if len(periodo_cierre) == 6:
                        ano_cierre = int(periodo_cierre[:4])
                        mes_cierre = int(periodo_cierre[4:6])
                    else:
                        raise ValueError("Formato de período no reconocido")
                
                # Comparar con la fecha extraída del archivo
                mes_archivo = int(fecha_extraida[2:4])
                ano_archivo = int(fecha_extraida[4:6])
                if ano_archivo < 50:
                    ano_archivo_completo = 2000 + ano_archivo
                else:
                    ano_archivo_completo = 1900 + ano_archivo
                
                if mes_archivo != mes_cierre or ano_archivo_completo != ano_cierre:
                    errores.append(
                        f"El período en el nombre del archivo ({mes_archivo:02d}/{ano_archivo_completo}) "
                        f"no coincide con el período del cierre ({mes_cierre:02d}/{ano_cierre})"
                    )
                    return _build_validation_result(False, errores, advertencias, {})
                    
            except (ValueError, IndexError):
                advertencias.append(f"No se pudo validar el período del cierre: {periodo_cierre}")
    
    # Si hay período del cierre pero no fecha en el archivo, es una advertencia
    if periodo_cierre and not fecha_extraida:
        advertencias.append(
            f"El archivo no incluye período en el nombre pero el cierre es para {periodo_cierre}. "
            f"Se recomienda usar formato con período: {{RUT}}_LibroRemuneraciones_MMAAAA.xlsx"
        )
    
    estadisticas = {
        'nombre_archivo': nombre_archivo,
        'rut_extraido': rut_extraido,
        'fecha_extraida': fecha_extraida,
        'formato_detectado': formato_detectado,
        'extension': nombre_archivo.split('.')[-1].lower()
    }
    
    return _build_validation_result(True, errores, advertencias, estadisticas)


def validar_nombre_archivo_movimientos_mes(nombre_archivo: str, rut_cliente: str = None, periodo_cierre: str = None) -> Dict[str, Any]:
    """
    Valida el nombre de archivo de movimientos del mes.
    
    Formato esperado:
    - {AAAAAMM}_movimientos_mes_{RUT}.xlsx
    
    Ejemplos: 
    - 202503_movimientos_mes_12345678.xlsx
    - 202412_movimientos_mes_87654321.xlsx
    
    Args:
        nombre_archivo (str): Nombre del archivo a validar
        rut_cliente (str, optional): RUT del cliente para validación específica
        periodo_cierre (str, optional): Período del cierre en formato "YYYY-MM" (ej: "2024-03")
        
    Returns:
        dict: Resultado de validación
    """
    errores = []
    advertencias = []
    
    # Validar extensión
    if not nombre_archivo.lower().endswith(('.xlsx', '.xls')):
        errores.append(f"Formato de archivo no soportado: {nombre_archivo}. Solo se aceptan archivos Excel (.xlsx, .xls)")
        return _build_validation_result(False, errores, advertencias, {})
    
    # Validar caracteres problemáticos
    caracteres_problematicos = ['<', '>', ':', '"', '|', '?', '*']
    if any(char in nombre_archivo for char in caracteres_problematicos):
        errores.append(f"El nombre del archivo contiene caracteres no permitidos: {nombre_archivo}")
        return _build_validation_result(False, errores, advertencias, {})
    
    # Patrón de validación: {AAAAAMM}_movimientos_mes_{RUT}.xlsx
    patron_movimientos = r'^(\d{6})_movimientos_mes_(\d{7,9})\.xlsx?$'
    match = re.match(patron_movimientos, nombre_archivo, re.IGNORECASE)
    
    if not match:
        errores.append(
            f"Nombre de archivo incorrecto: {nombre_archivo}. "
            f"Formato esperado: {{AAAAAMM}}_movimientos_mes_{{RUT}}.xlsx\n"
            f"Ejemplo: 202503_movimientos_mes_12345678.xlsx"
        )
        return _build_validation_result(False, errores, advertencias, {})
    
    # Extraer información del nombre
    fecha_extraida = match.group(1)  # AAAAAMM
    rut_extraido = match.group(2)    # RUT
    
    # Validar formato de fecha (AAAAAMM)
    try:
        año = int(fecha_extraida[:4])
        mes = int(fecha_extraida[4:6])
        
        if año < 2020 or año > 2030:
            errores.append(f"Año inválido en el nombre del archivo: {año}. Debe estar entre 2020 y 2030.")
            return _build_validation_result(False, errores, advertencias, {})
            
        if mes < 1 or mes > 12:
            errores.append(f"Mes inválido en el nombre del archivo: {mes}. Debe estar entre 01 y 12.")
            return _build_validation_result(False, errores, advertencias, {})
            
    except ValueError:
        errores.append(f"Formato de fecha inválido en el nombre del archivo: {fecha_extraida}")
        return _build_validation_result(False, errores, advertencias, {})
    
    # Validar RUT del cliente si se proporciona
    if rut_cliente:
        rut_cliente_sin_puntos = rut_cliente.replace('.', '').replace('-', '').replace('k', '').replace('K', '')
        if rut_extraido != rut_cliente_sin_puntos:
            errores.append(
                f"El RUT en el nombre del archivo ({rut_extraido}) no coincide con el RUT del cliente ({rut_cliente_sin_puntos})"
            )
            return _build_validation_result(False, errores, advertencias, {})
    
    # Validar período del cierre si se proporciona
    if periodo_cierre:
        try:
            # Convertir período del cierre (YYYY-MM) a formato del archivo (YYYYMM)
            año_cierre, mes_cierre = periodo_cierre.split('-')
            fecha_cierre_esperada = f"{año_cierre}{mes_cierre.zfill(2)}"
            
            if fecha_extraida != fecha_cierre_esperada:
                errores.append(
                    f"El período en el nombre del archivo ({fecha_extraida}) no coincide con el período del cierre ({fecha_cierre_esperada})"
                )
                return _build_validation_result(False, errores, advertencias, {})
                
        except (ValueError, IndexError):
            advertencias.append(f"No se pudo validar el período del cierre: {periodo_cierre}")
    
    estadisticas = {
        'nombre_archivo': nombre_archivo,
        'fecha_extraida': fecha_extraida,
        'rut_extraido': rut_extraido,
        'formato_detectado': 'movimientos_mes_estandar',
        'extension': nombre_archivo.split('.')[-1].lower(),
        'año': año,
        'mes': mes
    }
    
    return _build_validation_result(True, errores, advertencias, estadisticas)


def validar_nombre_archivo_analista(nombre_archivo: str, tipo_archivo: str, rut_cliente: str = None, periodo_cierre: str = None) -> Dict[str, Any]:
    """
    Valida el nombre de archivo para archivos del analista.
    
    Formatos esperados:
    - {AAAAAMM}_incidencias_{RUT}.xlsx (nota: puede ser incidencias o ausentismos)
    - {AAAAAMM}_finiquitos_{RUT}.xlsx
    - {AAAAAMM}_ingresos_{RUT}.xlsx
    
    Ejemplos: 
    - 202503_incidencias_12345678.xlsx
    - 202503_finiquitos_12345678.xlsx
    - 202503_ingresos_12345678.xlsx
    
    Args:
        nombre_archivo (str): Nombre del archivo a validar
        tipo_archivo (str): Tipo de archivo ('incidencias', 'finiquitos', 'ingresos')
        rut_cliente (str, optional): RUT del cliente para validación específica
        periodo_cierre (str, optional): Período del cierre en formato "YYYY-MM" (ej: "2024-03")
        
    Returns:
        dict: Resultado de validación
    """
    errores = []
    advertencias = []
    
    # Validar tipo de archivo
    tipos_validos = ['incidencias', 'finiquitos', 'ingresos']
    if tipo_archivo not in tipos_validos:
        errores.append(f"Tipo de archivo inválido: {tipo_archivo}. Debe ser uno de: {', '.join(tipos_validos)}")
        return _build_validation_result(False, errores, advertencias, {})
    
    # Validar extensión
    if not nombre_archivo.lower().endswith(('.xlsx', '.xls')):
        errores.append(f"Formato de archivo no soportado: {nombre_archivo}. Solo se aceptan archivos Excel (.xlsx, .xls)")
        return _build_validation_result(False, errores, advertencias, {})
    
    # Validar caracteres problemáticos
    caracteres_problematicos = ['<', '>', ':', '"', '|', '?', '*']
    if any(char in nombre_archivo for char in caracteres_problematicos):
        errores.append(f"El nombre del archivo contiene caracteres no permitidos: {nombre_archivo}")
        return _build_validation_result(False, errores, advertencias, {})
    
    # Patrón de validación: {AAAAAMM}_{tipo}_{RUT}.xlsx
    # Nota: para incidencias también acepta "ausentismos" como alias
    if tipo_archivo == 'incidencias':
        # Para incidencias, usa grupo sin captura para la alternancia
        patron_analista = rf'^(\d{{6}})_(?:incidencias|ausentismos)_(\d{{7,9}})\.xlsx?$'
    else:
        patron_analista = rf'^(\d{{6}})_{tipo_archivo}_(\d{{7,9}})\.xlsx?$'
    
    match = re.match(patron_analista, nombre_archivo, re.IGNORECASE)
    
    if not match:
        errores.append(
            f"Nombre de archivo incorrecto: {nombre_archivo}. "
            f"Formato esperado: {{AAAAAMM}}_{tipo_archivo}_{{RUT}}.xlsx\n"
            f"Ejemplo: 202503_{tipo_archivo}_12345678.xlsx"
        )
        return _build_validation_result(False, errores, advertencias, {})
    
    # Extraer información del nombre
    fecha_extraida = match.group(1)  # AAAAAMM
    rut_extraido = match.group(2)    # RUT (siempre es el segundo grupo de captura)
    
    # Validar formato de fecha (AAAAAMM)
    try:
        año = int(fecha_extraida[:4])
        mes = int(fecha_extraida[4:6])
        
        if año < 2020 or año > 2030:
            errores.append(f"Año inválido en el nombre del archivo: {año}. Debe estar entre 2020 y 2030.")
            return _build_validation_result(False, errores, advertencias, {})
            
        if mes < 1 or mes > 12:
            errores.append(f"Mes inválido en el nombre del archivo: {mes}. Debe estar entre 01 y 12.")
            return _build_validation_result(False, errores, advertencias, {})
            
    except ValueError:
        errores.append(f"Formato de fecha inválido en el nombre del archivo: {fecha_extraida}")
        return _build_validation_result(False, errores, advertencias, {})
    
    # Validar RUT del cliente si se proporciona
    if rut_cliente:
        rut_cliente_sin_puntos = rut_cliente.replace('.', '').replace('-', '').replace('k', '').replace('K', '')
        if rut_extraido != rut_cliente_sin_puntos:
            errores.append(
                f"El RUT en el nombre del archivo ({rut_extraido}) no coincide con el RUT del cliente ({rut_cliente_sin_puntos})"
            )
            return _build_validation_result(False, errores, advertencias, {})
    
    # Validar período del cierre si se proporciona
    if periodo_cierre:
        try:
            # Convertir período del cierre (YYYY-MM) a formato del archivo (YYYYMM)
            año_cierre, mes_cierre = periodo_cierre.split('-')
            fecha_cierre_esperada = f"{año_cierre}{mes_cierre.zfill(2)}"
            
            if fecha_extraida != fecha_cierre_esperada:
                errores.append(
                    f"El período en el nombre del archivo ({fecha_extraida}) no coincide con el período del cierre ({fecha_cierre_esperada})"
                )
                return _build_validation_result(False, errores, advertencias, {})
                
        except (ValueError, IndexError):
            advertencias.append(f"No se pudo validar el período del cierre: {periodo_cierre}")
    
    estadisticas = {
        'nombre_archivo': nombre_archivo,
        'tipo_archivo': tipo_archivo,
        'fecha_extraida': fecha_extraida,
        'rut_extraido': rut_extraido,
        'formato_detectado': f'{tipo_archivo}_estandar',
        'extension': nombre_archivo.split('.')[-1].lower(),
        'año': año,
        'mes': mes
    }
    
    return _build_validation_result(True, errores, advertencias, estadisticas)


def validar_nombre_archivo_novedades(nombre_archivo: str, rut_cliente: str = None, periodo_cierre: str = None) -> Dict[str, Any]:
    """
    Valida el nombre de archivo de novedades según el formato estándar:
    AAAAAMM_novedades_{RUT}.xlsx
    
    Args:
        nombre_archivo (str): Nombre del archivo a validar
        rut_cliente (str): RUT del cliente para validación (opcional)
        periodo_cierre (str): Período del cierre en formato YYYY-MM (opcional)
        
    Returns:
        dict: Resultado de validación con estructura:
            - es_valido (bool): True si el archivo pasa todas las validaciones
            - errores (list): Lista de errores críticos
            - advertencias (list): Lista de advertencias
            - estadisticas (dict): Estadísticas del archivo validado
    """
    errores = []
    advertencias = []
    
    if not nombre_archivo:
        errores.append("El nombre del archivo está vacío")
        return _build_validation_result(False, errores, advertencias, {})
    
    # Patrón para archivos de novedades: AAAAAMM_novedades_{RUT}.xlsx
    patron = r'^(\d{6})_novedades_([0-9]{7,8}-?[0-9kK])\.xlsx$'
    match = re.match(patron, nombre_archivo, re.IGNORECASE)
    
    if not match:
        errores.append(
            "El nombre del archivo no cumple con el formato estándar: AAAAAMM_novedades_{RUT}.xlsx\n"
            "Ejemplo: 202501_novedades_12345678-9.xlsx"
        )
        return _build_validation_result(False, errores, advertencias, {})
    
    # Extraer componentes del nombre
    fecha_str = match.group(1)
    rut_extraido = match.group(2)
    
    # Validar fecha
    try:
        año = int(fecha_str[:4])
        mes = int(fecha_str[4:6])
        
        if año < 2020 or año > 2030:
            errores.append(f"El año {año} está fuera del rango válido (2020-2030)")
        
        if mes < 1 or mes > 12:
            errores.append(f"El mes {mes} no es válido (debe estar entre 01-12)")
            
    except ValueError:
        errores.append(f"La fecha {fecha_str} no es válida")
    
    # Validar RUT extraído
    patron_rut = r'^[0-9]{7,8}-?[0-9kK]$'
    if not re.match(patron_rut, rut_extraido, re.IGNORECASE):
        errores.append(f"El RUT en el nombre del archivo ({rut_extraido}) no tiene un formato válido")
    
    # Validar coincidencia con RUT del cliente si se proporciona
    if rut_cliente:
        rut_cliente_limpio = rut_cliente.replace('.', '').replace('-', '').replace('k', '').replace('K', '')
        rut_archivo_limpio = rut_extraido.replace('-', '').replace('k', '').replace('K', '')
        
        if rut_cliente_limpio != rut_archivo_limpio:
            errores.append(
                f"El RUT en el nombre del archivo ({rut_extraido}) no coincide con el RUT del cliente ({rut_cliente})"
            )
    
    # Validar coincidencia con período del cierre si se proporciona
    if periodo_cierre:
        try:
            # Convertir período del cierre (YYYY-MM) a formato del archivo (YYYYMM)
            año_cierre, mes_cierre = periodo_cierre.split('-')
            fecha_cierre_esperada = f"{año_cierre}{mes_cierre.zfill(2)}"
            
            if fecha_str != fecha_cierre_esperada:
                errores.append(
                    f"El período en el nombre del archivo ({fecha_str}) no coincide con el período del cierre ({fecha_cierre_esperada})"
                )
                
        except (ValueError, IndexError):
            advertencias.append(f"No se pudo validar el período del cierre: {periodo_cierre}")
    
    # Si hay errores, retornar resultado inválido
    if errores:
        return _build_validation_result(False, errores, advertencias, {})
    
    estadisticas = {
        'nombre_archivo': nombre_archivo,
        'tipo_archivo': 'novedades',
        'fecha_extraida': fecha_str,
        'rut_extraido': rut_extraido,
        'formato_detectado': 'novedades_estandar',
        'extension': nombre_archivo.split('.')[-1].lower(),
        'año': año,
        'mes': mes
    }
    
    return _build_validation_result(True, errores, advertencias, estadisticas)
