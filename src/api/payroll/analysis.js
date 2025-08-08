// src/api/payroll/analysis.js
import { api, PAYROLL_ENDPOINTS, DEFAULT_TOLERANCES } from './config';

/**
 * API para análisis de datos de nómina (Payroll Analysis)
 * Sistema de análisis automático y detección de variaciones
 */

// ========== ANÁLISIS AUTOMÁTICO DE DATOS ==========

/**
 * Iniciar análisis de datos del cierre
 * @param {number} closureId - ID del cierre
 * @param {number} toleranceVariation - Tolerancia de variación (por defecto 30%)
 * @returns {Promise<Object>} Resultado del análisis
 */
export const startDataAnalysis = async (closureId, toleranceVariation = DEFAULT_TOLERANCES.SALARY_VARIATION) => {
  const response = await api.post(`${PAYROLL_ENDPOINTS.ANALYSIS}/start/${closureId}/`, {
    tolerance_variation: toleranceVariation
  });
  return response.data;
};

/**
 * Obtener análisis de datos de un cierre
 * @param {number} closureId - ID del cierre
 * @returns {Promise<Object>} Datos del análisis
 */
export const getDataAnalysis = async (closureId) => {
  const response = await api.get(PAYROLL_ENDPOINTS.ANALYSIS, {
    params: { closure: closureId }
  });
  return response.data;
};

/**
 * Obtener análisis completo temporal (comparaciones vs mes anterior)
 * @param {number} closureId - ID del cierre
 * @returns {Promise<Object>} Análisis completo temporal
 */
export const getCompleteTemporalAnalysis = async (closureId) => {
  const response = await api.get(`${PAYROLL_ENDPOINTS.ANALYSIS}/complete-temporal/${closureId}/`);
  return response.data;
};

// ========== INCIDENCIAS DE VARIACIÓN SALARIAL ==========

/**
 * Obtener incidencias de variación salarial
 * @param {number} closureId - ID del cierre
 * @param {Object} filters - Filtros opcionales
 * @returns {Promise<Array>} Lista de incidencias de variación
 */
export const getSalaryVariationIncidents = async (closureId, filters = {}) => {
  const params = { closure: closureId, ...filters };
  const response = await api.get(`${PAYROLL_ENDPOINTS.ANALYSIS}/salary-variations/`, { params });
  return response.data;
};

/**
 * Justificar incidencia de variación salarial
 * @param {number} incidentId - ID de la incidencia
 * @param {string} justification - Justificación de la variación
 * @returns {Promise<Object>} Incidencia actualizada
 */
export const justifySalaryVariationIncident = async (incidentId, justification) => {
  const response = await api.post(`${PAYROLL_ENDPOINTS.ANALYSIS}/salary-variations/${incidentId}/justify/`, {
    justification
  });
  return response.data;
};

/**
 * Aprobar incidencia de variación salarial
 * @param {number} incidentId - ID de la incidencia
 * @param {string} comment - Comentario de aprobación
 * @returns {Promise<Object>} Incidencia aprobada
 */
export const approveSalaryVariationIncident = async (incidentId, comment = '') => {
  const response = await api.post(`${PAYROLL_ENDPOINTS.ANALYSIS}/salary-variations/${incidentId}/approve/`, {
    comment
  });
  return response.data;
};

/**
 * Rechazar incidencia de variación salarial
 * @param {number} incidentId - ID de la incidencia
 * @param {string} comment - Comentario de rechazo
 * @returns {Promise<Object>} Incidencia rechazada
 */
export const rejectSalaryVariationIncident = async (incidentId, comment) => {
  const response = await api.post(`${PAYROLL_ENDPOINTS.ANALYSIS}/salary-variations/${incidentId}/reject/`, {
    comment
  });
  return response.data;
};

// ========== RESÚMENES DE VARIACIONES ==========

/**
 * Obtener resumen de incidencias de variación salarial
 * @param {number} closureId - ID del cierre
 * @returns {Promise<Object>} Resumen de variaciones
 */
export const getSalaryVariationsSummary = async (closureId) => {
  const response = await api.get(`${PAYROLL_ENDPOINTS.ANALYSIS}/salary-variations/summary/${closureId}/`);
  return response.data;
};

/**
 * Obtener resumen general de variaciones
 * @param {number} closureId - ID del cierre
 * @returns {Promise<Object>} Resumen de variaciones
 */
export const getVariationsSummary = async (closureId) => {
  const response = await api.get(`${PAYROLL_ENDPOINTS.ANALYSIS}/variations/summary/${closureId}/`);
  return response.data;
};

// ========== ANÁLISIS COMPARATIVO ==========

/**
 * Comparar datos de nómina entre períodos
 * @param {number} currentClosureId - ID del cierre actual
 * @param {number} previousClosureId - ID del cierre anterior
 * @returns {Promise<Object>} Comparación de datos
 */
export const compareClosures = async (currentClosureId, previousClosureId) => {
  const response = await api.post(`${PAYROLL_ENDPOINTS.ANALYSIS}/compare/`, {
    current_closure: currentClosureId,
    previous_closure: previousClosureId
  });
  return response.data;
};

/**
 * Obtener tendencias salariales por empleado
 * @param {number} closureId - ID del cierre
 * @param {number} employeeId - ID del empleado (opcional)
 * @returns {Promise<Object>} Tendencias salariales
 */
export const getSalaryTrends = async (closureId, employeeId = null) => {
  const params = { closure: closureId };
  if (employeeId) params.employee = employeeId;
  
  const response = await api.get(`${PAYROLL_ENDPOINTS.ANALYSIS}/salary-trends/`, { params });
  return response.data;
};

// ========== ANÁLISIS DE PATRONES ==========

/**
 * Detectar patrones anómalos en los datos
 * @param {number} closureId - ID del cierre
 * @param {Object} analysisConfig - Configuración del análisis
 * @returns {Promise<Object>} Patrones detectados
 */
export const detectAnomalousPatterns = async (closureId, analysisConfig = {}) => {
  const response = await api.post(`${PAYROLL_ENDPOINTS.ANALYSIS}/detect-patterns/${closureId}/`, analysisConfig);
  return response.data;
};

/**
 * Análisis de distribución salarial
 * @param {number} closureId - ID del cierre
 * @returns {Promise<Object>} Distribución salarial
 */
export const getSalaryDistribution = async (closureId) => {
  const response = await api.get(`${PAYROLL_ENDPOINTS.ANALYSIS}/salary-distribution/${closureId}/`);
  return response.data;
};

// ========== REPORTES DE ANÁLISIS ==========

/**
 * Generar reporte completo de análisis
 * @param {number} closureId - ID del cierre
 * @param {Object} reportConfig - Configuración del reporte
 * @returns {Promise<Object>} Reporte generado
 */
export const generateAnalysisReport = async (closureId, reportConfig = {}) => {
  const response = await api.post(`${PAYROLL_ENDPOINTS.ANALYSIS}/generate-report/${closureId}/`, reportConfig);
  return response.data;
};

/**
 * Exportar análisis a Excel
 * @param {number} closureId - ID del cierre
 * @param {string} analysisType - Tipo de análisis a exportar
 * @returns {Promise<Blob>} Archivo Excel
 */
export const exportAnalysisToExcel = async (closureId, analysisType = 'complete') => {
  const response = await api.get(`${PAYROLL_ENDPOINTS.ANALYSIS}/export/${closureId}/`, {
    params: { type: analysisType },
    responseType: 'blob'
  });
  return response.data;
};

// ========== CONFIGURACIÓN DE ANÁLISIS ==========

/**
 * Obtener configuración de análisis para un cliente
 * @param {number} clientId - ID del cliente
 * @returns {Promise<Object>} Configuración de análisis
 */
export const getAnalysisConfiguration = async (clientId) => {
  const response = await api.get(`${PAYROLL_ENDPOINTS.ANALYSIS}/configuration/${clientId}/`);
  return response.data;
};

/**
 * Actualizar configuración de análisis
 * @param {number} clientId - ID del cliente
 * @param {Object} configuration - Nueva configuración
 * @returns {Promise<Object>} Configuración actualizada
 */
export const updateAnalysisConfiguration = async (clientId, configuration) => {
  const response = await api.put(`${PAYROLL_ENDPOINTS.ANALYSIS}/configuration/${clientId}/`, configuration);
  return response.data;
};
