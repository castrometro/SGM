// src/modules/nomina/cierre-detalle/index.js

// Router
export { default as CierreDetalleNominaRouter } from './router/CierreDetalleNominaRouter';

// Pages
export { default as CierreDetalleNominaPage } from './pages/CierreDetalleNominaPage';

// API
export * from './api/cierreDetalle.api';

// Utils
export * from './utils/cierreDetalleHelpers';

// Components (exportar componentes principales si se necesitan fuera del módulo)
export { default as CierreProgresoNomina } from './components/CierreProgresoNomina';
export { default as CierreInfoBar } from './components/CierreInfoBar';
