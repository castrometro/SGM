/**
 * 🎯 Módulo de Historial de Cierres de Nómina
 * Exports públicos del módulo
 */

// Router
export { default as HistorialCierresNominaRouter } from './router/HistorialCierresNominaRouter';

// Página principal
export { default as HistorialCierresNominaPage } from './pages/HistorialCierresNominaPage';

// Componentes
export { default as EstadisticasCierres } from './components/EstadisticasCierres';
export { default as FiltrosCierres } from './components/FiltrosCierres';
export { default as TablaCierres } from './components/TablaCierres';

// API
export * from './api/historialCierres.api';

// Utilidades
export * from './utils/historialCierresHelpers';

// Export default de la página principal
export { default } from './pages/HistorialCierresNominaPage';
