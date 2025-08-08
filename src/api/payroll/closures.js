// src/api/payroll/closures.js
import { api, PAYROLL_ENDPOINTS, CLOSURE_STATES } from './config';

/**
 * API para gestión de cierres de nómina (Payroll Closures)
 * Versión mejorada y modular del sistema de cierres
 */

// ========== OPERACIONES BÁSICAS DE CIERRES ==========

/**
 * Obtener resumen de cierres de un cliente
 * @param {number} clientId - ID del cliente
 * @returns {Promise<Object>} Resumen de cierres del cliente
 */
export const getClientClosuresSummary = async (clientId) => {
  const response = await api.get(`${PAYROLL_ENDPOINTS.CLOSURES}/summary/${clientId}/`);
  return response.data;
};

/**
 * Obtener cierre mensual específico
 * @param {number} clientId - ID del cliente
 * @param {string} period - Período en formato YYYY-MM
 * @returns {Promise<Object|null>} Datos del cierre o null si no existe
 */
export const getMonthlyClosure = async (clientId, period) => {
  const response = await api.get(PAYROLL_ENDPOINTS.CLOSURES, { 
    params: { client: clientId, period: period } 
  });
  return response.data.length > 0 ? response.data[0] : null;
};

/**
 * Crear un nuevo cierre mensual
 * @param {number} clientId - ID del cliente
 * @param {string} period - Período en formato YYYY-MM
 * @param {Object} checklist - Checklist inicial del cierre
 * @returns {Promise<Object>} Datos del cierre creado
 */
export const createMonthlyClosure = async (clientId, period, checklist = {}) => {
  const payload = {
    client: Number(clientId),
    period: period,
    checklist,
    state: CLOSURE_STATES.PENDING,
  };
  const response = await api.post(PAYROLL_ENDPOINTS.CLOSURES, payload);
  return response.data;
};

/**
 * Obtener cierre por ID
 * @param {number} closureId - ID del cierre
 * @returns {Promise<Object>} Datos del cierre
 */
export const getClosureById = async (closureId) => {
  const response = await api.get(`${PAYROLL_ENDPOINTS.CLOSURES}/${closureId}/`);
  return response.data;
};

/**
 * Actualizar datos de un cierre
 * @param {number} closureId - ID del cierre
 * @param {Object} data - Datos a actualizar
 * @returns {Promise<Object>} Datos del cierre actualizado
 */
export const updateClosure = async (closureId, data) => {
  const response = await api.put(`${PAYROLL_ENDPOINTS.CLOSURES}/${closureId}/`, data);
  return response.data;
};

/**
 * Eliminar un cierre
 * @param {number} closureId - ID del cierre
 * @returns {Promise<Object>} Confirmación de eliminación
 */
export const deleteClosure = async (closureId) => {
  const response = await api.delete(`${PAYROLL_ENDPOINTS.CLOSURES}/${closureId}/`);
  return response.data;
};

// ========== GESTIÓN DE ESTADOS ==========

/**
 * Actualizar estado automático del cierre
 * @param {number} closureId - ID del cierre
 * @returns {Promise<Object>} Estado actualizado
 */
export const updateClosureState = async (closureId) => {
  const response = await api.post(`${PAYROLL_ENDPOINTS.CLOSURES}/${closureId}/update-state/`);
  return response.data;
};

/**
 * Cambiar estado manualmente
 * @param {number} closureId - ID del cierre
 * @param {string} newState - Nuevo estado (usar CLOSURE_STATES)
 * @param {string} comment - Comentario del cambio
 * @returns {Promise<Object>} Estado actualizado
 */
export const changeClosureState = async (closureId, newState, comment = '') => {
  const response = await api.post(`${PAYROLL_ENDPOINTS.CLOSURES}/${closureId}/change-state/`, {
    state: newState,
    comment
  });
  return response.data;
};

/**
 * Finalizar cierre (cuando no hay incidencias pendientes)
 * @param {number} closureId - ID del cierre
 * @returns {Promise<Object>} Confirmación de finalización
 */
export const finalizeClosure = async (closureId) => {
  const response = await api.post(`${PAYROLL_ENDPOINTS.CLOSURES}/${closureId}/finalize/`);
  return response.data;
};

// ========== CONSOLIDACIÓN DE DATOS ==========

/**
 * Consolidar datos de Talana (Libro + Novedades)
 * @param {number} closureId - ID del cierre
 * @returns {Promise<Object>} Resultado de la consolidación
 */
export const consolidateTalanaData = async (closureId) => {
  const response = await api.post(`${PAYROLL_ENDPOINTS.CLOSURES}/${closureId}/consolidate-data/`);
  return response.data;
};

/**
 * Consultar estado de tarea Celery
 * @param {number} closureId - ID del cierre
 * @param {string} taskId - ID de la tarea
 * @returns {Promise<Object>} Estado de la tarea
 */
export const getTaskStatus = async (closureId, taskId) => {
  const response = await api.get(`${PAYROLL_ENDPOINTS.CLOSURES}/${closureId}/task-status/${taskId}/`);
  return response.data;
};

// ========== FUNCIONES DE UTILIDAD ==========

/**
 * Obtener todos los cierres de un cliente
 * @param {number} clientId - ID del cliente
 * @returns {Promise<Array>} Lista de cierres del cliente
 */
export const getClientClosures = async (clientId) => {
  const response = await api.get(PAYROLL_ENDPOINTS.CLOSURES, { 
    params: { client: clientId } 
  });
  return response.data;
};

/**
 * Obtener todos los cierres (vista gerencial)
 * @param {Object} filters - Filtros opcionales
 * @returns {Promise<Array>} Lista de todos los cierres
 */
export const getAllClosures = async (filters = {}) => {
  const response = await api.get(PAYROLL_ENDPOINTS.CLOSURES, { params: filters });
  return response.data;
};

/**
 * Obtener estadísticas de cierres
 * @param {number} clientId - ID del cliente (opcional)
 * @returns {Promise<Object>} Estadísticas de cierres
 */
export const getClosuresStatistics = async (clientId = null) => {
  const params = clientId ? { client: clientId, stats: true } : { stats: true };
  const response = await api.get(PAYROLL_ENDPOINTS.CLOSURES, { params });
  return response.data;
};
