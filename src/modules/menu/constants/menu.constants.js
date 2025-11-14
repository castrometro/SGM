/**
 * Constantes del módulo de menú
 * 
 * Contiene configuraciones visuales y de comportamiento
 * para el menú principal del sistema.
 */

/**
 * Opacidad base de las tarjetas de menú
 * @type {number}
 * @range 0.1 - 1.0
 * @default 0.9
 */
export const CARD_OPACITY = 0.9;

/**
 * Incremento de delay para animaciones escalonadas (en milisegundos)
 * @type {number}
 * @default 100
 */
export const ANIMATION_DELAY_STEP = 100;

/**
 * Breakpoints de grid responsivo
 * @type {Object}
 */
export const GRID_BREAKPOINTS = {
  sm: 'sm:grid-cols-2',
  lg: 'lg:grid-cols-3'
};

/**
 * Duración de animaciones CSS (en segundos)
 */
export const ANIMATION_DURATIONS = {
  fadeIn: 0.8,
  slideUp: 0.6,
  hover: 0.2
};

/**
 * Tipos de usuario del sistema
 */
export const USER_TYPES = {
  ANALISTA: 'analista',
  SUPERVISOR: 'supervisor',
  GERENTE: 'gerente'
};

/**
 * Áreas de negocio
 */
export const BUSINESS_AREAS = {
  CONTABILIDAD: 'Contabilidad',
  NOMINA: 'Nomina'
};
