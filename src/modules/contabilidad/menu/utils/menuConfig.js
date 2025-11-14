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
 * 📊 MENU DE CONTABILIDAD
 * Configuración de opciones de menú específicas para el dominio de Contabilidad
 */

/**
 * Opciones disponibles para usuarios tipo Analista de Contabilidad
 */
const OPCIONES_ANALISTA = [
  { 
    label: "Clientes", 
    descripcion: "Ver y trabajar con tus clientes de contabilidad", 
    icon: FolderKanban, 
    color: "#4F46E5", 
    path: "/menu/clientes" 
  },
  { 
    label: "Gestión de Cobranza", 
    descripcion: "Seguimiento y gestión de cobros a clientes", 
    icon: CreditCard, 
    color: "#059669", 
    path: "/menu/gestion-cobranza-v2"
  },
  { 
    label: "Herramientas", 
    descripcion: "Acceso a recursos y utilidades de contabilidad", 
    icon: Wrench, 
    color: "#10B981", 
    path: "/menu/tools" 
  }
];

/**
 * Opciones disponibles para usuarios tipo Supervisor de Contabilidad
 */
const OPCIONES_SUPERVISOR = [
  { 
    label: "Mis Analistas", 
    descripcion: "Gestión y supervisión de analistas de contabilidad", 
    icon: Users, 
    color: "#EC4899", 
    path: "/menu/mis-analistas" 
  },
  { 
    label: "Clientes", 
    descripcion: "Ver y validar clientes de contabilidad", 
    icon: FolderKanban, 
    color: "#4F46E5", 
    path: "/menu/clientes" 
  },
  { 
    label: "Validaciones", 
    descripcion: "Revisar y aprobar cierres contables", 
    icon: ShieldCheck, 
    color: "#F59E0B", 
    path: "/menu/validaciones" 
  }
];

/**
 * Opciones base para gerentes de Contabilidad
 */
const OPCIONES_GERENTE_BASE = [
  { 
    label: "Clientes", 
    descripcion: "Visión general de todos los clientes de contabilidad", 
    icon: FolderKanban, 
    color: "#4F46E5", 
    path: "/menu/clientes" 
  }
];

/**
 * Opciones específicas para gerentes de Contabilidad
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
  },
  { 
    label: "Estados de Cierres", 
    descripcion: "Monitoreo en tiempo real de cierres contables", 
    icon: Monitor, 
    color: "#06B6D4", 
    path: "/menu/gerente/estados-cierres" 
  },
  { 
    label: "Cache Redis", 
    descripcion: "Estado y gestión del cache Redis", 
    icon: Database, 
    color: "#10B981", 
    path: "/menu/gerente/cache-redis" 
  }
];

/**
 * Herramientas comunes para gerentes
 */
const OPCIONES_GERENTE_FINALES = [
  { 
    label: "Herramientas", 
    descripcion: "Utilidades del sistema de contabilidad", 
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
 * Obtiene las opciones de menú de Contabilidad según el tipo de usuario
 * 
 * @param {Object} usuario - Objeto de usuario con tipo_usuario y areas
 * @returns {Array} Array de opciones de menú de contabilidad
 */
export const getUserMenuOptions = (usuario) => {
  const opciones = [];

  // Verificar que el usuario tenga área de Contabilidad
  const areas = usuario.areas || [];
  const tieneContabilidad = areas.some(area => area.nombre === BUSINESS_AREAS.CONTABILIDAD);
  
  if (!tieneContabilidad) {
    return opciones; // Retornar vacío si no es de contabilidad
  }

  // Opciones según tipo de usuario
  if (usuario.tipo_usuario === USER_TYPES.ANALISTA) {
    opciones.push(...OPCIONES_ANALISTA);
  }

  if (usuario.tipo_usuario === USER_TYPES.SUPERVISOR) {
    opciones.push(...OPCIONES_SUPERVISOR);
  }

  if (usuario.tipo_usuario === USER_TYPES.GERENTE) {
    // Opciones base
    opciones.push(...OPCIONES_GERENTE_BASE);
    
    // Opciones específicas de Contabilidad
    opciones.push(...OPCIONES_GERENTE_CONTABILIDAD);
    
    // Herramientas comunes
    opciones.push(...OPCIONES_GERENTE_FINALES);

    // Admin Sistema solo para gerentes de contabilidad
    opciones.push(...OPCIONES_ADMIN_SISTEMA);
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
  OPCIONES_GERENTE_FINALES,
  OPCIONES_ADMIN_SISTEMA
};
