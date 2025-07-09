# Sistema de Incidencias Simplificado - Cierre de Nómina

## 🎯 Objetivo

Detectar automáticamente diferencias entre archivos del proceso de Cierre de Nómina mediante un sistema **solo informativo** que impulse la corrección a través de resubida de archivos.

## 📋 Flujo Simplificado

### 1. **Generar Incidencias**
- Se ejecuta cuando el cierre está en estado `datos_consolidados`
- Compara automáticamente archivos procesados
- Genera lista de diferencias encontradas

### 2. **Revisar Incidencias**
- Tabla informativa con todas las incidencias detectadas
- Filtros por prioridad y tipo de incidencia
- Información detallada de cada diferencia

### 3. **Corregir Archivos**
- El analista corrige los archivos en su origen
- Utiliza la función "Resubir archivo" en cada tarjeta
- Los archivos se procesan nuevamente

### 4. **Repetir hasta 0**
- Volver a generar incidencias después de correcciones
- Repetir proceso hasta llegar a 0 incidencias
- Meta: archivos 100% consistentes

## 🔍 Tipos de Incidencias Detectadas

### **Grupo 1: Libro de Remuneraciones vs Novedades**
- **Empleado solo en Novedades**: Empleado tiene novedades pero no está en el libro
- **Diferencia en Datos Personales**: Nombres no coinciden
- **Diferencia en Sueldo Base**: Sueldo base diferente
- **Diferencia en Monto por Concepto**: Montos diferentes para el mismo concepto
- **Concepto solo en Novedades**: Concepto existe en novedades pero no en libro

### **Grupo 2: MovimientosMes vs Archivos del Analista**
- **Ingreso no reportado**: Ingreso en movimientos pero no en archivos del analista
- **Finiquito no reportado**: Finiquito en movimientos pero no reportado
- **Ausencia no reportada**: Ausencia en movimientos pero no en archivos del analista
- **Diferencias en fechas/días/tipo de ausencia**: Datos inconsistentes

## 🎨 Interfaz de Usuario

### **Sección Principal**
- Título: "Sistema de Incidencias"
- Contador total de incidencias en el header
- Botón "Generar Incidencias" (solo cuando está en estado adecuado)
- Botón "Vista Previa" para ver qué se detectaría

### **Métricas Resumidas**
- **Total de Incidencias**: Número total encontrado
- **Críticas**: Incidencias de alta prioridad
- **Impacto Monetario**: Suma del impacto económico

### **Tabla de Incidencias**
- **Solo lectura**: No hay botones de resolución
- **Columnas**: Empleado, Tipo, Descripción, Prioridad, Impacto Monetario, Fecha
- **Filtros**: Por prioridad, tipo de incidencia, búsqueda de texto
- **Estadísticas**: Contadores rápidos por prioridad

### **Mensajes de Estado**
- **0 incidencias**: "¡Perfecto! Los archivos están perfectamente sincronizados"
- **Con incidencias**: Información sobre cómo corregir resubiendo archivos

## 🔧 Implementación Técnica

### **Backend (mantiene arquitectura robusta)**
- Modelos completos para futuras fases
- Lógica de comparación intacta
- API endpoints listos para expansión

### **Frontend (simplificado)**
- Removidos modales de resolución
- Removidos estados de aprobación/rechazo
- Removidas funciones de asignación de usuarios
- Tabla informativa únicamente

## 🚀 Futuras Fases

Esta implementación mantiene la base para futuras expansiones:
- Sistema de resolución colaborativa
- Aprobaciones de supervisor
- Historial de resoluciones
- Notificaciones automáticas
- Métricas avanzadas

## ✅ Ventajas del Enfoque Simplificado

1. **Claridad**: Flujo directo y fácil de entender
2. **Eficiencia**: Resolución rápida mediante resubida
3. **Calidad**: Impulsa la corrección en la fuente
4. **Transparencia**: Información clara sobre qué corregir
5. **Escalabilidad**: Base sólida para futuras funcionalidades

## 🎯 Resultado Final

El sistema funciona como un "validador automático" que:
- Detecta inconsistencias entre archivos
- Presenta información clara y priorizada
- Guía al analista hacia la corrección
- Valida que los archivos estén perfectamente sincronizados
- Permite completar el cierre con confianza total
