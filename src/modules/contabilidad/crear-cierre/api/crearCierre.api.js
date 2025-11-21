// src/modules/contabilidad/crear-cierre/api/crearCierre.api.js
import api from '../../../../api/config';

/**
 * Obtiene un cierre mensual de contabilidad para un cliente y periodo
 * @param {number} clienteId - ID del cliente
 * @param {string} periodo - Periodo en formato AAAA-MM
 * @returns {Promise<Object|null>} Cierre si existe, null si no
 */
export const obtenerCierreMensual = async (clienteId, periodo) => {
  try {
    console.log('🔍 CrearCierreContabilidad API - Verificando cierre existente:', { clienteId, periodo });
    const response = await api.get(`/contabilidad/cierres/`, {
      params: { 
        cliente: clienteId,
        periodo: periodo
      }
    });
    
    const cierres = response.data;
    if (cierres && cierres.length > 0) {
      console.log('⚠️ CrearCierreContabilidad API - Ya existe cierre:', cierres[0]);
      return cierres[0];
    }
    
    console.log('✅ CrearCierreContabilidad API - No existe cierre para el periodo');
    return null;
  } catch (error) {
    console.error('❌ CrearCierreContabilidad API - Error verificando cierre:', error);
    throw error;
  }
};

/**
 * Crea un nuevo cierre mensual de contabilidad
 * @param {number} clienteId - ID del cliente
 * @param {string} periodo - Periodo en formato AAAA-MM
 * @returns {Promise<Object>} Cierre creado
 */
export const crearCierreMensual = async (clienteId, periodo) => {
  try {
    console.log('📝 CrearCierreContabilidad API - Creando cierre:', { clienteId, periodo });
    const response = await api.post('/contabilidad/cierres/', {
      cliente: Number(clienteId),
      periodo: periodo
    });
    console.log('✅ CrearCierreContabilidad API - Cierre creado:', response.data);
    return response.data;
  } catch (error) {
    console.error('❌ CrearCierreContabilidad API - Error creando cierre:', error);
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
    console.error('❌ CrearCierreContabilidad API - Error obteniendo cliente:', error);
    throw error;
  }
};

/**
 * Obtiene el resumen contable de un cliente
 * @param {number} clienteId - ID del cliente
 * @returns {Promise<Object>} Resumen contable
 */
export const obtenerResumenContable = async (clienteId) => {
  try {
    const response = await api.get(`/contabilidad/clientes/${clienteId}/resumen/`);
    return response.data;
  } catch (error) {
    console.error('❌ CrearCierreContabilidad API - Error obteniendo resumen:', error);
    throw error;
  }
};
