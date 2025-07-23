# 🏠 MenuUsuario.jsx - Documentación Detallada

## 🎯 Propósito
Dashboard principal y centro de navegación del sistema. Muestra opciones dinámicas según el tipo de usuario y sus permisos específicos.

## 👤 Usuarios Objetivo
- **Analistas**: Acceso a clientes asignados y herramientas básicas
- **Supervisores**: Gestión de analistas + validaciones
- **Gerentes**: Acceso completo con funciones administrativas avanzadas

## 📋 Funcionalidades

### ✅ Funcionalidades Principales
1. **Menú dinámico por rol**: Diferentes opciones según `usuario.tipo_usuario`
2. **Menú dinámico por área**: Gerentes ven opciones según sus `areas` asignadas
3. **Navegación con animaciones**: Efectos visuales en las tarjetas
4. **Interactividad**: Hover effects en las opciones
5. **Grid responsivo**: Adaptación a diferentes tamaños de pantalla

### 🔄 Lógica de Permisos por Rol

#### 👨‍💼 Analista
```jsx
opciones = [
  "Clientes",          // Ver clientes asignados
  "Herramientas"       // Utilities básicas
]
```

#### 👥 Supervisor  
```jsx
opciones = [
  "Mis Analistas",     // Gestión de analistas
  "Clientes",          // Ver y validar clientes
  "Validaciones"       // Revisar y aprobar cierres
]
```

#### 🏢 Gerente (Dinámico por Área)
```jsx
// Base siempre
opciones = ["Clientes", "Dashboard Gerencial"]

// Si tiene Contabilidad Y/O Nómina
if (tieneContabilidad || tieneNomina) {
  opciones.push("Analytics de Performance")
}

// Solo si tiene Contabilidad
if (tieneContabilidad) {
  opciones.push([
    "Logs y Actividad",
    "Estados de Cierres", 
    "Cache Redis",
    "Admin Sistema"
  ])
}

// Siempre para gerentes
opciones.push(["Gestión de Analistas", "Herramientas"])
```

---

## 🔗 Dependencias Frontend

### 📦 Componentes Utilizados
```jsx
import OpcionMenu from "../components/OpcionMenu";         // ✅ Tarjeta individual de opción
```

### 🎨 Iconografía
```jsx
import {
  FolderKanban,    // Clientes
  Wrench,          // Herramientas  
  ShieldCheck,     // Validaciones
  UserCog,         // Gestión analistas
  FileText,        // Logs
  BarChart3,       // Analytics
  Activity,        // Dashboard gerencial
  Users,           // Mis analistas
  Settings,        // Admin sistema
  Database,        // Cache Redis
  Monitor          // Estados cierres
} from "lucide-react";
```

---

## 🌐 Dependencias Backend

### 📊 Datos del Usuario
```javascript
const usuario = JSON.parse(localStorage.getItem("usuario"));
// Estructura esperada:
{
  id: number,
  nombre: string,
  correo: string, 
  tipo_usuario: "analista" | "supervisor" | "gerente",
  areas?: [
    { id: number, nombre: "Contabilidad" | "Nomina" }
  ]
}
```

### 🔌 APIs Indirectas
- **No consume APIs directamente**
- **Depende de**: Datos del usuario obtenidos en Login.jsx
- **Asume**: Usuario válido en localStorage

---

## 💾 Gestión de Estado

### 🗃️ LocalStorage (Solo lectura)
```javascript
const usuario = JSON.parse(localStorage.getItem("usuario"));
```

### 🎨 Estado Visual
```javascript
const cardOpacity = 0.9;  // Transparencia base de tarjetas
// Estados de hover manejados por CSS inline
```

### 🔄 Estado Dinámico
```javascript
const opciones = [];  // Array construido dinámicamente
const areas = usuario.areas || [];
const tieneContabilidad = areas.some(area => area.nombre === "Contabilidad");
const tieneNomina = areas.some(area => area.nombre === "Nomina");
```

---

## 🎨 Estilos y UI

### 🌈 Estructura Visual
```jsx
<div className="text-white">
  <h1>Menú Principal</h1>                    // Título principal
  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
    {opciones.map => <OpcionMenu />}         // Grid de opciones
  </div>
</div>
```

### 🎭 Animaciones CSS-in-JS
```css
@keyframes fade-in {
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes slide-up {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}
```

### 🖱️ Efectos Interactivos
```jsx
onMouseEnter={(e) => e.currentTarget.style.opacity = '1'}
onMouseLeave={(e) => e.currentTarget.style.opacity = cardOpacity}
// + animationDelay dinámico por index
```

---

## 🔄 Navegación y Rutas

### 📍 Rutas Generadas Dinámicamente
```jsx
// Ejemplos de paths por rol:

// Analista
"/menu/clientes"
"/menu/tools"

// Supervisor  
"/menu/mis-analistas"
"/menu/clientes"
"/menu/validaciones"

// Gerente
"/menu/clientes"
"/menu/dashboard-gerente"
"/menu/analytics"
"/menu/gerente/logs-actividad"
"/menu/gerente/estados-cierres"
"/menu/gerente/cache-redis"
"/menu/analistas"
"/menu/tools"
"/menu/gerente/admin-sistema"
```

### 🗺️ Flujo en App.jsx
```jsx
<Route index element={<MenuUsuario />} />  // Ruta default dentro de /menu
```

---

## 🧩 Componente Hijo: OpcionMenu

### 📋 Props Enviadas
```jsx
<OpcionMenu
  label={string}         // "Clientes", "Dashboard", etc.
  descripcion={string}   // Texto descriptivo
  icon={LucideIcon}      // Componente de icono
  color={string}         // Color hex (#4F46E5)
  path={string}          // Ruta de navegación
/>
```

---

## ⚠️ Problemas Identificados

### 🚨 Lógica Compleja en Componente
```jsx
// ❌ Problema: Lógica de roles muy compleja en renderizado
if (usuario.tipo_usuario === "gerente") {
  const areas = usuario.areas || [];
  const tieneContabilidad = areas.some(area => area.nombre === "Contabilidad");
  // ... 50+ líneas de lógica condicional
}
```
**Recomendación**: Extraer a custom hook `useMenuOpciones(usuario)`

### 🎨 CSS-in-JS Mezclado
```jsx
// ❌ Problema: Estilos inline + CSS-in-JS + clases Tailwind
<style>{` @keyframes fade-in { ... } `}</style>
onMouseEnter={(e) => e.currentTarget.style.opacity = '1'}
className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6"
```
**Recomendación**: Unificar en sistema de estilos consistente

### 🔒 Seguridad de Roles
```jsx
// ❌ Problema: Validación solo en frontend
if (usuario.tipo_usuario === "gerente") { ... }
```
**Recomendación**: Validar permisos también en backend

### 📱 Responsividad Limitada
```jsx
// ⚠️ Mejora: Solo 3 breakpoints
grid-cols-1 sm:grid-cols-2 lg:grid-cols-3
```
**Recomendación**: Más breakpoints para tablets

---

## 📊 Análisis de Complejidad

### 📈 Métricas
- **Líneas de código**: 164
- **Lógica condicional**: Alta (múltiples if/else por roles)
- **Responsabilidades**: 3 (UI + Lógica roles + Navegación)
- **Dependencias**: 12 iconos + 1 componente
- **Complejidad**: ⭐⭐⭐⭐ (Media-Alta)

### 🎯 Refactoring Sugerido
```jsx
// ✅ Separar en múltiples responsabilidades
const useMenuOpciones = (usuario) => { /* lógica roles */ }
const MenuGrid = ({ opciones }) => { /* UI grid */ }
const MenuOption = ({ opcion, index }) => { /* tarjeta individual */ }
```

---

## 🔍 Siguientes Análisis Requeridos

### 🧩 Componentes a Documentar
1. **OpcionMenu.jsx** - Componente hijo crítico
2. **Páginas destino**: Clientes.jsx, DashboardGerente.jsx, etc.

### 🔗 Flujos a Mapear  
1. **Flujo Analista**: MenuUsuario → Clientes → Detalle
2. **Flujo Gerente**: MenuUsuario → Dashboard → Analytics

---

*Documentado: 21 de julio de 2025*
*Estado: ✅ Completo*
*Complejidad: ⭐⭐⭐⭐ (Refactoring recomendado)*
