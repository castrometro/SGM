// src/api/payroll/clientes_api.js
// APIs específicas para obtener clientes con información de payroll

import api from "../config";

/**
 * Obtiene clientes asignados al usuario actual con información de estado de cierre payroll
 * Para analistas: solo clientes asignados
 */
export const obtenerClientesAsignadosPayroll = async () => {
  try {
    const response = await api.get("/payroll/clientes/asignados/");
    return response.data;
  } catch (error) {
    console.error("Error obteniendo clientes asignados payroll:", error);
    throw error;
  }
};

/**
 * Obtiene clientes del área del usuario actual con información de estado de cierre payroll
 * Para gerentes/supervisores: clientes de sus áreas
 */
export const obtenerClientesPorAreaPayroll = async () => {
  try {
    const response = await api.get("/payroll/clientes/por-area/");
    return response.data;
  } catch (error) {
    console.error("Error obteniendo clientes por área payroll:", error);
    throw error;
  }
};

/**
 * Función helper para obtener estado visual del cierre
 */
export const getEstadoCierreClass = (estado) => {
  switch (estado) {
    case 'completado':
      return 'text-green-400';
    case 'procesando':
      return 'text-yellow-400';
    case 'pendiente':
      return 'text-orange-400';
    case 'error':
      return 'text-red-400';
    case 'sin_cierres':
      return 'text-gray-400';
    default:
      return 'text-gray-400';
  }
};

/**
 * Función helper para obtener texto legible del estado
 */
export const getEstadoCierreText = (estado) => {
  switch (estado) {
    case 'completado':
      return 'Completado';
    case 'procesando':
      return 'Procesando';
    case 'pendiente':
      return 'Pendiente';
    case 'error':
      return 'Error';
    case 'sin_cierres':
      return 'Sin cierres';
    default:
      return 'Desconocido';
  }
};
