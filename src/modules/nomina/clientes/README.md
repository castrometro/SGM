# 📋 Módulo de Clientes de Nómina

Módulo refactorizado para la gestión de clientes del área de Nómina, siguiendo el patrón de arquitectura modular establecido.

## 🏗️ Estructura

```
nomina/clientes/
├── api/
│   └── clientes.api.js          # Llamadas al backend
├── components/
│   ├── ClienteRow.jsx           # Fila/Card de cliente (responsive)
│   ├── EstadoBadge.jsx          # Badge de estado de cierre
│   ├── ClienteActions.jsx       # Botones de acción
│   ├── ClientesListHeader.jsx   # Header de la lista
│   ├── ClientesTable.jsx        # Tabla/Grid responsive
│   └── EmptyState.jsx           # Estado vacío
├── constants/
│   └── clientes.constants.js    # Constantes y configuración
├── pages/
│   └── ClientesNominaPage.jsx   # Página principal
├── utils/
│   └── clientesHelpers.js       # Funciones auxiliares
├── index.js                     # Exports públicos
└── README.md                    # Esta documentación
```

## 🎯 Características

### Vista Adaptativa
- **Móvil/Tablet (< 1024px)**: Vista de cards con información compacta
- **Desktop (≥ 1024px)**: Vista de tabla completa con todas las columnas

### Filtrado por Tipo de Usuario
- **Analistas**: Solo ven clientes asignados (`/clientes/asignados/`)
- **Supervisores**: Ven clientes del área que supervisan (`/clientes-por-area/`)
- **Gerentes**: Ven todos los clientes de sus áreas asignadas (`/clientes-por-area/`)

### Funcionalidades
- ✅ Lista de clientes con resumen de último cierre
- ✅ Búsqueda en tiempo real por nombre o RUT
- ✅ Estados de cierre con badges de colores
- ✅ Botones de acción: Ver Cliente y Dashboard
- ✅ Animaciones con Framer Motion
- ✅ Modo debug para troubleshooting

## 📦 Uso

### Importación básica
```javascript
import { ClientesNominaPage } from '@/modules/nomina/clientes';
```

### Importación de componentes individuales
```javascript
import { 
  ClienteRow, 
  EstadoBadge, 
  ClienteActions 
} from '@/modules/nomina/clientes';
```

### En el router (App.jsx)
```javascript
import { ClientesNominaPage } from './modules/nomina/clientes';

<Route path="/menu/clientes" element={<ClientesNominaPage />} />
```

## 🔧 API

### `obtenerClientesAsignados()`
Obtiene clientes asignados al usuario actual (Analistas).

### `obtenerClientesPorArea()`
Obtiene clientes del área del usuario (Gerentes y Supervisores).

### `obtenerResumenNomina(clienteId)`
Obtiene resumen del último cierre de nómina de un cliente.

### `obtenerUsuario()`
Obtiene datos del usuario autenticado.

## 🎨 Componentes

### ClientesNominaPage
Página principal que orquesta la carga y visualización de clientes.

**Props:** Ninguna

**Estado:**
- `clientes`: Array de clientes
- `filtro`: String de búsqueda
- `usuario`: Datos del usuario actual
- `areaActiva`: Área activa del usuario
- `cargando`: Boolean de estado de carga
- `error`: String de mensaje de error

### ClienteRow
Renderiza un cliente en formato tabla o card según el breakpoint.

**Props:**
- `cliente` (Object): Datos del cliente
- `areaActiva` (String): Área activa (ej: "Nomina")
- `index` (Number): Índice para animación escalonada

### EstadoBadge
Badge de estado con colores semánticos.

**Props:**
- `estado` (String): Estado del cierre (abierto, validado, finalizado, etc.)

### ClienteActions
Botones de acción para ver cliente y dashboard.

**Props:**
- `onVerCliente` (Function): Callback al hacer clic en "Ver Cliente"
- `onVerDashboard` (Function): Callback al hacer clic en "Dashboard"
- `mobile` (Boolean): Si es vista móvil (layout diferente)

### ClientesTable
Tabla responsive que renderiza ClienteRow para cada cliente.

**Props:**
- `clientes` (Array): Lista de clientes a renderizar
- `areaActiva` (String): Área activa

### EmptyState
Mensaje cuando no hay clientes o no hay resultados de búsqueda.

**Props:**
- `totalClientes` (Number): Total de clientes sin filtro
- `filtro` (String): Filtro actual
- `areaActiva` (String): Área activa
- `tipoUsuario` (String): Tipo de usuario (para mensajes contextuales)

## 🛠️ Utilidades

### `determinarAreaActiva(userData)`
Determina el área activa del usuario.

### `determinarEndpointClientes(tipoUsuario)`
Retorna el endpoint apropiado según el tipo de usuario.

### `filtrarClientes(clientes, filtro)`
Filtra clientes por nombre o RUT.

### `generarInfoDebug(...)`
Genera string con información de debug para troubleshooting.

### `getMensajeSinClientes(tipoUsuario, areaActiva)`
Retorna mensaje apropiado cuando no hay clientes.

## 🎯 Constantes

### Estados de Cierre
```javascript
ESTADOS_CIERRE = {
  ABIERTO: 'abierto',
  VALIDADO: 'validado',
  FINALIZADO: 'finalizado',
  EN_PROCESO: 'en_proceso',
  PENDIENTE: 'pendiente'
}
```

### Configuración de Animaciones
```javascript
ANIMATION_CONFIG = {
  CARD_DELAY_STEP: 0.05,
  CARD_DURATION: 0.3,
  INITIAL_OPACITY: 0,
  INITIAL_Y: 20,
  INITIAL_X: -20
}
```

## 🔄 Flujo de Datos

1. **Carga inicial**: `ClientesNominaPage` obtiene usuario con `obtenerUsuario()`
2. **Determinar área**: Usa `determinarAreaActiva()` para obtener área del usuario
3. **Cargar clientes**: Llama al endpoint apropiado según tipo de usuario
4. **Renderizar**: Pasa clientes a `ClientesTable` que renderiza `ClienteRow` para cada uno
5. **Resúmenes**: Cada `ClienteRow` hace llamada individual a `obtenerResumenNomina()`

## 🎨 Estilos y Temas

- **TailwindCSS** para estilos
- **Framer Motion** para animaciones
- **Color principal**: Teal/Emerald (consistente con tema de nómina)
- **Responsive**: Mobile-first con breakpoints en 1024px

## 🐛 Debug

Clic en el botón "🔍 Debug" en el header para ver:
- Tipo de usuario
- Área activa
- Endpoint utilizado
- Total de clientes cargados
- Filtro actual
- Primeros 5 clientes con áreas

## 📚 Relacionado

- Módulo Auth: `/src/modules/shared/auth`
- Módulo Menu Nómina: `/src/modules/nomina/menu`
- API Config: `/src/api/config.js`
- Componente original: `/src/pages/Clientes.jsx` (legacy)

---

**Versión:** 1.0.0  
**Fecha:** 17 de noviembre de 2025  
**Patrón:** Arquitectura Modular con Principio de Colocación
