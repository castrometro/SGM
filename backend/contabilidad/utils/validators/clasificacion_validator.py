import os
import re
import pandas as pd
from django.db import models


def validar_archivo_clasificacion_excel(ruta_archivo, cliente_id):
    """Validation logic extracted from tasks."""
    errores = []
    advertencias = []
    estadisticas = {}
    try:
        if not os.path.exists(ruta_archivo):
            errores.append("El archivo no existe en la ruta especificada")
            return {'es_valido': False, 'errores': errores, 'advertencias': advertencias, 'estadisticas': estadisticas}
        if os.path.getsize(ruta_archivo) == 0:
            errores.append("El archivo está vacío (0 bytes)")
            return {'es_valido': False, 'errores': errores, 'advertencias': advertencias, 'estadisticas': estadisticas}
        df = pd.read_excel(ruta_archivo)
        if len(df) == 0:
            errores.append("El archivo no contiene filas de datos (solo headers o completamente vacío)")
            return {'es_valido': False, 'errores': errores, 'advertencias': advertencias, 'estadisticas': estadisticas}
        if len(df.columns) < 2:
            errores.append("El archivo debe tener al menos 2 columnas: códigos de cuenta y al menos un set de clasificación")
            return {'es_valido': False, 'errores': errores, 'advertencias': advertencias, 'estadisticas': estadisticas}
        columna_cuentas = df.columns[0]
        sets_columnas = list(df.columns[1:])
        for i, set_nombre in enumerate(sets_columnas, 2):
            if pd.isna(set_nombre) or str(set_nombre).strip() == '':
                errores.append(f"La columna {chr(65+i)} (columna {i+1}) no tiene nombre de set válido")
            elif len(str(set_nombre).strip()) > 100:
                errores.append(f"Nombre de set demasiado largo en columna {chr(65+i)}: '{str(set_nombre)[:50]}...' (máximo 100 caracteres)")
        cuentas_validas = 0
        cuentas_vacias = 0
        cuentas_formato_invalido = []
        cuentas_duplicadas = []
        patron_cuenta = r'^[\d\-]+$'
        cuentas_vistas = set()
        for index, cuenta in df[columna_cuentas].items():
            fila_excel = index + 2
            if pd.isna(cuenta) or str(cuenta).strip() == '':
                cuentas_vacias += 1
                continue
            cuenta_str = str(cuenta).strip()
            if not re.match(patron_cuenta, cuenta_str):
                cuentas_formato_invalido.append(f"Fila {fila_excel}: '{cuenta_str}'")
                continue
            if cuenta_str in cuentas_vistas:
                cuentas_duplicadas.append(f"Fila {fila_excel}: '{cuenta_str}'")
            else:
                cuentas_vistas.add(cuenta_str)
            cuentas_validas += 1
        filas_sin_clasificaciones = []
        clasificaciones_vacias_por_set = {set_name: 0 for set_name in sets_columnas}
        valores_muy_largos = []
        for index, row in df.iterrows():
            fila_excel = index + 2
            cuenta = row[columna_cuentas]
            if pd.isna(cuenta) or str(cuenta).strip() == '':
                continue
            tiene_alguna_clasificacion = False
            for set_nombre in sets_columnas:
                valor = row[set_nombre]
                if pd.isna(valor) or str(valor).strip() == '':
                    clasificaciones_vacias_por_set[set_nombre] += 1
                else:
                    tiene_alguna_clasificacion = True
                    if len(str(valor).strip()) > 100:
                        valores_muy_largos.append(f"Fila {fila_excel}, Set '{set_nombre}': '{str(valor)[:50]}...'")
            if not tiene_alguna_clasificacion:
                filas_sin_clasificaciones.append(f"Fila {fila_excel}: '{str(cuenta).strip()}'")
        if cuentas_formato_invalido:
            errores.append(f"Códigos de cuenta con caracteres inválidos ({len(cuentas_formato_invalido)}): {', '.join(cuentas_formato_invalido[:3])}")
            if len(cuentas_formato_invalido) > 3:
                errores.append(f"... y {len(cuentas_formato_invalido) - 3} más")
            errores.append("Los códigos de cuenta solo pueden contener números y guiones (-)")
        if cuentas_duplicadas:
            errores.append(f"Códigos de cuenta duplicados ({len(cuentas_duplicadas)}): {', '.join(cuentas_duplicadas[:3])}")
            if len(cuentas_duplicadas) > 3:
                errores.append(f"... y {len(cuentas_duplicadas) - 3} más")
        if valores_muy_largos:
            errores.append(f"Valores de clasificación demasiado largos (máximo 100 caracteres): {', '.join(valores_muy_largos[:3])}")
        if cuentas_vacias > 0:
            advertencias.append(f"Se encontraron {cuentas_vacias} filas con códigos de cuenta vacíos (serán omitidas)")
        if filas_sin_clasificaciones:
            advertencias.append(f"Cuentas sin ninguna clasificación ({len(filas_sin_clasificaciones)}): {', '.join(filas_sin_clasificaciones[:3])}")
            if len(filas_sin_clasificaciones) > 3:
                advertencias.append(f"... y {len(filas_sin_clasificaciones) - 3} más")
        for set_nombre, vacias in clasificaciones_vacias_por_set.items():
            if vacias > 0:
                porcentaje = (vacias / len(df)) * 100
                if porcentaje > 50:
                    advertencias.append(f"Set '{set_nombre}': {vacias} cuentas sin clasificación ({porcentaje:.1f}%)")
        estadisticas = {
            'total_filas': len(df),
            'total_sets': len(sets_columnas),
            'sets_nombres': sets_columnas,
            'cuentas_validas': cuentas_validas,
            'cuentas_vacias': cuentas_vacias,
            'cuentas_formato_invalido': len(cuentas_formato_invalido),
            'cuentas_duplicadas': len(cuentas_duplicadas),
            'filas_sin_clasificaciones': len(filas_sin_clasificaciones),
            'clasificaciones_vacias_por_set': clasificaciones_vacias_por_set
        }
        es_valido = len(errores) == 0 and cuentas_validas > 0
        return {'es_valido': es_valido, 'errores': errores, 'advertencias': advertencias, 'estadisticas': estadisticas}
    except Exception as e:
        errores.append(f"Error inesperado validando archivo: {str(e)}")
        return {'es_valido': False, 'errores': errores, 'advertencias': advertencias, 'estadisticas': estadisticas}
