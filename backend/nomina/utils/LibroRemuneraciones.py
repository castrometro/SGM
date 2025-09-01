import pandas as pd
import logging

from nomina.models import ConceptoRemuneracion, LibroRemuneracionesUpload, EmpleadoCierre, RegistroConceptoEmpleado

logger = logging.getLogger(__name__)

def _es_rut_valido(valor_rut):
    """
    Determina si un valor de RUT es válido para procesamiento.
    Retorna False para valores NaN, vacíos, o palabras como "total" que usa Talana.
    """
    if valor_rut is None:
        return False
    
    # Verificar si es NaN de pandas
    if pd.isna(valor_rut):
        return False
    
    # Convertir a string y limpiar
    rut_str = str(valor_rut).strip().lower()
    
    # Verificar si está vacío
    if not rut_str:
        return False
    
    # Verificar si es "nan" como string
    if rut_str == "nan":
        return False
    
    # Verificar palabras típicas de filas de totales que usa Talana
    palabras_invalidas = [
        "total", "totales", "suma", "sumatoria", 
        "resumen", "consolidado", "subtotal"
    ]
    
    if rut_str in palabras_invalidas:
        return False
    
    return True

def obtener_headers_libro_remuneraciones(path_archivo):
    """Obtiene los encabezados de un libro de remuneraciones.

    Filtra las columnas que se utilizan para poblar el modelo ``Empleado``
    antes de retornar el listado.
    """
    logger.info(f"Abriendo archivo de libro de remuneraciones: {path_archivo}")
    try:
        df = pd.read_excel(path_archivo, engine="openpyxl")
        headers = list(df.columns)

        # --- Heuristics for common employee columns ---
        rut_col = next((c for c in headers if 'rut' in c.lower() and 'trab' in c.lower()), None)
        dv_col = next((c for c in headers if 'dv' in c.lower() and 'trab' in c.lower()), None)
        ape_pat_col = next((c for c in headers if 'apellido' in c.lower() and 'pater' in c.lower()), None)
        ape_mat_col = next((c for c in headers if 'apellido' in c.lower() and 'mater' in c.lower()), None)
        nombres_col = next((c for c in headers if 'nombre' in c.lower()), None)
        ingreso_col = next((c for c in headers if 'ingreso' in c.lower()), None)

        heuristic_cols = {c for c in [rut_col, dv_col, ape_pat_col, ape_mat_col, nombres_col, ingreso_col] if c}

        # --- Explicit columns to drop regardless of heuristics ---
        explicit_drop = {
            'año',
            'mes',
            'rut de la empresa',
            'rut del trabajador',
            'nombre',
            'apellido paterno',
            'apellido materno',
        }
        explicit_cols = {h for h in headers if h.strip().lower() in explicit_drop}

        empleado_cols = heuristic_cols.union(explicit_cols)
        filtered_headers = [h for h in headers if h not in empleado_cols]

        logger.info(f"Headers encontrados: {filtered_headers}")
        return filtered_headers
    except Exception as e:
        logger.error(f"Error al leer el archivo: {e}")
        raise

def clasificar_headers_libro_remuneraciones(headers, cliente):
    """
    Clasifica los headers usando los ConceptoRemuneracion vigentes del cliente.
    Retorna dos listas: clasificados y sin clasificar.
    """
    # Obtén los conceptos vigentes del cliente, normalizados a lower y sin espacios
    conceptos_vigentes = set(
        c.nombre_concepto.strip().lower()
        for c in ConceptoRemuneracion.objects.filter(cliente=cliente, vigente=True)
    )
    headers_clasificados = []
    headers_sin_clasificar = []

    for h in headers:
        if h.strip().lower() in conceptos_vigentes:
            headers_clasificados.append(h)
        else:
            headers_sin_clasificar.append(h)

    logger.info(
        f"Clasificación automática: {len(headers_clasificados)} clasificados, {len(headers_sin_clasificar)} sin clasificar"
    )
    return headers_clasificados, headers_sin_clasificar

def actualizar_empleados_desde_libro_util(libro):
    """
    Función utilitaria para actualizar empleados desde un libro de remuneraciones
    
    🧹 REPLACE COMPLETO: Elimina todos los empleados del cierre y los crea desde cero
    """
    logger.info(f"🧹 Iniciando REPLACE completo de empleados para cierre {libro.cierre.id}")
    
    # 🗑️ PASO 1: ELIMINAR todos los empleados existentes del cierre
    empleados_existentes = libro.cierre.empleados.all()
    count_eliminados = empleados_existentes.count()
    
    if count_eliminados > 0:
        # Eliminar en cascada: EmpleadoCierre → RegistroConceptoEmpleado
        empleados_existentes.delete()
        logger.info(f"🗑️ Eliminados {count_eliminados} empleados existentes y sus registros")
    
    # 📊 PASO 2: PROCESAR archivo Excel
    df = pd.read_excel(libro.archivo.path, engine="openpyxl")

    expected = {
        "ano": "Año",
        "mes": "Mes",
        "rut_empresa": "Rut de la Empresa",
        "rut_trabajador": "Rut del Trabajador",
        "nombre": "Nombre",
        "ape_pat": "Apellido Paterno",
        "ape_mat": "Apellido Materno",
    }

    missing = [v for v in expected.values() if v not in df.columns]
    if missing:
        raise ValueError(f"Faltan columnas en el Excel: {', '.join(missing)}")

    cierre = libro.cierre
    primera_col = df.columns[0]
    count = 0
    filas_ignoradas = 0
    
    for _, row in df.iterrows():
        if not str(row.get(primera_col, "")).strip():
            continue
        
        # NUEVA VALIDACIÓN: Ignorar filas con RUT inválido (NaN, vacío, "total", etc.)
        rut_raw = row.get(expected["rut_trabajador"])
        if not _es_rut_valido(rut_raw):
            filas_ignoradas += 1
            logger.debug(f"Fila ignorada por RUT inválido: '{rut_raw}' (posible fila de totales de Talana)")
            continue
        
        rut = str(rut_raw).strip()
        
        # 📝 CREAR empleado (ya no update_or_create, solo create porque limpiamos antes)
        defaults = {
            "rut_empresa": str(row.get(expected["rut_empresa"], "")).strip(),
            "nombre": str(row.get(expected["nombre"], "")).strip(),
            "apellido_paterno": str(row.get(expected["ape_pat"], "")).strip(),
            "apellido_materno": str(row.get(expected["ape_mat"], "")).strip(),
        }
        
        EmpleadoCierre.objects.create(
            cierre=cierre,
            rut=rut,
            **defaults
        )
        count += 1
    
    if filas_ignoradas > 0:
        logger.info(f"Se ignoraron {filas_ignoradas} filas con RUT inválido (posibles totales de Talana)")
    
    logger.info(f"✅ REPLACE completo terminado: {count} empleados creados desde cero para libro {libro.id}")
    return count


def guardar_registros_nomina_util(libro):
    """
    Función utilitaria para guardar registros de nómina desde un libro de remuneraciones
    
    🎯 REPLACE COMPLETO: Los RegistroConceptoEmpleado ya fueron eliminados en cascada 
    cuando se eliminaron los EmpleadoCierre, así que solo creamos los nuevos registros.
    """
    logger.info(f"📝 Iniciando creación de registros de conceptos para libro {libro.id}")
    
    df = pd.read_excel(libro.archivo.path, engine="openpyxl")

    expected = {
        "ano": "Año",
        "mes": "Mes",
        "rut_empresa": "Rut de la Empresa",
        "rut_trabajador": "Rut del Trabajador",
        "nombre": "Nombre",
        "ape_pat": "Apellido Paterno",
        "ape_mat": "Apellido Materno",
    }

    missing = [v for v in expected.values() if v not in df.columns]
    if missing:
        raise ValueError(f"Faltan columnas en el Excel: {', '.join(missing)}")

    empleado_cols = set(expected.values())

    headers = libro.header_json
    if isinstance(headers, dict):
        headers = headers.get("headers_clasificados", []) + headers.get(
            "headers_sin_clasificar", []
        )
    if not headers:
        headers = [h for h in df.columns if h not in empleado_cols]

    primera_col = df.columns[0]
    count = 0
    filas_ignoradas = 0
    
    for _, row in df.iterrows():
        if not str(row.get(primera_col, "")).strip():
            continue
        
        # NUEVA VALIDACIÓN: Ignorar filas con RUT inválido (NaN, vacío, "total", etc.)
        rut_raw = row.get(expected["rut_trabajador"])
        if not _es_rut_valido(rut_raw):
            filas_ignoradas += 1
            logger.debug(f"Fila ignorada por RUT inválido: '{rut_raw}' (posible fila de totales de Talana)")
            continue
            
        rut = str(rut_raw).strip()
        empleado = EmpleadoCierre.objects.filter(
            cierre=libro.cierre, rut=rut
        ).first()
        if not empleado:
            continue

        for h in headers:
            try:
                valor_raw = row.get(h)
                
                # Procesamiento mejorado de valores (igual que en NovedadesRemuneraciones)
                if pd.isna(valor_raw) or valor_raw == '':
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

                concepto = ConceptoRemuneracion.objects.filter(
                    cliente=libro.cierre.cliente, nombre_concepto=h, vigente=True
                ).first()
                
                # 📝 CREAR registro (ya no update_or_create porque limpiamos en cascada)
                RegistroConceptoEmpleado.objects.create(
                    empleado=empleado,
                    nombre_concepto_original=h,
                    monto=valor,
                    concepto=concepto
                )
                
            except Exception as concepto_error:
                logger.error(f"❌ ERROR en concepto '{h}' para empleado RUT {rut}: {concepto_error}")
                logger.error(f"Valor problemático: {row.get(h)}")
                raise
        count += 1
    
    if filas_ignoradas > 0:
        logger.info(f"Se ignoraron {filas_ignoradas} filas con RUT inválido (posibles totales de Talana)")

    logger.info(f"✅ Registros de conceptos creados desde cero: {count} empleados procesados para libro {libro.id}")
    return count