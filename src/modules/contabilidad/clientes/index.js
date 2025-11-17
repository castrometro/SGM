/**
 * 🎯 Módulo de Clientes de Contabilidad
 * Exports públicos del módulo
 */

// Router
export { default as ClientesContabilidadRouter } from './router/ClientesContabilidadRouter';

// Página principal
export { default as ClientesContabilidadPage } from './pages/ClientesContabilidadPage';

// Componentes
export { default as ClienteRow } from './components/ClienteRow';
export { default as EstadoBadge } from './components/EstadoBadge';
export { default as ClienteActions } from './components/ClienteActions';
export { default as ClientesListHeader } from './components/ClientesListHeader';
export { default as ClientesTable } from './components/ClientesTable';
export { default as EmptyState } from './components/EmptyState';

// API
export * from './api/clientes.api';

// Utilidades
export * from './utils/clientesHelpers';

// Constantes
export * from './constants/clientes.constants';

// Export default de la página principal
export { default } from './pages/ClientesContabilidadPage';
