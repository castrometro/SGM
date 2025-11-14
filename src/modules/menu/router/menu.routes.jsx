// src/modules/menu/router/menu.routes.jsx
import MenuPage from '../pages/MenuPage';

/**
 * Configuración de rutas del módulo de menú
 */
export const menuRoutes = [
  {
    path: '/menu',
    element: <MenuPage />,
    meta: {
      title: 'Menú Principal - SGM',
      requiresAuth: true,
    },
  },
];

export default menuRoutes;
