# 🧪 INSTRUCCIONES DE PRUEBA - Flujo 2: Movimientos del Mes

**Fecha**: 27 de octubre de 2025  
**Estado**: 🔄 EN EJECUCIÓN  
**Propósito**: Validar procesamiento de movimientos de personal (altas, bajas, ausentismos, vacaciones, cambios)

---

## ✅ PRE-REQUISITOS (Verificados)

```
✅ Cierre ID: 35
✅ Cliente: EMPRESA SMOKE TEST
✅ Periodo: 2025-10
✅ Estado: pendiente
✅ Empleados existentes: 5 (del Flujo 1)
✅ Excel generado: /tmp/movimientos_mes_smoke_test.xlsx (8.9K)
```

---

## 📋 Datos de Prueba

### 📥 Altas (3 nuevos empleados)
- **66666666-6** - Juan Nuevo Empleado - Ingreso: 2025-10-01
- **77777777-7** - María Nueva Empleada - Ingreso: 2025-10-01
- **88888888-8** - Pedro Nuevo Empleado - Ingreso: 2025-10-15

### 📤 Bajas/Finiquitos (2 empleados existentes)
- **11111111-1** - Juan Pérez - Finiquito: 2025-10-31
- **22222222-2** - María González - Finiquito: 2025-10-31

### 🏥 Ausentismos (2)
- **33333333-3** - Pedro Rodríguez - Licencia Médica (3 días)
- **44444444-4** - Ana Martínez - Permiso Personal (1 día)

### 🏖️ Vacaciones (1)
- **55555555-5** - Carlos López - Vacaciones (10 días)

### 💰 Variaciones de Sueldo (2)
- **55555555-5** - Carlos López - $950,000 → $1,050,000 (+10.53%)
- **33333333-3** - Pedro Rodríguez - $900,000 → $980,000 (+8.89%)

### 📄 Variaciones de Contrato (2)
- **33333333-3** - Pedro Rodríguez - Indefinido → Plazo Fijo
- **44444444-4** - Ana Martínez - Jornada Completa → Part-Time

**Total Movimientos: 12**

---

## 🚀 PASO A PASO - Prueba Manual

### PASO 1: Abrir la Interfaz Web

```bash
# URL del cierre
http://172.17.11.18:5174/nomina/cierre/35
```

**Verificar:**
- ✅ Página carga correctamente
- ✅ Título muestra "Cierre EMPRESA SMOKE TEST - 2025-10"
- ✅ Sección "Movimientos del Mes" visible

---

### PASO 2: Preparar Monitoreo de Logs

**Terminal 1 - Celery Worker:**
```bash
docker compose logs celery_worker -f | grep -E "(movimientos_mes|MovimientosMesUpload|ERROR)"
```

**Terminal 2 - Django Backend:**
```bash
docker compose logs django -f | grep -E "(movimientos_mes|MovimientosMesUpload|ERROR)"
```

---

### PASO 3: Copiar Excel al Host (si es necesario)

```bash
# Copiar desde el contenedor al host
docker compose cp django:/tmp/movimientos_mes_smoke_test.xlsx /tmp/

# Verificar
ls -lh /tmp/movimientos_mes_smoke_test.xlsx
```

---

### PASO 4: Subir Archivo en Frontend

1. **Localizar sección**: "Movimientos del Mes"

2. **Click en botón**: "Seleccionar archivo" o "Subir archivo"

3. **Seleccionar archivo**: 
   - Archivo: `/tmp/movimientos_mes_smoke_test.xlsx`
   - Tamaño: 8.9 KB

4. **Click en**: "Subir" o "Procesar"

5. **Observar spinner**: "Subiendo archivo..." → "Procesando..."

**⏱️ Tiempo esperado**: 3-5 segundos

---

### PASO 5: Verificar Estado en Frontend

**Resultado esperado:**
```
✅ Archivo subido exitosamente
Estado: "procesado" o "completado"
Ícono: Check verde ✅
```

**Si hay error:**
- Ver logs en Terminal 1 y Terminal 2
- Revisar consola del navegador (F12)
- Verificar mensaje de error

---

## 🔍 VERIFICACIÓN EN BASE DE DATOS

### Verificar Upload

```bash
docker compose exec -T django python manage.py shell <<'EOF'
from nomina.models import MovimientosMesUpload

upload = MovimientosMesUpload.objects.filter(cierre_id=35).first()
if upload:
    print(f"\n📤 Upload ID: {upload.id}")
    print(f"   Estado: {upload.estado}")
    print(f"   Archivo: {upload.archivo.name if upload.archivo else 'N/A'}")
    print(f"   Fecha: {upload.fecha_subida}")
else:
    print("❌ No se encontró upload")
EOF
```

**Resultado esperado:**
```
📤 Upload ID: 1
   Estado: procesado
   Archivo: movimientos_mes/...xlsx
   Fecha: 2025-10-27 ...
```

---

### Verificar Altas/Bajas

```bash
docker compose exec -T django python manage.py shell <<'EOF'
from nomina.models import MovimientoAltaBaja

movimientos = MovimientoAltaBaja.objects.filter(cierre_id=35)
print(f"\n👤 Altas/Bajas: {movimientos.count()}")

altas = movimientos.filter(tipo_movimiento='ingreso')
print(f"   📥 Altas: {altas.count()}")
for mov in altas:
    print(f"      - {mov.rut}: {mov.fecha_movimiento}")

bajas = movimientos.filter(tipo_movimiento='finiquito')
print(f"   📤 Bajas: {bajas.count()}")
for mov in bajas:
    print(f"      - {mov.rut}: {mov.fecha_movimiento}")
EOF
```

**Resultado esperado:**
```
👤 Altas/Bajas: 5
   📥 Altas: 3
      - 66666666-6: 2025-10-01
      - 77777777-7: 2025-10-01
      - 88888888-8: 2025-10-15
   📤 Bajas: 2
      - 11111111-1: 2025-10-31
      - 22222222-2: 2025-10-31
```

---

### Verificar Ausentismos

```bash
docker compose exec -T django python manage.py shell <<'EOF'
from nomina.models import MovimientoAusentismo

ausentismos = MovimientoAusentismo.objects.filter(cierre_id=35)
print(f"\n🏥 Ausentismos: {ausentismos.count()}")
for aus in ausentismos:
    print(f"   - {aus.rut}: {aus.tipo_ausentismo} ({aus.dias} días)")
EOF
```

**Resultado esperado:**
```
🏥 Ausentismos: 2
   - 33333333-3: Licencia Médica (3 días)
   - 44444444-4: Permiso Personal (1 días)
```

---

### Verificar Vacaciones

```bash
docker compose exec -T django python manage.py shell <<'EOF'
from nomina.models import MovimientoVacaciones

vacaciones = MovimientoVacaciones.objects.filter(cierre_id=35)
print(f"\n🏖️  Vacaciones: {vacaciones.count()}")
for vac in vacaciones:
    print(f"   - {vac.rut}: {vac.fecha_inicial} a {vac.fecha_fin} ({vac.cantidad_dias} días)")
EOF
```

**Resultado esperado:**
```
🏖️  Vacaciones: 1
   - 55555555-5: 2025-10-15 a 2025-10-25 (10 días)
```

---

### Verificar Variaciones de Sueldo

```bash
docker compose exec -T django python manage.py shell <<'EOF'
from nomina.models import MovimientoVariacionSueldo

variaciones = MovimientoVariacionSueldo.objects.filter(cierre_id=35)
print(f"\n💰 Variaciones de Sueldo: {variaciones.count()}")
for var in variaciones:
    print(f"   - {var.rut}: ${var.sueldo_anterior:,.0f} → ${var.sueldo_actual:,.0f} ({var.porcentaje_reajuste:.2f}%)")
EOF
```

**Resultado esperado:**
```
💰 Variaciones de Sueldo: 2
   - 55555555-5: $950,000 → $1,050,000 (10.53%)
   - 33333333-3: $900,000 → $980,000 (8.89%)
```

---

### Verificar Variaciones de Contrato

```bash
docker compose exec -T django python manage.py shell <<'EOF'
from nomina.models import MovimientoVariacionContrato

variaciones = MovimientoVariacionContrato.objects.filter(cierre_id=35)
print(f"\n📄 Variaciones de Contrato: {variaciones.count()}")
for var in variaciones:
    print(f"   - {var.rut}: {var.tipo_contrato_anterior} → {var.tipo_contrato_actual}")
EOF
```

**Resultado esperado:**
```
📄 Variaciones de Contrato: 2
   - 33333333-3: Indefinido → Plazo Fijo
   - 44444444-4: Jornada Completa → Part-Time
```

---

## 📊 VERIFICAR LOGGING DUAL

### TarjetaActivityLogNomina (User-facing)

```bash
docker compose exec -T django python manage.py shell <<'EOF'
from nomina.models_logging import TarjetaActivityLogNomina

logs = TarjetaActivityLogNomina.objects.filter(
    tarjeta='movimientos_mes',
    cierre_id=35
).order_by('timestamp')

print("\n📊 LOGS DE MOVIMIENTOS DEL MES")
for log in logs:
    print(f"\n{log.accion}:")
    print(f"  Usuario: {log.usuario.correo_bdo} (ID: {log.usuario.id})")
    print(f"  Descripción: {log.descripcion}")
    print(f"  Resultado: {log.resultado}")
    print(f"  Timestamp: {log.timestamp}")
EOF
```

**Verificar:**
- ✅ Usuario correcto (NO "Pablo Castro", ID: 1)
- ✅ Acciones esperadas: `archivo_subido`, `procesamiento_iniciado`, `procesamiento_completado`
- ✅ Resultados: `success`

---

### ActivityEvent (Audit Trail)

```bash
docker compose exec -T django python manage.py shell <<'EOF'
from nomina.models import ActivityEvent

events = ActivityEvent.objects.filter(
    resource_type='movimientos_mes',
    resource_id='35'
).order_by('timestamp')

print("\n🔍 ACTIVITY EVENTS (Celery)")
for evt in events:
    print(f"\n{evt.action}:")
    print(f"  Usuario: {evt.user.correo_bdo if evt.user else 'Sistema'}")
    print(f"  Event Type: {evt.event_type}")
    print(f"  Detalles: {evt.details}")
    print(f"  Timestamp: {evt.timestamp}")
EOF
```

**Verificar:**
- ✅ Eventos: `procesamiento_celery_iniciado`, `procesamiento_completado`
- ✅ Usuario correcto en `details['usuario_id']`
- ✅ `celery_task_id` presente

---

## ✅ CHECKLIST DE VALIDACIÓN

### 📤 Subida de Archivo
- [ ] Archivo se sube sin errores
- [ ] Se crea registro `MovimientosMesUpload`
- [ ] Estado inicial: `pendiente` o `en_proceso`
- [ ] `TarjetaActivityLogNomina` registra `archivo_subido`
- [ ] Usuario correcto en log

### 🔄 Procesamiento Automático
- [ ] Task Celery se ejecuta automáticamente
- [ ] Estado cambia a `procesado`
- [ ] Se crean todos los tipos de movimientos:
  - [ ] 5 MovimientoAltaBaja (3 altas + 2 bajas)
  - [ ] 2 MovimientoAusentismo
  - [ ] 1 MovimientoVacaciones
  - [ ] 2 MovimientoVariacionSueldo
  - [ ] 2 MovimientoVariacionContrato
- [ ] Total: 12 movimientos registrados

### 📝 Logging
- [ ] `TarjetaActivityLogNomina` registra todas las acciones
- [ ] `ActivityEvent` registra eventos de Celery
- [ ] Usuario correcto en todos los logs (NO Pablo Castro)
- [ ] Timestamps correctos
- [ ] Detalles completos en `details` field

### 🎨 Frontend
- [ ] Estado se actualiza automáticamente
- [ ] Ícono check verde aparece
- [ ] Botón "Eliminar" se habilita (si aplica)
- [ ] No hay errores en consola del navegador
- [ ] Mensajes de éxito se muestran

---

## ❌ POSIBLES ERRORES

### Error: "Columnas faltantes en Excel"
**Causa:** Formato incorrecto del archivo  
**Solución:** Regenerar con `generar_excel_movimientos_mes.py`

### Error: "Usuario Pablo Castro en logs"
**Causa:** Bug en propagación de usuario  
**Solución:** Verificar que `usuario_id` se pasa en la llamada a la tarea

### Error: "Estado no cambia a procesado"
**Causa:** Tarea Celery falló  
**Solución:** Ver logs de Celery: `docker compose logs celery_worker -f`

### Error: "Empleado no encontrado"
**Causa:** RUT no existe en `EmpleadoCierre`  
**Solución:** Verificar que empleados del Flujo 1 existen

---

## 🎯 TAREA BAJO PRUEBA

**Función:** `procesar_movimientos_mes_con_logging`  
**Ubicación:** `backend/nomina/tasks_refactored/movimientos_mes.py`

**Responsabilidades:**
1. Leer Excel de movimientos (5 hojas)
2. Validar formato y columnas
3. Crear registros por tipo de movimiento
4. Actualizar estado del upload
5. Registrar en TarjetaActivityLogNomina
6. Registrar en ActivityEvent

**Logging Dual:**
- **TarjetaActivityLogNomina**: Eventos de usuario (frontend)
- **ActivityEvent**: Eventos técnicos de Celery (backend)

---

## 📝 REGISTRO DE RESULTADOS

```
Fecha: 27 de octubre de 2025
Tester: _________________
Hora inicio: _____________
Hora fin: ________________

✅ Subida exitosa: [ ]
✅ Procesamiento completado: [ ]
✅ Movimientos creados: [ ]
   - Altas/Bajas: [ ]
   - Ausentismos: [ ]
   - Vacaciones: [ ]
   - Variaciones Sueldo: [ ]
   - Variaciones Contrato: [ ]
✅ Usuario correcto en logs: [ ]
✅ Estado final "procesado": [ ]
✅ Frontend actualiza: [ ]

Tiempo de procesamiento: _______ segundos

Errores encontrados:
___________________________________
___________________________________

Notas adicionales:
___________________________________
___________________________________
```

---

**URL de prueba:** http://172.17.11.18:5174/nomina/cierre/35  
**Archivo:** `/tmp/movimientos_mes_smoke_test.xlsx`  
**Documentar resultados en:** `SMOKE_TEST_FLUJO_2_RESULTADOS.md`
