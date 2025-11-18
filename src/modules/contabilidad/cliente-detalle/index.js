/**
 * 🎯 Módulo de Detalle de Cliente de Contabilidad
 * Exports públicos del módulo
 */

// Router
export { default as ClienteDetalleContabilidadRouter } from './router/ClienteDetalleContabilidadRouter';

// Página principal
export { default as ClienteDetalleContabilidadPage } from './pages/ClienteDetalleContabilidadPage';

// Componentes
export { default as ClienteInfoCard } from './components/ClienteInfoCard';
export { default as KpiResumenContabilidad } from './components/KpiResumenContabilidad';
export { default as ClienteActionButtons } from './components/ClienteActionButtons';

// API
export * from './api/clienteDetalle.api';

// Utilidades
export * from './utils/clienteDetalleHelpers';

// Export default de la página principal
export { default } from './pages/ClienteDetalleContabilidadPage';
