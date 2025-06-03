#backend/contabilidad/tasks.py
from celery import shared_task
from contabilidad.utils.parser_tipo_documento import parsear_tipo_documento_excel
from contabilidad.utils.parser_libro_mayor import parsear_libro_mayor
from contabilidad.utils.parser_nombre_ingles import procesar_archivo_nombres_ingles
from contabilidad.models import LibroMayorUpload
from django.utils import timezone
from django.core.files.storage import default_storage
import time
import os


@shared_task
def tarea_de_prueba(nombre):
    print(f"👋 ¡Hola {nombre} desde Celery!") #print1
    time.sleep(999)
    print("✅ Tarea completada.") #print2
    return f"Completado por {nombre}" #esto sale en succeeded


@shared_task
def parsear_tipo_documento(cliente_id, ruta_relativa):
    ok, msg = parsear_tipo_documento_excel(cliente_id, ruta_relativa)
    if ok:
        print("✅", msg)
    else:
        print("❌", msg)
    return msg

@shared_task
def procesar_libro_mayor(libro_mayor_id):
    libro = LibroMayorUpload.objects.get(id=libro_mayor_id)
    cierre = libro.cierre
    ruta = libro.archivo.path

    # 1. Al iniciar: Procesando
    libro.estado = "procesando"
    libro.save()
    cierre.estado = "procesando"
    cierre.save(update_fields=["estado"])

    try:
        errores, fecha_inicio, fecha_fin, resumen = parsear_libro_mayor(ruta, libro)
        libro.estado = "completado" if not errores else "error"
        libro.errores = "\n".join(errores)
        libro.save()

        # Actualiza fechas en el cierre
        if fecha_inicio:
            cierre.fecha_inicio_libro = fecha_inicio
        if fecha_fin:
            cierre.fecha_fin_libro = fecha_fin

        cierre.cuentas_nuevas = resumen.get("cuentas_nuevas", 0)
        cierre.resumen_parsing = resumen
        cierre.parsing_completado = True

        # 2. Al terminar, cambia a Esperando Clasificación o Completo
        if errores:
            cierre.estado = "pendiente"  # O el estado que uses para error
        elif resumen.get("cuentas_nuevas", 0) > 0:
            cierre.estado = "clasificacion"  # O "esperando_clasificacion" según tu lista de choices
        else:
            cierre.estado = "completo"
        cierre.save(update_fields=[
            'fecha_inicio_libro', 
            'fecha_fin_libro',
            'cuentas_nuevas', 
            'resumen_parsing',
            'parsing_completado',
            'estado'
        ])
    except Exception as e:
        libro.estado = "error"
        libro.errores = str(e)
        libro.save()
        cierre.estado = "pendiente"  # O "error" según prefieras
        cierre.save(update_fields=["estado"])


@shared_task
def procesar_nombres_ingles(cliente_id, path_archivo):
    actualizados = procesar_archivo_nombres_ingles(cliente_id, path_archivo)
    # Borra archivo temporal
    try:
        os.remove(path_archivo)
    except Exception:
        pass
    return actualizados