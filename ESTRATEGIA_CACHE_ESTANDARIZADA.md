# 🔄 ESTRATEGIA DE CACHÉ ESTANDARIZADA - SGM

## 📊 NIVELES DE CACHÉ IDENTIFICADOS

### 1. REDIS NÓMINA (DB 2) - `sgm:nomina:*`
- **Datos:** Informes, libro_resumen_v2, estadísticas
- **TTL:** Informes sin TTL, datos 5-10 min
- **Invalidación:** `cache.invalidate_cliente_periodo()`

### 2. REDIS CONTABILIDAD (DB 0) - `sgm:contabilidad:*`  
- **Datos:** KPIs, estados financieros, movimientos
- **TTL:** Variable por tipo
- **Invalidación:** `cache_system.invalidate_cliente_periodo()`

### 3. DJANGO CACHE (DB 1) - `sgm_backend:1:*`
- **Datos:** Incidencias optimizadas (solo contabilidad)
- **TTL:** Variable
- **Invalidación:** Pattern matching + delete

### 4. INFORMES PERSISTENTES (PostgreSQL)
- **Datos:** Datos históricos finalizados
- **TTL:** Sin expiración
- **Invalidación:** Marcador de invalidación

### 5. BROWSER HTTP CACHE
- **Datos:** Respuestas API
- **TTL:** Por defecto browser
- **Invalidación:** Cache-Control headers + timestamp

### 6. REACT STATE CACHE
- **Datos:** Estado componentes
- **TTL:** Hasta remount
- **Invalidación:** setState o key change

## 🎯 PROTOCOLO ESTANDARIZADO DE INVALIDACIÓN

### ESCENARIO: Reclasificación de Conceptos

**NIVELES A INVALIDAR:**
1. ✅ Redis Nómina (datos consolidados)
2. ✅ Informes Persistentes (marcar invalidado)
3. ❌ Browser Cache (NO se está invalidando)
4. ❌ React State (NO se está invalidando)

**SOLUCIÓN:**

#### A) Backend - Headers HTTP Anti-Cache
```python
@api_view(["POST"])
def reclasificar_concepto_consolidado(request, cierre_id: int):
    # ... lógica existente ...
    
    response = Response(data, status=200)
    # NUEVO: Headers para invalidar browser cache
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    return response
```

#### B) Backend - Endpoint libro_resumen_v2 con Headers
```python
@api_view(["GET"])
def libro_resumen_v2(request, cierre_id: int):
    # ... lógica existente ...
    
    response = Response(data, status=200)
    # Headers dinámicos según estado
    if cierre.estado != 'finalizado':
        response['Cache-Control'] = 'no-cache, max-age=0'
    else:
        # Solo cachear en browser si está finalizado Y no invalidado
        meta = data.get('meta', {})
        if meta.get('invalidado_por_reclasificacion'):
            response['Cache-Control'] = 'no-cache, max-age=0'
        else:
            response['Cache-Control'] = 'public, max-age=300'  # 5 min
    
    return response
```

#### C) Frontend - Cache Busting Automático
```javascript
// En nominaApi.js
export const obtenerLibroResumenV2 = async (cierreId, bustCache = false) => {
  const timestamp = bustCache ? `?_t=${Date.now()}` : '';
  const res = await api.get(`/nomina/cierres/${cierreId}/libro/v2/resumen/${timestamp}`);
  return res.data;
};

// En reclasificación exitosa
const handleReclasificar = async () => {
  await reclasificarConcepto(data);
  // Recargar con cache busting
  const newData = await obtenerLibroResumenV2(cierreId, true);
  setResumenV2(newData);
};
```

## 📋 CHECKLIST DE INVALIDACIÓN COMPLETA

### Al Reclasificar Concepto:
- [ ] Redis Nómina: Marcar datos consolidados como invalidados
- [ ] Informes Persistentes: Agregar meta.invalidado_por_reclasificacion
- [ ] Response Headers: Cache-Control no-cache
- [ ] Frontend: Recargar datos con cache busting
- [ ] React State: Actualizar estado con nuevos datos

### Al Finalizar Cierre:
- [ ] Redis Nómina: Guardar informe definitivo
- [ ] Redis Contabilidad: Limpiar datos temporales
- [ ] Informes Persistentes: Crear registro final
- [ ] Browser Cache: Permitir cache (headers public)

### Al Modificar Datos:
- [ ] Identificar nivel de caché afectado
- [ ] Invalidar en orden: Persistente > Redis > Browser > React
- [ ] Verificar headers HTTP apropiados
- [ ] Confirmar actualización en frontend

## 🛠️ HERRAMIENTAS DE MONITOREO

### Redis Keys por Patrón:
```bash
# Nómina
redis-cli -n 2 KEYS "sgm:nomina:*"

# Contabilidad  
redis-cli -n 0 KEYS "sgm:contabilidad:*"

# Django Cache
redis-cli -n 1 KEYS "sgm_backend:1:*"
```

### Browser Cache Inspector:
- DevTools > Network > Disable cache
- Headers Cache-Control verification
- Hard refresh (Ctrl+F5) test

### Informes Invalidados:
```sql
SELECT id, datos_cierre->'libro_resumen_v2'->'meta'->>'invalidado_por_reclasificacion' as invalidado
FROM nomina_informenomina 
WHERE datos_cierre->'libro_resumen_v2'->'meta'->>'invalidado_por_reclasificacion' = 'true';
```

## 🎯 REGLAS DE ORO

1. **NEVER CACHE**: Datos de cierres no finalizados
2. **ALWAYS INVALIDATE**: Todos los niveles en modificaciones
3. **HEADERS FIRST**: HTTP headers son la primera línea de defensa
4. **TIMESTAMP FALLBACK**: Cache busting como plan B
5. **MONITOR ALWAYS**: Logs de hit/miss en cada nivel

## 🚀 PRÓXIMOS PASOS

1. Implementar headers HTTP en reclasificación
2. Agregar cache busting en frontend reclasificación
3. Documentar patrones de invalidación por operación
4. Crear utilidad de limpieza total de caché
5. Monitoreo proactivo de inconsistencias de caché