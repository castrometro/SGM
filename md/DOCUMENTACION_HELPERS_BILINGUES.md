# Guía de Uso: Helpers Bilingües para Clasificaciones

Este documento explica cómo usar las funciones helper para detectar automáticamente el idioma del cliente y mostrar las opciones de clasificación en el idioma correcto en los informes.

## 🎯 Funciones Principales

### 1. Detección Automática de Idioma

```python
from contabilidad.utils.bilingual_helpers import detectar_idioma_cliente

# Detectar idioma del cliente
idioma = detectar_idioma_cliente(cliente_id=123)
print(idioma)  # 'es' o 'en'

# Si el cliente ya está cargado
cliente = Cliente.objects.get(id=123)
idioma = detectar_idioma_desde_objeto_cliente(cliente)
```

### 2. Obtener Opciones Bilingües

```python
from contabilidad.utils.bilingual_helpers import obtener_opciones_bilingues

# Obtener opciones con detección automática
opciones = obtener_opciones_bilingues(set_id=1, cliente_id=123)

# Usar las opciones
for opcion in opciones:
    print(opcion.get_valor(opcion._idioma_detectado))
    print(opcion.get_descripcion(opcion._idioma_detectado))

# Idioma específico
opciones = obtener_opciones_bilingues(set_id=1, idioma='en')
```

### 3. Formatear para Reportes

```python
from contabilidad.utils.bilingual_helpers import formatear_opcion_para_reporte

# Formatear una opción específica
resultado = formatear_opcion_para_reporte(opcion, cliente_id=123)
print(resultado)
# {
#     'valor': 'Current Assets',
#     'descripcion': 'Short-term assets',
#     'valor_completo': 'Current Assets - Short-term assets',
#     'idioma_usado': 'en',
#     'tiene_traduccion': True
# }
```

## 🌐 Endpoints de API

### 1. Detectar Idioma del Cliente
```
GET /contabilidad/clasificaciones/detectar-idioma/{cliente_id}/

Response:
{
    "idioma": "en",
    "es_bilingue": true,
    "cliente_nombre": "Empresa ABC"
}
```

### 2. Obtener Sets Bilingües
```
GET /contabilidad/clasificaciones/sets-bilingues/{cliente_id}/?idioma=en

Response:
{
    "idioma_detectado": "en",
    "total_sets": 2,
    "sets": [
        {
            "id": 1,
            "nombre": "Asset Classification",
            "descripcion": "Classification for assets",
            "opciones": [
                {
                    "id": 1,
                    "valor": "Current Assets",
                    "descripcion": "Short-term assets",
                    "valor_completo": "Current Assets - Short-term assets",
                    "tiene_traduccion": true
                }
            ]
        }
    ]
}
```

### 3. Estadísticas de Traducción
```
GET /contabilidad/clasificaciones/estadisticas-traduccion/{cliente_id}/

Response:
{
    "total_opciones": 25,
    "con_traduccion_completa": 20,
    "solo_espanol": 3,
    "solo_ingles": 0,
    "sin_traducir": 2,
    "porcentaje_completitud": 80.0,
    "recomendacion": "Buena cobertura de traducción. Considera completar las opciones faltantes."
}
```

### 4. Opciones de Set Específico
```
GET /contabilidad/clasificaciones/opciones-bilingues/{set_id}/?cliente_id=123

Response:
{
    "set_id": 1,
    "set_nombre": "Asset Classification",
    "idioma_usado": "en",
    "total_opciones": 5,
    "opciones": [...]
}
```

## 📊 Uso en Vistas Django

### Ejemplo 1: Vista de Reporte
```python
from rest_framework.decorators import api_view
from contabilidad.utils.bilingual_helpers import crear_filtro_idioma_para_reporte, obtener_sets_cliente_bilingues

@api_view(['GET'])
def reporte_clasificaciones(request, cliente_id):
    # Crear filtro de idioma
    filtro = crear_filtro_idioma_para_reporte(request, cliente_id)
    
    # Obtener datos bilingües
    sets = obtener_sets_cliente_bilingues(cliente_id, filtro['idioma'])
    
    return Response({
        'cliente_id': cliente_id,
        'idioma_reporte': filtro['idioma'],
        'es_cliente_bilingue': filtro['es_bilingue'],
        'sets': sets
    })
```

### Ejemplo 2: Serializer Contextual
```python
from contabilidad.serializers import ClasificacionOptionBilingueSerializer

# En una vista
def get_opciones_contextuales(request, set_id):
    opciones = ClasificacionOption.objects.filter(set_clas_id=set_id)
    
    # Pasar contexto al serializer
    serializer = ClasificacionOptionBilingueSerializer(
        opciones, 
        many=True, 
        context={'request': request}
    )
    
    return Response(serializer.data)
```

## 📝 Uso en Templates Django

### Template Filter Personalizado
```python
# En templatetags/bilingual_tags.py
from django import template
from contabilidad.utils.bilingual_helpers import detectar_idioma_cliente, formatear_opcion_para_reporte

register = template.Library()

@register.filter
def opcion_bilingue(opcion, cliente_id):
    """Template filter para mostrar opciones en el idioma correcto"""
    return formatear_opcion_para_reporte(opcion, cliente_id=cliente_id)

@register.simple_tag
def idioma_cliente(cliente_id):
    """Template tag para obtener el idioma del cliente"""
    return detectar_idioma_cliente(cliente_id)
```

### Uso en Template
```html
{% load bilingual_tags %}

<!-- Detectar idioma del cliente -->
{% idioma_cliente cliente.id as idioma_actual %}

<!-- Mostrar opción en idioma correcto -->
{% for opcion in opciones %}
    {% opcion_bilingue opcion cliente.id as opcion_formateada %}
    <div>
        <strong>{{ opcion_formateada.valor_completo }}</strong>
        <small>({{ opcion_formateada.idioma_usado }})</small>
    </div>
{% endfor %}
```

## 🔧 Uso en Reports/Informes

### Ejemplo: Reporte Excel Bilingüe
```python
import openpyxl
from contabilidad.utils.bilingual_helpers import obtener_sets_cliente_bilingues

def generar_reporte_excel(cliente_id):
    # Detectar idioma y obtener datos
    sets = obtener_sets_cliente_bilingues(cliente_id)
    idioma = sets[0]['idioma_cliente'] if sets else 'es'
    
    wb = openpyxl.Workbook()
    ws = wb.active
    
    # Headers bilingües
    headers = {
        'es': ['Código', 'Clasificación', 'Descripción'],
        'en': ['Code', 'Classification', 'Description']
    }
    
    # Usar headers apropiados
    ws.append(headers[idioma])
    
    # Datos en idioma correcto
    for set_data in sets:
        for opcion in set_data['opciones']:
            ws.append([
                set_data['nombre'],
                opcion['valor'],
                opcion['descripcion']
            ])
    
    return wb
```

## 🎨 Uso en Frontend (JavaScript)

### Fetch con detección automática
```javascript
// Detectar idioma del cliente
async function detectarIdiomaCliente(clienteId) {
    const response = await fetch(`/contabilidad/clasificaciones/detectar-idioma/${clienteId}/`);
    const data = await response.json();
    return data.idioma;
}

// Obtener opciones en idioma correcto
async function obtenerOpcionesBilingues(setId, clienteId) {
    const response = await fetch(
        `/contabilidad/clasificaciones/opciones-bilingues/${setId}/?cliente_id=${clienteId}`
    );
    return await response.json();
}

// Uso
const idioma = await detectarIdiomaCliente(123);
const opciones = await obtenerOpcionesBilingues(1, 123);

console.log('Idioma detectado:', idioma);
console.log('Opciones:', opciones.opciones);
```

## 📈 Mejores Prácticas

### 1. Cache de Detección de Idioma
```python
from django.core.cache import cache

def detectar_idioma_cliente_cached(cliente_id):
    cache_key = f"idioma_cliente_{cliente_id}"
    idioma = cache.get(cache_key)
    
    if idioma is None:
        idioma = detectar_idioma_cliente(cliente_id)
        cache.set(cache_key, idioma, 3600)  # Cache por 1 hora
    
    return idioma
```

### 2. Middleware para Detección Automática
```python
class IdiomaClienteMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Detectar cliente_id de la URL o sesión
        cliente_id = self.extraer_cliente_id(request)
        
        if cliente_id:
            request.idioma_cliente = detectar_idioma_cliente_cached(cliente_id)
        
        response = self.get_response(request)
        return response
```

### 3. Validación de Completitud
```python
# Antes de generar reportes bilingües
stats = obtener_estadisticas_traduccion(cliente_id)

if stats['porcentaje_completitud'] < 70:
    # Mostrar advertencia o usar fallback
    warnings.warn(f"Cliente {cliente_id} tiene solo {stats['porcentaje_completitud']}% de traducciones completas")
```

## 🚨 Consideraciones Importantes

1. **Performance**: Las funciones usan select_related para optimizar queries
2. **Fallbacks**: Siempre hay fallback a español si no se encuentra traducción
3. **Cache**: Considera usar cache para detección de idioma en aplicaciones de alto tráfico
4. **Validación**: Usa las estadísticas de traducción para validar completitud antes de reportes
5. **Consistencia**: Mantén coherencia en el uso de idiomas a través de toda la sesión del usuario

## 🔮 Futuras Mejoras

1. **Campo idioma_preferido en Cliente**: Permitir override manual del idioma
2. **Detección por Headers HTTP**: Usar Accept-Language del navegador
3. **Configuración por Usuario**: Preferencias de idioma por usuario
4. **API Batch**: Endpoints para obtener múltiples recursos bilingües de una vez
5. **Traducción Automática**: Integración con servicios de traducción para completar traducciones faltantes
