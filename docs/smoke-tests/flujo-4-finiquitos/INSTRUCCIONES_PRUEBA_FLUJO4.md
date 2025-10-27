# 📋 Instrucciones de Prueba - Flujo 4: Finiquitos

**Flujo**: Procesamiento de archivos de finiquitos (terminaciones de contrato)  
**Arquitectura**: **MISMA** que Flujo 3 (Ingresos) - ya validada ✅  
**Tiempo estimado**: ~15 minutos

---

## 🎯 Objetivo

Validar que el procesamiento de archivos de finiquitos funciona correctamente:
- Upload y procesamiento asíncrono
- Creación de registros `AnalistaFiniquito`
- Fechas sin desfase
- Logging completo

---

## 📋 Pre-requisitos

- ✅ Sistema SGM corriendo (frontend + backend + Celery)
- ✅ Usuario analista: `analista.nomina@bdo.cl`
- ✅ Cierre de nómina activo (EMPRESA SMOKE TEST - 2025-10)
- ✅ Archivo de prueba: `finiquitos_smoke_test.xlsx`

---

## 🚀 Pasos de Ejecución

### 1. Limpiar Datos Anteriores

```bash
docker compose exec -T django python manage.py shell <<'PYEOF'
from nomina.models import ArchivoAnalistaUpload, AnalistaFiniquito

# Eliminar finiquitos y uploads anteriores
AnalistaFiniquito.objects.filter(cierre_id=35).delete()
ArchivoAnalistaUpload.objects.filter(cierre_id=35, tipo_archivo='finiquitos').delete()

print("✅ Datos limpiados")
PYEOF
```

### 2. Subir Archivo desde Frontend

1. Acceder a http://172.17.11.18:5174
2. Login con `analista.nomina@bdo.cl`
3. Ir a **Nómina** → Cierre **EMPRESA SMOKE TEST - 2025-10**
4. En la tarjeta **"Finiquitos"**:
   - Click en "Seleccionar archivo"
   - Seleccionar `finiquitos_smoke_test.xlsx`
   - Click en "Subir Finiquitos"

### 3. Verificar Logs en Frontend

Deberías ver 2 logs:
- **Process_Start** (info) - "Iniciando procesamiento..."
- **Process_Complete** (success) - "Procesamiento completado..."

---

## ✅ Verificación de Resultados

### Script de Verificación Rápida

```bash
docker compose exec -T django python manage.py shell <<'PYEOF'
from nomina.models import ArchivoAnalistaUpload, AnalistaFiniquito, TarjetaActivityLogNomina

# Buscar el upload más reciente
upload = ArchivoAnalistaUpload.objects.filter(
    tipo_archivo='finiquitos',
    cierre_id=35
).order_by('-id').first()

print(f"\n{'='*70}")
print(f"VERIFICACIÓN - FLUJO 4 (FINIQUITOS)")
print(f"{'='*70}\n")

if upload:
    print(f"1️⃣ UPLOAD: ID {upload.id}, estado={upload.estado}")
    
    # Registros creados
    finiquitos = AnalistaFiniquito.objects.filter(archivo_origen=upload)
    print(f"2️⃣ REGISTROS: {finiquitos.count()}/5 finiquitos")
    
    for f in finiquitos:
        print(f"   • {f.rut}: {f.nombre}")
        print(f"     Retiro: {f.fecha_retiro}, Motivo: {f.motivo}")
    
    # Logs
    logs = TarjetaActivityLogNomina.objects.filter(
        tarjeta='analista_finiquitos',
        cierre_id=35
    ).order_by('timestamp')
    
    print(f"\n3️⃣ LOGS: {logs.count()} eventos")
    for log in logs:
        print(f"   • {log.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"     {log.accion}: {log.resultado}")
    
    # Resultado final
    if upload.estado == 'procesado' and finiquitos.count() == 5:
        print(f"\n{'='*70}")
        print(f"✅ ÉXITO: Flujo 4 funcionando correctamente")
        print(f"{'='*70}\n")
    else:
        print(f"\n⚠️  REVISAR: Estado={upload.estado}, Registros={finiquitos.count()}")
else:
    print("❌ No se encontró el upload")

PYEOF
```

### Verificaciones Esperadas

| # | Verificación | Esperado | ¿Pasa? |
|---|--------------|----------|--------|
| 1 | Upload creado | ID presente, estado='procesado' | □ |
| 2 | Registros creados | 5 finiquitos | □ |
| 3 | Fechas correctas | Sin desfase de 1 día | □ |
| 4 | Usuario | analista.nomina@bdo.cl | □ |
| 5 | Logs | 2 eventos (start + complete) | □ |
| 6 | Asociaciones | Todos tienen archivo_origen | □ |

---

## 📊 Datos Esperados

### 5 Finiquitos

1. **19111111-1** - Juan Carlos Pérez López
   - Fecha Retiro: **2025-10-31**
   - Motivo: Renuncia Voluntaria

2. **19222222-2** - María Francisca González Muñoz
   - Fecha Retiro: **2025-10-15**
   - Motivo: Término de Contrato

3. **19333333-3** - Pedro Antonio Silva Rojas
   - Fecha Retiro: **2025-10-20**
   - Motivo: Mutuo Acuerdo

4. **19444444-4** - Ana María Torres Castro
   - Fecha Retiro: **2025-10-10**
   - Motivo: Necesidades de la Empresa

5. **19555555-5** - Carlos Alberto Ramírez Flores
   - Fecha Retiro: **2025-10-25**
   - Motivo: Renuncia Voluntaria

---

## 🐛 Troubleshooting

### Problema: Archivo no se procesa

**Solución**: Verificar Celery worker
```bash
docker compose logs celery_worker --tail=50
```

### Problema: Headers incorrectos

**Error esperado**: "Faltan columnas requeridas: X"

**Verificar**:
- El archivo tiene las columnas: `Rut`, `Nombre`, `Fecha Retiro`, `Motivo`
- Los nombres son exactos (case-sensitive)

### Problema: Fechas con desfase

**Verificar**:
```python
from nomina.models import AnalistaFiniquito
f = AnalistaFiniquito.objects.first()
print(f.fecha_retiro)  # Debe ser 2025-10-31, no 2025-10-30
```

---

## 📝 Documentar Resultados

Al finalizar, anotar:
- ✅ o ❌ para cada verificación
- Bugs encontrados (si los hay)
- Performance (tiempo de procesamiento)
- Cualquier comportamiento inesperado

---

**Nota**: Este flujo usa la **misma arquitectura que Flujo 3 (Ingresos)**, por lo que se espera el mismo nivel de estabilidad y performance.
