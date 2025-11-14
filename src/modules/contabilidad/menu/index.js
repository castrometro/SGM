/**
 * Módulo de Menú Principal
 * 
 * Proporciona la interfaz de navegación principal del sistema SGM.
 * Gestiona la visualización dinámica de opciones según roles y áreas.
 * 
 * @module menu
 * @version 1.0.0
 * @author Sistema SGM
 */

// Páginas
export { default as MenuUsuarioPage } from "./pages/MenuUsuarioPage";

// Componentes
export { default as MenuCard } from "./components/MenuCard";

// Utilidades
export { 
  getUserMenuOptions, 
  hasArea, 
  MENU_CONFIG 
} from "./utils/menuConfig";

// Constantes
export {
  CARD_OPACITY,
  ANIMATION_DELAY_STEP,
  GRID_BREAKPOINTS,
  ANIMATION_DURATIONS,
  USER_TYPES,
  BUSINESS_AREAS
} from "./constants/menu.constants";

// Router
export { default as menuRoutes } from "./router/menu.routes";

/**
 * Exportación por defecto: Página principal del menú
 */
export { default } from "./pages/MenuUsuarioPage";
