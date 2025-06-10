import pandas as pd
import logging

from nomina.models import ConceptoRemuneracion, LibroRemuneracionesUpload, EmpleadoCierre, RegistroConceptoEmpleado

logger = logging.getLogger(__name__)

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
    """
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
    
    for _, row in df.iterrows():
        if not str(row.get(primera_col, "")).strip():
            continue
        rut = str(row.get(expected["rut_trabajador"], "")).strip()
        defaults = {
            "rut_empresa": str(row.get(expected["rut_empresa"], "")).strip(),
            "nombre": str(row.get(expected["nombre"], "")).strip(),
            "apellido_paterno": str(row.get(expected["ape_pat"], "")).strip(),
            "apellido_materno": str(row.get(expected["ape_mat"], "")).strip(),
        }
        EmpleadoCierre.objects.update_or_create(
            cierre=cierre,
            rut=rut,
            defaults=defaults,
        )
        count += 1
    
    logger.info(f"Actualizados {count} empleados desde libro {libro.id}")
    return count


def guardar_registros_nomina_util(libro):
    """
    Función utilitaria para guardar registros de nómina desde un libro de remuneraciones
    """
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
    
    for _, row in df.iterrows():
        if not str(row.get(primera_col, "")).strip():
            continue
        rut = str(row.get(expected["rut_trabajador"], "")).strip()
        empleado = EmpleadoCierre.objects.filter(
            cierre=libro.cierre, rut=rut
        ).first()
        if not empleado:
            continue

        for h in headers:
            try:
                valor_raw = row.get(h)
                
                # Convertir todo a string y limpiar
                if pd.isna(valor_raw) or valor_raw == '':
                    valor = ""  # Valor vacío
                else:
                    valor = str(valor_raw).strip()
                    # Si es "nan" como string, convertir a vacío
                    if valor.lower() == 'nan':
                        valor = ""

                concepto = ConceptoRemuneracion.objects.filter(
                    cliente=libro.cierre.cliente, nombre_concepto=h, vigente=True
                ).first()
                
                RegistroConceptoEmpleado.objects.update_or_create(
                    empleado=empleado,
                    nombre_concepto_original=h,
                    defaults={"monto": valor, "concepto": concepto},
                )
                
            except Exception as concepto_error:
                logger.error(f"❌ ERROR en concepto '{h}' para empleado RUT {rut}: {concepto_error}")
                logger.error(f"Valor problemático: {row.get(h)}")
                raise
        count += 1

    logger.info(f"Registros nómina guardados desde libro {libro.id}: {count}")
    return count