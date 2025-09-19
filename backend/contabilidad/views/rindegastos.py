from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from openpyxl import load_workbook, Workbook
from io import BytesIO
import unicodedata
from django.http import HttpResponse
import json
from contabilidad.tasks import (
    get_headers_salida_contabilidad,
    get_redis_client_db1,
    get_redis_client_db1_binary,
)
from contabilidad.task_rindegastos import rg_procesar_step1_task


def _normalize(text):
    if text is None:
        return ""
    if not isinstance(text, str):
        text = str(text)
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
    return text.strip().lower()


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def leer_headers_excel_rindegastos(request):
    """
    Contabilidad: Endpoint exclusivo RindeGastos para leer headers y detectar CC
    como el rango entre la última columna 'Nombre cuenta' y la columna 'Fecha aprobacion'.
    """
    try:
        if 'archivo' not in request.FILES:
            return Response({'error': 'No se encontró archivo en la petición'}, status=400)

        archivo = request.FILES['archivo']

        if not archivo.name.lower().endswith(('.xlsx', '.xls')):
            return Response({'error': 'El archivo debe ser un Excel (.xlsx o .xls)'}, status=400)

        contenido = archivo.read()
        wb = load_workbook(BytesIO(contenido), read_only=True)
        ws = wb.active

        primera_fila = next(ws.iter_rows(min_row=1, max_row=1, values_only=True))
        headers = [(v if v is not None else '') for v in primera_fila]

        # Última columna que contiene "Nombre cuenta"
        last_nombre_idx = -1
        for i, h in enumerate(headers):
            if 'nombre cuenta' in _normalize(h):
                last_nombre_idx = i

        # Columna de "Fecha aprobacion"
        fecha_ap_idx = None
        for i, h in enumerate(headers):
            hn = _normalize(h)
            if 'fecha' in hn and 'aprobacion' in hn:
                fecha_ap_idx = i
                break

        centros_costo = {}
        if last_nombre_idx != -1 and fecha_ap_idx is not None and fecha_ap_idx - last_nombre_idx > 1:
            for pos in range(last_nombre_idx + 1, fecha_ap_idx):
                nombre = headers[pos]
                if nombre and str(nombre).strip() != '':
                    centros_costo[str(nombre)] = {"posicion": pos, "nombre": str(nombre)}

        # Fallback por nombres conocidos
        if not centros_costo:
            conocidos = ['PyC', 'PS', 'EB', 'CO', 'RE', 'TR', 'CF', 'LRC']
            for i, h in enumerate(headers):
                hs = str(h).strip() if h is not None else ''
                if hs in conocidos:
                    centros_costo[hs] = {"posicion": i, "nombre": hs}

        wb.close()

        return Response({
            'headers': [str(h) if h is not None else '' for h in headers],
            'total_columnas': len(headers),
            'centros_costo': centros_costo,
            'mensaje': 'Headers leídos exitosamente (RindeGastos/Contabilidad)'
        })

    except Exception as e:
        return Response({'error': f'Error leyendo headers del Excel: {str(e)}'}, status=500)


def _find_cc_range(headers):
    """Encuentra el rango (start_exclusive, end_inclusive_exclusive) para CC: entre última 'Nombre cuenta' y 'Fecha aprobacion'.
    Retorna (start_idx, end_idx). Si no hay coincidencia válida, retorna (None, None)."""
    last_nombre_idx = -1
    for i, h in enumerate(headers):
        if 'nombre cuenta' in _normalize(h):
            last_nombre_idx = i
    fecha_ap_idx = None
    for i, h in enumerate(headers):
        hn = _normalize(h)
        if 'fecha' in hn and 'aprobacion' in hn:
            fecha_ap_idx = i
            break
    if last_nombre_idx != -1 and fecha_ap_idx is not None and fecha_ap_idx - last_nombre_idx > 1:
        return last_nombre_idx + 1, fecha_ap_idx
    return None, None


def _parse_numeric(value):
    """Intenta parsear a float. Acepta strings con % o espacios. Retorna None si no parseable."""
    if value is None:
        return None
    try:
        if isinstance(value, str):
            s = value.replace('%', '').replace(',', '.').strip()
            if s == '':
                return None
            return float(s)
        if isinstance(value, (int, float)):
            return float(value)
    except Exception:
        return None
    return None


def _sanitize_sheet_name(name: str) -> str:
    s = str(name).replace(':', '-').replace('/', '-').replace('\\', '-')
    return s[:31] if len(s) > 31 else s


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def procesar_step1_rindegastos(request):
    """
    Inicia Step1 de forma asíncrona: sube archivo, dispara Celery y retorna task_id.
    """
    try:
        if 'archivo' not in request.FILES:
            return Response({'error': 'No se encontró archivo en la petición'}, status=400)

        archivo = request.FILES['archivo']
        if not archivo.name.lower().endswith(('.xlsx', '.xls')):
            return Response({'error': 'El archivo debe ser un Excel (.xlsx o .xls)'}, status=400)

        contenido = archivo.read()

        task = rg_procesar_step1_task.delay(contenido, archivo.name, request.user.id)
        return Response({
            'task_id': task.id,
            'estado': 'procesando',
            'archivo_nombre': archivo.name,
            'mensaje': 'Archivo enviado para Step1 (RG)'
        }, status=202)
    except Exception as e:
        return Response({'error': f'Error iniciando Step1: {str(e)}'}, status=500)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def procesar_step1_sync_rindegastos(request):
    """
    Fallback sincrónico: genera y devuelve el Excel de Step1 directamente.
    """
    try:
        if 'archivo' not in request.FILES:
            return Response({'error': 'No se encontró archivo en la petición'}, status=400)

        archivo = request.FILES['archivo']
        if not archivo.name.lower().endswith(('.xlsx', '.xls')):
            return Response({'error': 'El archivo debe ser un Excel (.xlsx o .xls)'}, status=400)

        contenido = archivo.read()
        wb_in = load_workbook(BytesIO(contenido), read_only=True)
        ws_in = wb_in.active

        headers = [(v if v is not None else '') for v in next(ws_in.iter_rows(min_row=1, max_row=1, values_only=True))]

        # Ubicar columna Tipo Doc
        idx_tipo_doc = None
        for i, h in enumerate(headers):
            if _normalize(h) == 'tipo doc':
                idx_tipo_doc = i
                break
        if idx_tipo_doc is None:
            return Response({'error': "No se encontró la columna 'Tipo Doc'"}, status=400)

        # Rango de CC por regla dinámica
        cc_start, cc_end = _find_cc_range(headers)

        # Fallback: CC conocidos si no hay rango
        conocidos = ['PyC', 'PS', 'EB', 'CO', 'RE', 'TR', 'CF', 'LRC']
        cc_indices_conocidos = {str(h).strip(): i for i, h in enumerate(headers) if str(h).strip() in conocidos}

        grupos = {}
        # Recorrer filas
        for row in ws_in.iter_rows(min_row=2, values_only=True):
            if not row or not any(row):
                continue
            tipo_doc = row[idx_tipo_doc] if idx_tipo_doc < len(row) else None
            tipo_doc = str(tipo_doc) if tipo_doc is not None else 'Sin Tipo'

            # Contar CC válidos
            cc_count = 0
            if cc_start is not None and cc_end is not None:
                for col in range(cc_start, cc_end):
                    val = row[col] if col < len(row) else None
                    num = _parse_numeric(val)
                    if num is not None and abs(num) > 0:
                        cc_count += 1
            else:
                # Fallback por nombres conocidos
                vistos = set()
                for nombre, col in cc_indices_conocidos.items():
                    if nombre == 'EB' and 'PS' in cc_indices_conocidos:
                        # evitar duplicar PS/EB equivalentes si ambos estuvieran
                        continue
                    val = row[col] if col < len(row) else None
                    num = _parse_numeric(val)
                    if num is not None and abs(num) > 0 and nombre not in vistos:
                        cc_count += 1
                        vistos.add(nombre)

            clave = f"{tipo_doc} con {cc_count}CC"
            grupos[clave] = grupos.get(clave, 0) + 1

        wb_in.close()

        # Crear workbook de salida con una hoja por grupo y headers contables
        wb_out = Workbook()
        # Remover sheet por defecto
        default_sheet = wb_out.active
        wb_out.remove(default_sheet)

        headers_salida = get_headers_salida_contabilidad()
        for clave in sorted(grupos.keys()):
            ws = wb_out.create_sheet(title=_sanitize_sheet_name(clave))
            for col_idx, h in enumerate(headers_salida, start=1):
                ws.cell(row=1, column=col_idx, value=h)

        buffer = BytesIO()
        wb_out.save(buffer)
        data = buffer.getvalue()

        response = HttpResponse(
            data,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="rg_step1_{request.user.id}.xlsx"'
        return response

    except Exception as e:
        return Response({'error': f'Error en procesamiento step1 (sync): {str(e)}'}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def estado_step1_rindegastos(request, task_id):
    try:
        r = get_redis_client_db1()
        meta_raw = r.get(f"rg_step1_meta:{request.user.id}:{task_id}")
        if not meta_raw:
            return Response({'error': 'No se encontró información de la tarea'}, status=404)
        return Response(json.loads(meta_raw))
    except Exception as e:
        return Response({'error': f'Error consultando estado: {str(e)}'}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def descargar_step1_rindegastos(request, task_id):
    try:
        r = get_redis_client_db1()
        meta_raw = r.get(f"rg_step1_meta:{request.user.id}:{task_id}")
        if not meta_raw:
            return Response({'error': 'No se encontró información de la tarea'}, status=404)
        meta = json.loads(meta_raw)
        if meta.get('estado') != 'completado':
            return Response({'error': 'La tarea aún no ha sido completada'}, status=400)

        r_bin = get_redis_client_db1_binary()
        excel_content = r_bin.get(f"rg_step1_excel:{request.user.id}:{task_id}")
        if not excel_content:
            return Response({'error': 'El archivo procesado no está disponible'}, status=404)

        resp = HttpResponse(
            excel_content,
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        resp['Content-Disposition'] = f'attachment; filename="rg_step1_{task_id}.xlsx"'
        return resp
    except Exception as e:
        return Response({'error': f'Error descargando archivo: {str(e)}'}, status=500)
