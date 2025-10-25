# 🧪 Smoke Tests - Tareas Refactorizadas

Esta carpeta contiene toda la documentación, scripts y resultados de las pruebas de humo (smoke tests) para validar las tareas refactorizadas del sistema SGM.

## 📂 Estructura

### 📋 Documentación Principal

- **`PLAN_PRUEBA_SMOKE_TEST.md`** - Plan maestro con los 9 flujos a probar
- **`RESUMEN_SESION_SMOKE_TEST_DIA_1.md`** - Resumen de la primera sesión de pruebas

### ✅ Resultados por Flujo

#### Flujo 1: Libro de Remuneraciones (✅ Completado)
- **`SMOKE_TEST_FLUJO_1_RESULTADOS.md`** - Resultados detallados y métricas
- **`FLUJO_1_COMPLETO_DESDE_SUBIDA.md`** - Documentación técnica del flujo completo
- **`INSTRUCCIONES_PRUEBA_FLUJO1.md`** - Guía paso a paso para ejecutar la prueba

### 🛠️ Scripts de Generación

- **`crear_cierre_prueba_smoke_test.py`** - Crea cliente y cierre de prueba
- **`generar_excel_previred.py`** - Genera Excel con formato Previred estándar
- **`generar_excel_prueba_libro.py`** - Generador alternativo (formato simplificado)

### 📊 Datos de Prueba

- **`libro_remuneraciones_previred.xlsx`** - Excel de prueba (5 empleados, 10 conceptos)

## 🎯 Objetivo

Identificar qué funciones del código refactorizado:
- ✅ Funcionan correctamente
- ⚠️ Son stubs que explotan (necesitan implementación)
- 🔇 Nunca se llaman (código muerto candidato)

## 📊 Progreso

```
Estado: 1/9 flujos completados (11%)

✅ Flujo 1: Libro de Remuneraciones - EXITOSO
   - 4 tareas validadas
   - 5 empleados, 65 conceptos
   - Tiempo: ~0.35s
   
⏭️ Flujo 2: Movimientos Contables - PENDIENTE
⏭️ Flujo 3: Novedades de Nómina - PENDIENTE
⏭️ Flujo 4: Conciliación Bancaria - PENDIENTE
⏭️ Flujo 5: Cargas Familiares - PENDIENTE
⏭️ Flujo 6: Contratos y Anexos - PENDIENTE
⏭️ Flujo 7: Liquidaciones de Sueldo - PENDIENTE
⏭️ Flujo 8: Previred - PENDIENTE
⏭️ Flujo 9: Centralización Contable - PENDIENTE
```

## 🔄 Metodología

Para cada flujo:

1. **Preparación**
   - Crear datos de prueba (cliente, cierre, archivos)
   - Documentar flujo técnico completo

2. **Ejecución**
   - Probar desde frontend (no scripts backend)
   - Monitorear logs de Celery
   - Registrar tiempos y errores

3. **Validación**
   - Verificar datos en base de datos
   - Confirmar estados correctos
   - Documentar hallazgos

4. **Documentación**
   - Crear archivo de resultados
   - Actualizar plan maestro
   - Registrar lecciones aprendidas

## 🚀 Cómo Usar

### Ejecutar Pruebas

1. **Iniciar servicios:**
   ```bash
   cd /root/SGM
   docker-compose up -d
   npm run dev
   ```

2. **Crear ambiente de prueba:**
   ```bash
   docker compose exec django python /app/docs/smoke-tests/crear_cierre_prueba_smoke_test.py
   docker compose cp docs/smoke-tests/generar_excel_previred.py django:/tmp/
   docker compose exec django python /tmp/generar_excel_previred.py
   ```

3. **Seguir instrucciones del flujo:**
   - Ver `INSTRUCCIONES_PRUEBA_FLUJO*.md` para cada flujo

### Limpiar Datos de Prueba

```python
# En Django shell
from nomina.models import CierreNomina, Cliente
from contabilidad.models import CierreContable

# Eliminar cierres de prueba
CierreNomina.objects.filter(cliente__nombre="EMPRESA SMOKE TEST").delete()
CierreContable.objects.filter(cliente__nombre="EMPRESA SMOKE TEST").delete()

# Eliminar cliente de prueba
Cliente.objects.filter(nombre="EMPRESA SMOKE TEST").delete()
```

## 📚 Referencias

### Código Refactorizado

- **Nómina:** `/backend/nomina/tasks_refactored/`
  - `libro_remuneraciones.py`
  - `novedades.py`
  - `previred.py`

- **Contabilidad:** `/backend/contabilidad/tasks_refactored/`
  - `movimientos.py`
  - `cierres.py`
  - `conciliacion.py`

### Proxy Tasks

- `/backend/nomina/tasks.py` - Re-exporta tareas de tasks_refactored
- `/backend/contabilidad/tasks.py` - Re-exporta tareas de tasks_refactored

## 🎓 Hallazgos Clave

### Flujo 1: Libro de Remuneraciones

- ✅ Todas las tareas refactorizadas funcionan
- ⚠️ Clasificación flexible: campos adicionales se clasifican como conceptos
- 📊 Performance excelente: 0.35s para 5 empleados
- 🔍 Requiere formato Previred estricto (7 columnas obligatorias)

## 📞 Contacto

Para preguntas sobre las pruebas:
- Ver documentación en cada archivo de resultados
- Revisar logs en `docker compose logs celery_worker`
- Consultar plan maestro para estado general

---

**Última actualización:** 25 de octubre de 2025  
**Estado:** En progreso - Flujo 1 completado
