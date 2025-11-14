// src/modules/menu/data/menu-options.map.js
import { MENU_OPTION_KEYS, USER_ROLES, AREA_NAMES, MENU_ICON_MAP } from '../constants/menu.constants';

/**
 * Opciones base duplicadas desde MenuUsuario.jsx
 */
export const BASE_MENU_OPTIONS = {
  [MENU_OPTION_KEYS.CLIENTES]: {
    label: 'Clientes',
    descripcion: 'Ver y trabajar con tus clientes asignados',
    icon: MENU_ICON_MAP[MENU_OPTION_KEYS.CLIENTES],
    color: '#4F46E5',
    path: '/menu/clientes',
  },
  [MENU_OPTION_KEYS.HERRAMIENTAS]: {
    label: 'Herramientas',
    descripcion: 'Acceso a recursos y utilidades',
    icon: MENU_ICON_MAP[MENU_OPTION_KEYS.HERRAMIENTAS],
    color: '#10B981',
    path: '/menu/tools',
  },
  [MENU_OPTION_KEYS.MIS_ANALISTAS]: {
    label: 'Mis Analistas',
    descripcion: 'Gestión y supervisión de analistas asignados',
    icon: MENU_ICON_MAP[MENU_OPTION_KEYS.MIS_ANALISTAS],
    color: '#EC4899',
    path: '/menu/mis-analistas',
  },
  [MENU_OPTION_KEYS.VALIDACIONES]: {
    label: 'Validaciones',
    descripcion: 'Revisar y aprobar cierres',
    icon: MENU_ICON_MAP[MENU_OPTION_KEYS.VALIDACIONES],
    color: '#F59E0B',
    path: '/menu/validaciones',
  },
  [MENU_OPTION_KEYS.GESTION_COBRANZA]: {
    label: 'Gestión de Cobranza',
    descripcion: 'Seguimiento y gestión de cobros a clientes',
    icon: MENU_ICON_MAP[MENU_OPTION_KEYS.GESTION_COBRANZA],
    color: '#059669',
    path: '/menu/gestion-cobranza-v2',
  },
  [MENU_OPTION_KEYS.LOGS_ACTIVIDAD]: {
    label: 'Logs y Actividad',
    descripcion: 'Auditoría y logs de actividades de usuarios',
    icon: MENU_ICON_MAP[MENU_OPTION_KEYS.LOGS_ACTIVIDAD],
    color: '#F97316',
    path: '/menu/gerente/logs-actividad',
  },
  [MENU_OPTION_KEYS.LOGS_ACTIVIDAD_NOMINA]: {
    label: 'Logs y Actividad Nómina',
    descripcion: 'Auditoría y logs de actividades de nómina',
    icon: MENU_ICON_MAP[MENU_OPTION_KEYS.LOGS_ACTIVIDAD_NOMINA],
    color: '#F97316',
    path: '/menu/gerente/logs-actividad-nomina',
  },
  [MENU_OPTION_KEYS.ESTADOS_CIERRES_NOMINA]: {
    label: 'Estados de Cierres Nómina',
    descripcion: 'Monitoreo en tiempo real de cierres de nómina',
    icon: MENU_ICON_MAP[MENU_OPTION_KEYS.ESTADOS_CIERRES_NOMINA],
    color: '#06B6D4',
    path: '/menu/gerente/estados-cierres-nomina',
  },
  [MENU_OPTION_KEYS.CACHE_REDIS_NOMINA]: {
    label: 'Cache Redis Nómina',
    descripcion: 'Estado y gestión del cache Redis de nómina',
    icon: MENU_ICON_MAP[MENU_OPTION_KEYS.CACHE_REDIS_NOMINA],
    color: '#10B981',
    path: '/menu/gerente/cache-redis-nomina',
  },
  [MENU_OPTION_KEYS.ESTADOS_CIERRES]: {
    label: 'Estados de Cierres',
    descripcion: 'Monitoreo en tiempo real de estados de cierres',
    icon: MENU_ICON_MAP[MENU_OPTION_KEYS.ESTADOS_CIERRES],
    color: '#06B6D4',
    path: '/menu/gerente/estados-cierres',
  },
  [MENU_OPTION_KEYS.CACHE_REDIS]: {
    label: 'Cache Redis',
    descripcion: 'Estado y gestión del cache Redis de cierres',
    icon: MENU_ICON_MAP[MENU_OPTION_KEYS.CACHE_REDIS],
    color: '#10B981',
    path: '/menu/gerente/cache-redis',
  },
  [MENU_OPTION_KEYS.ADMIN_SISTEMA]: {
    label: 'Admin Sistema',
    descripcion: 'Creación de usuarios, clientes y herramientas avanzadas',
    icon: MENU_ICON_MAP[MENU_OPTION_KEYS.ADMIN_SISTEMA],
    color: '#DC2626',
    path: '/menu/gerente/admin-sistema',
  },
  [MENU_OPTION_KEYS.PROYECTOS_BDO_LATAM]: {
    label: 'Proyectos BDO Latam',
    descripcion: 'Gestión de proyectos BDO en Latinoamérica',
    icon: MENU_ICON_MAP[MENU_OPTION_KEYS.PROYECTOS_BDO_LATAM],
    color: '#3B82F6',
    path: '/menu/proyectos-bdo-latam',
  },
  [MENU_OPTION_KEYS.LOGS_CONTABILIDAD]: {
    label: 'Logs y Actividad',
    descripcion: 'Auditoría y logs de actividades de contabilidad',
    icon: MENU_ICON_MAP[MENU_OPTION_KEYS.LOGS_CONTABILIDAD],
    color: '#F97316',
    path: '/menu/gerente/logs-actividad',
  },
};

/**
 * Opciones por rol del usuario
 */
export const ROLE_OPTION_KEYS = {
  [USER_ROLES.ANALISTA]: [
    MENU_OPTION_KEYS.CLIENTES,
    MENU_OPTION_KEYS.HERRAMIENTAS,
  ],
  [USER_ROLES.SUPERVISOR]: [
    MENU_OPTION_KEYS.MIS_ANALISTAS,
    MENU_OPTION_KEYS.CLIENTES,
    MENU_OPTION_KEYS.VALIDACIONES,
  ],
  [USER_ROLES.GERENTE]: [
    MENU_OPTION_KEYS.CLIENTES,
    MENU_OPTION_KEYS.HERRAMIENTAS,
  ],
};

/**
 * Opciones adicionales para gerentes según área
 */
export const GERENTE_AREA_OPTION_KEYS = {
  [AREA_NAMES.CONTABILIDAD]: [
    MENU_OPTION_KEYS.GESTION_COBRANZA,
    MENU_OPTION_KEYS.LOGS_ACTIVIDAD,
    MENU_OPTION_KEYS.PROYECTOS_BDO_LATAM,
    MENU_OPTION_KEYS.ADMIN_SISTEMA,
  ],
  [AREA_NAMES.NOMINA]: [
    MENU_OPTION_KEYS.LOGS_ACTIVIDAD_NOMINA,
    MENU_OPTION_KEYS.ESTADOS_CIERRES_NOMINA,
    MENU_OPTION_KEYS.CACHE_REDIS_NOMINA,
  ],
};

/**
 * Opciones compartidas por usuarios de contabilidad (no gerentes)
 */
export const CONTABILIDAD_SHARED_KEYS = [MENU_OPTION_KEYS.GESTION_COBRANZA];

/**
 * Etiquetas descriptivas para vacíos de opciones
 */
export const EMPTY_STATE_COPY = {
  title: 'No hay opciones disponibles',
  description: 'Actualiza tus áreas o contacta al administrador para solicitar acceso.',
};
