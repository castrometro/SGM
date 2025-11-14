// src/modules/menu/constants/menu.constants.js
import {
  Activity,
  BarChart3,
  CreditCard,
  Database,
  FileText,
  FolderKanban,
  Monitor,
  Settings,
  ShieldCheck,
  UserCog,
  Users,
  Wrench,
} from 'lucide-react';

/**
 * Roles soportados por el menú principal
 */
export const USER_ROLES = {
  ANALISTA: 'analista',
  SUPERVISOR: 'supervisor',
  GERENTE: 'gerente',
};

/**
 * Nombres de áreas utilizados para condicionar opciones
 */
export const AREA_NAMES = {
  CONTABILIDAD: 'Contabilidad',
  NOMINA: 'Nomina',
};

/**
 * Identificadores de tarjetas del menú
 */
export const MENU_OPTION_KEYS = {
  CLIENTES: 'clientes',
  HERRAMIENTAS: 'herramientas',
  MIS_ANALISTAS: 'misAnalistas',
  VALIDACIONES: 'validaciones',
  GESTION_COBRANZA: 'gestionCobranza',
  LOGS_ACTIVIDAD: 'logsActividad',
  LOGS_ACTIVIDAD_NOMINA: 'logsActividadNomina',
  ESTADOS_CIERRES_NOMINA: 'estadosCierresNomina',
  CACHE_REDIS_NOMINA: 'cacheRedisNomina',
  ESTADOS_CIERRES: 'estadosCierres',
  CACHE_REDIS: 'cacheRedis',
  ADMIN_SISTEMA: 'adminSistema',
  PROYECTOS_BDO_LATAM: 'proyectosBdoLatam',
  LOGS_CONTABILIDAD: 'logsContabilidad',
};

/**
 * Propiedades visuales compartidas por las tarjetas
 */
export const MENU_CARD_DEFAULTS = {
  opacity: 0.9,
  animationDelayStep: 100,
};

/**
 * Mapa de iconos del menú (duplicado desde la implementación legacy)
 */
export const MENU_ICON_MAP = {
  [MENU_OPTION_KEYS.CLIENTES]: FolderKanban,
  [MENU_OPTION_KEYS.HERRAMIENTAS]: Wrench,
  [MENU_OPTION_KEYS.MIS_ANALISTAS]: Users,
  [MENU_OPTION_KEYS.VALIDACIONES]: ShieldCheck,
  [MENU_OPTION_KEYS.GESTION_COBRANZA]: CreditCard,
  [MENU_OPTION_KEYS.LOGS_ACTIVIDAD]: FileText,
  [MENU_OPTION_KEYS.LOGS_ACTIVIDAD_NOMINA]: FileText,
  [MENU_OPTION_KEYS.ESTADOS_CIERRES_NOMINA]: Monitor,
  [MENU_OPTION_KEYS.CACHE_REDIS_NOMINA]: Database,
  [MENU_OPTION_KEYS.ESTADOS_CIERRES]: Monitor,
  [MENU_OPTION_KEYS.CACHE_REDIS]: Database,
  [MENU_OPTION_KEYS.ADMIN_SISTEMA]: Settings,
  [MENU_OPTION_KEYS.PROYECTOS_BDO_LATAM]: Users,
  [MENU_OPTION_KEYS.LOGS_CONTABILIDAD]: FileText,
  dashboardGerente: Activity,
  analyticsPerformance: BarChart3,
  gestionAnalistas: UserCog,
};
