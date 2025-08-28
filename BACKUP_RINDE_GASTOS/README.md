# 📦 BACKUP COMPLETO - HERRAMIENTA RINDE GASTOS
## Fecha: $(date)
## Estado: Pre-reset al 31 de julio

### 🎯 DESCRIPCIÓN
Esta es la herramienta de "Captura Masiva de Gastos" que permite:
- Subir archivos Excel con gastos
- Mapear centros de costos
- Procesar facturas con diferentes tipos (33, 34, 61)
- Generar libro mayor automáticamente
- Descargar resultados procesados

### 📁 ESTRUCTURA DEL BACKUP

#### Frontend:
- `frontend_CapturaMasivaGastos/` - Página completa con componentes
- `api_capturaGastos.js` - API cliente para comunicarse con backend

#### Backend:
- `backend_contabilidad/` - App Django completa con:
  - `tasks.py` - Tareas Celery para procesamiento
  - `models.py` - Modelos de datos
  - `views/` - ViewSets de la API
  - `serializers.py` - Serializadores
  - `urls.py` - URLs de la app

#### API Integration:
- `api_views_gastos_functions.py` - Funciones específicas de gastos en api/views.py
- `api_urls_gastos.py` - URLs de gastos en api/urls.py
- `app_routes.jsx` - Rutas en App.jsx

### 🔗 ENDPOINTS PRINCIPALES
- POST `/api/captura-masiva-gastos/` - Subir archivo
- GET `/api/estado-captura-gastos/{task_id}/` - Consultar estado
- GET `/api/descargar-resultado-gastos/{task_id}/` - Descargar resultado

### 🔧 TECNOLOGÍAS
- **Frontend**: React.js, hooks personalizados
- **Backend**: Django, Celery, pandas, openpyxl
- **Processing**: Reglas de negocio complejas para tipos de documento
- **Storage**: Redis para cache, archivos temporales

### 📋 PASOS PARA REINTEGRACIÓN
1. Restaurar app `contabilidad` en Django
2. Agregar rutas en `api/urls.py`
3. Agregar funciones en `api/views.py` 
4. Restaurar página frontend en `src/pages/`
5. Agregar ruta en `App.jsx`
6. Restaurar API cliente
7. Configurar Celery para tasks de procesamiento

### ⚠️ DEPENDENCIAS IMPORTANTES
- Celery workers corriendo
- Redis para cache y resultados
- pandas, openpyxl para procesamiento Excel
- Permisos de usuario para contabilidad

### 🎨 CARACTERÍSTICAS DESTACADAS
- Interface moderna con drag & drop
- Mapeo dinámico de centros de costos
- Procesamiento asíncrono con polling
- Validación robusta de datos
- Generación automática de asientos contables
- Soporte para múltiples tipos de documento (33, 34, 61)
- Manejo inteligente de IVA y exenciones
