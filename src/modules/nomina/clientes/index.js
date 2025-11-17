/**
 * 🎯 Módulo de Clientes de Nómina
 * Exports públicos del módulo
 */

// Página principal
export { default as ClientesNominaPage } from './pages/ClientesNominaPage';

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
export { default } from './pages/ClientesNominaPage';
