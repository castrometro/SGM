# 📋 Propuesta de Refactorización - Módulo Menu

**Ubicación actual:** `src/pages/MenuUsuario.jsx`
**Alcance:** Creación del módulo `menu/` siguiendo la arquitectura modular definida en la refactorización de Login (`/src/modules/auth/`).
**Fecha:** 11 de noviembre de 2025
**Autor:** Equipo Refactorización Frontend

---

## 1. Estado Actual del Menú

### 1.1 Componente Principal
- El archivo `MenuUsuario.jsx` concentra toda la lógica de visualización del menú principal.
- Se basa en la lectura directa de `localStorage` para obtener al usuario autenticado.
- Construye dinámicamente un arreglo `opciones` con base en `tipo_usuario` y `areas`.
- Contiene estilos inline, animaciones declaradas vía `<style>` embebido y lógica de `onMouseEnter`/`onMouseLeave`.

### 1.2 Dependencias
- Usa `OpcionMenu` desde `src/components/OpcionMenu.jsx`.
- Importa íconos directamente de `lucide-react`.
- No utiliza hooks reutilizables para sesión ni helpers de permisos (duplicación potencial con otros módulos).

### 1.3 Problemas Detectados
1. **Acoplamiento directo con `localStorage`:** se repite la lógica que ya se resolvió en el módulo Auth (`storage.js`).
2. **Opciones mezcladas:** la construcción de `opciones` para analistas, supervisores y gerentes está en un único bloque largo.
3. **Estilos inline y animaciones locales:** difícil de testear y reutilizar; rompe el principio de colocación.
4. **Falta de documentación específica:** no existe README ni guía sobre cómo extender el menú.
5. **Sin pruebas de regresión:** cualquier cambio en el objeto `usuario` puede romper opciones visibles.

---

## 2. Objetivo de la Refactorización

Crear un **módulo autocontenido** `src/modules/menu/` que:
- Centralice componentes, hooks y constantes relacionados con el menú principal.
- Duplique (no reimporte) lo necesario desde `src/components` para mantener compatibilidad.
- Exponga un punto de entrada `index.js` con exports públicos (similar a `modules/auth`).
- Incluya documentación (`README.md`) y rutas (`router/menu.routes.jsx`).
- Prepare el terreno para migrar gradualmente desde `MenuUsuario.jsx` sin eliminar el código existente.

---

## 3. Propuesta de Arquitectura del Módulo

```
menu/
├── README.md
├── index.js
├── router/
│   └── menu.routes.jsx
├── pages/
│   └── MenuPage.jsx
├── components/
│   ├── MenuLayout.jsx
│   ├── MenuHero.jsx
│   ├── MenuGrid.jsx
│   └── MenuOptionCard.jsx
├── hooks/
│   ├── useMenuOptions.js
│   └── useUserContext.js
├── utils/
│   └── permissions.js
├── constants/
│   └── menu.constants.js
└── data/
    └── menu-options.map.js
```

### 3.1 Detalle por carpeta
- **pages/MenuPage.jsx**: página principal; orquesta layout, hooks, loading states.
- **components/**: componentes presentacionales copiados (no importados) a partir de `OpcionMenu` y estructura actual.
- **hooks/**:
  - `useUserContext`: wrapper sobre `authStorage` (copiado) para leer usuario/token; evita acceder directo a `localStorage`.
  - `useMenuOptions`: encapsula la lógica de construcción de opciones según rol y áreas.
- **utils/permissions.js**: helpers para validar roles (`isGerente`, `hasContabilidad`, etc.).
- **constants/menu.constants.js**: define nombres de roles, colores e íconos (importando `lucide-react`).
- **data/menu-options.map.js**: mapa base de opciones por rol/area para facilitar mantenimiento.
- **router/menu.routes.jsx**: exporta rutas del módulo (`/menu`, `/menu/*`), lista para integrarse con router principal.

---

## 4. Estrategia de Migración (Sin Romper Nada)

1. **Crear el módulo `menu/`** copiando el código actual.
2. **Duplicar `OpcionMenu`:** generar `MenuOptionCard.jsx` con la misma UI, adaptada a props tipadas.
3. **Implementar `MenuPage`:** reutilizar lógica actual pero separando responsabilidades en hooks y helpers.
4. **Incluir documentación completa (`README.md`):** explicar estructura, flujos y cómo extender opciones.
5. **Exponer exports en `index.js`:** `MenuPage`, `MenuRoutes`, `useMenuOptions`, `menuConstants`, etc.
6. **Agregar showcase temporal:** ruta de desarrollo para validar layout (similar a `AuthModuleDemo`).
7. **Mantener `MenuUsuario.jsx` original:** hasta que el router principal consuma el nuevo módulo.
8. **Actualizar router principal (fase posterior):** apuntar `/menu` a `<MenuPage />` desde `modules/menu` cuando se valide.

---

## 5. Copias Necesarias (Respetando Regla "No Importar")

- Copiar `OpcionMenu.jsx` a `modules/menu/components/MenuOptionCard.jsx` y ajustar nombres internos.
- Replicar helpers de `localStorage` desde `modules/auth/utils/storage.js` creando versión específica del módulo o wrapper que use los helpers expuestos por Auth.
- Reutilizar animaciones creando archivos CSS/JS dedicados (evitar `<style>` inline). Posible `MenuAnimations.css` dentro de `components/` o `styles/`.
- Duplicar cualquier texto/constante relevante en `menu.constants.js`.

---

## 6. Consideraciones de UX/UI

- Mantener gradientes y animaciones existentes, pero migrarlos a clases CSS o Tailwind utilities.
- Añadir estados vacíos por rol (ej. supervisor sin áreas asignadas).
- Preparar soporte para internacionalización futura (constantes de texto centralizadas).
- Garantizar accesibilidad básica (roles ARIA en cards, foco manejable).

---

## 7. Plan de Pruebas

1. **Smoke Test Manual:** validar visualización de opciones para analista, supervisor y gerente (con y sin áreas).
2. **Validar Animaciones:** asegurar que `hover` y efectos se mantengan tras mover estilos.
3. **LocalStorage Mock:** verificar que `useUserContext` maneje ausencia de usuario (redirigir o mostrar mensaje).
4. **Router Integration:** pruebas con `PrivateRoute` de Auth para confirmar acceso solo con sesión válida.

---

## 8. Próximos Pasos

- [ ] Crear carpeta `src/modules/menu/` con estructura propuesta.
- [ ] Documentar estado actual del menú (agregar a `/docs/refactorizacion/01_MENU_ESTADO_ACTUAL.md`).
- [ ] Implementar `MenuPage.jsx` usando hooks y componentes descritos.
- [ ] Actualizar documentación general (`docs/refactorizacion/README.md`) marcando el avance del módulo Menu.
- [ ] Planificar migración de rutas globales tras validación.

---

## 9. Beneficios Esperados

- Código organizado por responsabilidades y fácil de extender.
- Reutilización de patrones establecidos en Login (coherencia del frontend).
- Menor riesgo al modificar opciones del menú (tests + hooks específicos).
- Base preparada para futuras dashboards y analíticas sin mezclar roles.

---

> ✅ **Resultado:** Plan de refactorización alineado con los lineamientos establecidos: duplicar componentes necesarios, documentar la arquitectura y mantener compatibilidad total mientras se introduce el nuevo módulo `menu/`.
