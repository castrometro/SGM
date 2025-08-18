import { obtenerResumenContable } from '../../../api/contabilidad';
import { obtenerResumenPayrollCliente } from '../../../api/payroll/clientes_payroll';
// import { obtenerResumenNomina } from '../../../api/nomina'; // REMOVIDO - Limpieza de nómina

/**
 * Configuración de áreas y sus APIs correspondientes
 */
export const AREAS_CONFIG = {
  Contabilidad: {
    title: "Contabilidad",
    color: "bg-blue-600", // Puedes ajustar según getAreaColor
    apiFunction: obtenerResumenContable,
    showKpiResumen: true,
    services: {
      title: "Servicios Contables",
      types: ["contabilidad", "facturacion", "tesoreria"]
    }
  },
  Payroll: {
    title: "Payroll", 
    color: "bg-green-600",
    apiFunction: obtenerResumenPayrollCliente,
    showKpiResumen: true,
    services: {
      title: "Servicios de Payroll",
      types: ["payroll", "nomina", "rrhh", "liquidaciones"]
    }
  },
  Nomina: {
    title: "Nómina", 
    color: "bg-green-600",
    apiFunction: obtenerResumenPayrollCliente, // Usar la misma API de Payroll
    showKpiResumen: false,
    services: {
      title: "Servicios de Nómina",
      types: ["nomina", "rrhh", "liquidaciones"]
    }
  }
};

/**
 * Configuración por defecto
 */
export const DEFAULT_AREA = "Contabilidad";

/**
 * Mensajes de la aplicación
 */
export const MESSAGES = {
  loading: "Cargando cliente...",
  error: "Error cargando datos del cliente",
  noArea: "No se pudo determinar el área activa",
  pageTitle: "Detalle de Cliente"
};

/**
 * Función para obtener la configuración del área
 */
export const getAreaConfig = (area) => {
  return AREAS_CONFIG[area] || AREAS_CONFIG[DEFAULT_AREA];
};

/**
 * Función para determinar el área activa del usuario
 */
export const determinarAreaActiva = (usuario) => {
  let area = localStorage.getItem("area_activa");
  
  if (!area) {
    if (usuario.area_activa) {
      area = usuario.area_activa;
    } else if (usuario.areas && usuario.areas.length > 0) {
      area = usuario.areas[0].nombre || usuario.areas[0];
    } else if (usuario.area) {
      area = usuario.area; // fallback al campo area si existe
    } else {
      area = DEFAULT_AREA; // fallback final
    }
    localStorage.setItem("area_activa", area);
  }
  
  return area;
};
