// src/modules/menu/index.js

/**
 * Punto de entrada del módulo de menú principal
 * Exporta páginas, componentes, hooks y utilidades públicas
 */

// Páginas
export { default as MenuPage } from './pages/MenuPage';

// Componentes
export { default as MenuLayout } from './components/MenuLayout';
export { default as MenuHero } from './components/MenuHero';
export { default as MenuGrid } from './components/MenuGrid';
export { default as MenuOptionCard } from './components/MenuOptionCard';

// Hooks
export { default as useMenuOptions } from './hooks/useMenuOptions';
export { default as useUserContext } from './hooks/useUserContext';

// Utilidades
export * as menuPermissions from './utils/permissions';
export * as menuUserStorage from './utils/user-storage';

// Constantes y datos
export * from './constants/menu.constants';
export * from './data/menu-options.map';

// Rutas
export { default as menuRoutes } from './router/menu.routes';
