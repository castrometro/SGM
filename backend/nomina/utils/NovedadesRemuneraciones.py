import pandas as pd
import logging

from nomina.models import (
    ConceptoRemuneracionNovedades, 
    ArchivoNovedadesUpload, 
    EmpleadoCierreNovedades, 
    RegistroConceptoEmpleadoNovedades
)
from .LibroRemuneraciones import _es_rut_valido

logger = logging.getLogger(__name__)

def _normalizar_monto_peso(valor_raw):
    """Normaliza un valor numérico a pesos (entero) con redondeo HALF_UP.
    Retorna string con entero si es numérico; en caso contrario retorna None.
    """
    try:
        from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
        import re
        if valor_raw is None:
            return None
        # Si ya es número (int/float), usarlo directo
        if isinstance(valor_raw, (int, float)):
            d = Decimal(str(valor_raw)).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
            return str(int(d))
        # Si es string, limpiar y detectar separadores
        s = str(valor_raw).strip()
        if s == '' or s.lower() == 'nan':
            return None
        # Mantener solo dígitos, separadores y signo
        s = re.sub(r"[^0-9,\.\-]", "", s)
        if not s:
            return None
        # Resolver separador decimal: si hay ambos, tomar el último como decimal
        if ',' in s and '.' in s:
            if s.rfind(',') > s.rfind('.'):
                s = s.replace('.', '')
                s = s.replace(',', '.')
            else:
                s = s.replace(',', '')
        elif ',' in s and '.' not in s:
            s = s.replace(',', '.')
        # Convertir a Decimal y redondear
        d = Decimal(s)
        d0 = d.quantize(Decimal('1'), rounding=ROUND_HALF_UP)
        return str(int(d0))
    except Exception:
        return None


def normalizar_valor_concepto_novedades(valor):
    """
    Normaliza valores de conceptos en archivos de novedades.
    
    REGLA DE NEGOCIO: En archivos de novedades, ciertos valores especiales
    significan "cero" o "no aplica":
    - "X" o "x" → valor cero
    - "-" (guión) → valor cero
    - "N/A" o "n/a" → valor cero
    - "" (vacío) → valor cero
    - None → valor cero
    
    Esta normalización previene falsos positivos al comparar con Libro de
    Remuneraciones, donde estos conceptos aparecen como 0 o simplemente no existen.
    
    Args:
        valor: Valor raw del concepto (puede ser string, número, None)
        
    Returns:
        str: Valor normalizado como string. "0" para valores especiales,
             valor original para números válidos.
             
    Ejemplo:
        >>> normalizar_valor_concepto_novedades("X")
        "0"
        >>> normalizar_valor_concepto_novedades("150000")
        "150000"
        >>> normalizar_valor_concepto_novedades("-")
        "0"
    """
    # Lista de valores que se consideran "cero" o "no aplica"
    VALORES_CERO_EQUIVALENTES = ['X', 'x', '-', 'N/A', 'n/a', 'NA', 'na', '']
    
    # Caso 1: None o NaN
    if valor is None or pd.isna(valor):
        return "0"
    
    # Caso 2: String que necesita normalización
    if isinstance(valor, str):
        valor_limpio = valor.strip()
        
        # Si está en la lista de equivalentes a cero
        if valor_limpio in VALORES_CERO_EQUIVALENTES:
            logger.debug(f"🔧 Valor '{valor}' normalizado a '0' (equivalente a cero)")
            return "0"
        
        # Si es "nan" como string (case insensitive)
        if valor_limpio.lower() == 'nan':
            logger.debug(f"🔧 Valor 'nan' normalizado a '0'")
            return "0"
        
        # Si está vacío después de limpiar
        if not valor_limpio:
            return "0"
    
    # Caso 3: Ya es un número válido, retornar como string
    if isinstance(valor, (int, float)):
        return str(valor)
    
    # Caso 4: Valor ya procesado, retornar como está
    return str(valor)


def obtener_headers_archivo_novedades(path_archivo):
    """Obtiene los encabezados de un archivo de novedades.

    Filtra únicamente las primeras 4 columnas (RUT, Nombre, Apellido Paterno, Apellido Materno)
    que se utilizan para poblar el modelo ``EmpleadoCierreNovedades`` antes de retornar el listado.
    """
    logger.info(f"Abriendo archivo de novedades: {path_archivo}")
    try:
        df = pd.read_excel(path_archivo, engine="openpyxl")
        headers = list(df.columns)

        # Para novedades, solo ignoramos las primeras 4 columnas
        # (RUT, Nombre, Apellido Paterno, Apellido Materno)
        if len(headers) <= 4:
            logger.warning(f"El archivo tiene solo {len(headers)} columnas, esperado al menos 5")
            return []
        
        # Filtramos las primeras 4 columnas
        filtered_headers = headers[4:]

        logger.info(f"Headers encontrados para novedades: {filtered_headers}")
        return filtered_headers
    except Exception as e:
        logger.error(f"Error al leer el archivo de novedades: {e}")
        raise

def clasificar_headers_archivo_novedades(headers, cliente):
    """
    Clasifica los headers usando los mapeos ConceptoRemuneracionNovedades vigentes del cliente.
    Retorna dos listas: clasificados y sin clasificar.
    """
    # Obtén los headers ya mapeados del cliente, normalizados a lower y sin espacios
    headers_mapeados = set(
        c.nombre_concepto_novedades.strip().lower()
        for c in ConceptoRemuneracionNovedades.objects.filter(
            cliente=cliente, 
            activo=True,
            concepto_libro__vigente=True
        )
    )
    headers_clasificados = []
    headers_sin_clasificar = []

    for h in headers:
        # Convertir a string si es necesario antes de aplicar strip() y lower()
        header_str = str(h).strip().lower() if h is not None else ""
        if header_str in headers_mapeados:
            headers_clasificados.append(h)
        else:
            headers_sin_clasificar.append(h)

    logger.info(
        f"Clasificación automática novedades: {len(headers_clasificados)} mapeados, {len(headers_sin_clasificar)} sin mapear"
    )
    return headers_clasificados, headers_sin_clasificar

def actualizar_empleados_desde_novedades(archivo_novedades):
    """
    Función utilitaria para actualizar empleados desde un archivo de novedades
    """
    df = pd.read_excel(archivo_novedades.archivo.path, engine="openpyxl")

    # Para novedades, las primeras 4 columnas deben ser:
    # RUT, Nombre, Apellido Paterno, Apellido Materno
    if len(df.columns) < 4:
        raise ValueError("El archivo debe tener al menos 4 columnas: RUT, Nombre, Apellido Paterno, Apellido Materno")

    # Tomamos las primeras 4 columnas sin importar su nombre
    columnas_empleado = list(df.columns[:4])
    rut_col, nombre_col, apellido_pat_col, apellido_mat_col = columnas_empleado

    cierre = archivo_novedades.cierre
    primera_col = df.columns[0]
    count = 0
    filas_ignoradas = 0
    
    for _, row in df.iterrows():
        if not str(row.get(primera_col, "")).strip():
            continue
        
        # NUEVA VALIDACIÓN: Ignorar filas con RUT inválido (NaN, vacío, "total", etc.)
        rut_raw = row.get(rut_col)
        if not _es_rut_valido(rut_raw):
            filas_ignoradas += 1
            logger.debug(f"Fila ignorada por RUT inválido en novedades: '{rut_raw}' (posible fila de totales de Talana)")
            continue
        
        rut = str(rut_raw).strip()
        defaults = {
            "nombre": str(row.get(nombre_col, "")).strip(),
            "apellido_paterno": str(row.get(apellido_pat_col, "")).strip(),
            "apellido_materno": str(row.get(apellido_mat_col, "")).strip(),
        }
        
        EmpleadoCierreNovedades.objects.update_or_create(
            cierre=cierre,
            rut=rut,
            defaults=defaults,
        )
        count += 1
    
    if filas_ignoradas > 0:
        logger.info(f"Se ignoraron {filas_ignoradas} filas con RUT inválido en novedades (posibles totales de Talana)")
    
    logger.info(f"Actualizados {count} empleados desde archivo novedades {archivo_novedades.id}")
    return count


def guardar_registros_novedades(archivo_novedades):
    """
    Función utilitaria para guardar registros de novedades desde un archivo
    """
    df = pd.read_excel(archivo_novedades.archivo.path, engine="openpyxl")

    # Verificar que tenga al menos 4 columnas
    if len(df.columns) < 4:
        raise ValueError("El archivo debe tener al menos 4 columnas: RUT, Nombre, Apellido Paterno, Apellido Materno")

    # Las primeras 4 columnas son para datos del empleado
    columnas_empleado = list(df.columns[:4])
    rut_col = columnas_empleado[0]

    # Obtener headers de conceptos (columnas 5 en adelante)
    headers = archivo_novedades.header_json
    if isinstance(headers, dict):
        headers = headers.get("headers_clasificados", []) + headers.get(
            "headers_sin_clasificar", []
        )
    if not headers:
        headers = list(df.columns[4:])  # Todas las columnas después de las primeras 4

    primera_col = df.columns[0]
    count = 0
    filas_ignoradas = 0
    
    for _, row in df.iterrows():
        if not str(row.get(primera_col, "")).strip():
            continue
            
        # NUEVA VALIDACIÓN: Ignorar filas con RUT inválido (NaN, vacío, "total", etc.)
        rut_raw = row.get(rut_col)
        if not _es_rut_valido(rut_raw):
            filas_ignoradas += 1
            logger.debug(f"Fila ignorada por RUT inválido en novedades: '{rut_raw}' (posible fila de totales de Talana)")
            continue
            
        rut = str(rut_raw).strip()
        empleado = EmpleadoCierreNovedades.objects.filter(
            cierre=archivo_novedades.cierre, rut=rut
        ).first()
        if not empleado:
            continue

        for h in headers:
            try:
                valor_raw = row.get(h)
                
                # 🔧 NORMALIZACIÓN DE VALORES ESPECIALES (Issue #3)
                # Aplicar normalización ANTES de cualquier otro procesamiento
                # para tratar "X", "-", "N/A", etc. como cero
                valor_raw = normalizar_valor_concepto_novedades(valor_raw)
                
                # Si después de normalizar es "0", usar ese valor directamente
                if valor_raw == "0":
                    valor = "0"
                # Procesamiento mejorado de valores
                elif pd.isna(valor_raw) or valor_raw == '':
                    valor = ""  # Valor vacío
                else:
                    # Si es un número, preservar su precisión original
                    if isinstance(valor_raw, (int, float)):
                        # Para números enteros, mantener sin decimales
                        if isinstance(valor_raw, int) or (isinstance(valor_raw, float) and valor_raw.is_integer()):
                            valor = str(int(valor_raw))
                        else:
                            # Para decimales, usar precisión limitada
                            valor = f"{valor_raw:.2f}".rstrip('0').rstrip('.')
                        
                        # Log para valores numéricos grandes (posible problema)
                        if isinstance(valor_raw, (int, float)) and abs(valor_raw) > 10000000:  # > 10 millones
                            logger.debug(f"⚠️ Valor numérico grande detectado en '{h}' para RUT {rut}: {valor_raw} → {valor}")
                    else:
                        # Para strings, limpiar y validar
                        valor = str(valor_raw).strip()
                        # Si es "nan" como string, convertir a vacío
                        if valor.lower() == 'nan':
                            valor = ""
                        # Intentar limpiar formato monetario si existe
                        elif valor:
                            # Remover símbolos de moneda y espacios
                            valor_limpio = valor.replace('$', '').replace(',', '').replace('.', '').strip()
                            # Si después de limpiar es un número válido, usar esa representación
                            try:
                                numero = float(valor_limpio) if '.' in valor else int(valor_limpio)
                                if isinstance(numero, int) or numero.is_integer():
                                    valor_final = str(int(numero))
                                else:
                                    valor_final = f"{numero:.2f}".rstrip('0').rstrip('.')
                                
                                # Log si hubo transformación significativa
                                if valor != valor_final:
                                    logger.debug(f"🔧 Valor transformado en '{h}' para RUT {rut}: '{valor}' → '{valor_final}'")
                                valor = valor_final
                                
                            except (ValueError, TypeError):
                                # Si no se puede convertir a número, mantener el valor original limpio
                                pass

                # Normalización a pesos en persistencia (si es numérico)
                valor_norm = _normalizar_monto_peso(valor_raw)
                if valor_norm is not None:
                    valor = valor_norm

                # Buscar el mapeo del header de novedades
                concepto = ConceptoRemuneracionNovedades.objects.filter(
                    cliente=archivo_novedades.cierre.cliente, 
                    nombre_concepto_novedades=h, 
                    activo=True,
                    concepto_libro__vigente=True
                ).first()
                
                RegistroConceptoEmpleadoNovedades.objects.update_or_create(
                    empleado=empleado,
                    nombre_concepto_original=h,
                    defaults={"monto": valor, "concepto": concepto},
                )
                
            except Exception as concepto_error:
                logger.error(f"❌ ERROR en concepto '{h}' para empleado RUT {rut}: {concepto_error}")
                logger.error(f"Valor problemático: {row.get(h)}")
                raise
        count += 1
    
    if filas_ignoradas > 0:
        logger.info(f"Se ignoraron {filas_ignoradas} filas con RUT inválido en novedades (posibles totales de Talana)")

    logger.info(f"Registros novedades guardados desde archivo {archivo_novedades.id}: {count}")
    return count
