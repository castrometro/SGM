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
  CreditCard,
  Calculator,
  UserCheck,
  ClipboardList
} from "lucide-react";
import { USER_TYPES, BUSINESS_AREAS } from "../constants/menu.constants";

/**
 * 💼 MENU DE NÓMINA
 * Configuración de opciones de menú específicas para el dominio de Nómina
 */

/**
 * Opciones disponibles para usuarios tipo Analista de Nómina
 */
const OPCIONES_ANALISTA = [
  { 
    label: "Clientes", 
    descripcion: "Ver y trabajar con tus clientes de nómina", 
    icon: FolderKanban, 
    color: "#4F46E5", 
    path: "/menu/clientes" 
  },
  { 
    label: "Empleados", 
    descripcion: "Gestión de empleados y colaboradores", 
    icon: Users, 
    color: "#8B5CF6", 
    path: "/menu/empleados" 
  },
  { 
    label: "Herramientas", 
    descripcion: "Acceso a recursos y utilidades de nómina", 
    icon: Wrench, 
    color: "#10B981", 
    path: "/menu/nomina/tools" 
  }
];

/**
 * Opciones disponibles para usuarios tipo Supervisor de Nómina
 */
const OPCIONES_SUPERVISOR = [
  { 
    label: "Mis Analistas", 
    descripcion: "Gestión y supervisión de analistas de nómina", 
    icon: Users, 
    color: "#EC4899", 
    path: "/menu/mis-analistas" 
  },
  { 
    label: "Clientes", 
    descripcion: "Ver y validar clientes de nómina", 
    icon: FolderKanban, 
    color: "#4F46E5", 
    path: "/menu/clientes" 
  },
  { 
    label: "Validaciones", 
    descripcion: "Revisar y aprobar cierres de nómina", 
    icon: ShieldCheck, 
    color: "#F59E0B", 
    path: "/menu/validaciones" 
  }
];

/**
 * Opciones base para gerentes de Nómina
 */
const OPCIONES_GERENTE_BASE = [
  { 
    label: "Clientes", 
    descripcion: "Visión general de todos los clientes de nómina", 
    icon: FolderKanban, 
    color: "#4F46E5", 
    path: "/menu/clientes" 
  }
];

/**
 * Opciones específicas para gerentes de Nómina
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
  },
  { 
    label: "Dashboards Nómina", 
    descripcion: "Visualización de datos y métricas de nómina", 
    icon: BarChart3, 
    color: "#8B5CF6", 
    path: "/menu/dashboards-nomina" 
  }
];

/**
 * Herramientas comunes para gerentes de Nómina
 */
const OPCIONES_GERENTE_FINALES = [
  { 
    label: "Herramientas", 
    descripcion: "Utilidades del sistema de nómina", 
    icon: Wrench, 
    color: "#10B981", 
    path: "/menu/nomina/tools" 
  }
];

/**
 * Obtiene las opciones de menú de Nómina según el tipo de usuario
 * 
 * @param {Object} usuario - Objeto de usuario con tipo_usuario y areas
 * @returns {Array} Array de opciones de menú de nómina
 */
export const getUserMenuOptions = (usuario) => {
  const opciones = [];

  // Helper para normalizar nombres (sin tildes, lowercase)
  const normalizar = (str) => str.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();

  // Verificar que el usuario tenga área de Nómina
  const areas = usuario.areas || [];
  // Soportar tanto objetos {nombre: 'Nomina'} como strings 'Nómina'
  const tieneNomina = areas.some(area => {
    const nombreArea = typeof area === 'string' ? area : area.nombre;
    return normalizar(nombreArea) === 'nomina';
  });
  
  if (!tieneNomina) {
    console.log('Usuario sin área de Nómina:', usuario);
    return opciones; // Retornar vacío si no es de nómina
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
    
    // Opciones específicas de Nómina
    opciones.push(...OPCIONES_GERENTE_NOMINA);
    
    // Herramientas comunes
    opciones.push(...OPCIONES_GERENTE_FINALES);
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
  const normalizar = (str) => str.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
  const areas = usuario.areas || [];
  return areas.some(area => {
    const nombreArea = typeof area === 'string' ? area : area.nombre;
    return normalizar(nombreArea) === normalizar(areaNombre);
  });
};

/**
 * Exportaciones de configuraciones para uso directo
 */
export const MENU_CONFIG = {
  OPCIONES_ANALISTA,
  OPCIONES_SUPERVISOR,
  OPCIONES_GERENTE_BASE,
  OPCIONES_GERENTE_NOMINA,
  OPCIONES_GERENTE_FINALES
};
