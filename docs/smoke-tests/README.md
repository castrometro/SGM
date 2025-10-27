# 🧪 Smoke Tests - Tareas Refactorizadas

Esta carpeta contiene toda la documentación, scripts y resultados de las pruebas de humo (smoke tests) para validar las tareas refactorizadas del sistema SGM.

## 📂 Estructura

```
docs/smoke-tests/
├── README.md                              # Este archivo
├── PLAN_PRUEBA_SMOKE_TEST.md             # Plan maestro con 9 flujos
├── RESUMEN_SESION_SMOKE_TEST_DIA_1.md    # Resumen primera sesión
│
├── flujo-1-libro-remuneraciones/         # ✅ COMPLETADO
│   ├── SMOKE_TEST_FLUJO_1_RESULTADOS.md
│   ├── FLUJO_1_COMPLETO_DESDE_SUBIDA.md
│   ├── FLUJO_1_LIBRO_REMUNERACIONES.md
│   ├── INSTRUCCIONES_PRUEBA_FLUJO1.md
│   ├── generar_excel_prueba_libro.py
│   ├── crear_cierre_prueba_smoke_test.py
│   └── ejecutar_flujo1_completo.py
│
├── flujo-2-movimientos-mes/              # � EN PROGRESO
│   └── (archivos por crear)
│
└── generar_excel_previred.py             # Compartido entre flujos
    libro_remuneraciones_previred.xlsx     # Datos de prueba
```

### �📋 Documentación Principal

- **`PLAN_PRUEBA_SMOKE_TEST.md`** - Plan maestro con los 9 flujos a probar
- **`RESUMEN_SESION_SMOKE_TEST_DIA_1.md`** - Resumen de la primera sesión de pruebas

### ✅ Flujos Organizados por Carpeta

#### Flujo 1: Libro de Remuneraciones (✅ Completado)
📁 **`flujo-1-libro-remuneraciones/`**
- `SMOKE_TEST_FLUJO_1_RESULTADOS.md` - Resultados detallados y métricas
- `FLUJO_1_COMPLETO_DESDE_SUBIDA.md` - Documentación técnica del flujo completo
- `FLUJO_1_LIBRO_REMUNERACIONES.md` - Análisis de tareas involucradas
- `INSTRUCCIONES_PRUEBA_FLUJO1.md` - Guía paso a paso para ejecutar la prueba
- `generar_excel_prueba_libro.py` - Script generador de datos
- `crear_cierre_prueba_smoke_test.py` - Script de preparación
- `ejecutar_flujo1_completo.py` - Script automatizado completo

#### Flujo 2: Movimientos del Mes (🔄 En Progreso)
📁 **`flujo-2-movimientos-mes/`**
- Archivos por crear durante la prueba

### 🛠️ Scripts Compartidos

- **`generar_excel_previred.py`** - Genera Excel con formato Previred estándar

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
   📁 docs/smoke-tests/flujo-1-libro-remuneraciones/
   - 4 tareas validadas
   - 5 empleados, 65 conceptos
   - Tiempo: ~0.35s
   
🔄 Flujo 2: Movimientos del Mes - EN PROGRESO
   📁 docs/smoke-tests/flujo-2-movimientos-mes/
   - Tarea: procesar_movimientos_mes_con_logging
   - Usuario correcto validado
   
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

### Ver Resultados de Flujo 1
```bash
cd docs/smoke-tests/flujo-1-libro-remuneraciones
cat SMOKE_TEST_FLUJO_1_RESULTADOS.md
```

### Ejecutar Flujo 2 (Movimientos del Mes)
```bash
cd docs/smoke-tests/flujo-2-movimientos-mes
# Seguir instrucciones cuando estén disponibles
```

### Ejecutar Pruebas (General)

1. **Iniciar servicios:**
   ```bash
   cd /root/SGM
   docker-compose up -d
   npm run dev
   ```

2. **Crear ambiente de prueba:**
   ```bash
   # Para Flujo 1
   docker compose exec django python /app/docs/smoke-tests/flujo-1-libro-remuneraciones/crear_cierre_prueba_smoke_test.py
   
   # Para otros flujos, seguir instrucciones en su carpeta respectiva
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

### ✅ Flujo 1: Libro de Remuneraciones

**Carpeta:** `flujo-1-libro-remuneraciones/`

- ✅ Todas las tareas refactorizadas funcionan
- ⚠️ Clasificación flexible: campos adicionales se clasifican como conceptos
- 📊 Performance excelente: 0.35s para 5 empleados
- 🔍 Requiere formato Previred estricto (7 columnas obligatorias)

**Tareas validadas:**
1. `procesar_libro_remuneraciones_con_logging` - Procesamiento principal
2. `limpiar_libro_remuneraciones_con_logging` - Limpieza de datos
3. `clasificar_libro_remuneraciones_con_logging` - Clasificación de conceptos
4. `crear_empleados_desde_libro_con_logging` - Creación de empleados

### 🔄 Flujo 2: Movimientos del Mes

**Carpeta:** `flujo-2-movimientos-mes/`

- 🔄 En preparación
- 🎯 Objetivo: Validar procesamiento de altas/bajas/cambios
- 📝 Tarea principal: `procesar_movimientos_mes_con_logging`

## 📞 Contacto

Para preguntas sobre las pruebas:
- Ver documentación en cada archivo de resultados
- Revisar logs en `docker compose logs celery_worker`
- Consultar plan maestro para estado general

---

**Última actualización:** 27 de octubre de 2025  
**Estado:** En progreso - Flujo 1 completado, Flujo 2 en preparación
