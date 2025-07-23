# Funcionalidad de Creación y Selección Masiva de Cuentas

## 📋 Descripción
Se han implementado dos nuevas funcionalidades en el Modal de Clasificaciones:
1. **Creación masiva**: Crear múltiples cuentas nuevas mediante pegado de Excel
2. **Selección masiva**: Seleccionar múltiples cuentas existentes para clasificación masiva mediante pegado de Excel

## 🚀 Funcionalidades implementadas

### 1. Creación Masiva de Cuentas Nuevas

#### Cómo usar:
1. Haz clic en "Nuevo Registro (o pegar Excel)"
2. En el campo "Número de cuenta", pega directamente una columna copiada de Excel
3. El sistema detectará automáticamente múltiples cuentas y cambiará al modo masivo
4. Opcionalmente, aplica clasificaciones a todas las cuentas a la vez
5. Revisa la lista y haz clic en "Crear Todas"

#### Características:
- **Detección automática** de múltiples líneas
- **Validación previa** de cuentas existentes
- **Clasificación masiva** aplicable a todas las cuentas nuevas
- **Creación secuencial** con manejo de errores individual

### 2. Selección Masiva para Clasificación (🆕)

#### Cómo usar:
1. Activa el modo "Clasificación Masiva"
2. En el campo "Buscar/Seleccionar cuentas", pega la columna de Excel con las cuentas
3. El sistema buscará automáticamente las cuentas que coincidan
4. Confirmará cuántas encontró y cuántas no
5. Seleccionará automáticamente todas las cuentas encontradas
6. Aplica la clasificación deseada a todas las seleccionadas

#### Características:
- **Búsqueda inteligente**: Encuentra cuentas por coincidencia parcial o exacta
- **Selección automática**: Marca todas las cuentas encontradas
- **Reporte de resultados**: Muestra encontradas vs no encontradas
- **Búsqueda individual**: También funciona para búsquedas de una sola cuenta
- **Indicadores visuales**: Muestra estado de selección y búsqueda activa

## 🚀 Cómo usar

### Creación Individual (modo anterior)
1. Haz clic en "Nuevo Registro (o pegar Excel)"
2. Escribe el número de cuenta manualmente
3. Agrega clasificaciones
4. Guarda

### Creación Masiva (nueva funcionalidad)
1. Haz clic en "Nuevo Registro (o pegar Excel)"
2. En el campo "Número de cuenta", pega directamente una columna copiada de Excel con múltiples cuentas
3. El sistema detectará automáticamente que son múltiples cuentas y cambiará al modo masivo
4. Opcionalmente, aplica clasificaciones a todas las cuentas a la vez
5. Revisa la lista de cuentas y sus clasificaciones
6. Haz clic en "Crear Todas" para procesar todas las cuentas

### Selección Masiva para Clasificación (🆕)
1. Activa el modo "Clasificación Masiva" con el botón correspondiente
2. En el campo "Buscar/Seleccionar cuentas", pega la columna de Excel con las cuentas existentes
3. El sistema buscará y mostrará cuántas cuentas encontró vs no encontradas
4. Confirma para seleccionar automáticamente todas las encontradas
5. Selecciona el set y opción de clasificación deseada
6. Haz clic en "Aplicar" para clasificar todas las cuentas seleccionadas

## 🔧 Características

### Detección Automática
- El sistema detecta automáticamente cuando se pegan múltiples líneas
- Muestra un preview de todas las cuentas que se van a crear
- Valida que las cuentas no existan previamente

### Validaciones
- **Cuentas existentes**: Se detectan y muestran cuentas que ya existen, permitiendo al usuario decidir si continuar
- **Formato válido**: Se procesan solo líneas no vacías
- **Confirmación**: Se requiere confirmación antes de procesar múltiples cuentas

### Clasificación Masiva
- **Aplicar a todas**: Selecciona un set y opción para aplicar a todas las cuentas
- **Revisión individual**: Cada cuenta muestra sus clasificaciones asignadas
- **Eliminación selectiva**: Puedes remover clasificaciones de cuentas específicas

### Interface Visual
- **Indicador en título**: El modal muestra cuántas cuentas están en modo masivo
- **Lista organizada**: Cada cuenta se muestra en una fila separada con sus clasificaciones
- **Códigos de color**: Verde para creación masiva, azul para creación individual
- **Contador de progreso**: Muestra el estado de creación en tiempo real

## 📊 Ejemplos de uso

### Ejemplo 1: Creación Masiva (cuentas nuevas)
**Datos de entrada (copiados de Excel):**
```
1-01-001-001-0001
1-01-001-001-0004
1-01-001-002-0001
1-01-002-001-0001
1-01-003-001-0001
```

**Proceso:**
1. Usuario copia esta columna de Excel
2. Pega en el campo "Número de cuenta" del formulario de creación
3. Sistema detecta 5 cuentas nuevas y cambia a modo masivo
4. Se pueden aplicar clasificaciones masivas (opcional)
5. Se crean todas las cuentas con un solo clic

### Ejemplo 2: Selección Masiva (cuentas existentes) 🆕
**Datos de entrada (copiados de Excel):**
```
1-01-001-001-0001
1-01-001-001-0004
1-01-002-001-0001
1-01-999-999-9999  (no existe)
1-01-003-001-0001
```

**Proceso:**
1. Usuario activa "Clasificación Masiva"
2. Copia y pega la columna en "Buscar/Seleccionar cuentas"
3. Sistema busca y encuentra 4 de 5 cuentas
4. Muestra: "✅ 4 encontradas, ❌ 1 no encontrada (1-01-999-999-9999)"
5. Usuario confirma y se seleccionan automáticamente las 4 encontradas
6. Aplica clasificación deseada a todas las seleccionadas

## ⚠️ Consideraciones

### Rendimiento
- Las cuentas se crean secuencialmente para evitar sobrecarga del servidor
- Se muestra progreso durante la creación
- Los errores individuales no detienen el proceso completo

### Logging
- Cada cuenta creada se registra individualmente en el log de actividades
- Se genera un resumen final del proceso masivo
- Los errores se registran para auditoría

### Manejo de Errores
- **Cuentas duplicadas**: Se omiten automáticamente con advertencia
- **Errores de validación**: Se reportan individualmente sin afectar otras cuentas
- **Errores de red**: Se reintenta automáticamente para cuentas específicas

## 🎯 Beneficios

### Para Creación Masiva:
1. **Eficiencia**: Reduce significativamente el tiempo de creación de múltiples cuentas
2. **Compatibilidad**: Funciona directamente con datos copiados de Excel
3. **Flexibilidad**: Permite tanto creación individual como masiva en el mismo interface
4. **Seguridad**: Validaciones previas evitan duplicados y errores
5. **Trazabilidad**: Registro completo de todas las operaciones realizadas

### Para Selección Masiva (🆕):
1. **Velocidad**: Selecciona decenas de cuentas instantáneamente
2. **Precisión**: Encuentra cuentas por coincidencia inteligente
3. **Feedback**: Muestra claramente qué encontró y qué no
4. **Flexibilidad**: Funciona con búsquedas individuales o masivas
5. **Control**: Permite revisar selección antes de aplicar clasificaciones

## 🔄 Comparación de flujos

### Flujo tradicional (antes):
```
Para clasificar 20 cuentas específicas:
1. Buscar cuenta 1 manualmente → Seleccionar
2. Buscar cuenta 2 manualmente → Seleccionar
3. Buscar cuenta 3 manualmente → Seleccionar
...
20. Buscar cuenta 20 manualmente → Seleccionar
21. Aplicar clasificación
⏱️ Tiempo: ~10-15 minutos
```

### Flujo nuevo (ahora):
```
Para clasificar 20 cuentas específicas:
1. Activar "Clasificación Masiva"
2. Pegar lista de 20 cuentas → Auto-selección
3. Aplicar clasificación
⏱️ Tiempo: ~30 segundos
✨ Mejora: 95% más rápido
```

## 🔄 Flujo técnico

1. **Detección de paste**: Event listener en el input detecta pegado
2. **Procesamiento**: Función `procesarTextoPegado()` analiza el contenido
3. **Validación**: Se verifican cuentas existentes y formato
4. **Modo masivo**: Se activa interface especial para múltiples cuentas
5. **Clasificación**: Opción de aplicar clasificaciones a todas las cuentas
6. **Creación**: Procesamiento secuencial con manejo de errores
7. **Logging**: Registro detallado de cada operación
8. **Cleanup**: Limpieza del estado y recarga de datos

## 📝 Notas para desarrolladores

### Estados agregados:
- `creandoMasivo`: Boolean que indica si está en modo masivo de creación
- `cuentasMasivas`: Array de cuentas pendientes de crear
- `aplicandoCreacionMasiva`: Boolean para el estado de loading de creación
- `textoBusquedaMasiva`: String para búsqueda/pegado en clasificación masiva (🆕)

### Funciones principales:

#### Para creación masiva:
- `procesarTextoPegado()`: Analiza el texto pegado para creación
- `handleTextoPegado()`: Maneja la lógica de detección masiva de creación
- `handleGuardarCreacionMasiva()`: Procesa la creación de todas las cuentas
- `aplicarClasificacionMasivaACuentas()`: Aplica clasificaciones a todas las cuentas nuevas

#### Para selección masiva (🆕):
- `procesarTextoPegadoClasificacionMasiva()`: Analiza el texto pegado para selección
- `handleTextoPegadoClasificacionMasiva()`: Maneja la lógica de selección masiva
- `buscarYSeleccionarCuentas()`: Busca y selecciona cuentas por texto de búsqueda

### Componentes UI:

#### Para creación masiva:
- Sección de creación masiva en la tabla
- Indicador en el título del modal
- Panel de clasificación masiva para cuentas nuevas
- Lista de cuentas con preview de clasificaciones

#### Para selección masiva (🆕):
- Campo de búsqueda/pegado en panel de clasificación masiva
- Indicadores de estado de selección
- Tooltips informativos
- Feedback visual de búsqueda activa

### Algoritmos de búsqueda implementados:

#### Búsqueda inteligente para selección masiva:
```javascript
// Criterios de coincidencia (en orden de prioridad):
1. Coincidencia exacta: cuenta === textoPegado
2. Contiene: cuenta.includes(textoPegado)
3. Está contenida: textoPegado.includes(cuenta)
4. Case-insensitive para todos los casos
```

#### Validaciones:
- **Para creación**: Verifica que las cuentas NO existan
- **Para selección**: Busca cuentas que SÍ existan
- **Ambos casos**: Manejo de líneas vacías y limpieza de espacios
