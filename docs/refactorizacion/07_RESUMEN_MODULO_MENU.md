# 📋 Refactorización del Módulo de Menú

**Fecha:** 14 de noviembre de 2025  
**Módulo:** `/src/modules/menu`  
**Patrón:** Estructura modular basada en `/auth`

---

## 🎯 Objetivo

Aplicar el mismo patrón de refactorización modular usado en el módulo `/auth` al módulo de menú principal del sistema, mejorando la organización, mantenibilidad y documentación del código.

---

## 📊 Estructura Creada

```
src/
└── modules/
    └── menu/
        ├── README.md                          # 📄 Documentación completa
        ├── index.js                           # 📦 Exportaciones públicas
        │
        ├── pages/
        │   └── MenuUsuarioPage.jsx           # 🖥️ Página principal del menú
        │
        ├── components/
        │   └── MenuCard.jsx                   # 🎴 Tarjeta de opción de menú
        │
        ├── utils/
        │   └── menuConfig.js                  # ⚙️ Configuración de opciones
        │
        ├── constants/
        │   └── menu.constants.js              # 📊 Constantes del módulo
        │
        └── router/
            └── menu.routes.jsx                # 🛣️ Configuración de rutas
```

---

## 🔄 Archivos Migrados

### **Antes** (Estructura dispersa)

```
/src/pages/MenuUsuario.jsx         → Página en carpeta genérica
/src/components/OpcionMenu.jsx     → Componente en carpeta compartida
```

### **Después** (Estructura modular)

```
/src/modules/menu/pages/MenuUsuarioPage.jsx      ✅ Página en su módulo
/src/modules/menu/components/MenuCard.jsx        ✅ Componente colocado
/src/modules/menu/utils/menuConfig.js            ✅ Nueva: Lógica extraída
/src/modules/menu/constants/menu.constants.js    ✅ Nueva: Constantes centralizadas
```

---

## ✨ Mejoras Implementadas

### 1. **Separación de Responsabilidades**

**Antes:**
- `MenuUsuario.jsx`: 200+ líneas con lógica, UI y configuración mezcladas

**Después:**
- `MenuUsuarioPage.jsx`: Solo orquestación y renderizado (80 líneas)
- `menuConfig.js`: Lógica de opciones y filtrado (200 líneas)
- `menu.constants.js`: Configuraciones visuales (50 líneas)
- `MenuCard.jsx`: Componente reutilizable (50 líneas)

### 2. **Colocación de Componentes**

- `OpcionMenu.jsx` ahora vive dentro del módulo como `MenuCard.jsx`
- Nombre más descriptivo y estándar
- Uso de constantes del módulo (`CARD_OPACITY`)

### 3. **Extracción de Lógica**

**Nueva función:** `getUserMenuOptions(usuario)`
- Centraliza toda la lógica de construcción del menú
- Testeable de forma aislada
- Reutilizable en otros contextos

**Nueva función:** `hasArea(usuario, areaNombre)`
- Helper para verificar áreas de usuario
- Simplifica condicionales complejos

### 4. **Constantes Centralizadas**

```javascript
export const CARD_OPACITY = 0.9;
export const ANIMATION_DELAY_STEP = 100;
export const USER_TYPES = { ... };
export const BUSINESS_AREAS = { ... };
```

- Fácil ajuste de configuraciones visuales
- Tipado implícito de roles y áreas
- Punto único de verdad

### 5. **Documentación Integrada**

- **README.md completo** dentro del módulo
- **JSDoc** en todas las funciones y componentes
- **Ejemplos de uso** inline
- **Troubleshooting** incluido

---

## 🚀 Cómo Usar el Nuevo Módulo

### **Importación Simple**

```jsx
// Antes
import MenuUsuario from "./pages/MenuUsuario";

// Después
import { MenuUsuarioPage } from "@/modules/menu";
```

### **Uso en App.jsx**

```jsx
import { MenuUsuarioPage } from "@/modules/menu";

<Route path="/menu" element={<MenuUsuarioPage />} />
```

### **Uso de Utilidades**

```jsx
import { getUserMenuOptions, hasArea } from "@/modules/menu";

const usuario = JSON.parse(localStorage.getItem("usuario"));
const opciones = getUserMenuOptions(usuario);
const esContabilidad = hasArea(usuario, "Contabilidad");
```

### **Personalización**

```jsx
// Cambiar opacidad de tarjetas
import { CARD_OPACITY } from "@/modules/menu";
// O modificar directamente en menu.constants.js
```

---

## 🔧 Configuración de Opciones

### **Estructura de una Opción**

```javascript
{
  label: "Clientes",                    // Título
  descripcion: "Ver tus clientes",      // Descripción
  icon: FolderKanban,                   // Icono de Lucide
  color: "#4F46E5",                     // Color hex
  path: "/menu/clientes"                // Ruta de navegación
}
```

### **Agregar Nueva Opción**

1. Abrir `/src/modules/menu/utils/menuConfig.js`
2. Agregar a la constante correspondiente:

```javascript
const OPCIONES_ANALISTA = [
  // ... opciones existentes
  { 
    label: "Nueva Función", 
    descripcion: "Descripción de la función", 
    icon: NuevoIcono, 
    color: "#COLOR", 
    path: "/menu/nueva-ruta" 
  }
];
```

3. Importar el icono si es nuevo:

```javascript
import { NuevoIcono } from "lucide-react";
```

---

## 🧪 Testing

### **Testear Lógica de Menú**

```javascript
import { getUserMenuOptions, hasArea } from "@/modules/menu";

describe("Menu Config", () => {
  it("should return analyst options", () => {
    const usuario = { tipo_usuario: "analista", areas: [] };
    const opciones = getUserMenuOptions(usuario);
    expect(opciones).toHaveLength(2);
  });

  it("should detect contabilidad area", () => {
    const usuario = { areas: [{ nombre: "Contabilidad" }] };
    expect(hasArea(usuario, "Contabilidad")).toBe(true);
  });
});
```

### **Testear Componente MenuCard**

```javascript
import { render, screen, fireEvent } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { MenuCard } from "@/modules/menu";
import { FolderKanban } from "lucide-react";

test("navigates on click", () => {
  const mockNavigate = jest.fn();
  render(
    <BrowserRouter>
      <MenuCard 
        label="Test"
        descripcion="Test desc"
        icon={FolderKanban}
        color="#000"
        path="/test"
      />
    </BrowserRouter>
  );
  
  fireEvent.click(screen.getByRole("button"));
  // ... assertions
});
```

---

## 📝 Cambios en Archivos Externos

### **App.jsx**

**Cambio necesario:**

```jsx
// Antes
import MenuUsuario from "./pages/MenuUsuario";

// Después
import { MenuUsuarioPage } from "./modules/menu";

// En las rutas
<Route path="/menu" element={<MenuUsuarioPage />} />
```

### **Archivos NO Modificados**

Los archivos originales NO se modificaron:
- `/src/pages/MenuUsuario.jsx` (sigue existiendo)
- `/src/components/OpcionMenu.jsx` (sigue existiendo)

**Razón:** Seguir el principio de "no romper nada" durante la refactorización.

---

## 🎨 Personalización de Estilo

### **Cambiar Opacidad de Tarjetas**

```javascript
// /src/modules/menu/constants/menu.constants.js
export const CARD_OPACITY = 0.85; // Cambiar valor
```

### **Ajustar Delays de Animación**

```javascript
// /src/modules/menu/constants/menu.constants.js
export const ANIMATION_DELAY_STEP = 150; // ms
```

### **Modificar Grid Breakpoints**

```javascript
// /src/modules/menu/constants/menu.constants.js
export const GRID_BREAKPOINTS = {
  sm: 'sm:grid-cols-2',
  md: 'md:grid-cols-3',  // Agregar breakpoint
  lg: 'lg:grid-cols-4'   // Cambiar columnas
};
```

---

## 🔍 Comparación Antes/Después

### **Antes: MenuUsuario.jsx**

```jsx
// Todo mezclado en un archivo
const MenuUsuario = () => {
  const usuario = JSON.parse(localStorage.getItem("usuario"));
  const opciones = [];
  
  // 150+ líneas de lógica condicional
  if (usuario.tipo_usuario === "analista") {
    opciones.push({ ... });
  }
  
  // ... más código
  
  return (
    <div>
      {opciones.map(op => <OpcionMenu {...op} />)}
    </div>
  );
};
```

### **Después: MenuUsuarioPage.jsx**

```jsx
import MenuCard from "../components/MenuCard";
import { getUserMenuOptions } from "../utils/menuConfig";

const MenuUsuarioPage = () => {
  const usuario = JSON.parse(localStorage.getItem("usuario"));
  const opciones = getUserMenuOptions(usuario);

  return (
    <div>
      {opciones.map(op => <MenuCard {...op} />)}
    </div>
  );
};
```

**Resultado:**
- ✅ Más limpio y legible
- ✅ Lógica separada
- ✅ Testeable
- ✅ Mantenible

---

## 🐛 Troubleshooting

### **Error: Cannot find module '@/modules/menu'**

**Solución:** Verificar alias de importación en `vite.config.js`:

```javascript
resolve: {
  alias: {
    '@': path.resolve(__dirname, './src')
  }
}
```

### **Opciones no se muestran**

**Debug:**
```javascript
const usuario = JSON.parse(localStorage.getItem("usuario"));
console.log("Usuario:", usuario);
console.log("Tipo:", usuario.tipo_usuario);
console.log("Áreas:", usuario.areas);

import { getUserMenuOptions } from "@/modules/menu";
const opciones = getUserMenuOptions(usuario);
console.log("Opciones:", opciones);
```

### **Estilos no se aplican**

Verificar que las constantes se importan correctamente:

```javascript
import { CARD_OPACITY } from "../constants/menu.constants";
```

---

## 📚 Referencias

- [Módulo Auth (patrón base)](/src/modules/auth/)
- [Principio de Colocación](/docs/refactorizacion/06_PRINCIPIO_COLOCACION.md)
- [Propuesta Estructura Modular](/docs/refactorizacion/02_PROPUESTA_ESTRUCTURA_MODULAR.md)
- [Lucide React Icons](https://lucide.dev/)

---

## ✅ Checklist de Implementación

- [x] Crear estructura de carpetas
- [x] Migrar MenuUsuario.jsx → MenuUsuarioPage.jsx
- [x] Migrar OpcionMenu.jsx → MenuCard.jsx
- [x] Extraer lógica a menuConfig.js
- [x] Crear menu.constants.js
- [x] Crear menu.routes.jsx
- [x] Crear index.js con exportaciones
- [x] Documentar en README.md del módulo
- [x] Documentar refactorización
- [ ] Actualizar App.jsx (manual)
- [ ] Testing unitario
- [ ] Eliminar archivos antiguos (cuando esté validado)

---

## 🎯 Próximos Pasos

1. **Actualizar App.jsx** para usar el nuevo módulo
2. **Probar** en todos los roles de usuario
3. **Escribir tests** para `menuConfig.js`
4. **Validar** con el equipo
5. **Eliminar** archivos antiguos una vez confirmado

---

## 👥 Créditos

- **Patrón de refactorización:** Basado en módulo `/auth`
- **Implementación:** Sistema SGM
- **Fecha:** 14 de noviembre de 2025
