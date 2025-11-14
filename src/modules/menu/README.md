# Módulo de Menú Principal

Este módulo encapsula la interfaz del menú principal respetando los lineamientos de la refactorización del frontend:

- Código autocontenido dentro de `src/modules/menu/`.
- Componentes duplicados desde la implementación legacy (`MenuUsuario` y `OpcionMenu`).
- Acceso controlado al estado de sesión mediante utilidades locales.
- Rutas listas para integrarse con el router global sin eliminar la versión original.

## Estructura

```
modules/menu/
├── README.md
├── index.js
├── router/
│   └── menu.routes.jsx
├── pages/
│   └── MenuPage.jsx
├── components/
│   ├── MenuAnimations.css
│   ├── MenuGrid.jsx
│   ├── MenuHero.jsx
│   ├── MenuLayout.jsx
│   └── MenuOptionCard.jsx
├── hooks/
│   ├── useMenuOptions.js
│   └── useUserContext.js
├── utils/
│   ├── permissions.js
│   └── user-storage.js
├── constants/
│   └── menu.constants.js
└── data/
    └── menu-options.map.js
```

## Uso rápido

```jsx
import { MenuPage, menuRoutes } from '@/modules/menu';

// Dentro del router
<Route path="/menu" element={<MenuPage />} />
```

## Próximos pasos

- Integrar `menuRoutes` en el router principal cuando se complete la migración.
- Eliminar `MenuUsuario.jsx` sólo después de validar la paridad visual y funcional.
