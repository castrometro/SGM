# Módulo de Herramientas de Nómina

Módulo completo para gestión de herramientas y utilidades específicas del área de Nómina.

## 📁 Estructura

```
herramientas/
├── components/
│   ├── ToolCard.jsx           # Card individual de herramienta
│   ├── CategoryTabs.jsx       # Navegación por categorías
│   └── InfoBanner.jsx         # Banner informativo
├── constants/
│   └── herramientas.constants.js  # Constantes del módulo
├── pages/
│   └── HerramientasNominaPage.jsx # Página principal
├── utils/
│   └── toolsConfig.js         # Configuración de herramientas
├── index.js                   # Exports públicos
└── README.md                  # Esta documentación
```

## 🎯 Características

- ✅ Organización por categorías (General, Nómina, Reportes, Integraciones)
- ✅ Sistema de estados (Disponible, Beta, Próximamente, Mantenimiento)
- ✅ Animaciones escalonadas con Framer Motion
- ✅ Cards interactivos con estados visuales
- ✅ Estadísticas de herramientas disponibles
- ✅ Navegación fluida entre categorías
- ✅ Responsive design

## 🚀 Uso

### Importar la página

```javascript
import { HerramientasNominaPage } from './modules/nomina/herramientas';

// En tu router
<Route path="/menu/tools" element={<HerramientasNominaPage />} />
```

### Agregar nueva herramienta

En `utils/toolsConfig.js`:

```javascript
export const NOMINA_TOOLS = [
  // ... herramientas existentes
  {
    title: "Nueva Herramienta",
    description: "Descripción de la herramienta",
    icon: IconComponent, // De lucide-react
    color: TOOL_COLORS.blue,
    path: "/ruta/a/la/herramienta",
    status: TOOL_STATUS.AVAILABLE
  }
];
```

## 📋 Categorías de Herramientas

### 1. Herramientas Generales
- Captura Masiva de Gastos ✅
- Exportar Datos (próximamente)
- Importar Empleados (próximamente)

### 2. Gestión de Nómina
- Libro de Remuneraciones (próximamente)
- Cálculo de Finiquitos (próximamente)
- Gestión de Incidencias (próximamente)
- Calendario Laboral (próximamente)

### 3. Reportes y Análisis
- Dashboard de Nómina (beta)
- Reportes Personalizados (próximamente)
- Análisis de Costos (próximamente)
- Gestión de Analistas (próximamente)

### 4. Integraciones
- Integración Previred (próximamente)
- Integración SII (próximamente)

## 🎨 Componentes

### ToolCard
Card individual para cada herramienta con animación y estados visuales.

**Props:**
- `title`: string - Título de la herramienta
- `description`: string - Descripción breve
- `icon`: Component - Ícono de Lucide React
- `color`: string - Clase de color
- `onClick`: Function - Callback al hacer click
- `status`: string - Estado de la herramienta
- `index`: number - Para animación escalonada

### CategoryTabs
Navegación con tabs animados para cambiar entre categorías.

**Props:**
- `categories`: Array - Lista de categorías
- `activeCategory`: string - ID de categoría activa
- `onCategoryChange`: Function - Callback al cambiar categoría

### InfoBanner
Banner informativo con estilos consistentes del módulo.

## 🔧 Configuración

### Estados de Herramientas

```javascript
TOOL_STATUS.AVAILABLE    // Herramienta funcional
TOOL_STATUS.BETA         // En pruebas
TOOL_STATUS.COMING_SOON  // En desarrollo
TOOL_STATUS.MAINTENANCE  // En mantenimiento
```

### Colores Disponibles

```javascript
TOOL_COLORS.emerald
TOOL_COLORS.blue
TOOL_COLORS.green
TOOL_COLORS.purple
// ... ver herramientas.constants.js para lista completa
```

## 📊 Estadísticas

El módulo incluye `getToolsStats()` que retorna:

```javascript
{
  total: 15,        // Total de herramientas
  available: 1,     // Disponibles
  beta: 1,          // En beta
  comingSoon: 13    // Próximamente
}
```

## 🎯 Principios de Diseño

1. **Colocación**: Todo relacionado con herramientas está junto
2. **Modularidad**: Cada componente es independiente
3. **Escalabilidad**: Fácil agregar nuevas herramientas
4. **Consistencia**: Mismo patrón que otros módulos
5. **UX**: Animaciones y feedback visual claro

## 📝 Notas

- Las herramientas se habilitan progresivamente
- El estado "Beta" permite acceso con advertencia
- Las rutas null previenen navegación prematura
- Incluye logs para debugging en desarrollo
