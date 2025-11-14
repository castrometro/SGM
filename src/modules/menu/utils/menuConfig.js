import {
  FolderKanban,
  Wrench,
  ShieldCheck,
  UserCog,
  FileText,
  BarChart3,
  Activity,
  Users,
  Settings,
  Database,
  Monitor,
  CreditCard
} from "lucide-react";
import { USER_TYPES, BUSINESS_AREAS } from "../constants/menu.constants";

/**
 * Configuración de opciones de menú por tipo de usuario y área
 */

/**
 * Opciones disponibles para usuarios tipo Analista
 */
const OPCIONES_ANALISTA = [
  { 
    label: "Clientes", 
    descripcion: "Ver y trabajar con tus clientes asignados", 
    icon: FolderKanban, 
    color: "#4F46E5", 
    path: "/menu/clientes" 
  },
  { 
    label: "Herramientas", 
    descripcion: "Acceso a recursos y utilidades", 
    icon: Wrench, 
    color: "#10B981", 
    path: "/menu/tools" 
  }
];

/**
 * Opciones disponibles para usuarios tipo Supervisor
 */
const OPCIONES_SUPERVISOR = [
  { 
    label: "Mis Analistas", 
    descripcion: "Gestión y supervisión de analistas asignados", 
    icon: Users, 
    color: "#EC4899", 
    path: "/menu/mis-analistas" 
  },
  { 
    label: "Clientes", 
    descripcion: "Ver y validar clientes asignados", 
    icon: FolderKanban, 
    color: "#4F46E5", 
    path: "/menu/clientes" 
  },
  { 
    label: "Validaciones", 
    descripcion: "Revisar y aprobar cierres", 
    icon: ShieldCheck, 
    color: "#F59E0B", 
    path: "/menu/validaciones" 
  }
];

/**
 * Opciones base disponibles para todos los gerentes
 */
const OPCIONES_GERENTE_BASE = [
  { 
    label: "Clientes", 
    descripcion: "Visión general de todos los clientes", 
    icon: FolderKanban, 
    color: "#4F46E5", 
    path: "/menu/clientes" 
  }
];

/**
 * Opciones específicas para gerentes del área de Contabilidad
 */
const OPCIONES_GERENTE_CONTABILIDAD = [
  { 
    label: "Gestión de Cobranza", 
    descripcion: "Seguimiento y gestión de cobros a clientes", 
    icon: CreditCard, 
    color: "#059669", 
    path: "/menu/gestion-cobranza-v2" 
  },
  { 
    label: "Logs y Actividad", 
    descripcion: "Auditoría y logs de actividades de usuarios", 
    icon: FileText, 
    color: "#F97316", 
    path: "/menu/gerente/logs-actividad" 
  },
  { 
    label: "Proyectos BDO Latam", 
    descripcion: "Gestión de proyectos BDO en Latinoamérica", 
    icon: Users, 
    color: "#3B82F6", 
    path: "/menu/proyectos-bdo-latam" 
  }
];

/**
 * Opciones específicas para gerentes del área de Nómina
 */
const OPCIONES_GERENTE_NOMINA = [
  { 
    label: "Logs y Actividad Nómina", 
    descripcion: "Auditoría y logs de actividades de nómina", 
    icon: FileText, 
    color: "#F97316", 
    path: "/menu/gerente/logs-actividad-nomina" 
  },
  { 
    label: "Estados de Cierres Nómina", 
    descripcion: "Monitoreo en tiempo real de cierres de nómina", 
    icon: Monitor, 
    color: "#06B6D4", 
    path: "/menu/gerente/estados-cierres-nomina" 
  },
  { 
    label: "Cache Redis Nómina", 
    descripcion: "Estado y gestión del cache Redis de nómina", 
    icon: Database, 
    color: "#10B981", 
    path: "/menu/gerente/cache-redis-nomina" 
  }
];

/**
 * Opciones finales comunes para gerentes
 */
const OPCIONES_GERENTE_FINALES = [
  { 
    label: "Herramientas", 
    descripcion: "Utilidades del sistema", 
    icon: Wrench, 
    color: "#10B981", 
    path: "/menu/tools" 
  }
];

/**
 * Opciones de administración del sistema (solo Gerentes de Contabilidad)
 */
const OPCIONES_ADMIN_SISTEMA = [
  {
    label: "Admin Sistema", 
    descripcion: "Creación de usuarios, clientes y herramientas avanzadas", 
    icon: Settings, 
    color: "#DC2626", 
    path: "/menu/gerente/admin-sistema"
  }
];

/**
 * Opción de gestión de cobranza para usuarios de contabilidad (no gerentes)
 */
const OPCION_COBRANZA_NO_GERENTE = [
  {
    label: "Gestión de Cobranza", 
    descripcion: "Seguimiento y gestión de cobros a clientes", 
    icon: CreditCard, 
    color: "#059669", 
    path: "/menu/gestion-cobranza-v2"
  }
];

/**
 * Obtiene las opciones de menú según el tipo de usuario y áreas asignadas
 * 
 * @param {Object} usuario - Objeto de usuario con tipo_usuario y areas
 * @returns {Array} Array de opciones de menú
 */
export const getUserMenuOptions = (usuario) => {
  const opciones = [];

  // Opciones según tipo de usuario
  if (usuario.tipo_usuario === USER_TYPES.ANALISTA) {
    opciones.push(...OPCIONES_ANALISTA);
  }

  if (usuario.tipo_usuario === USER_TYPES.SUPERVISOR) {
    opciones.push(...OPCIONES_SUPERVISOR);
  }

  if (usuario.tipo_usuario === USER_TYPES.GERENTE) {
    const areas = usuario.areas || [];
    const tieneContabilidad = areas.some(area => area.nombre === BUSINESS_AREAS.CONTABILIDAD);
    const tieneNomina = areas.some(area => area.nombre === BUSINESS_AREAS.NOMINA);
    
    // Opciones base
    opciones.push(...OPCIONES_GERENTE_BASE);
    
    // Opciones específicas de Contabilidad
    if (tieneContabilidad) {
      opciones.push(...OPCIONES_GERENTE_CONTABILIDAD);
    }

    // Opciones específicas de Nómina
    if (tieneNomina) {
      opciones.push(...OPCIONES_GERENTE_NOMINA);
    }
    
    // Opciones finales comunes
    opciones.push(...OPCIONES_GERENTE_FINALES);

    // Admin Sistema solo para gerentes de contabilidad
    if (tieneContabilidad) {
      opciones.push(...OPCIONES_ADMIN_SISTEMA);
    }
  }

  // Gestión de cobranza para usuarios de contabilidad no gerentes
  const areas = usuario.areas || [];
  const tieneContabilidad = areas.some(area => area.nombre === BUSINESS_AREAS.CONTABILIDAD);
  
  if (tieneContabilidad && usuario.tipo_usuario !== USER_TYPES.GERENTE) {
    opciones.push(...OPCION_COBRANZA_NO_GERENTE);
  }

  return opciones;
};

/**
 * Verifica si un usuario tiene una área específica
 * 
 * @param {Object} usuario - Objeto de usuario
 * @param {string} areaNombre - Nombre del área a verificar
 * @returns {boolean}
 */
export const hasArea = (usuario, areaNombre) => {
  const areas = usuario.areas || [];
  return areas.some(area => area.nombre === areaNombre);
};

/**
 * Exportaciones de configuraciones para uso directo
 */
export const MENU_CONFIG = {
  OPCIONES_ANALISTA,
  OPCIONES_SUPERVISOR,
  OPCIONES_GERENTE_BASE,
  OPCIONES_GERENTE_CONTABILIDAD,
  OPCIONES_GERENTE_NOMINA,
  OPCIONES_GERENTE_FINALES,
  OPCIONES_ADMIN_SISTEMA,
  OPCION_COBRANZA_NO_GERENTE
};
