[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/castrometro/SGM)

Based on the documentation found in your repository, here's a comprehensive README file:

---

# SGM - Sistema de Gestión de Movimientos

Sistema integral de gestión financiera que incluye módulos de contabilidad, nómina y procesamiento masivo de gastos.

## 📋 Descripción

SGM (Sistema de Gestión de Movimientos) es una plataforma completa para la gestión de datos financieros que incluye:

- **Módulo de Contabilidad**: Manejo de estados financieros (ESF, ERI, ECP), cierres contables y procesamiento de gastos
- **Módulo de Nómina**: Gestión de datos y reportes de nómina
- **Captura Masiva de Gastos**: Procesamiento masivo de gastos desde archivos Excel [1](#0-0) 

## 🏗️ Arquitectura

El sistema utiliza una arquitectura moderna con los siguientes componentes: [2](#0-1) 

- **Frontend React**: Interfaz de usuario con Vite y TailwindCSS
- **Backend Django**: API REST con Django REST Framework
- **PostgreSQL**: Base de datos relacional
- **Redis**: Sistema de caché y cola de tareas
- **Celery**: Procesamiento asíncrono de archivos Excel
- **Nginx**: Servidor web y proxy reverso

## 📊 Requisitos del Sistema

### Configuración Mínima (Pruebas) [3](#0-2) 

- CPU: 2 cores
- RAM: 6 GB
- Almacenamiento: 50 GB SSD
- Red: 10 Mbps
- Capacidad: 2-3 usuarios simultáneos

### Configuración Recomendada (Producción) [4](#0-3) 

- CPU: 4 cores
- RAM: 8 GB
- Almacenamiento: 100 GB SSD
- Red: 50 Mbps
- Capacidad: 3-5 usuarios simultáneos

### Configuración Óptima (Futuro-proof) [5](#0-4) 

- CPU: 6 cores
- RAM: 16 GB
- Almacenamiento: 200 GB NVMe SSD
- Red: 100 Mbps
- Capacidad: 5+ usuarios simultáneos

## 🚀 Instalación y Configuración

### Prerrequisitos

- Docker y Docker Compose
- Node.js >= 20.19.5 [6](#0-5) 
- npm >= 11.6.2

### Variables de Entorno

Crear un archivo `.env` en la raíz del proyecto: [7](#0-6) 

```env
# Base de datos
POSTGRES_PASSWORD=tu_password_seguro_aqui
POSTGRES_DB=sgm_contabilidad
POSTGRES_USER=sgm_user
POSTGRES_HOST=db
POSTGRES_PORT=5432

# Django
SECRET_KEY=tu_secret_key_django_aqui
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,tu-dominio.com

# Redis
REDIS_PASSWORD=tu_redis_password_aqui

# Configuración para usuarios concurrentes
MAX_CONCURRENT_UPLOADS=3
MAX_FILE_SIZE=50MB
CELERY_WORKER_CONCURRENCY=2
```

### Iniciar el Sistema

```bash
# Levantar los servicios con Docker Compose
docker-compose up -d

# Ejecutar migraciones
docker-compose exec django python manage.py migrate

# Crear superusuario
docker-compose exec django python manage.py createsuperuser

# Construir el frontend
npm install
npm run build
```

## 🛠️ Tecnologías

### Frontend [8](#0-7) 

- React 19.0.0
- Vite 7.1.9
- TailwindCSS 4.0.13
- React Router DOM 7.3.0
- Axios 1.9.0
- Lucide React (iconos)
- DaisyUI 5.0.3
- XLSX 0.18.5

### Backend [9](#0-8) 

- Django 5.2.7
- Django REST Framework 3.16.0
- Celery 5.5.2
- Redis 6.0.0
- PostgreSQL (psycopg2-binary 2.9.10)
- Pandas 2.2.3
- OpenPyXL 3.1.5

## 📁 Estructura del Proyecto

```
SGM/
├── backend/                 # Aplicación Django
│   ├── api/                # API endpoints
│   ├── contabilidad/       # Módulo de contabilidad
│   ├── nomina/             # Módulo de nómina
│   └── sgm_backend/        # Configuración Django
├── frontend/               # Aplicación React (build)
├── src/                    # Código fuente React
│   ├── api/               # Servicios API
│   ├── components/        # Componentes compartidos
│   ├── pages/             # Páginas de la aplicación
│   └── hooks/             # Custom hooks
├── docs/                   # Documentación
├── scripts/               # Scripts de utilidad
├── streamlit_conta/       # Dashboard de contabilidad
├── streamlit_nomina/      # Dashboard de nómina
├── docker-compose.yml     # Configuración Docker
└── package.json           # Dependencias frontend
```

## 🔧 Comandos Útiles

### Backend (Django)

```bash
# Ejecutar tests
docker-compose exec django python manage.py test
``` [10](#0-9) 

### Celery Worker

```bash
# Iniciar worker de Celery
cd backend
./celery_worker.sh
``` [11](#0-10) 

### Frontend

```bash
# Modo desarrollo
npm run dev

# Construir para producción
npm run build

# Vista previa de producción
npm run preview
``` [12](#0-11) 

### Docker

```bash
# Ver logs en tiempo real
docker-compose logs -f

# Reiniciar servicio específico
docker-compose restart celery_worker

# Backup de base de datos
docker-compose exec db pg_dump -U sgm_user sgm_contabilidad > backup_$(date +%Y%m%d).sql
```

## 📈 Funcionalidades Principales

### Captura Masiva de Gastos [13](#0-12) 

- Carga de archivos Excel con múltiples gastos
- Detección automática de centros de costos
- Configuración dinámica de mapeo contable
- Procesamiento asíncrono con Celery
- Monitoreo en tiempo real del procesamiento
- Descarga de resultados procesados

### Registro de Nómina [14](#0-13) 

- Procesamiento de Libro de Remuneraciones
- Almacenamiento en modelo `RegistroNomina`
- Consulta a través del endpoint `/registros-nomina/`

### Contabilidad [15](#0-14) 

- Filtrado de movimientos por clasificación
- Cierres contables
- Reportes financieros (ESF, ERI, ECP)

## 🔒 Seguridad

- Autenticación con JWT [16](#0-15) 
- CORS configurado [17](#0-16) 
- Redis con contraseña [18](#0-17) 
- Persistencia de datos en volúmenes Docker [19](#0-18) 

## 📊 Monitoreo

El sistema incluye Flower para monitorear las tareas de Celery: [20](#0-19) 

- Acceso: `http://localhost:5555`
- Visualización de tareas en ejecución
- Histórico de tareas completadas

## 🤝 Contribución

1. Fork el proyecto
2. Crea una rama para tu funcionalidad (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

## 📝 Notas

- El sistema está optimizado para 3 usuarios concurrentes [21](#0-20) 
- Los archivos Excel deben tener un tamaño máximo de 50 MB
- El procesamiento asíncrono puede tardar entre 1-3 minutos por archivo
- Se recomienda monitorear el consumo de RAM del worker de Celery [22](#0-21) 

## 📄 Licencia

Ver archivo LICENSE para más detalles.

---

**Última actualización**: 2025

### Citations

**File:** analisis_captura_masiva_gastos.md (L1-8)
```markdown
# Análisis Completo e Intenso: Página CapturaMasivaGastos

## 📋 Resumen Ejecutivo

La página **CapturaMasivaGastos** es un módulo funcional y complejo del sistema SGM que permite el procesamiento masivo de gastos desde archivos Excel. Esta implementada siguiendo el patrón de **Feature Folders** y utiliza un enfoque asíncrono con Celery/Redis para el procesamiento de archivos grandes.

---

```

**File:** analisis_captura_masiva_gastos.md (L32-95)
```markdown
## 🚀 Flujo Operativo Principal

### Paso 1: Navegación y Acceso
- **Ruta**: `/menu/tools/captura-masiva-gastos`
- **Acceso**: Desde la página `/menu/tools` → Card "Captura Masiva de Gastos"
- **Componente Router**: Definido en `App.jsx` línea 120

### Paso 2: Proceso de Captura de Gastos

#### 2.1 Descarga de Plantilla (Opcional)
- **Componente**: `DownloadTemplateSection`
- **Función**: Actualmente simulada, muestra alerta
- **Estado**: Funcionalidad placeholder

#### 2.2 Selección de Archivo Excel
- **Componente**: `FileUploadSection`
- **Formatos soportados**: `.xlsx, .xls`
- **Trigger**: `handleArchivoSeleccionado` en el hook

#### 2.3 Análisis Automático de Headers
- **API Endpoint**: `rgLeerHeadersExcel` (POST `/api/contabilidad/rindegastos/leer-headers/`)
- **Proceso**:
  1. Envía archivo al backend
  2. Backend analiza headers Excel
  3. Detecta columnas de centros de costos automáticamente
  4. Retorna estructura: `{ headers: [], centros_costo: {} }`

#### 2.4 Configuración de Mapeo de Centros de Costos
- **Componente**: `MapeoCC`
- **Funcionamiento**:
  - **Dinámico**: Basado en detección automática del backend
  - **Fallback**: 7 tipos predefinidos (PyC, PS/EB, CO, RE, TR, CF, LRC)
  - **Validación**: Formato `XX-XXX` o `XXX-XXX` (ej: 01-003, 001-003)
  - **Flexibilidad**: Campos opcionales, puede dejarse vacío

#### 2.5 Configuración de Cuentas Globales (OBLIGATORIO)
- **Componente**: `CuentasGlobalesSection`
- **Campos requeridos**:
  - **Cuenta IVA** (1xxx): Ej. 1191001
  - **Cuenta Gasto** (5xxx): Ej. 5111001  
  - **Cuenta Proveedores** (2xxx): Ej. 2111001
- **Validación**: Los 3 campos son obligatorios antes del procesamiento

#### 2.6 Procesamiento Asíncrono
- **API Endpoint**: `rgIniciarStep1` (POST `/api/contabilidad/rindegastos/step1/iniciar/`)
- **Parámetros enviados**:
  ```javascript
  parametros_contables: {
    cuentasGlobales: { iva, proveedores, gasto_default },
    mapeoCC: { [columna]: codigoCC }
  }
  ```
- **Respuesta**: `{ task_id, estado, archivo_nombre }`

#### 2.7 Monitoreo en Tiempo Real
- **Polling**: Cada 3 segundos
- **API Endpoint**: `rgEstadoStep1` (GET `/api/contabilidad/rindegastos/step1/estado/{taskId}/`)
- **Estados posibles**: `procesando`, `completado`, `error`

#### 2.8 Descarga de Resultados
- **Componente**: `ResultsSection`
- **API Endpoint**: `rgDescargarStep1` (GET `/api/contabilidad/rindegastos/step1/descargar/{taskId}/`)
- **Output**: Archivo Excel con resultados procesados

```

**File:** docs/sgm-contabilidad-3-usuarios.md (L6-14)
```markdown
## Arquitectura Simplificada

El sistema incluye solo los componentes esenciales:
- **Frontend React**: Interfaz de usuario para captura masiva de gastos
- **Backend Django**: API REST con endpoints de rinde gastos
- **PostgreSQL**: Base de datos para almacenar datos contables
- **Redis**: Cache y cola de tareas asíncronas
- **Celery Worker**: Procesamiento asíncrono de archivos Excel

```

**File:** docs/sgm-contabilidad-3-usuarios.md (L196-215)
```markdown
## Variables de Entorno (.env)

```bash
# Base de datos
POSTGRES_PASSWORD=tu_password_seguro_aqui
SECRET_KEY=tu_secret_key_django_aqui

# Redis
REDIS_PASSWORD=tu_redis_password_aqui

# Django
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,tu-dominio.com
CORS_ALLOWED_ORIGINS=http://localhost,https://tu-dominio.com

# Configuración para 3 usuarios
MAX_CONCURRENT_UPLOADS=3
MAX_FILE_SIZE=50MB
CELERY_WORKER_CONCURRENCY=2
```
```

**File:** docs/REQUISITOS_FINALES_SGM_CONTABILIDAD.md (L1-2)
```markdown
# 🎯 REQUISITOS REALES PARA SGM CONTABILIDAD (3 USUARIOS)
## Análisis Basado en Mediciones Reales - 10 Oct 2025
```

**File:** docs/REQUISITOS_FINALES_SGM_CONTABILIDAD.md (L73-83)
```markdown
```yaml
CPU: 2 cores
RAM: 6 GB
Almacenamiento: 50 GB SSD
Red: 10 Mbps

Capacidad real:
- 2-3 usuarios navegando simultáneamente
- 1 usuario procesando Excel a la vez
- Uso: 80-90% recursos en picos
```
```

**File:** docs/REQUISITOS_FINALES_SGM_CONTABILIDAD.md (L85-97)
```markdown
#### 🥈 Configuración Recomendada (Producción estable)
```yaml
CPU: 4 cores
RAM: 8 GB
Almacenamiento: 100 GB SSD
Red: 50 Mbps

Capacidad real:
- 3-5 usuarios navegando simultáneamente
- 2-3 usuarios procesando Excel simultáneamente
- Uso: 60-70% recursos en picos
- Margen para crecimiento
```
```

**File:** docs/REQUISITOS_FINALES_SGM_CONTABILIDAD.md (L99-111)
```markdown
#### 🥇 Configuración Óptima (Futuro-proof)
```yaml
CPU: 6 cores (o 4 cores + alta frecuencia)
RAM: 16 GB
Almacenamiento: 200 GB NVMe SSD
Red: 100 Mbps

Capacidad real:
- 5+ usuarios simultáneos
- 3+ usuarios procesando Excel simultáneamente
- Uso: 40-50% recursos en picos
- Capacidad para nuevas funcionalidades
```
```

**File:** docs/REQUISITOS_FINALES_SGM_CONTABILIDAD.md (L155-157)
```markdown
1. **Usar la configuración Docker optimizada** que creamos
2. **Monitorear principalmente Celery workers** (mayor consumo)
3. **Implementar alertas** cuando RAM > 80% o CPU > 70%
```

**File:** package.json (L7-13)
```json
  "scripts": {
    "preinstall": "node scripts/check-node.js",
    "dev": "vite",
    "build": "vite build",
    "lint": "eslint .",
    "preview": "vite preview"
  },
```

**File:** package.json (L14-16)
```json
  "engines": {
    "node": ">=20.19.5"
  },
```

**File:** package.json (L18-31)
```json
  "dependencies": {
    "@tailwindcss/vite": "^4.0.13",
    "axios": "^1.9.0",
    "daisyui": "^5.0.3",
    "framer-motion": "^12.7.3",
    "lucide-react": "^0.488.0",
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "react-router-dom": "^7.3.0",
    "react-select": "^5.10.1",
    "recharts": "^2.15.2",
    "tailwindcss": "^4.0.13",
    "xlsx": "^0.18.5"
  },
```

**File:** backend/requirements.txt (L1-31)
```text
amqp==5.3.1
asgiref==3.8.1
billiard==4.2.1
celery==5.5.2
click==8.1.8
click-didyoumean==0.3.1
click-plugins==1.1.1
click-repl==0.3.0
Django==5.2.7
django-cors-headers==4.7.0
django-extensions==3.2.3
pydotplus==2.0.2
pyparsing==3.1.2
djangorestframework==3.16.0
djangorestframework_simplejwt==5.5.0
django-redis>=5.4.0
et_xmlfile==2.0.0
kombu==5.5.3
numpy==2.2.5
openpyxl==3.1.5
pandas==2.2.3
prompt_toolkit==3.0.51
psycopg2-binary==2.9.10
PyJWT==2.9.0
python-dateutil==2.9.0.post0
pytz==2025.2
redis==6.0.0
six==1.17.0
sqlparse==0.5.3
tzdata==2025.2
vine==5.1.0
```

**File:** README.md (L16-20)
```markdown
Run the backend tests with:

```bash
backend/venv/bin/python backend/manage.py test
```
```

**File:** README.md (L26-30)
```markdown
### Registro de nómina

Cada fila del Libro de Remuneraciones se almacena en el modelo `RegistroNomina`.
Los valores se guardan en el campo JSON `data` y pueden consultarse a través del
endpoint `/registros-nomina/`.
```

**File:** README.md (L32-42)
```markdown
### Filtro de movimientos por clasificación

El endpoint `/contabilidad/cierres/<id>/movimientos-resumen/` acepta los
parámetros opcionales `set_id` y `opcion_id` para filtrar las cuentas según su
clasificación. Ejemplo:

```
/api/contabilidad/cierres/1/movimientos-resumen/?set_id=2&opcion_id=5
```

Retorna únicamente las cuentas que estén clasificadas con la opción indicada.
```

**File:** README.md (L44-51)
```markdown
## Celery worker

Algunas tareas se procesan de forma asíncrona con Celery. Para procesar el
Libro de Remuneraciones es necesario que el worker esté en ejecución.

```bash
cd backend
./celery_worker.sh
```

**File:** docker-compose.yml (L21-21)
```yaml
    command: redis-server --appendonly yes  --requirepass ${REDIS_PASSWORD} # ← AGREGADO: Habilitar persistencia
```

**File:** docker-compose.yml (L62-73)
```yaml
  flower:
    image: mher/flower
    command: python -m celery --broker=redis://:${REDIS_PASSWORD}@redis:6379/0 flower
    ports:
      - "5555:5555"
    environment:
      - REDIS_PASSWORD=${REDIS_PASSWORD}  # ← AGREGAR
    env_file:
      - .env  # ← AGREGAR
    depends_on:
      - redis
      - celery_worker
```

**File:** docker-compose.yml (L93-95)
```yaml
volumes:
  postgres_data:
  redis_data:        # ← NUEVO: Persistencia para Redis
```
