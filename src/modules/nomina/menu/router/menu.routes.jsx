import MenuUsuarioPage from "../pages/MenuUsuarioPage";

/**
 * Configuración de rutas del módulo de menú
 * 
 * Define las rutas relacionadas con el menú principal.
 * Actualmente solo exporta la página principal, pero puede
 * expandirse para incluir sub-rutas del menú en el futuro.
 * 
 * @module menu/router
 */

/**
 * Rutas del módulo de menú
 * 
 * @example
 * // En App.jsx
 * import { menuRoutes } from '@/modules/menu';
 * 
 * <Route path="/menu" element={menuRoutes.main} />
 */
export const menuRoutes = {
  main: MenuUsuarioPage,
  // Futuras expansiones:
  // settings: MenuSettingsPage,
  // favorites: MenuFavoritesPage,
};

export default menuRoutes;
