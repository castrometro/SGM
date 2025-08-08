// src/api/payroll/discrepancies.js
import { api, PAYROLL_ENDPOINTS } from './config';

/**
 * API para gestión de discrepancias de nómina (Payroll Discrepancies)
 * Sistema para detectar y resolver discrepancias en los datos
 */

// ========== OPERACIONES BÁSICAS DE DISCREPANCIAS ==========

/**
 * Obtener discrepancias de un cierre
 * @param {number} closureId - ID del cierre
 * @param {Object} filters - Filtros opcionales
 * @returns {Promise<Array>} Lista de discrepancias
 */
export const getClosureDiscrepancies = async (closureId, filters = {}) => {
  console.log("🔍 [API] getClosureDiscrepancies - Iniciando con:", { closureId, filters });
  
  const params = { closure: closureId, ...filters };
  console.log("🔍 [API] getClosureDiscrepancies - Parámetros de la petición:", params);
  
  try {
    const response = await api.get(PAYROLL_ENDPOINTS.DISCREPANCIES, { params });
    console.log("✅ [API] getClosureDiscrepancies - Respuesta exitosa:", response.data);
    return response.data;
  } catch (error) {
    console.error("❌ [API] getClosureDiscrepancies - Error:", error);
    throw error;
  }
};

/**
 * Generar discrepancias para un cierre
 * @param {number} closureId - ID del cierre
 * @param {Object} config - Configuración para la generación
 * @returns {Promise<Object>} Resultado de la generación
 */
export const generateClosureDiscrepancies = async (closureId, config = {}) => {
  const response = await api.post(`${PAYROLL_ENDPOINTS.DISCREPANCIES}/generate/${closureId}/`, config);
  return response.data;
};

/**
 * Obtener una discrepancia específica
 * @param {number} discrepancyId - ID de la discrepancia
 * @returns {Promise<Object>} Datos de la discrepancia
 */
export const getDiscrepancy = async (discrepancyId) => {
  const response = await api.get(`${PAYROLL_ENDPOINTS.DISCREPANCIES}/${discrepancyId}/`);
  return response.data;
};

/**
 * Limpiar discrepancias de un cierre
 * @param {number} closureId - ID del cierre
 * @returns {Promise<Object>} Confirmación de limpieza
 */
export const clearClosureDiscrepancies = async (closureId) => {
  const response = await api.delete(`${PAYROLL_ENDPOINTS.DISCREPANCIES}/clear/${closureId}/`);
  return response.data;
};

// ========== RESÚMENES Y ESTADOS ==========

/**
 * Obtener resumen de discrepancias de un cierre
 * @param {number} closureId - ID del cierre
 * @returns {Promise<Object>} Resumen de discrepancias
 */
export const getDiscrepanciesSummary = async (closureId) => {
  console.log("🔍 [API] getDiscrepanciesSummary - Iniciando para cierre:", closureId);
  
  try {
    const response = await api.get(`${PAYROLL_ENDPOINTS.DISCREPANCIES}/summary/${closureId}/`);
    console.log("✅ [API] getDiscrepanciesSummary - Respuesta exitosa:", response.data);
    return response.data;
  } catch (error) {
    console.error("❌ [API] getDiscrepanciesSummary - Error:", error);
    throw error;
  }
};

/**
 * Obtener estado de discrepancias de un cierre
 * @param {number} closureId - ID del cierre
 * @returns {Promise<Object>} Estado de discrepancias
 */
export const getClosureDiscrepanciesState = async (closureId) => {
  console.log("🔍 [API] getClosureDiscrepanciesState - Iniciando para cierre:", closureId);
  
  try {
    const response = await api.get(`${PAYROLL_ENDPOINTS.DISCREPANCIES}/state/${closureId}/`);
    console.log("✅ [API] getClosureDiscrepanciesState - Respuesta exitosa:", response.data);
    return response.data;
  } catch (error) {
    console.error("❌ [API] getClosureDiscrepanciesState - Error:", error);
    throw error;
  }
};

// ========== RESOLUCIÓN DE DISCREPANCIAS ==========

/**
 * Marcar discrepancia como resuelta
 * @param {number} discrepancyId - ID de la discrepancia
 * @param {string} resolution - Descripción de la resolución
 * @param {Object} resolutionData - Datos adicionales de la resolución
 * @returns {Promise<Object>} Discrepancia resuelta
 */
export const resolveDiscrepancy = async (discrepancyId, resolution, resolutionData = {}) => {
  const response = await api.post(`${PAYROLL_ENDPOINTS.DISCREPANCIES}/${discrepancyId}/resolve/`, {
    resolution,
    resolution_data: resolutionData
  });
  return response.data;
};

/**
 * Aprobar resolución de discrepancia
 * @param {number} discrepancyId - ID de la discrepancia
 * @param {string} comment - Comentario de aprobación
 * @returns {Promise<Object>} Discrepancia aprobada
 */
export const approveDiscrepancy = async (discrepancyId, comment = '') => {
  const response = await api.post(`${PAYROLL_ENDPOINTS.DISCREPANCIES}/${discrepancyId}/approve/`, {
    comment
  });
  return response.data;
};

/**
 * Rechazar resolución de discrepancia
 * @param {number} discrepancyId - ID de la discrepancia
 * @param {string} comment - Comentario de rechazo
 * @returns {Promise<Object>} Discrepancia rechazada
 */
export const rejectDiscrepancy = async (discrepancyId, comment) => {
  const response = await api.post(`${PAYROLL_ENDPOINTS.DISCREPANCIES}/${discrepancyId}/reject/`, {
    comment
  });
  return response.data;
};

// ========== TIPOS DE DISCREPANCIAS ==========

/**
 * Obtener tipos de discrepancias disponibles
 * @returns {Promise<Array>} Tipos de discrepancias
 */
export const getDiscrepancyTypes = async () => {
  const response = await api.get(`${PAYROLL_ENDPOINTS.DISCREPANCIES}/types/`);
  return response.data;
};

/**
 * Obtener discrepancias por tipo
 * @param {number} closureId - ID del cierre
 * @param {string} discrepancyType - Tipo de discrepancia
 * @returns {Promise<Array>} Discrepancias del tipo especificado
 */
export const getDiscrepanciesByType = async (closureId, discrepancyType) => {
  const response = await api.get(PAYROLL_ENDPOINTS.DISCREPANCIES, {
    params: { closure: closureId, type: discrepancyType }
  });
  return response.data;
};

// ========== ANÁLISIS DE DISCREPANCIAS ==========

/**
 * Analizar patrones de discrepancias
 * @param {number} closureId - ID del cierre
 * @returns {Promise<Object>} Análisis de patrones
 */
export const analyzeDiscrepancyPatterns = async (closureId) => {
  const response = await api.post(`${PAYROLL_ENDPOINTS.DISCREPANCIES}/analyze-patterns/${closureId}/`);
  return response.data;
};

/**
 * Obtener estadísticas de discrepancias
 * @param {number} closureId - ID del cierre
 * @returns {Promise<Object>} Estadísticas de discrepancias
 */
export const getDiscrepancyStatistics = async (closureId) => {
  const response = await api.get(`${PAYROLL_ENDPOINTS.DISCREPANCIES}/statistics/${closureId}/`);
  return response.data;
};

// ========== COMPARACIONES Y VALIDACIONES ==========

/**
 * Comparar datos entre sistemas
 * @param {number} closureId - ID del cierre
 * @param {Array} systemsToCompare - Sistemas a comparar
 * @returns {Promise<Object>} Resultado de la comparación
 */
export const compareSystemsData = async (closureId, systemsToCompare) => {
  const response = await api.post(`${PAYROLL_ENDPOINTS.DISCREPANCIES}/compare-systems/${closureId}/`, {
    systems: systemsToCompare
  });
  return response.data;
};

/**
 * Validar consistencia de datos
 * @param {number} closureId - ID del cierre
 * @param {Object} validationRules - Reglas de validación
 * @returns {Promise<Object>} Resultado de la validación
 */
export const validateDataConsistency = async (closureId, validationRules = {}) => {
  const response = await api.post(`${PAYROLL_ENDPOINTS.DISCREPANCIES}/validate-consistency/${closureId}/`, validationRules);
  return response.data;
};

// ========== EXPORTACIÓN Y REPORTES ==========

/**
 * Exportar discrepancias a Excel
 * @param {number} closureId - ID del cierre
 * @param {Object} exportConfig - Configuración de exportación
 * @returns {Promise<Blob>} Archivo Excel
 */
export const exportDiscrepanciesToExcel = async (closureId, exportConfig = {}) => {
  const response = await api.get(`${PAYROLL_ENDPOINTS.DISCREPANCIES}/export/${closureId}/`, {
    params: exportConfig,
    responseType: 'blob'
  });
  return response.data;
};

/**
 * Generar reporte de discrepancias
 * @param {number} closureId - ID del cierre
 * @param {Object} reportConfig - Configuración del reporte
 * @returns {Promise<Object>} Reporte generado
 */
export const generateDiscrepancyReport = async (closureId, reportConfig = {}) => {
  const response = await api.post(`${PAYROLL_ENDPOINTS.DISCREPANCIES}/generate-report/${closureId}/`, reportConfig);
  return response.data;
};

// ========== CONFIGURACIÓN DE TOLERANCIAS ==========

/**
 * Obtener configuración de tolerancias para discrepancias
 * @param {number} clientId - ID del cliente
 * @returns {Promise<Object>} Configuración de tolerancias
 */
export const getDiscrepancyTolerances = async (clientId) => {
  const response = await api.get(`${PAYROLL_ENDPOINTS.DISCREPANCIES}/tolerances/${clientId}/`);
  return response.data;
};

/**
 * Actualizar configuración de tolerancias
 * @param {number} clientId - ID del cliente
 * @param {Object} tolerances - Nuevas tolerancias
 * @returns {Promise<Object>} Configuración actualizada
 */
export const updateDiscrepancyTolerances = async (clientId, tolerances) => {
  const response = await api.put(`${PAYROLL_ENDPOINTS.DISCREPANCIES}/tolerances/${clientId}/`, tolerances);
  return response.data;
};
