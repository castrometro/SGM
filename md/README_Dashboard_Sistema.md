# Dashboard Contable SGM - Integración con Sistema de Cierre

## Descripción

El dashboard de Streamlit ha sido actualizado para integrarse directamente con el sistema de cache Redis del backend SGM, mostrando los datos finales generados por el sistema de cierre contable.

## Características Principales

### 🔴 Sistema de Cierre (Redis)
- **Datos finales del sistema**: Estados financieros generados automáticamente
- **Estados disponibles**: ESF, ESR, ERI, ECP
- **Información adicional**: KPIs, alertas, estado de procesamiento
- **Datos en tiempo real**: Sincronizado con el backend

### 🟠 Datos de Pruebas (Redis)
- **Datos de testing**: ESF de pruebas de diferentes tipos
- **Compatibilidad legacy**: Mantiene funcionalidad anterior
- **Útil para desarrollo**: Testing y validación

### 📁 Archivo de Ejemplo
- **Datos estáticos**: Para demostración sin Redis
- **Fallback**: Cuando Redis no está disponible

## Estructura de Datos en Redis

### Cache del Sistema SGM
```
sgm:contabilidad:{cliente_id}:{periodo}/
├── esf          # Estado de Situación Financiera
├── esr          # Estado de Resultados  
├── eri          # Estado de Resultados Integral
├── ecp          # Estado de Cambios en el Patrimonio
├── kpis         # Indicadores clave
├── alertas      # Alertas del sistema
├── procesamiento # Estado del procesamiento
├── movimientos  # Movimientos contables
└── cuentas      # Catálogo de cuentas
```

### Estructura del ESF (Ejemplo)
```json
{
  "metadata": {
    "cliente_id": 1,
    "cliente_nombre": "Empresa Demo",
    "periodo": "2025-07",
    "fecha_generacion": "2025-07-08T...",
    "moneda": "CLP"
  },
  "activos": {
    "corrientes": {
      "grupos": {...},
      "total": 100000000
    },
    "no_corrientes": {
      "grupos": {...}, 
      "total": 100000000
    },
    "total_activos": 200000000
  },
  "pasivos": {...},
  "patrimonio": {...},
  "totales": {
    "total_pasivos_patrimonio": 200000000,
    "diferencia": 0
  }
}
```

## Configuración y Uso

### 1. Configurar Redis

El sistema utiliza Redis DB 1 para datos de contabilidad:

```bash
# Variables de entorno (ya configuradas en Docker)
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=Redis_Password_2025!
REDIS_DB_CONTABILIDAD=1
```

### 2. Poblar Cache con Datos de Ejemplo

Para testing y demostración:

```bash
cd /root/SGM
python poblar_cache_dashboard.py
```

Esto creará:
- ESF completo con activos, pasivos y patrimonio
- ESR con ingresos y gastos
- KPIs del cierre
- Alertas del sistema
- Estado de procesamiento

### 3. Ejecutar Streamlit

```bash
cd /root/SGM/streamlit_conta
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

### 4. Usar el Dashboard

1. **Seleccionar fuente de datos**:
   - 🔴 Sistema de Cierre: Datos finales del backend
   - 🟠 Datos de Pruebas: ESF de testing
   - 📁 Archivo de Ejemplo: Datos estáticos

2. **Configurar parámetros**:
   - Cliente ID: 1 (por defecto)
   - Período: 2025-07 (formato YYYY-MM)

3. **Explorar reportes**:
   - 📊 Dashboard General: Resumen ejecutivo
   - 🏛️ ESF: Estado de Situación Financiera
   - 📈 ESR: Estado de Resultados
   - 📊 ERI: Estado de Resultados Integral
   - 💰 ECP: Estado de Cambios en el Patrimonio
   - ⚠️ Alertas y KPIs: Indicadores del sistema

## Integración con el Backend

### Guardado Automático en Redis

Cuando el sistema genera reportes finales (por ejemplo, en `tasks_reportes.py`), automáticamente guarda los datos en Redis:

```python
from .cache_redis import get_cache_system

cache_system = get_cache_system()
cache_system.set_estado_financiero(
    cliente_id=cierre.cliente.id,
    periodo=cierre.periodo,
    tipo_estado='esf',
    datos=datos_esf
)
```

### Carga Inteligente en Streamlit

El dashboard busca datos en orden de prioridad:
1. **Sistema de cierre**: Datos finales en Redis
2. **Datos de pruebas**: ESF de testing
3. **Archivo de ejemplo**: Fallback estático

```python
# En loader_contabilidad.py
datos_sistema = cargar_datos_sistema_cierre(cliente_id, periodo)
if datos_sistema:
    # Usar datos del sistema
else:
    # Fallback a pruebas o ejemplo
```

## Nuevas Funcionalidades

### Dashboard General Mejorado
- KPIs del sistema de cierre
- Métricas de ESF automáticas
- Indicadores del ESR si está disponible
- Estado de completitud de datos

### Estados Financieros del Sistema
- **ESF**: Estructura completa con activos, pasivos y patrimonio
- **ESR**: Ingresos, gastos y márgenes automáticos
- **ERI**: Resultado integral con componentes OCI
- **ECP**: Movimientos patrimoniales del período

### Vista de Alertas y KPIs
- KPIs específicos del cierre
- Alertas del sistema
- Estado del procesamiento
- Métricas de performance

### Información Contextual
- Fuente de datos clara
- Metadata de generación
- Estado del cierre
- Completitud de información

## Desarrollo y Extensiones

### Agregar Nuevos Estados Financieros

1. **En el backend** (`tasks_reportes.py`):
```python
# Generar datos del nuevo estado
datos_estado = _generar_nuevo_estado(cierre)

# Guardar en Redis
cache_system.set_estado_financiero(
    cliente_id=cierre.cliente.id,
    periodo=cierre.periodo,
    tipo_estado='nuevo_estado',
    datos=datos_estado
)
```

2. **En Streamlit** (`estados_financieros_sistema.py`):
```python
def mostrar_nuevo_estado(data):
    estado_data = data.get('nuevo_estado', {})
    if not estado_data:
        st.warning("Estado no disponible")
        return
    
    # Lógica de visualización
```

3. **Agregar al sidebar** (`sidebar.py`):
```python
selected_tab = st.sidebar.radio("Selecciona un reporte:", [
    # ... otros reportes
    "📋 Nuevo Estado Financiero"
])
```

### Personalizar KPIs

Modificar `crear_datos_ejemplo_kpis()` en `poblar_cache_dashboard.py` o agregar lógica de cálculo automático en el backend.

### Agregar Gráficos

Usar Plotly para visualizaciones interactivas:
```python
import plotly.graph_objects as go

fig = go.Figure(data=[
    go.Bar(x=categorias, y=valores)
])
st.plotly_chart(fig, use_container_width=True)
```

## Solución de Problemas

### Redis no conecta
```bash
# Verificar estado de Redis
docker exec -it sgm-redis-1 redis-cli ping

# Verificar logs
docker logs sgm-redis-1
```

### Cache vacío
```bash
# Poblar con datos de ejemplo
python poblar_cache_dashboard.py

# Verificar datos en Redis
docker exec -it sgm-redis-1 redis-cli
> SELECT 1
> KEYS sgm:contabilidad:*
```

### Streamlit no carga datos
1. Verificar conexión a Redis en logs
2. Comprobar variables de entorno
3. Usar modo de datos de ejemplo como fallback

### Datos incompletos
El dashboard muestra el nivel de completitud:
- 🎯 Datos completos (5+ tipos)
- 🔗 Datos parciales (2-4 tipos)  
- ⚠️ Datos limitados (1-2 tipos)

## Monitoreo

### Estadísticas de Cache
El sistema proporciona métricas de uso:
```python
stats = cache_system.get_cache_stats()
# cache_hits, cache_misses, cache_writes, etc.
```

### Health Check
```python
health = cache_system.health_check()
# Estado de conexión, memoria, estadísticas
```

## Roadmap

### Próximas Funcionalidades
- [ ] Comparación de períodos múltiples
- [ ] Exportación de reportes a PDF/Excel
- [ ] Gráficos de evolución temporal
- [ ] Alertas configurables por usuario
- [ ] Dashboard personalizable por rol
- [ ] Integración con sistema de autenticación
- [ ] API REST para datos de dashboard
- [ ] Notificaciones en tiempo real

### Mejoras Técnicas
- [ ] Cache distribuido para múltiples instancias
- [ ] Compresión de datos en Redis
- [ ] TTL dinámico basado en uso
- [ ] Backup automático de cache
- [ ] Métricas de performance detalladas
