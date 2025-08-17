import { obtenerClientesAsignadosContabilidad, obtenerClientesPorAreaContabilidad } from '../../../api/clientes';
import { obtenerClientesAsignadosPayroll, obtenerClientesPorAreaPayroll } from '../../../api/payroll/clientes_api';

/**
 * Configuración de tipos de usuario y sus APIs correspondientes
 * Maneja tanto CONTABILIDAD como PAYROLL según el área activa
 */

// Configuraciones para CONTABILIDAD
export const CONTABILIDAD_CONFIG = {
  gerente: {
    title: "Gerente",
    description: "Ve todos los clientes de sus áreas asignadas",
    apiFunction: obtenerClientesPorAreaContabilidad,
    endpoint: "📊 /clientes-por-area/ + cierres contables (Gerente - clientes de sus áreas)",
    tipoModulo: 'contabilidad'
  },
  analista: {
    title: "Analista", 
    description: "Ve solo los clientes que tienen asignados",
    apiFunction: obtenerClientesAsignadosContabilidad,
    endpoint: "👤 /clientes/asignados/ + cierres contables (Analista - solo asignados)",
    tipoModulo: 'contabilidad'
  },
  supervisor: {
    title: "Supervisor",
    description: "Ve clientes del área que supervisan", 
    apiFunction: obtenerClientesPorAreaContabilidad,
    endpoint: "👁️ /clientes-por-area/ + cierres contables (Supervisor - área supervisada)",
    tipoModulo: 'contabilidad'
  },
  default: {
    title: "Usuario",
    description: "Ve clientes por área por defecto",
    apiFunction: obtenerClientesPorAreaContabilidad,
    endpoint: "🔧 /clientes-por-area/ + cierres contables (Por defecto)",
    tipoModulo: 'contabilidad'
  }
};

// Configuraciones para PAYROLL
export const PAYROLL_CONFIG = {
  gerente: {
    title: "Gerente",
    description: "Ve todos los clientes de sus áreas asignadas",
    apiFunction: obtenerClientesPorAreaPayroll,
    endpoint: "📊 /payroll/clientes/por-area/ (Gerente - clientes de sus áreas)",
    tipoModulo: 'payroll'
  },
  analista: {
    title: "Analista", 
    description: "Ve solo los clientes que tienen asignados",
    apiFunction: obtenerClientesAsignadosPayroll,
    endpoint: "👤 /payroll/clientes/asignados/ (Analista - solo asignados)",
    tipoModulo: 'payroll'
  },
  supervisor: {
    title: "Supervisor",
    description: "Ve clientes del área que supervisan", 
    apiFunction: obtenerClientesPorAreaPayroll,
    endpoint: "👁️ /payroll/clientes/por-area/ (Supervisor - área supervisada)",
    tipoModulo: 'payroll'
  },
  default: {
    title: "Usuario",
    description: "Ve clientes por área por defecto",
    apiFunction: obtenerClientesPorAreaPayroll,
    endpoint: "🔧 /payroll/clientes/por-area/ (Por defecto)",
    tipoModulo: 'payroll'
  }
};

/**
 * Función para obtener la configuración según el tipo de usuario y área activa
 */
export const getUserConfig = (tipoUsuario, areaActiva) => {
  // Determinar qué configuración usar según el área activa
  const isPayrollArea = areaActiva === "Payroll" || areaActiva === "Nomina";
  const configSet = isPayrollArea ? PAYROLL_CONFIG : CONTABILIDAD_CONFIG;
  
  return configSet[tipoUsuario] || configSet.default;
};

/**
 * Mensajes de la aplicación
 */
export const MESSAGES = {
  loading: "Cargando clientes...",
  error: "No se pudo cargar el usuario o los clientes. Intenta más tarde.",
  noArea: "No tienes un área activa asignada. Contacta a tu administrador.",
  noUser: "No se pudo determinar tu área activa.",
  searchPlaceholder: "Buscar por nombre o RUT...",
  noClients: "No hay clientes en tu área",
  noClientsFound: "No se encontraron clientes que coincidan con",
  analistaNoClients: "No tienes clientes asignados. Contacta a tu supervisor.",
  defaultNoClients: "No hay clientes registrados para esta área."
};
