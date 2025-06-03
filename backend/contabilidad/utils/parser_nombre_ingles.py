import openpyxl
from contabilidad.models import CuentaContable
from django.core.files.storage import default_storage

def procesar_archivo_nombres_ingles(cliente_id, path_archivo):
    path = default_storage.path(path_archivo)
    print(f"Procesando archivo de nombres en inglés: {path}")
    wb = openpyxl.load_workbook(filename=path)
    ws = wb.active
    actualizados = 0
    for idx, row in enumerate(ws.iter_rows(min_row=2), start=2):
        codigo = str(row[0].value).strip() if row[0].value else ""
        nombre_en = str(row[1].value).strip() if len(row) > 1 and row[1].value else ""
        print(f"[Fila {idx}] codigo: '{codigo}' | nombre_en: '{nombre_en}'")
        if codigo and nombre_en:
            try:
                cuenta = CuentaContable.objects.get(cliente_id=cliente_id, codigo=codigo)
                cuenta.nombre_en = nombre_en
                cuenta.save(update_fields=["nombre_en"])
                actualizados += 1
            except CuentaContable.DoesNotExist:
                print(f"[Fila {idx}] No existe cuenta con código: '{codigo}' para cliente: {cliente_id}")
                continue
        else:
            print(f"[Fila {idx}] Código vacío o nombre_en vacío: '{codigo}', '{nombre_en}'")
    default_storage.delete(path_archivo)
    print (f"✅ Procesados {actualizados} nombres en inglés para cliente {cliente_id}")
    return actualizados
