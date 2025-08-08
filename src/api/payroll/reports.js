// src/api/payroll/reports.js
import { api, PAYROLL_ENDPOINTS } from './config';

/**
 * API para generación de reportes de nómina (Payroll Reports)
 * Sistema completo de reportes y visualización de datos
 */

// ========== REPORTES BÁSICOS ==========

/**
 * Generar reporte de resumen de cierre
 * @param {number} closureId - ID del cierre
 * @param {Object} config - Configuración del reporte
 * @returns {Promise<Object>} Reporte de resumen
 */
export const generateClosureSummaryReport = async (closureId, config = {}) => {
  const response = await api.post(`${PAYROLL_ENDPOINTS.REPORTS}/closure-summary/${closureId}/`, config);
  return response.data;
};

/**
 * Generar reporte de empleados
 * @param {number} closureId - ID del cierre
 * @param {Object} filters - Filtros para empleados
 * @returns {Promise<Object>} Reporte de empleados
 */
export const generateEmployeeReport = async (closureId, filters = {}) => {
  const response = await api.post(`${PAYROLL_ENDPOINTS.REPORTS}/employees/${closureId}/`, filters);
  return response.data;
};

/**
 * Generar reporte de conceptos de pago
 * @param {number} closureId - ID del cierre
 * @param {Object} config - Configuración del reporte
 * @returns {Promise<Object>} Reporte de conceptos
 */
export const generatePaymentConceptsReport = async (closureId, config = {}) => {
  const response = await api.post(`${PAYROLL_ENDPOINTS.REPORTS}/payment-concepts/${closureId}/`, config);
  return response.data;
};

// ========== REPORTES COMPARATIVOS ==========

/**
 * Generar reporte comparativo entre períodos
 * @param {number} currentClosureId - ID del cierre actual
 * @param {number} previousClosureId - ID del cierre anterior
 * @param {Object} config - Configuración de la comparación
 * @returns {Promise<Object>} Reporte comparativo
 */
export const generateComparativeReport = async (currentClosureId, previousClosureId, config = {}) => {
  const response = await api.post(`${PAYROLL_ENDPOINTS.REPORTS}/comparative/`, {
    current_closure: currentClosureId,
    previous_closure: previousClosureId,
    ...config
  });
  return response.data;
};

/**
 * Generar reporte de variaciones salariales
 * @param {number} closureId - ID del cierre
 * @param {Object} config - Configuración del reporte
 * @returns {Promise<Object>} Reporte de variaciones
 */
export const generateSalaryVariationsReport = async (closureId, config = {}) => {
  const response = await api.post(`${PAYROLL_ENDPOINTS.REPORTS}/salary-variations/${closureId}/`, config);
  return response.data;
};

/**
 * Generar reporte de tendencias históricas
 * @param {number} clientId - ID del cliente
 * @param {string} startPeriod - Período inicial (YYYY-MM)
 * @param {string} endPeriod - Período final (YYYY-MM)
 * @returns {Promise<Object>} Reporte de tendencias
 */
export const generateHistoricalTrendsReport = async (clientId, startPeriod, endPeriod) => {
  const response = await api.post(`${PAYROLL_ENDPOINTS.REPORTS}/historical-trends/`, {
    client_id: clientId,
    start_period: startPeriod,
    end_period: endPeriod
  });
  return response.data;
};

// ========== REPORTES DE CUMPLIMIENTO ==========

/**
 * Generar reporte de cumplimiento normativo
 * @param {number} closureId - ID del cierre
 * @param {Array} regulations - Normativas a validar
 * @returns {Promise<Object>} Reporte de cumplimiento
 */
export const generateComplianceReport = async (closureId, regulations = []) => {
  const response = await api.post(`${PAYROLL_ENDPOINTS.REPORTS}/compliance/${closureId}/`, {
    regulations
  });
  return response.data;
};

/**
 * Generar reporte de auditoría
 * @param {number} closureId - ID del cierre
 * @param {Object} auditConfig - Configuración de auditoría
 * @returns {Promise<Object>} Reporte de auditoría
 */
export const generateAuditReport = async (closureId, auditConfig = {}) => {
  const response = await api.post(`${PAYROLL_ENDPOINTS.REPORTS}/audit/${closureId}/`, auditConfig);
  return response.data;
};

// ========== REPORTES DE INCIDENCIAS ==========

/**
 * Generar reporte de incidencias
 * @param {number} closureId - ID del cierre
 * @param {Object} filters - Filtros para incidencias
 * @returns {Promise<Object>} Reporte de incidencias
 */
export const generateIncidentsReport = async (closureId, filters = {}) => {
  const response = await api.post(`${PAYROLL_ENDPOINTS.REPORTS}/incidents/${closureId}/`, filters);
  return response.data;
};

/**
 * Generar reporte de resoluciones
 * @param {number} closureId - ID del cierre
 * @param {Object} config - Configuración del reporte
 * @returns {Promise<Object>} Reporte de resoluciones
 */
export const generateResolutionsReport = async (closureId, config = {}) => {
  const response = await api.post(`${PAYROLL_ENDPOINTS.REPORTS}/resolutions/${closureId}/`, config);
  return response.data;
};

/**
 * Generar reporte de tiempos de resolución
 * @param {number} closureId - ID del cierre
 * @param {Object} config - Configuración del reporte
 * @returns {Promise<Object>} Reporte de tiempos
 */
export const generateResolutionTimesReport = async (closureId, config = {}) => {
  const response = await api.post(`${PAYROLL_ENDPOINTS.REPORTS}/resolution-times/${closureId}/`, config);
  return response.data;
};

// ========== REPORTES FINANCIEROS ==========

/**
 * Generar reporte de costos laborales
 * @param {number} closureId - ID del cierre
 * @param {Object} config - Configuración del reporte
 * @returns {Promise<Object>} Reporte de costos
 */
export const generateLaborCostsReport = async (closureId, config = {}) => {
  const response = await api.post(`${PAYROLL_ENDPOINTS.REPORTS}/labor-costs/${closureId}/`, config);
  return response.data;
};

/**
 * Generar reporte de provisiones
 * @param {number} closureId - ID del cierre
 * @param {Object} config - Configuración del reporte
 * @returns {Promise<Object>} Reporte de provisiones
 */
export const generateProvisionsReport = async (closureId, config = {}) => {
  const response = await api.post(`${PAYROLL_ENDPOINTS.REPORTS}/provisions/${closureId}/`, config);
  return response.data;
};

/**
 * Generar reporte de obligaciones laborales
 * @param {number} closureId - ID del cierre
 * @param {Object} config - Configuración del reporte
 * @returns {Promise<Object>} Reporte de obligaciones
 */
export const generateLaborObligationsReport = async (closureId, config = {}) => {
  const response = await api.post(`${PAYROLL_ENDPOINTS.REPORTS}/labor-obligations/${closureId}/`, config);
  return response.data;
};

// ========== REPORTES PERSONALIZADOS ==========

/**
 * Crear reporte personalizado
 * @param {Object} reportDefinition - Definición del reporte
 * @returns {Promise<Object>} Reporte creado
 */
export const createCustomReport = async (reportDefinition) => {
  const response = await api.post(`${PAYROLL_ENDPOINTS.REPORTS}/custom/`, reportDefinition);
  return response.data;
};

/**
 * Ejecutar reporte personalizado
 * @param {number} reportId - ID del reporte personalizado
 * @param {Object} parameters - Parámetros del reporte
 * @returns {Promise<Object>} Resultado del reporte
 */
export const executeCustomReport = async (reportId, parameters = {}) => {
  const response = await api.post(`${PAYROLL_ENDPOINTS.REPORTS}/custom/${reportId}/execute/`, parameters);
  return response.data;
};

/**
 * Obtener plantillas de reportes disponibles
 * @returns {Promise<Array>} Plantillas de reportes
 */
export const getReportTemplates = async () => {
  const response = await api.get(`${PAYROLL_ENDPOINTS.REPORTS}/templates/`);
  return response.data;
};

// ========== EXPORTACIÓN DE REPORTES ==========

/**
 * Exportar reporte a Excel
 * @param {number} reportId - ID del reporte
 * @param {Object} exportConfig - Configuración de exportación
 * @returns {Promise<Blob>} Archivo Excel
 */
export const exportReportToExcel = async (reportId, exportConfig = {}) => {
  const response = await api.get(`${PAYROLL_ENDPOINTS.REPORTS}/${reportId}/export/excel/`, {
    params: exportConfig,
    responseType: 'blob'
  });
  return response.data;
};

/**
 * Exportar reporte a PDF
 * @param {number} reportId - ID del reporte
 * @param {Object} exportConfig - Configuración de exportación
 * @returns {Promise<Blob>} Archivo PDF
 */
export const exportReportToPDF = async (reportId, exportConfig = {}) => {
  const response = await api.get(`${PAYROLL_ENDPOINTS.REPORTS}/${reportId}/export/pdf/`, {
    params: exportConfig,
    responseType: 'blob'
  });
  return response.data;
};

/**
 * Exportar reporte a CSV
 * @param {number} reportId - ID del reporte
 * @param {Object} exportConfig - Configuración de exportación
 * @returns {Promise<Blob>} Archivo CSV
 */
export const exportReportToCSV = async (reportId, exportConfig = {}) => {
  const response = await api.get(`${PAYROLL_ENDPOINTS.REPORTS}/${reportId}/export/csv/`, {
    params: exportConfig,
    responseType: 'blob'
  });
  return response.data;
};

// ========== GESTIÓN DE REPORTES ==========

/**
 * Obtener lista de reportes generados
 * @param {Object} filters - Filtros para reportes
 * @returns {Promise<Array>} Lista de reportes
 */
export const getGeneratedReports = async (filters = {}) => {
  const response = await api.get(PAYROLL_ENDPOINTS.REPORTS, { params: filters });
  return response.data;
};

/**
 * Obtener detalles de un reporte específico
 * @param {number} reportId - ID del reporte
 * @returns {Promise<Object>} Detalles del reporte
 */
export const getReportDetails = async (reportId) => {
  const response = await api.get(`${PAYROLL_ENDPOINTS.REPORTS}/${reportId}/`);
  return response.data;
};

/**
 * Eliminar reporte
 * @param {number} reportId - ID del reporte
 * @returns {Promise<Object>} Confirmación de eliminación
 */
export const deleteReport = async (reportId) => {
  const response = await api.delete(`${PAYROLL_ENDPOINTS.REPORTS}/${reportId}/`);
  return response.data;
};

/**
 * Programar generación automática de reporte
 * @param {Object} scheduleConfig - Configuración de programación
 * @returns {Promise<Object>} Programación creada
 */
export const scheduleReport = async (scheduleConfig) => {
  const response = await api.post(`${PAYROLL_ENDPOINTS.REPORTS}/schedule/`, scheduleConfig);
  return response.data;
};

// ========== DASHBOARDS Y VISUALIZACIONES ==========

/**
 * Obtener datos para dashboard de cierre
 * @param {number} closureId - ID del cierre
 * @returns {Promise<Object>} Datos del dashboard
 */
export const getClosureDashboardData = async (closureId) => {
  const response = await api.get(`${PAYROLL_ENDPOINTS.REPORTS}/dashboard/closure/${closureId}/`);
  return response.data;
};

/**
 * Obtener datos para dashboard de cliente
 * @param {number} clientId - ID del cliente
 * @param {string} period - Período opcional
 * @returns {Promise<Object>} Datos del dashboard
 */
export const getClientDashboardData = async (clientId, period = null) => {
  const params = period ? { period } : {};
  const response = await api.get(`${PAYROLL_ENDPOINTS.REPORTS}/dashboard/client/${clientId}/`, { params });
  return response.data;
};

/**
 * Obtener métricas KPI
 * @param {Object} filters - Filtros para métricas
 * @returns {Promise<Object>} Métricas KPI
 */
export const getKPIMetrics = async (filters = {}) => {
  const response = await api.get(`${PAYROLL_ENDPOINTS.REPORTS}/kpi/`, { params: filters });
  return response.data;
};
