# SGM Contabilidad & Nómina - AI Coding Guidelines

## 🏗️ Architecture Overview

**SGM** is a comprehensive **accounting and payroll management system** built as a **React + Django REST API** application with **async processing via Celery**. The system handles **Excel-based data processing**, **multi-tenant client management**, and **role-based workflows**.

### Core Service Boundaries
- **Frontend** (`/src`): React SPA with role-based routing (`/pages`) and modular API clients (`/src/api`)  
- **Django API** (`/backend/api`): Core business logic, user management, client assignments
- **Contabilidad** (`/backend/contabilidad`): Accounting closures, classifications, book analysis
- **Nómina** (`/backend/nomina`): Payroll processing, employee records, incidents
- **Celery Workers**: Async Excel processing with dedicated queues (`nomina_queue`, `contabilidad_queue`)

## ⚡ Critical Developer Workflows

### Local Development Setup
```bash
# Backend with workers (REQUIRED for Excel processing)
cd backend && ./celery_worker.sh  # Multi-queue worker system
python manage.py runserver

# Frontend development server  
npm run dev  # Runs on port 5174 with --host=0.0.0.0
```

### Container Environment
```bash
docker-compose up  # Full stack: Django + Celery + Redis + PostgreSQL
# Django auto-migrates and serves on port 8000
# Frontend must be started separately with npm run dev
```

## 📐 Project-Specific Conventions

### API Architecture Pattern
- **ViewSets** for CRUD: `class ClienteViewSet(viewsets.ModelViewSet)`
- **Custom actions** for complex operations: `@action(detail=True, methods=['post'])`
- **Celery tasks** for file processing: Files in `tasks.py` with queue routing
- **Permission classes**: Custom `IsGerenteOrReadOnly`, `IsAnalistaOrReadOnly`

### Frontend State Management
- **No global state library** - uses React context for auth (`/src/contexts`)
- **API clients** per domain: `authApi.js`, `contabilidadApi.js`, `nominaApi.js`
- **Route protection**: `<PrivateRoute>` wrapper with role-based access
- **File uploads**: Direct multipart/form-data to Django with progress tracking

### File Processing Workflow
**Critical**: Excel processing is **asynchronous**. Pattern:
1. Upload file → Get `task_id` 
2. Poll status: `GET /api/task-status/{task_id}/`
3. Download results when `status === 'SUCCESS'`

Example in `contabilidad/tasks.py`:
```python
@shared_task(bind=True, queue='contabilidad_queue')
def procesar_libro_mayor(self, archivo_path, cliente_id):
    # Heavy Excel processing here
```

## 🔗 Integration Points & Data Flow

### Authentication Flow
- **JWT tokens** with refresh: `CustomTokenObtainPairView` 
- **Role hierarchy**: `Gerente > Analista > Usuario`
- **Client assignments**: Users access only assigned clients

### Database Relationships
- **Multi-tenant**: All models filtered by `cliente_id`
- **Accounting**: `CierreContable` → `MovimientoContable` → `CuentaContable`
- **Payroll**: `CierreNomina` → `RegistroNomina` → `Empleado`
- **Classifications**: Hierarchical account classification system

### Cache Strategy
- **Redis**: Session data, task results, expensive query caching
- **File caching**: Processed Excel files stored in `/media` with expiration
- **Query optimization**: Heavy use of `select_related()` and `prefetch_related()`

## 🎯 Key Implementation Patterns

### Error Handling
```python
# Backend: Structured API responses
return Response({"error": "Specific message"}, status=400)

# Frontend: Centralized error handling in API interceptors
api.interceptors.response.use(response => response, error => {
    // Global error handling logic
});
```

### File Upload Pattern
```javascript
// Always use FormData for file uploads
const formData = new FormData();
formData.append('archivo', file);
formData.append('cliente_id', clienteId);

// Backend processes with Celery task
```

### Role-Based Access
- **Frontend**: Route-level protection with role checking
- **Backend**: ViewSet-level permissions + method-specific decorators
- **Database**: Row-level security via client assignments

## 📁 Critical File Locations

- `/backend/celery_worker.sh` - Multi-queue worker configuration
- `/src/api/config.js` - API base URL and interceptors  
- `/backend/sgm_backend/settings.py` - Redis, Celery, and cache configuration
- `/docs/REQUISITOS_FINALES_SGM_CONTABILIDAD.md` - System requirements and scaling info
- Docker setup: `docker-compose.yml` with PostgreSQL, Redis, and environment variables

## ⚠️ Common Gotchas

- **Celery queues**: Use correct queue names (`nomina_queue`, `contabilidad_queue`) for task routing
- **File paths**: Always use absolute paths; media files served from `/backend/media/`
- **Database migrations**: Run in containers AND locally when schema changes
- **CORS**: Configured for `172.17.11.18` - update for different environments
- **Excel processing**: Can consume significant memory; monitor worker resources

## 🔄 Testing Strategy

```bash
# Backend tests
cd backend && python manage.py test

# Critical validation after payroll upload
# Check that employee creation columns don't appear in header_json
# Verify RegistroNomina.data contains row values correctly
```

Focus on **Excel processing workflows** and **role-based access control** when testing changes.