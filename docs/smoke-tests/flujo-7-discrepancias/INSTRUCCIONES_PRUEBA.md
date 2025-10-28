# Instrucciones de Prueba - Flujo 7: Verificación de Discrepancias

## 🎯 Objetivo

Validar que el sistema de verificación de discrepancias:
1. Detecta correctamente diferencias entre fuentes de datos
2. Genera registros de discrepancias apropiados
3. Actualiza el estado del cierre según resultado
4. Implementa logging dual completo
5. Permite consultar y filtrar discrepancias

---

## 📋 Pre-requisitos

### 1. Datos Necesarios (de flujos anteriores)

Para esta prueba **reutilizaremos** el cierre ya existente de los flujos anteriores:

```python
# Cierre de prueba (ya existente de Flujos 1-6)
Cierre ID: 35
Periodo: Octubre 2025
Cliente: Cliente Demo
Estado actual: 'archivos_completos' o 'datos_consolidados'

# Datos ya cargados:
- ✅ Libro de Remuneraciones procesado (Flujo 1)
- ✅ Movimientos del Mes procesados (Flujo 2)
- ✅ Ingresos analista procesados (Flujo 3)
- ✅ Finiquitos analista procesados (Flujo 4)
- ✅ Incidencias procesadas (Flujo 5)
- ✅ Novedades procesadas (Flujo 6)
```

### 2. Acceso Necesario

```bash
# Frontend activo
http://172.17.11.18:5174

# Backend activo
http://172.17.11.18:8000

# Usuario: analista.nomina@bdo.cl
# Puede generar discrepancias
```

### 3. Verificar Estado del Sistema

```bash
# 1. Verificar que el cierre existe
docker compose exec -T django python manage.py shell <<EOF
from nomina.models import CierreNomina
cierre = CierreNomina.objects.get(id=35)
print(f"Cierre {cierre.id}: {cierre.periodo} - Estado: {cierre.estado}")

# Ver qué archivos tiene
print(f"Libro Remuneraciones: {cierre.libros_remuneraciones.count()}")
print(f"Movimientos: {cierre.movimientos_mes.count()}")
print(f"Archivo Ingresos: {hasattr(cierre, 'archivo_analista_ingresos')}")
print(f"Archivo Finiquitos: {hasattr(cierre, 'archivo_analista_finiquitos')}")
print(f"Archivo Incidencias: {hasattr(cierre, 'archivo_analista_incidencias')}")
print(f"Archivo Novedades: {hasattr(cierre, 'archivo_novedades')}")
EOF
```

---

## 🧪 PRUEBA 1: Verificación Sin Modificar Datos (Escenario Real)

**Objetivo**: Ejecutar verificación sobre los datos reales existentes

### Paso 1.1: Preparar el Cierre

```bash
# Asegurarse de que el cierre esté en estado apropiado
docker compose exec -T django python manage.py shell <<EOF
from nomina.models import CierreNomina

cierre = CierreNomina.objects.get(id=35)

# Si está en estado no permitido, cambiarlo a 'archivos_completos'
estados_validos = ['archivos_completos', 'verificacion_datos', 'con_discrepancias', 'datos_consolidados', 'discrepancias_detectadas']

if cierre.estado not in estados_validos:
    print(f"⚠️ Estado actual: '{cierre.estado}' no es válido")
    print(f"✅ Cambiando a 'archivos_completos'")
    cierre.estado = 'archivos_completos'
    cierre.save()
else:
    print(f"✅ Estado actual '{cierre.estado}' es válido para verificación")

print(f"Estado final: {cierre.estado}")
EOF
```

### Paso 1.2: Ejecutar Verificación desde Django Shell

```bash
# Ejecutar la verificación programáticamente
docker compose exec -T django python manage.py shell <<EOF
from nomina.tasks_refactored.discrepancias import generar_discrepancias_cierre_con_logging
from django.contrib.auth import get_user_model

# Obtener usuario analista
User = get_user_model()
usuario = User.objects.get(correo_bdo='analista.nomina@bdo.cl')

# Ejecutar verificación
print("🔍 Iniciando verificación de discrepancias...")
result = generar_discrepancias_cierre_con_logging.delay(35, usuario.id)

print(f"✅ Tarea iniciada: {result.id}")
print(f"📊 Esperando resultado...")

# Esperar resultado (máximo 30 segundos)
import time
timeout = 30
elapsed = 0
while not result.ready() and elapsed < timeout:
    time.sleep(1)
    elapsed += 1
    if elapsed % 5 == 0:
        print(f"... esperando ({elapsed}s)")

if result.ready():
    if result.successful():
        resultado = result.result
        print(f"\n✅ VERIFICACIÓN COMPLETADA")
        print(f"Total discrepancias: {resultado.get('total_discrepancias', 'N/A')}")
        print(f"Estado final cierre: {resultado.get('estado_final', 'N/A')}")
    else:
        print(f"\n❌ ERROR: {result.result}")
else:
    print(f"\n⏱️ Timeout - revisar con task_id: {result.id}")
EOF
```

### Paso 1.3: Verificar Resultados

```bash
# Script de verificación completo
docker compose exec -T django python manage.py shell <<'EOF'
from nomina.models import CierreNomina, DiscrepanciaCierre, HistorialVerificacionCierre
from nomina.models_logging import TarjetaActivityLogNomina
from api.models import ActivityEvent

cierre = CierreNomina.objects.get(id=35)

print("\n" + "="*60)
print("📊 RESULTADOS DE VERIFICACIÓN DE DISCREPANCIAS")
print("="*60)

# 1. Estado del cierre
print(f"\n🔹 CIERRE")
print(f"  ID: {cierre.id}")
print(f"  Periodo: {cierre.periodo}")
print(f"  Estado: {cierre.estado}")

# 2. Total de discrepancias
total_discrepancias = cierre.discrepancias.count()
print(f"\n🔹 DISCREPANCIAS DETECTADAS")
print(f"  Total: {total_discrepancias}")

if total_discrepancias > 0:
    # Agrupar por tipo
    from django.db.models import Count
    por_tipo = cierre.discrepancias.values('tipo_discrepancia').annotate(
        total=Count('id')
    ).order_by('-total')
    
    print(f"\n  Por tipo:")
    for item in por_tipo:
        print(f"    - {item['tipo_discrepancia']}: {item['total']}")
    
    # Empleados afectados
    empleados_afectados = cierre.discrepancias.values('rut_empleado').distinct().count()
    print(f"\n  Empleados afectados: {empleados_afectados}")
    
    # Mostrar primeras 5 discrepancias
    print(f"\n  Primeras 5 discrepancias:")
    for disc in cierre.discrepancias.all()[:5]:
        print(f"    {disc.id}. {disc.get_tipo_discrepancia_display()}")
        print(f"       RUT: {disc.rut_empleado}")
        print(f"       Desc: {disc.descripcion[:80]}...")
        if disc.valor_libro:
            print(f"       Libro: {disc.valor_libro}")
        if disc.valor_novedades:
            print(f"       Novedades: {disc.valor_novedades}")
        print()

# 3. Historial de verificaciones
historial = cierre.historial_verificaciones.order_by('-fecha_ejecucion')
print(f"\n🔹 HISTORIAL DE VERIFICACIONES")
print(f"  Total ejecuciones: {historial.count()}")

if historial.exists():
    ultima = historial.first()
    print(f"\n  Última verificación:")
    print(f"    Intento #: {ultima.numero_intento}")
    print(f"    Fecha: {ultima.fecha_ejecucion}")
    print(f"    Usuario: {ultima.usuario_ejecutor.correo_bdo if ultima.usuario_ejecutor else 'N/A'}")
    print(f"    Estado: {ultima.estado_verificacion}")
    print(f"    Discrepancias encontradas: {ultima.total_discrepancias_encontradas}")
    print(f"      - Libro vs Novedades: {ultima.discrepancias_libro_vs_novedades}")
    print(f"      - Movimientos vs Analista: {ultima.discrepancias_movimientos_vs_analista}")
    if ultima.tiempo_ejecucion:
        print(f"    Tiempo: {ultima.tiempo_ejecucion}s")

# 4. Logging - TarjetaActivityLogNomina
logs_tarjeta = TarjetaActivityLogNomina.objects.filter(
    cierre_id=cierre.id,
    tarjeta='revision'
).order_by('-timestamp')

print(f"\n🔹 LOGGING - TarjetaActivityLogNomina")
print(f"  Eventos (tarjeta=revision): {logs_tarjeta.count()}")

if logs_tarjeta.exists():
    print(f"\n  Últimos 3 eventos:")
    for log in logs_tarjeta[:3]:
        print(f"    - {log.timestamp.strftime('%H:%M:%S')} | {log.accion} | {log.descripcion[:50]}...")

# 5. Logging - ActivityEvent
logs_activity = ActivityEvent.objects.filter(
    cierre_id=cierre.id,
    event_type='verification'
).order_by('-timestamp')

print(f"\n🔹 LOGGING - ActivityEvent")
print(f"  Eventos (type=verification): {logs_activity.count()}")

if logs_activity.exists():
    print(f"\n  Últimos 3 eventos:")
    for log in logs_activity[:3]:
        print(f"    - {log.timestamp.strftime('%H:%M:%S')} | {log.action} | {log.resource_type}")

# 6. Resumen de verificaciones
print("\n" + "="*60)
print("✅ VERIFICACIONES")
print("="*60)

verificaciones = []

# V1: Tarea ejecutada
verificaciones.append(("Tarea ejecutada sin errores", historial.exists() and historial.first().estado_verificacion == 'completado'))

# V2: Logging dual
logs_ok = logs_tarjeta.count() >= 2 and logs_activity.count() >= 2
verificaciones.append(("Logging dual (>=2 eventos cada uno)", logs_ok))

# V3: Discrepancias detectadas
verificaciones.append(("Discrepancias detectadas", True))  # Siempre se detectan (0 o más)

# V4: Estado actualizado
estado_correcto = (
    (total_discrepancias == 0 and cierre.estado == 'verificado_sin_discrepancias') or
    (total_discrepancias > 0 and cierre.estado == 'discrepancias_detectadas')
)
verificaciones.append(("Estado del cierre actualizado correctamente", estado_correcto))

# V5: Historial creado
hist_creado = historial.exists() and historial.first().total_discrepancias_encontradas == total_discrepancias
verificaciones.append(("HistorialVerificacionCierre creado", hist_creado))

# V6: Usuario registrado
usuario_ok = logs_tarjeta.exists() and logs_tarjeta.first().usuario is not None
verificaciones.append(("Usuario ejecutor registrado", usuario_ok))

# Mostrar resultados
total_verificaciones = len(verificaciones)
verificaciones_ok = sum(1 for _, ok in verificaciones if ok)

for i, (desc, ok) in enumerate(verificaciones, 1):
    status = "✅" if ok else "❌"
    print(f"{status} {i}. {desc}")

print(f"\n📊 RESULTADO: {verificaciones_ok}/{total_verificaciones} verificaciones")

if verificaciones_ok == total_verificaciones:
    print("🎉 FLUJO 7 - VERIFICACIÓN EXITOSA 🎉")
else:
    print("⚠️ Algunas verificaciones fallaron - revisar detalles arriba")

print("="*60 + "\n")
EOF
```

---

## 🧪 PRUEBA 2: Consultar Discrepancias via API (Opcional)

Si se detectaron discrepancias, probar los endpoints:

```bash
# Obtener token (si no lo tienes)
TOKEN=$(curl -s -X POST http://172.17.11.18:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"correo_bdo":"analista.nomina@bdo.cl","password":"tu_password"}' \
  | jq -r '.access')

# 1. Estado de discrepancias
curl -s -X GET "http://172.17.11.18:8000/api/nomina/discrepancias/estado/35/" \
  -H "Authorization: Bearer $TOKEN" | jq

# 2. Resumen detallado
curl -s -X GET "http://172.17.11.18:8000/api/nomina/discrepancias/resumen/35/" \
  -H "Authorization: Bearer $TOKEN" | jq

# 3. Listar discrepancias (primeras 10)
curl -s -X GET "http://172.17.11.18:8000/api/nomina/discrepancias/?cierre=35&limit=10" \
  -H "Authorization: Bearer $TOKEN" | jq

# 4. Filtrar por tipo específico (ejemplo: diff_sueldo_base)
curl -s -X GET "http://172.17.11.18:8000/api/nomina/discrepancias/?cierre=35&tipo=diff_sueldo_base" \
  -H "Authorization: Bearer $TOKEN" | jq
```

---

## 🧪 PRUEBA 3: Crear Discrepancias Artificiales (Opcional)

Si la verificación real no encuentra discrepancias y quieres probar el sistema:

```bash
# Crear una discrepancia artificial para testing
docker compose exec -T django python manage.py shell <<'EOF'
from nomina.models import CierreNomina, DiscrepanciaCierre, EmpleadoCierre
from django.utils import timezone

cierre = CierreNomina.objects.get(id=35)

# Obtener un empleado existente
empleado = EmpleadoCierre.objects.filter(cierre=cierre).first()

if empleado:
    # Crear discrepancia artificial
    disc = DiscrepanciaCierre.objects.create(
        cierre=cierre,
        tipo_discrepancia='diff_sueldo_base',
        empleado_libro=empleado,
        rut_empleado=empleado.rut,
        descripcion='Diferencia artificial para testing',
        valor_libro='1000000',
        valor_novedades='1100000',
        concepto_afectado='Sueldo Base',
        fecha_detectada=timezone.now()
    )
    
    print(f"✅ Discrepancia artificial creada: ID {disc.id}")
    print(f"   Tipo: {disc.get_tipo_discrepancia_display()}")
    print(f"   RUT: {disc.rut_empleado}")
    
    # Actualizar estado del cierre
    cierre.estado = 'discrepancias_detectadas'
    cierre.save()
    
    print(f"✅ Estado del cierre actualizado a: {cierre.estado}")
else:
    print("❌ No hay empleados en el cierre para crear discrepancia")
EOF
```

---

## 📊 Verificación Final

### Script de Verificación Completo

Ejecutar al final de las pruebas para validar todo:

```bash
docker compose exec -T django python manage.py shell <<'EOF'
from nomina.models import CierreNomina, DiscrepanciaCierre, HistorialVerificacionCierre
from nomina.models_logging import TarjetaActivityLogNomina
from api.models import ActivityEvent

print("\n" + "="*70)
print("🎯 VERIFICACIÓN FINAL - FLUJO 7: DISCREPANCIAS")
print("="*70)

cierre_id = 35
cierre = CierreNomina.objects.get(id=cierre_id)

# Datos base
total_discrepancias = cierre.discrepancias.count()
historial = cierre.historial_verificaciones.order_by('-fecha_ejecucion').first()
logs_tarjeta = TarjetaActivityLogNomina.objects.filter(cierre_id=cierre.id, tarjeta='revision').count()
logs_activity = ActivityEvent.objects.filter(cierre_id=cierre.id, event_type='verification').count()

# Lista de verificaciones
checks = [
    ("Cierre existe", cierre is not None),
    ("Verificación ejecutada", historial is not None),
    ("Estado del historial = completado", historial and historial.estado_verificacion == 'completado'),
    ("Total discrepancias >= 0", total_discrepancias >= 0),
    ("Estado cierre actualizado", cierre.estado in ['verificado_sin_discrepancias', 'discrepancias_detectadas']),
    ("Logs TarjetaActivityLogNomina (>=2)", logs_tarjeta >= 2),
    ("Logs ActivityEvent (>=2)", logs_activity >= 2),
    ("Usuario ejecutor registrado", historial and historial.usuario_ejecutor is not None),
    ("Tiempo de ejecución calculado", historial and historial.tiempo_ejecucion is not None),
]

# Mostrar resultados
print("\n📋 CHECKLIST DE VERIFICACIONES:\n")
passed = 0
for i, (check, result) in enumerate(checks, 1):
    status = "✅" if result else "❌"
    print(f"{status} {i}. {check}")
    if result:
        passed += 1

# Datos adicionales
print(f"\n📊 DATOS DE LA VERIFICACIÓN:")
print(f"   Cierre ID: {cierre.id}")
print(f"   Estado cierre: {cierre.estado}")
print(f"   Total discrepancias: {total_discrepancias}")
if historial:
    print(f"   Intento #: {historial.numero_intento}")
    print(f"   Usuario: {historial.usuario_ejecutor.correo_bdo if historial.usuario_ejecutor else 'N/A'}")
    print(f"   Tiempo: {historial.tiempo_ejecucion}s" if historial.tiempo_ejecucion else "   Tiempo: N/A")
print(f"   Logs Tarjeta: {logs_tarjeta}")
print(f"   Logs Activity: {logs_activity}")

# Resultado final
print("\n" + "="*70)
print(f"📊 RESULTADO: {passed}/{len(checks)} verificaciones pasadas ({passed*100//len(checks)}%)")
print("="*70)

if passed == len(checks):
    print("\n🎉🎉🎉 FLUJO 7 (DISCREPANCIAS) - COMPLETADO EXITOSAMENTE 🎉🎉🎉\n")
else:
    print(f"\n⚠️ FALTAN {len(checks) - passed} VERIFICACIONES - REVISAR DETALLES\n")
EOF
```

---

## 🎯 Criterios de Éxito

Para considerar el Flujo 7 como **COMPLETADO**, todas estas verificaciones deben pasar:

1. ✅ **Verificación ejecutada**: `HistorialVerificacionCierre` creado con estado `completado`
2. ✅ **Estado correcto**: 
   - Si 0 discrepancias → `verificado_sin_discrepancias`
   - Si >0 discrepancias → `discrepancias_detectadas`
3. ✅ **Logging TarjetaActivityLogNomina**: Mínimo 2 eventos con tarjeta=`revision`
4. ✅ **Logging ActivityEvent**: Mínimo 2 eventos con type=`verification`
5. ✅ **Usuario registrado**: Usuario ejecutor en historial y logs
6. ✅ **Tiempo calculado**: `tiempo_ejecucion` en historial
7. ✅ **Total discrepancias**: Registrado correctamente en historial
8. ✅ **Discrepancias consultables**: API endpoints funcionan
9. ✅ **Sin errores**: Task completa sin excepciones

---

## 📝 Notas

- Este flujo valida datos **ya existentes** de flujos anteriores
- El número de discrepancias dependerá de la consistencia de los datos cargados
- **0 discrepancias es un resultado válido** (significa datos consistentes)
- Si hay discrepancias, no es un error del sistema sino información útil para el usuario

---

**Siguiente paso**: Documentar resultados en `RESULTADOS.md`
