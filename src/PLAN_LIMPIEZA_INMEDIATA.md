# 🧹 Plan de Limpieza Inmediata - Frontend

## ⚡ Acciones de Limpieza Inmediata

### 1. 🗂️ Eliminar Estructura Duplicada

**Problema**: Existe una carpeta `/root/SGM/frontend/` que está prácticamente vacía y duplica la estructura principal.

```bash
# Estructura actual problemática:
/root/SGM/
├── src/                    # ✅ Estructura principal (EN USO)
└── frontend/               # ❌ Estructura duplicada (VACÍA)
    └── src/                # Solo tiene ejemplo_finalizacion_component.jsx
        ├── components/     # Vacío
        ├── hooks/          # Vacío
        └── utils/          # Vacío
```

**Acción**: Eliminar completamente `/root/SGM/frontend/`

### 2. 🚮 Archivos Duplicados a Eliminar YA

```bash
# Archivos con versiones duplicadas:
src/components/TarjetasCierreNomina/
├── CierreProgresoNominaConLogging.jsx      # ❌ ELIMINAR
├── LibroRemuneracionesCardConLogging.jsx   # ❌ ELIMINAR  
├── MovimientosMesCardConLogging.jsx        # ❌ ELIMINAR

# Archivos de respaldo/temporales:
├── IncidenciasEncontradasSectionRespaldo.jsx  # ❌ ELIMINAR

src/components/TarjetasCierreContabilidad/
├── NombresEnInglesCard_new.jsx             # ❌ ELIMINAR
```

## 🔧 Scripts de Limpieza

### Script 1: Backup de Seguridad
```bash
# Crear backup antes de eliminar
mkdir -p /root/SGM/backup_cleanup_$(date +%Y%m%d_%H%M%S)
cp -r /root/SGM/frontend /root/SGM/backup_cleanup_*/
cp -r /root/SGM/src/components/TarjetasCierre* /root/SGM/backup_cleanup_*/
```

### Script 2: Limpieza de Duplicados
```bash
# Eliminar estructura duplicada
rm -rf /root/SGM/frontend/

# Eliminar archivos duplicados específicos  
cd /root/SGM/src/components/TarjetasCierreNomina/
rm -f CierreProgresoNominaConLogging.jsx
rm -f LibroRemuneracionesCardConLogging.jsx
rm -f MovimientosMesCardConLogging.jsx
rm -f IncidenciasEncontradasSectionRespaldo.jsx

cd /root/SGM/src/components/TarjetasCierreContabilidad/
rm -f NombresEnInglesCard_new.jsx
```

## 📋 Checklist de Verificación

### Antes de Ejecutar:
- [ ] ✅ Documentación creada (README_FRONTEND.md, ANALISIS_TARJETAS_CRITICO.md)
- [ ] ✅ Backup de seguridad creado
- [ ] ✅ Git commit de estado actual

### Después de Ejecutar:
- [ ] 🔍 Verificar que no hay imports rotos
- [ ] 🔍 Buscar referencias a archivos eliminados
- [ ] 🔍 Probar que la aplicación arranca sin errores
- [ ] ✅ Git commit de limpieza

## 🔍 Comandos de Verificación

### Buscar Referencias a Archivos Eliminados:
```bash
# Buscar imports de archivos que vamos a eliminar
grep -r "ConLogging" /root/SGM/src/ --include="*.jsx" --include="*.js"
grep -r "_new" /root/SGM/src/ --include="*.jsx" --include="*.js"
grep -r "Respaldo" /root/SGM/src/ --include="*.jsx" --include="*.js"

# Buscar referencias a la carpeta frontend duplicada
grep -r "frontend/" /root/SGM/ --include="*.json" --include="*.js" --include="*.jsx"
```

### Verificar Integridad Post-Limpieza:
```bash
# Contar archivos antes y después
find /root/SGM/src/components/TarjetasCierre* -name "*.jsx" | wc -l

# Verificar imports en App.jsx
node -c /root/SGM/src/App.jsx

# Verificar si hay archivos sin extensión o temporales
find /root/SGM/src -name "*~" -o -name "*.tmp" -o -name "*.bak"
```

---

## ⚠️ IMPORTANTE: Orden de Ejecución

1. **PRIMERO**: Crear documentación ✅ (YA HECHO)
2. **SEGUNDO**: Crear backup de seguridad
3. **TERCERO**: Verificar referencias
4. **CUARTO**: Ejecutar limpieza
5. **QUINTO**: Verificar integridad
6. **SEXTO**: Commit de limpieza

**NO EJECUTAR** scripts de limpieza sin antes completar los pasos 1-3.

---
*Plan creado: 21 de julio de 2025*
*Estado: 📋 Listo para ejecutar*
