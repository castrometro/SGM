// src/modules/auth/index.js

/**
 * Punto de entrada del módulo de autenticación
 * Exporta todos los componentes, hooks, utilidades y configuraciones públicas
 */

// Páginas
export { default as LoginPage } from './pages/LoginPage';

// Componentes
export { default as LoginForm } from './components/LoginForm';
export { default as LoginHeader } from './components/LoginHeader';
export { default as PrivateRoute } from './components/PrivateRoute';
export { default as DevModulesButton } from './components/DevModulesButton';
export { default as DocsViewer } from './components/DocsViewer';

// API
export * as authApi from './api/auth.api';

// Utilidades
export * as authStorage from './utils/storage';
export * as authValidators from './utils/validators';

// Constantes
export * from './constants/auth.constants';

// Rutas
export { default as authRoutes } from './router/auth.routes';
