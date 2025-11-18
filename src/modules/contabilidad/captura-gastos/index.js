// src/modules/contabilidad/captura-gastos/index.js

/**
 * 💰 Módulo de Captura Masiva de Gastos
 * 
 * Herramienta para procesar gastos desde archivos Excel de forma masiva.
 * Exclusivo para área de Contabilidad.
 */

// Router
export { default as CapturaGastosRouter } from './router/CapturaGastosRouter';

// Páginas
export { default as CapturaGastosPage } from './pages/CapturaGastosPage';

// API
export * from './api/capturaGastos.api';

// Hooks
export { useCapturaGastos } from './hooks/useCapturaGastos';

// Utils
export * from './utils/capturaGastosHelpers';

// Constants
export * from './constants/capturaGastos.constants';

// Export por defecto
export { default } from './pages/CapturaGastosPage';
