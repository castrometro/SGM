import { obtenerClientesAsignados, obtenerTodosLosClientes, obtenerClientesPorArea } from '../../../api/clientes';

/**
 * Configuración de tipos de usuario y sus APIs correspondientes
 */
export const USER_TYPES_CONFIG = {
  gerente: {
    title: "Gerente",
    description: "Ve todos los clientes de sus áreas asignadas",
    apiFunction: obtenerClientesPorArea,
    endpoint: "📊 /clientes-por-area/ (Gerente - clientes de sus áreas)"
  },
  analista: {
    title: "Analista", 
    description: "Ve solo los clientes que tienen asignados",
    apiFunction: obtenerClientesAsignados,
    endpoint: "👤 /clientes/asignados/ (Analista - solo asignados)"
  },
  supervisor: {
    title: "Supervisor",
    description: "Ve clientes del área que supervisan", 
    apiFunction: obtenerClientesPorArea,
    endpoint: "👁️ /clientes-por-area/ (Supervisor - área supervisada)"
  },
  default: {
    title: "Usuario",
    description: "Ve clientes por área por defecto",
    apiFunction: obtenerClientesPorArea,
    endpoint: "🔧 /clientes-por-area/ (Por defecto)"
  }
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

/**
 * Función para obtener la configuración según el tipo de usuario
 */
export const getUserConfig = (tipoUsuario) => {
  return USER_TYPES_CONFIG[tipoUsuario] || USER_TYPES_CONFIG.default;
};
