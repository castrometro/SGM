# PLAN DE LIMPIEZA - Sistema de Logging V1 → V2
# ================================================

## 📋 ARCHIVOS A ELIMINAR COMPLETAMENTE

### Backend - Archivos obsoletos:
- ❌ backend/nomina/models_logging.py
- ❌ backend/nomina/views_logging.py  
- ❌ backend/nomina/api_logging.py
- ❌ backend/nomina/views_upload_con_logging.py
- ❌ backend/nomina/utils/activity_logging.py

### Frontend - Archivos obsoletos:
- ❌ src/utils/activityLogger.js (v1)
- ❌ frontend/src/utils/activityLogger.js (duplicado)

## 🧹 ARCHIVOS A LIMPIAR (remover imports/código)

### Backend:
- 🧹 backend/nomina/views.py → Remover imports y calls de logging v1
- 🧹 backend/nomina/views_archivos_analista.py → Limpiar logging calls
- 🧹 backend/nomina/tasks.py → Remover logging v1 
- 🧹 backend/nomina/utils/mixins.py → Simplificar mixins
- 🧹 backend/nomina/urls.py → Remover rutas de activity-log v1
- 🧹 backend/nomina/admin.py → Limpiar imports si existen

### Frontend:
- 🧹 src/components/TarjetasCierreNomina/IngresosCard.jsx → Remover imports v1
- 🧹 src/components/TarjetasCierreNomina/AusentismosCard.jsx → Remover imports v1
- 🧹 src/components/TarjetasCierreNomina/FiniquitosCard.jsx → Remover imports v1
- 🧹 Otros componentes que importen activityLogger v1

## ⚠️ PRECAUCIONES

1. **Backup antes de limpiar**: Crear branch de backup
2. **Verificar dependencias**: Algunos modelos pueden tener FK a models_logging
3. **Migración de BD**: Crear migración para eliminar tablas v1
4. **Tests**: Verificar que no hay tests que dependan del sistema v1
5. **Frontend builds**: Asegurar que no rompa el build al eliminar imports

## 🔄 ORDEN DE LIMPIEZA

1. **Paso 1**: Limpiar frontend (menos riesgo)
2. **Paso 2**: Limpiar imports en backend (sin eliminar archivos aún)  
3. **Paso 3**: Verificar que todo funciona sin el sistema v1
4. **Paso 4**: Eliminar archivos obsoletos
5. **Paso 5**: Crear migración para eliminar tablas
6. **Paso 6**: Verificar tests y funcionalidad

## 📝 CHECKLIST DE VERIFICACIÓN

- [ ] Frontend compila sin errores
- [ ] Backend arranca sin errores de import
- [ ] No hay referencias a TarjetaActivityLogNomina en migraciones
- [ ] No hay referencias a UploadLogNomina en modelos activos
- [ ] URLs de activity-log v1 removidas
- [ ] Tests pasan (si existen)
- [ ] Admin no referencia modelos eliminados