# 📚 Índice de Documentación - SGM

Este archivo sirve como índice central para toda la documentación del proyecto SGM.

## 🧪 Pruebas y Testing

### Smoke Tests (Tareas Refactorizadas)
**Ubicación:** [`docs/smoke-tests/`](docs/smoke-tests/)

Documentación completa de las pruebas de validación de tareas refactorizadas:
- ✅ Flujo 1: Libro de Remuneraciones completado
- 📋 8 flujos pendientes
- 🛠️ Scripts de generación de datos
- 📊 Resultados y métricas

Ver: [`docs/smoke-tests/README.md`](docs/smoke-tests/README.md)

## 📖 Documentación Técnica

### Requisitos
- [`docs/REQUISITOS_FINALES_SGM_CONTABILIDAD.md`](docs/REQUISITOS_FINALES_SGM_CONTABILIDAD.md) - Especificaciones del sistema

### Arquitectura
- [`.github/copilot-instructions.md`](.github/copilot-instructions.md) - Guía para desarrollo con AI

## 🔄 Flujos de Trabajo

### Nómina
- **Libro de Remuneraciones:** Ver smoke tests
- **Novedades:** Pendiente documentación
- **Previred:** Pendiente documentación

### Contabilidad
- **Movimientos:** Pendiente documentación
- **Cierres:** Pendiente documentación
- **Conciliación:** Pendiente documentación

## 🐛 Fixes y Resoluciones

Archivos de documentación de problemas resueltos:
- `CVE-2024-3566-RESUELTO.md` - Vulnerabilidad de seguridad
- `FIX_CAMPOS_ACTIVITYEVENT_255.txt` - Fix campos Activity Event
- `FIX_LIBRO_REMUNERACIONES_RESUMEN.txt` - Resumen fix libro
- Y más en el directorio raíz (legacy)

## 📊 Diagramas y Análisis

Archivos de visualización:
- `DIAGRAMA_CONSOLIDACION_SIMPLE.md`
- `FLUJO_CONSOLIDACION_VISUAL.md`
- `generate_diagrams.py`

## 🛠️ Scripts Útiles

### Monitoreo
- `monitor_consolidacion.py`
- `monitor-completo-datos.sh`
- `monitor-flower.sh`

### Limpieza
- `cleanup_backend_logging.sh`
- `cleanup_frontend_logging.sh`
- `clean_nomina_tables.sql`

### Gestión de Workers
- `celery_manager.sh`
- `iniciar_sistema_paralelo.sh`
- `iniciar_workers_optimizados.sh`

## 📝 Notas

Esta es una estructura de documentación en evolución. Los archivos se están organizando progresivamente en carpetas temáticas.

**Próximos pasos:**
1. Mover archivos legacy a carpetas apropiadas
2. Consolidar documentación de fixes
3. Crear carpeta para scripts de monitoreo
4. Organizar diagramas en carpeta docs/diagrams/

---

**Última actualización:** 25 de octubre de 2025
