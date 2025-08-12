import { obtenerResumenContable } from '../../../api/contabilidad';
// import { obtenerResumenNomina } from '../../../api/nomina'; // REMOVIDO - Limpieza de nómina

/**
 * Configuración de áreas para crear cierres
 */
export const AREAS_CONFIG = {
  Contabilidad: {
    title: "Crear Cierre Contable",
    description: "Crear un nuevo cierre contable para el cliente",
    apiFunction: obtenerResumenContable,
    defaultArea: true
  },
  Nomina: {
    title: "Crear Cierre de Nómina",
    description: "Crear un nuevo cierre de nómina para el cliente", 
    apiFunction: obtenerResumenContable, // Por ahora usar contabilidad como base
    defaultArea: false
  }
};

export const DEFAULT_AREA = "Contabilidad";

export const MESSAGES = {
  loading: "Cargando datos del cliente...",
  error: "Error cargando datos del cliente",
  pageTitle: "Crear Cierre"
};

/**
 * Función para determinar el área activa
 */
export const determinarAreaActiva = (propAreaActiva) => {
  return propAreaActiva || 
         localStorage.getItem("area_activa") || 
         DEFAULT_AREA;
};

/**
 * Obtener configuración del área
 */
export const getAreaConfig = (area) => {
  return AREAS_CONFIG[area] || AREAS_CONFIG[DEFAULT_AREA];
};

/**
 * Estilos de layout para la página
 */
export const LAYOUT_STYLES = {
  container: "max-w-2xl mx-auto mt-8 space-y-8",
  loadingContainer: "text-white text-center mt-8"
};
