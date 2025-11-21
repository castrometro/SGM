// src/modules/nomina/crear-cierre/api/crearCierre.api.js
import api from '../../../../api/config';

/**
 * Obtiene un cierre mensual de nómina para un cliente y periodo
 * @param {number} clienteId - ID del cliente
 * @param {string} periodo - Periodo en formato AAAA-MM
 * @returns {Promise<Object|null>} Cierre si existe, null si no
 */
export const obtenerCierreMensual = async (clienteId, periodo) => {
  try {
    console.log('🔍 CrearCierreNomina API - Verificando cierre existente:', { clienteId, periodo });
    const response = await api.get(`/nomina/cierres/`, {
      params: { 
        cliente: clienteId,
        periodo: periodo
      }
    });
    
    const cierres = response.data;
    if (cierres && cierres.length > 0) {
      console.log('⚠️ CrearCierreNomina API - Ya existe cierre:', cierres[0]);
      return cierres[0];
    }
    
    console.log('✅ CrearCierreNomina API - No existe cierre para el periodo');
    return null;
  } catch (error) {
    console.error('❌ CrearCierreNomina API - Error verificando cierre:', error);
    throw error;
  }
};

/**
 * Crea un nuevo cierre mensual de nómina
 * @param {number} clienteId - ID del cliente
 * @param {string} periodo - Periodo en formato AAAA-MM
 * @param {Array} tareas - Array de objetos {descripcion: string}
 * @returns {Promise<Object>} Cierre creado
 */
export const crearCierreMensual = async (clienteId, periodo, tareas) => {
  try {
    console.log('📝 CrearCierreNomina API - Creando cierre:', { clienteId, periodo, tareas });
    
    const payload = {
      cliente: Number(clienteId),
      periodo: periodo,
      checklist: tareas // Backend espera "checklist" no "tareas"
    };
    
    const response = await api.post('/nomina/cierres/', payload);
    console.log('✅ CrearCierreNomina API - Cierre creado:', response.data);
    return response.data;
  } catch (error) {
    console.error('❌ CrearCierreNomina API - Error creando cierre:', error);
    throw error;
  }
};

/**
 * Obtiene un cliente por ID
 * @param {number} id - ID del cliente
 * @returns {Promise<Object>} Datos del cliente
 */
export const obtenerCliente = async (id) => {
  try {
    const response = await api.get(`/clientes/${id}/`);
    return response.data;
  } catch (error) {
    console.error('❌ CrearCierreNomina API - Error obteniendo cliente:', error);
    throw error;
  }
};

/**
 * Obtiene el resumen de nómina de un cliente
 * @param {number} clienteId - ID del cliente
 * @returns {Promise<Object>} Resumen de nómina
 */
export const obtenerResumenNomina = async (clienteId) => {
  try {
    const response = await api.get(`/nomina/clientes/${clienteId}/resumen/`);
    return response.data;
  } catch (error) {
    console.error('❌ CrearCierreNomina API - Error obteniendo resumen:', error);
    throw error;
  }
};
