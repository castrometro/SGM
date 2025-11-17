/**
 * Módulo de Herramientas de Nómina
 * 
 * Exporta componentes y utilidades del módulo de herramientas.
 * Sigue el principio de colocación manteniendo todo relacionado junto.
 */

// Router
export { default as HerramientasNominaRouter } from './router/HerramientasNominaRouter';

// Página principal
export { default as HerramientasNominaPage } from './pages/HerramientasNominaPage';

// Componentes
export { default as ToolCard } from './components/ToolCard';
export { default as CategoryTabs } from './components/CategoryTabs';
export { default as InfoBanner } from './components/InfoBanner';

// Utilidades
export { 
  getToolCategories, 
  getToolsStats,
  GENERAL_TOOLS,
  NOMINA_TOOLS,
  REPORTES_TOOLS,
  INTEGRACIONES_TOOLS
} from './utils/toolsConfig';

// Constantes
export {
  TOOL_CATEGORIES,
  TOOL_STATUS,
  TOOL_COLORS,
  ANIMATION_CONFIG
} from './constants/herramientas.constants';
