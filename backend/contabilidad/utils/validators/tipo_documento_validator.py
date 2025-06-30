import os
import pandas as pd


def validar_archivo_tipo_documento_excel(ruta_archivo):
    errores = []
    advertencias = []
    if not os.path.exists(ruta_archivo):
        errores.append("El archivo no existe en la ruta especificada")
        return {"es_valido": False, "errores": errores, "advertencias": advertencias, "estadisticas": {}}
    if os.path.getsize(ruta_archivo) == 0:
        errores.append("El archivo está vacío (0 bytes)")
        return {"es_valido": False, "errores": errores, "advertencias": advertencias, "estadisticas": {}}
    try:
        df = pd.read_excel(ruta_archivo)
    except Exception as e:
        errores.append(f"Error leyendo el archivo Excel: {str(e)}")
        return {"es_valido": False, "errores": errores, "advertencias": advertencias, "estadisticas": {}}
    if len(df) == 0:
        errores.append("El archivo no contiene filas de datos")
        return {"es_valido": False, "errores": errores, "advertencias": advertencias, "estadisticas": {}}
    if len(df.columns) < 2:
        errores.append("El archivo debe tener al menos 2 columnas: código y descripción")
        return {"es_valido": False, "errores": errores, "advertencias": advertencias, "estadisticas": {}}
    col_codigo = df.columns[0]
    col_desc = df.columns[1]
    codigos_vacios = 0
    codigos_duplicados = []
    codigos_largos = []
    codigos_vistos = set()
    for idx, codigo in df[col_codigo].items():
        fila = idx + 2
        if pd.isna(codigo) or str(codigo).strip() == "":
            codigos_vacios += 1
            continue
        codigo_str = str(codigo).strip()
        if len(codigo_str) > 10:
            codigos_largos.append(f"Fila {fila}: '{codigo_str}'")
        if codigo_str in codigos_vistos:
            codigos_duplicados.append(f"Fila {fila}: '{codigo_str}'")
        codigos_vistos.add(codigo_str)
    descripciones_vacias = int(df[col_desc].apply(lambda x: pd.isna(x) or str(x).strip() == "").sum())
    if codigos_largos:
        errores.append(f"Códigos demasiado largos (máximo 10 caracteres): {', '.join(codigos_largos[:3])}")
    if codigos_duplicados:
        errores.append(f"Códigos duplicados ({len(codigos_duplicados)}): {', '.join(codigos_duplicados[:3])}")
    estadisticas = {
        "total_filas": len(df),
        "codigos_vacios": codigos_vacios,
        "codigos_duplicados": len(codigos_duplicados),
        "codigos_largos": len(codigos_largos),
        "descripciones_vacias": descripciones_vacias,
    }
    es_valido = len(errores) == 0 and (len(df) - codigos_vacios) > 0
    return {
        "es_valido": es_valido,
        "errores": errores,
        "advertencias": advertencias,
        "estadisticas": estadisticas,
    }
