/**
 * 🎯 Módulo de Detalle de Cliente de Nómina
 * Exports públicos del módulo
 */

// Router
export { default as ClienteDetalleNominaRouter } from './router/ClienteDetalleNominaRouter';

// Página principal
export { default as ClienteDetalleNominaPage } from './pages/ClienteDetalleNominaPage';

// Componentes
export { default as ClienteInfoCard } from './components/ClienteInfoCard';
export { default as KpiResumenNomina } from './components/KpiResumenNomina';
export { default as ClienteActionButtons } from './components/ClienteActionButtons';

// API
export * from './api/clienteDetalle.api';

// Utilidades
export * from './utils/clienteDetalleHelpers';

// Export default de la página principal
export { default } from './pages/ClienteDetalleNominaPage';
