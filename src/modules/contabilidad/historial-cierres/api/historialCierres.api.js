// src/modules/contabilidad/historial-cierres/api/historialCierres.api.js
import api from '../../../../api/config';

/**
 * Obtiene todos los cierres de contabilidad de un cliente
 * @param {number} clienteId - ID del cliente
 * @returns {Promise<Array>} Lista de cierres
 */
export const obtenerCierresContabilidadCliente = async (clienteId) => {
  try {
    console.log('🔍 HistorialCierresContabilidad API - Obteniendo cierres para cliente:', clienteId);
    const response = await api.get(`/contabilidad/cierres/`, {
      params: { cliente: clienteId }
    });
    console.log('✅ HistorialCierresContabilidad API - Cierres obtenidos:', response.data.length);
    return response.data;
  } catch (error) {
    console.error('❌ HistorialCierresContabilidad API - Error obteniendo cierres:', error);
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
    console.error('❌ Error obteniendo cliente:', error);
    throw error;
  }
};

/**
 * Obtiene el usuario actual
 * @returns {Promise<Object>} Datos del usuario
 */
export const obtenerUsuario = async () => {
  try {
    const response = await api.get('/usuarios/me/');
    return response.data;
  } catch (error) {
    console.error('❌ Error obteniendo usuario:', error);
    throw error;
  }
};
