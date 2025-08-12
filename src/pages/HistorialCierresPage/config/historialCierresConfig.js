/**
 * Configuración para el historial de cierres
 */

export const AREAS_CONFIG = {
  Contabilidad: {
    title: "Cierres Contables",
    description: "Historial de cierres contables del cliente",
    defaultArea: true
  },
  Nomina: {
    title: "Cierres de Nómina", 
    description: "Historial de cierres de nómina del cliente",
    defaultArea: false
  }
};

export const DEFAULT_AREA = "Contabilidad";

export const MESSAGES = {
  loading: "Cargando...",
  error: "Error determinando área activa",
  pageTitle: "Historial de Cierres"
};

/**
 * Función para determinar el área activa del usuario
 */
export const determinarAreaActiva = async (obtenerUsuario) => {
  try {
    // Primero intentar desde localStorage
    let area = localStorage.getItem("area_activa");
    
    if (!area) {
      // Si no hay área en localStorage, obtenerla del usuario
      const userData = await obtenerUsuario();
      if (userData.area_activa) {
        area = userData.area_activa;
      } else if (userData.areas && userData.areas.length > 0) {
        area = userData.areas[0].nombre || userData.areas[0];
      } else {
        area = DEFAULT_AREA; // fallback
      }
      localStorage.setItem("area_activa", area);
    }
    
    return area;
  } catch (error) {
    console.error("Error determinando área activa:", error);
    return DEFAULT_AREA; // fallback
  }
};

/**
 * Obtener configuración del área
 */
export const getAreaConfig = (area) => {
  return AREAS_CONFIG[area] || AREAS_CONFIG[DEFAULT_AREA];
};
