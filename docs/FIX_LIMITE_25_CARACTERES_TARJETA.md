# 🔧 FIX: Límite de 25 caracteres en campo tarjeta

## ❌ Problema Encontrado

Al intentar usar tarjetas específicas largas:
```
archivos_analista_finiquitos  = 29 caracteres ❌
archivos_analista_incidencias = 30 caracteres ❌
archivos_analista_ingresos    = 27 caracteres ❌
```

**Error de base de datos:**
```
django.db.utils.DataError: value too long for type character varying(25)
```

El campo `tarjeta` en `TarjetaActivityLogNomina` tiene un límite de **25 caracteres**.

## ✅ Solución: Nombres Abreviados

Cambiamos a nombres más cortos que caben en el límite:

```python
# ✅ Nombres abreviados (caben en 25 chars)
'analista_finiquitos'   = 20 caracteres ✅
'analista_incidencias'  = 21 caracteres ✅
'analista_ingresos'     = 18 caracteres ✅
```

## 📊 Comparación Final

### ActivityEvent (sin límite)
```python
resource_type = 'archivo_analista_finiquitos'   # 29 chars OK
resource_type = 'archivo_analista_incidencias'  # 30 chars OK
resource_type = 'archivo_analista_ingresos'     # 27 chars OK
```

### TarjetaActivityLogNomina (límite 25 chars)
```python
tarjeta = 'analista_finiquitos'    # 20 chars ✅
tarjeta = 'analista_incidencias'   # 21 chars ✅
tarjeta = 'analista_ingresos'      # 18 chars ✅
```

## 🔍 Queries Actualizadas

```python
# Ver finiquitos
TarjetaActivityLogNomina.objects.filter(tarjeta='analista_finiquitos')

# Ver incidencias
TarjetaActivityLogNomina.objects.filter(tarjeta='analista_incidencias')

# Ver ingresos
TarjetaActivityLogNomina.objects.filter(tarjeta='analista_ingresos')

# Ver todos los archivos analista
TarjetaActivityLogNomina.objects.filter(tarjeta__startswith='analista_')
```

## 📝 Cambios Aplicados

### 1. tasks_refactored/archivos_analista.py
```python
# Cambio de:
tarjeta_especifica = f'archivos_analista_{tipo_archivo}'

# A:
tarjeta_especifica = f'analista_{tipo_archivo}'
```

### 2. views_archivos_analista.py
```python
# Cambio de:
tarjeta_especifica = f"archivos_analista_{tipo}"

# A:
tarjeta_especifica = f"analista_{tipo}"
```

## ✅ Validación

| Nombre | Longitud | Estado |
|--------|----------|--------|
| `analista_finiquitos` | 20 | ✅ < 25 |
| `analista_incidencias` | 21 | ✅ < 25 |
| `analista_ingresos` | 18 | ✅ < 25 |

## 🎯 Beneficios Mantenidos

A pesar del nombre más corto, se mantienen todos los beneficios:

✅ Filtrado directo por tipo  
✅ Diferenciación clara en logs  
✅ Queries simples sin revisar detalles  
✅ Estadísticas por tipo de archivo  

## 🔮 Recomendación Futura

Si se requiere cambiar el límite de la base de datos en el futuro:

```python
# En models_logging.py
class TarjetaActivityLogNomina(models.Model):
    tarjeta = models.CharField(
        max_length=50,  # Aumentar de 25 a 50
        db_index=True
    )
```

Luego generar y aplicar migración:
```bash
python manage.py makemigrations
python manage.py migrate
```

---

**Fix aplicado:** 18 de octubre de 2025  
**Estado:** ✅ Resuelto y desplegado
