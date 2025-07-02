"""
Utilidades para el manejo bilingüe de opciones de clasificación y informes.

Este módulo proporciona funciones para:
1. Detectar automáticamente el idioma preferido del cliente
2. Obtener opciones de clasificación en el idioma correcto
3. Formatear datos bilingües para informes
"""

from django.conf import settings
from api.models import Cliente
from ..models import ClasificacionOption, ClasificacionSet


def detectar_idioma_cliente(cliente_id):
    """
    Detecta automáticamente el idioma preferido del cliente.
    
    Args:
        cliente_id (int): ID del cliente
        
    Returns:
        str: 'es' para español, 'en' para inglés
        
    Estrategia de detección:
    1. Si el cliente tiene el campo bilingue=True, retorna 'en'
    2. Si no, retorna 'es' (español por defecto)
    
    Futuras mejoras pueden incluir:
    - Campo idioma_preferido en el modelo Cliente
    - Configuración por usuario/sesión
    - Detección por headers HTTP Accept-Language
    """
    try:
        cliente = Cliente.objects.get(id=cliente_id)
        return 'en' if cliente.bilingue else 'es'
    except Cliente.DoesNotExist:
        # Fallback a español si no se encuentra el cliente
        return 'es'


def detectar_idioma_desde_objeto_cliente(cliente):
    """
    Detecta el idioma desde un objeto Cliente ya cargado.
    
    Args:
        cliente (Cliente): Instancia del modelo Cliente
        
    Returns:
        str: 'es' para español, 'en' para inglés
    """
    return 'en' if cliente.bilingue else 'es'


def obtener_opciones_bilingues(set_id, idioma=None, cliente_id=None):
    """
    Obtiene las opciones de clasificación en el idioma apropiado.
    
    Args:
        set_id (int): ID del set de clasificación
        idioma (str, optional): Idioma específico ('es' o 'en'). Si no se especifica, se detecta automáticamente.
        cliente_id (int, optional): ID del cliente para detección automática de idioma
        
    Returns:
        QuerySet: Opciones con métodos bilingües disponibles
        
    Usage:
        # Detección automática basada en cliente
        opciones = obtener_opciones_bilingues(set_id, cliente_id=123)
        
        # Idioma específico
        opciones = obtener_opciones_bilingues(set_id, idioma='en')
        
        # Usar las opciones
        for opcion in opciones:
            print(opcion.get_valor(idioma))
            print(opcion.get_descripcion(idioma))
    """
    if idioma is None and cliente_id is not None:
        idioma = detectar_idioma_cliente(cliente_id)
    elif idioma is None:
        idioma = 'es'  # Fallback por defecto
        
    try:
        set_clas = ClasificacionSet.objects.get(id=set_id)
        opciones = set_clas.opciones.all()
        
        # Añadir el idioma detectado como atributo para uso posterior
        for opcion in opciones:
            opcion._idioma_detectado = idioma
            
        return opciones
        
    except ClasificacionSet.DoesNotExist:
        return ClasificacionOption.objects.none()


def formatear_opcion_para_reporte(opcion, idioma=None, cliente_id=None):
    """
    Formatea una opción de clasificación para mostrar en reportes.
    
    Args:
        opcion (ClasificacionOption): La opción a formatear
        idioma (str, optional): Idioma específico ('es' o 'en')
        cliente_id (int, optional): ID del cliente para detección automática
        
    Returns:
        dict: Diccionario con los valores formateados
        
    Example:
        {
            'valor': 'Assets',
            'descripcion': 'Asset classification',
            'valor_completo': 'Assets - Asset classification',
            'idioma_usado': 'en'
        }
    """
    if idioma is None and cliente_id is not None:
        idioma = detectar_idioma_cliente(cliente_id)
    elif idioma is None:
        idioma = 'es'
        
    valor = opcion.get_valor(idioma)
    descripcion = opcion.get_descripcion(idioma)
    
    return {
        'valor': valor,
        'descripcion': descripcion,
        'valor_completo': f"{valor} - {descripcion}" if descripcion else valor,
        'idioma_usado': idioma,
        'tiene_traduccion': bool(opcion.valor_en) if idioma == 'en' else bool(opcion.valor)
    }


def obtener_sets_cliente_bilingues(cliente_id, idioma=None):
    """
    Obtiene todos los sets de clasificación de un cliente con soporte bilingüe.
    
    Args:
        cliente_id (int): ID del cliente
        idioma (str, optional): Idioma específico, si no se especifica se detecta automáticamente
        
    Returns:
        list: Lista de diccionarios con sets y sus opciones formateadas
        
    Example:
        [
            {
                'set': <ClasificacionSet>,
                'nombre': 'Asset Classification',
                'opciones': [
                    {
                        'id': 1,
                        'valor': 'Current Assets',
                        'descripcion': 'Short-term assets',
                        'valor_completo': 'Current Assets - Short-term assets'
                    },
                    ...
                ]
            },
            ...
        ]
    """
    if idioma is None:
        idioma = detectar_idioma_cliente(cliente_id)
        
    try:
        cliente = Cliente.objects.get(id=cliente_id)
        sets = ClasificacionSet.objects.filter(cliente=cliente)
        
        resultado = []
        for set_clas in sets:
            opciones_formateadas = []
            
            for opcion in set_clas.opciones.all():
                opciones_formateadas.append({
                    'id': opcion.id,
                    **formatear_opcion_para_reporte(opcion, idioma)
                })
            
            resultado.append({
                'set': set_clas,
                'id': set_clas.id,
                'nombre': set_clas.nombre,
                'descripcion': set_clas.descripcion,
                'idioma_cliente': idioma,
                'opciones': opciones_formateadas
            })
            
        return resultado
        
    except Cliente.DoesNotExist:
        return []


def crear_filtro_idioma_para_reporte(request=None, cliente_id=None):
    """
    Crea un filtro de idioma para usar en vistas y serializers de reportes.
    
    Args:
        request (HttpRequest, optional): Request para obtener preferencias del usuario
        cliente_id (int, optional): ID del cliente
        
    Returns:
        dict: Filtro con información de idioma
        
    Example:
        {
            'idioma': 'en',
            'es_bilingue': True,
            'cliente_id': 123
        }
        
    Usage en vistas:
        filtro = crear_filtro_idioma_para_reporte(request, cliente_id)
        # Usar filtro['idioma'] para obtener datos en el idioma correcto
    """
    idioma = 'es'  # Default
    es_bilingue = False
    
    if cliente_id:
        try:
            cliente = Cliente.objects.get(id=cliente_id)
            es_bilingue = cliente.bilingue
            idioma = 'en' if es_bilingue else 'es'
        except Cliente.DoesNotExist:
            pass
    
    # Futuras mejoras: chequear headers Accept-Language del request
    # if request and 'Accept-Language' in request.headers:
    #     accept_lang = request.headers['Accept-Language']
    #     if 'en' in accept_lang and es_bilingue:
    #         idioma = 'en'
    
    return {
        'idioma': idioma,
        'es_bilingue': es_bilingue,
        'cliente_id': cliente_id
    }


def validar_traduccion_completa(opcion):
    """
    Valida si una opción tiene traducción completa en ambos idiomas.
    
    Args:
        opcion (ClasificacionOption): La opción a validar
        
    Returns:
        dict: Estado de la traducción
        
    Example:
        {
            'completa': True,
            'tiene_espanol': True,
            'tiene_ingles': True,
            'faltantes': []  # o ['valor_en', 'descripcion_en']
        }
    """
    faltantes = []
    
    if not opcion.valor:
        faltantes.append('valor')
    if not opcion.valor_en:
        faltantes.append('valor_en')
    
    # Solo validar descripciones si al menos una está presente
    if opcion.descripcion or opcion.descripcion_en:
        if not opcion.descripcion:
            faltantes.append('descripcion')
        if not opcion.descripcion_en:
            faltantes.append('descripcion_en')
    
    return {
        'completa': len(faltantes) == 0,
        'tiene_espanol': bool(opcion.valor),
        'tiene_ingles': bool(opcion.valor_en),
        'faltantes': faltantes
    }


def obtener_estadisticas_traduccion(cliente_id):
    """
    Obtiene estadísticas de traducción para un cliente.
    
    Args:
        cliente_id (int): ID del cliente
        
    Returns:
        dict: Estadísticas de traducción
        
    Example:
        {
            'total_opciones': 25,
            'con_traduccion_completa': 20,
            'solo_espanol': 3,
            'solo_ingles': 0,
            'sin_traducir': 2,
            'porcentaje_completitud': 80.0
        }
    """
    try:
        cliente = Cliente.objects.get(id=cliente_id)
        sets = ClasificacionSet.objects.filter(cliente=cliente)
        
        total_opciones = 0
        con_traduccion_completa = 0
        solo_espanol = 0
        solo_ingles = 0
        sin_traducir = 0
        
        for set_clas in sets:
            opciones = set_clas.opciones.all()
            total_opciones += opciones.count()
            
            for opcion in opciones:
                validacion = validar_traduccion_completa(opcion)
                
                if validacion['completa']:
                    con_traduccion_completa += 1
                elif validacion['tiene_espanol'] and not validacion['tiene_ingles']:
                    solo_espanol += 1
                elif validacion['tiene_ingles'] and not validacion['tiene_espanol']:
                    solo_ingles += 1
                else:
                    sin_traducir += 1
        
        porcentaje_completitud = (con_traduccion_completa / total_opciones * 100) if total_opciones > 0 else 0
        
        return {
            'total_opciones': total_opciones,
            'con_traduccion_completa': con_traduccion_completa,
            'solo_espanol': solo_espanol,
            'solo_ingles': solo_ingles,
            'sin_traducir': sin_traducir,
            'porcentaje_completitud': round(porcentaje_completitud, 1)
        }
        
    except Cliente.DoesNotExist:
        return {
            'total_opciones': 0,
            'con_traduccion_completa': 0,
            'solo_espanol': 0,
            'solo_ingles': 0,
            'sin_traducir': 0,
            'porcentaje_completitud': 0.0
        }
