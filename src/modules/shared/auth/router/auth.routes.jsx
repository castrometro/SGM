// src/modules/auth/router/auth.routes.jsx
import LoginPage from '../pages/LoginPage';

/**
 * Configuración de rutas del módulo de autenticación
 * Para usar con React Router
 */
export const authRoutes = [
  {
    path: '/',
    element: <LoginPage />,
    meta: {
      title: 'Iniciar Sesión - SGM',
      requiresAuth: false,
      public: true,
    },
  },
];

export default authRoutes;
