# backend/nomina/utils/clientes.py

def get_client_ip(request):
    """
    Obtiene la IP del cliente de la request
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_user_agent(request):
    """
    Obtiene el User-Agent del cliente
    """
    return request.META.get('HTTP_USER_AGENT', '')


def get_client_info(request):
    """
    Obtiene información completa del cliente
    """
    return {
        'ip': get_client_ip(request),
        'user_agent': get_user_agent(request),
        'referer': request.META.get('HTTP_REFERER', ''),
        'method': request.method,
        'path': request.path,
    }
