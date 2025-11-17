// src/modules/nomina/clientes/constants/clientes.constants.js

/**
 * 🎯 Constantes del módulo de Clientes de Nómina
 */

/**
 * Estados de los cierres de nómina
 */
export const ESTADOS_CIERRE = {
  ABIERTO: 'abierto',
  VALIDADO: 'validado',
  FINALIZADO: 'finalizado',
  EN_PROCESO: 'en_proceso',
  PENDIENTE: 'pendiente'
};

/**
 * Mapeo de colores para estados (TailwindCSS)
 */
export const ESTADO_COLORS = {
  [ESTADOS_CIERRE.ABIERTO]: 'bg-yellow-500',
  [ESTADOS_CIERRE.VALIDADO]: 'bg-blue-500',
  [ESTADOS_CIERRE.FINALIZADO]: 'bg-green-500',
  [ESTADOS_CIERRE.EN_PROCESO]: 'bg-orange-500',
  [ESTADOS_CIERRE.PENDIENTE]: 'bg-gray-500'
};

/**
 * Labels para estados
 */
export const ESTADO_LABELS = {
  [ESTADOS_CIERRE.ABIERTO]: 'Abierto',
  [ESTADOS_CIERRE.VALIDADO]: 'Validado',
  [ESTADOS_CIERRE.FINALIZADO]: 'Finalizado',
  [ESTADOS_CIERRE.EN_PROCESO]: 'En Proceso',
  [ESTADOS_CIERRE.PENDIENTE]: 'Pendiente'
};

/**
 * Tipos de usuario
 */
export const TIPO_USUARIO = {
  GERENTE: 'gerente',
  ANALISTA: 'analista',
  SUPERVISOR: 'supervisor'
};

/**
 * Configuración de animaciones
 */
export const ANIMATION_CONFIG = {
  CARD_DELAY_STEP: 0.05,
  CARD_DURATION: 0.3,
  INITIAL_OPACITY: 0,
  INITIAL_Y: 20,
  INITIAL_X: -20
};

/**
 * Mensajes del sistema
 */
export const MENSAJES = {
  CARGANDO: 'Cargando clientes...',
  SIN_AREA: 'No tienes un área activa asignada. Contacta a tu administrador.',
  SIN_CLIENTES_AREA: 'No hay clientes en tu área',
  SIN_CLIENTES_ASIGNADOS: 'No tienes clientes asignados. Contacta a tu supervisor.',
  SIN_RESULTADOS_FILTRO: 'No se encontraron clientes que coincidan con',
  ERROR_CARGA: 'No se pudo cargar el usuario o los clientes. Intenta más tarde.'
};

/**
 * Configuración de URLs externas
 */
export const URLS = {
  DASHBOARD_NOMINA: (clienteId) => `/menu/nomina/clientes/${clienteId}/dashboard`
};
