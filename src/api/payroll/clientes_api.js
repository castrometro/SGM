// src/api/payroll/clientes_api.js
// APIs específicas para obtener clientes con información de payroll

import api from "../config";

/**
 * Función para obtener cierres de payroll por cliente
 */
export const obtenerCierresClientePayroll = async (clienteId) => {
  try {
    const response = await api.get(`/payroll/api/cierres/?cliente=${clienteId}`);
    return response.data;
  } catch (error) {
    console.error(`Error obteniendo cierres payroll para cliente ${clienteId}:`, error);
    return [];
  }
};

/**
 * Función para enriquecer clientes con información de último cierre de payroll
 */
export const obtenerClientesConEstadoCierrePayroll = async (clientes) => {
  console.log('🔍 Enriqueciendo', clientes.length, 'clientes con información de cierres de payroll...');
  
  const clientesConCierres = await Promise.all(
    clientes.map(async (cliente) => {
      try {
        const cierres = await obtenerCierresClientePayroll(cliente.id);
        const ultimoCierre = cierres.length > 0 ? cierres[cierres.length - 1] : null;
        
        console.log(`✅ Cliente ${cliente.nombre}: ${cierres.length} cierres payroll, último:`, 
          ultimoCierre ? `${ultimoCierre.periodo} (${ultimoCierre.estado})` : 'Sin cierres');
        
        return {
          ...cliente,
          ultimo_cierre_payroll: ultimoCierre ? {
            id: ultimoCierre.id,
            periodo: ultimoCierre.periodo,
            estado: ultimoCierre.estado,
            fecha_inicio: ultimoCierre.fecha_inicio,
            fecha_termino: ultimoCierre.fecha_termino
          } : null
        };
      } catch (error) {
        console.error(`❌ Error obteniendo cierres payroll para cliente ${cliente.id}:`, error);
        return {
          ...cliente,
          ultimo_cierre_payroll: null
        };
      }
    })
  );
  
  console.log('🎯 Clientes enriquecidos con payroll:', clientesConCierres.length);
  return clientesConCierres;
};

/**
 * Obtiene clientes asignados al usuario actual con información de estado de cierre payroll
 * Para analistas: solo clientes asignados
 */
export const obtenerClientesAsignadosPayroll = async () => {
  try {
    // Primero obtenemos el usuario actual para obtener su ID
    const userResponse = await api.get("/usuarios/me/");
    const usuarioId = userResponse.data.id;
    
    // Luego obtenemos los clientes asignados usando el ID del usuario
    const response = await api.get(`/clientes-asignados/${usuarioId}/`);
    
    // Enriquecemos los clientes con información de cierres de payroll
    const clientesConCierres = await obtenerClientesConEstadoCierrePayroll(response.data);
    
    return clientesConCierres;
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
    // Usamos el endpoint existente de clientes por área en el módulo api
    const response = await api.get("/clientes-por-area/");
    
    // Enriquecemos los clientes con información de cierres de payroll
    const clientesConCierres = await obtenerClientesConEstadoCierrePayroll(response.data);
    
    return clientesConCierres;
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
