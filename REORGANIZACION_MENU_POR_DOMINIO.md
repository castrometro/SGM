# 🔄 Reorganización: Menu por Dominio

**Fecha:** 14 de noviembre de 2025  
**Decisión:** Menu NO es shared - cada dominio tiene su propio menu

## 📋 Estructura Final

```
src/modules/
├── shared/
│   ├── auth/          ✅ Autenticación (transversal)
│   └── common/        ✅ Header, Footer, Layout (transversal)
│       ├── Header.jsx
│       ├── Footer.jsx
│       └── index.js
├── contabilidad/
│   └── menu/          ✅ Menu específico de Contabilidad
│       ├── components/
│       ├── constants/
│       ├── pages/
│       ├── router/
│       ├── utils/
│       └── index.js
└── nomina/
    └── menu/          ✅ Menu específico de Nómina
        ├── components/
        ├── constants/
        ├── pages/
        ├── router/
        ├── utils/
        └── index.js
```

## 🎯 Rationale

### ¿Por qué Menu NO es Shared?

1. **Opciones específicas por dominio:**
   - Contabilidad: Cierre Contable, Libro Mayor, etc.
   - Nómina: Cierre Nómina, Incidencias, Empleados, etc.

2. **Evolución independiente:**
   - Cada dominio puede agregar/quitar opciones sin afectar al otro
   - Diferentes permisos y roles por dominio

3. **Mantenibilidad:**
   - Código más claro: `contabilidad/menu` vs `nomina/menu`
   - Menos condicionales if/else en un solo archivo

## 🔄 Cambios Realizados

### 1. Estructura de Carpetas
```bash
# Copiar menu a ambos dominios
cp -r shared/menu contabilidad/
cp -r shared/menu nomina/

# Eliminar de shared
rm -rf shared/menu

# Mover Header/Footer a shared/common
cp components/Header.jsx modules/shared/common/
cp components/Footer.jsx modules/shared/common/
```

### 2. Archivos Actualizados

#### MenuModuleDemo.jsx
```javascript
// ANTES:
import { MenuUsuarioPage } from '../modules/shared/menu';
import Header from '../components/Header';
import Footer from '../components/Footer';

// DESPUÉS:
import { MenuUsuarioPage } from '../modules/contabilidad/menu';
import { Header, Footer } from '../modules/shared/common';
```

### 3. Nuevo Módulo: shared/common

**Archivo:** `/src/modules/shared/common/index.js`
```javascript
export { default as Header } from './Header';
export { default as Footer } from './Footer';
```

**Componentes:**
- `Header.jsx` - Header del sistema
- `Footer.jsx` - Footer del sistema
- Futuros: `Layout.jsx`, `Breadcrumb.jsx`, etc.

## 📝 Próximos Pasos

### 1. Personalizar Menus por Dominio

**Contabilidad (`contabilidad/menu/utils/menuConfig.js`):**
```javascript
const contabilidadOptions = [
  {
    title: "Cierre Contable",
    description: "Gestión de cierres contables",
    icon: FolderKanban,
    path: "/contabilidad/cierre"
  },
  {
    title: "Libro Mayor",
    description: "Análisis de libro mayor",
    icon: BookOpen,
    path: "/contabilidad/libro-mayor"
  }
  // ... más opciones de contabilidad
];
```

**Nómina (`nomina/menu/utils/menuConfig.js`):**
```javascript
const nominaOptions = [
  {
    title: "Cierre Nómina",
    description: "Gestión de cierres de nómina",
    icon: Calculator,
    path: "/nomina/cierre"
  },
  {
    title: "Empleados",
    description: "Gestión de empleados",
    icon: Users,
    path: "/nomina/empleados"
  }
  // ... más opciones de nómina
];
```

### 2. Actualizar Router Principal (App.jsx)

```javascript
// Importar menus por dominio
import { MenuUsuarioPage as ContabilidadMenu } from './modules/contabilidad/menu';
import { MenuUsuarioPage as NominaMenu } from './modules/nomina/menu';

// Rutas
<Route path="/contabilidad/menu" element={<ContabilidadMenu />} />
<Route path="/nomina/menu" element={<NominaMenu />} />
```

### 3. Refactorizar Módulos Existentes

**Usar el prompt template:**
```
Refactoriza el módulo [NOMBRE_MODULO] siguiendo el patrón establecido.

**Dominio:** [contabilidad | nomina]
**Ubicación:** /src/modules/[dominio]/[nombre-modulo]

**Patrón:**
- components/ - Componentes específicos
- constants/ - Constantes y configuración
- pages/ - Páginas principales
- router/ - Rutas del módulo
- utils/ - Utilidades y lógica
- index.js - Exports públicos
```

## ✅ Beneficios de esta Arquitectura

1. **Separación clara de dominios**
2. **Código más mantenible y escalable**
3. **Componentes compartidos centralizados en `shared/`**
4. **Evolución independiente de cada dominio**
5. **Onboarding más fácil** (desarrollador de nómina no necesita entender contabilidad)

## 🎨 Patrón de Importación

### ✅ Correcto:
```javascript
// Módulos de dominio
import { MenuUsuarioPage } from '../modules/contabilidad/menu';
import { CierreForm } from '../modules/contabilidad/cierre';

// Módulos compartidos
import { LoginPage } from '../modules/shared/auth';
import { Header, Footer } from '../modules/shared/common';
```

### ❌ Incorrecto:
```javascript
// NO mezclar dominios
import { MenuUsuarioPage } from '../modules/shared/menu'; // ❌ No existe

// NO importar directamente de components/
import Header from '../components/Header'; // ❌ Usar shared/common
```

## 📚 Documentación Relacionada

- `ESTRATEGIA_SEPARACION_DOMINIOS.md` - Estrategia general
- `RESUMEN_SEPARACION_DOMINIOS.txt` - Resumen ejecutivo
- `docs/refactorizacion/07_RESUMEN_MODULO_MENU.md` - Documentación módulo menu
- `docs/refactorizacion/PROMPT_REFACTORIZACION_MODULOS.md` - Template para refactorizar

---

**Estado:** ✅ Implementado  
**Próxima acción:** Personalizar opciones de menu para cada dominio
