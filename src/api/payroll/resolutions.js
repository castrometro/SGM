// src/api/payroll/resolutions.js
import { api, PAYROLL_ENDPOINTS } from './config';

/**
 * API para gestión de resoluciones de incidencias (Payroll Resolutions)
 * Sistema de seguimiento y gestión de resoluciones de problemas
 */

// ========== OPERACIONES BÁSICAS DE RESOLUCIONES ==========

/**
 * Crear una nueva resolución para una incidencia
 * @param {number} incidentId - ID de la incidencia
 * @param {Object} resolutionData - Datos de la resolución
 * @returns {Promise<Object>} Resolución creada
 */
export const createIncidentResolution = async (incidentId, resolutionData) => {
  const response = await api.post(PAYROLL_ENDPOINTS.RESOLUTIONS, {
    incident: incidentId,
    ...resolutionData
  });
  return response.data;
};

/**
 * Obtener una resolución específica
 * @param {number} resolutionId - ID de la resolución
 * @returns {Promise<Object>} Datos de la resolución
 */
export const getResolution = async (resolutionId) => {
  const response = await api.get(`${PAYROLL_ENDPOINTS.RESOLUTIONS}/${resolutionId}/`);
  return response.data;
};

/**
 * Actualizar una resolución
 * @param {number} resolutionId - ID de la resolución
 * @param {Object} updateData - Datos a actualizar
 * @returns {Promise<Object>} Resolución actualizada
 */
export const updateResolution = async (resolutionId, updateData) => {
  const response = await api.patch(`${PAYROLL_ENDPOINTS.RESOLUTIONS}/${resolutionId}/`, updateData);
  return response.data;
};

/**
 * Eliminar una resolución
 * @param {number} resolutionId - ID de la resolución
 * @returns {Promise<Object>} Confirmación de eliminación
 */
export const deleteResolution = async (resolutionId) => {
  const response = await api.delete(`${PAYROLL_ENDPOINTS.RESOLUTIONS}/${resolutionId}/`);
  return response.data;
};

// ========== HISTORIAL Y SEGUIMIENTO ==========

/**
 * Obtener historial de resoluciones de una incidencia
 * @param {number} incidentId - ID de la incidencia
 * @returns {Promise<Array>} Historial de resoluciones
 */
export const getIncidentResolutionHistory = async (incidentId) => {
  const response = await api.get(`${PAYROLL_ENDPOINTS.RESOLUTIONS}/incident-history/${incidentId}/`);
  return response.data;
};

/**
 * Obtener historial completo de un cierre
 * @param {number} closureId - ID del cierre
 * @returns {Promise<Array>} Historial de resoluciones del cierre
 */
export const getClosureResolutionHistory = async (closureId) => {
  const response = await api.get(`${PAYROLL_ENDPOINTS.RESOLUTIONS}/closure-history/${closureId}/`);
  return response.data;
};

/**
 * Obtener cronología de resoluciones
 * @param {number} incidentId - ID de la incidencia
 * @returns {Promise<Array>} Cronología ordenada de resoluciones
 */
export const getResolutionTimeline = async (incidentId) => {
  const response = await api.get(`${PAYROLL_ENDPOINTS.RESOLUTIONS}/timeline/${incidentId}/`);
  return response.data;
};

// ========== RESOLUCIONES POR USUARIO ==========

/**
 * Obtener resoluciones de un usuario
 * @param {number} userId - ID del usuario
 * @param {Object} filters - Filtros opcionales
 * @returns {Promise<Array>} Resoluciones del usuario
 */
export const getUserResolutions = async (userId, filters = {}) => {
  const response = await api.get(PAYROLL_ENDPOINTS.RESOLUTIONS, {
    params: { user: userId, ...filters }
  });
  return response.data;
};

/**
 * Obtener estadísticas de resoluciones por usuario
 * @param {number} userId - ID del usuario
 * @param {string} period - Período de análisis (opcional)
 * @returns {Promise<Object>} Estadísticas del usuario
 */
export const getUserResolutionStatistics = async (userId, period = null) => {
  const params = { user: userId, stats: true };
  if (period) params.period = period;
  
  const response = await api.get(PAYROLL_ENDPOINTS.RESOLUTIONS, { params });
  return response.data;
};

// ========== GESTIÓN DE TURNOS Y ASIGNACIONES ==========

/**
 * Obtener incidencias que requieren mi atención (turnos de conversación)
 * @returns {Promise<Array>} Incidencias de mi turno
 */
export const getMyTurnIncidents = async () => {
  const response = await api.get(`${PAYROLL_ENDPOINTS.RESOLUTIONS}/my-turn/`);
  return response.data;
};

/**
 * Asignar turno a usuario específico
 * @param {number} incidentId - ID de la incidencia
 * @param {number} userId - ID del usuario
 * @param {string} comment - Comentario de asignación
 * @returns {Promise<Object>} Resultado de la asignación
 */
export const assignTurnToUser = async (incidentId, userId, comment = '') => {
  const response = await api.post(`${PAYROLL_ENDPOINTS.RESOLUTIONS}/assign-turn/`, {
    incident_id: incidentId,
    user_id: userId,
    comment
  });
  return response.data;
};

/**
 * Transferir turno a otro usuario
 * @param {number} incidentId - ID de la incidencia
 * @param {number} toUserId - ID del usuario destino
 * @param {string} reason - Razón de la transferencia
 * @returns {Promise<Object>} Resultado de la transferencia
 */
export const transferTurn = async (incidentId, toUserId, reason) => {
  const response = await api.post(`${PAYROLL_ENDPOINTS.RESOLUTIONS}/transfer-turn/`, {
    incident_id: incidentId,
    to_user_id: toUserId,
    reason
  });
  return response.data;
};

// ========== TIPOS Y CATEGORÍAS DE RESOLUCIONES ==========

/**
 * Obtener tipos de resoluciones disponibles
 * @returns {Promise<Array>} Tipos de resoluciones
 */
export const getResolutionTypes = async () => {
  const response = await api.get(`${PAYROLL_ENDPOINTS.RESOLUTIONS}/types/`);
  return response.data;
};

/**
 * Obtener resoluciones por tipo
 * @param {string} resolutionType - Tipo de resolución
 * @param {Object} filters - Filtros adicionales
 * @returns {Promise<Array>} Resoluciones del tipo especificado
 */
export const getResolutionsByType = async (resolutionType, filters = {}) => {
  const response = await api.get(PAYROLL_ENDPOINTS.RESOLUTIONS, {
    params: { type: resolutionType, ...filters }
  });
  return response.data;
};

// ========== APROBACIONES Y VALIDACIONES ==========

/**
 * Aprobar una resolución
 * @param {number} resolutionId - ID de la resolución
 * @param {string} comment - Comentario de aprobación
 * @returns {Promise<Object>} Resolución aprobada
 */
export const approveResolution = async (resolutionId, comment = '') => {
  const response = await api.post(`${PAYROLL_ENDPOINTS.RESOLUTIONS}/${resolutionId}/approve/`, {
    comment
  });
  return response.data;
};

/**
 * Rechazar una resolución
 * @param {number} resolutionId - ID de la resolución
 * @param {string} comment - Comentario de rechazo
 * @returns {Promise<Object>} Resolución rechazada
 */
export const rejectResolution = async (resolutionId, comment) => {
  const response = await api.post(`${PAYROLL_ENDPOINTS.RESOLUTIONS}/${resolutionId}/reject/`, {
    comment
  });
  return response.data;
};

/**
 * Solicitar revisión de una resolución
 * @param {number} resolutionId - ID de la resolución
 * @param {string} reason - Razón de la solicitud de revisión
 * @returns {Promise<Object>} Resultado de la solicitud
 */
export const requestReview = async (resolutionId, reason) => {
  const response = await api.post(`${PAYROLL_ENDPOINTS.RESOLUTIONS}/${resolutionId}/request-review/`, {
    reason
  });
  return response.data;
};

// ========== COMENTARIOS Y COMUNICACIÓN ==========

/**
 * Agregar comentario a una resolución
 * @param {number} resolutionId - ID de la resolución
 * @param {string} comment - Comentario
 * @param {boolean} isPrivate - Si el comentario es privado
 * @returns {Promise<Object>} Comentario agregado
 */
export const addResolutionComment = async (resolutionId, comment, isPrivate = false) => {
  const response = await api.post(`${PAYROLL_ENDPOINTS.RESOLUTIONS}/${resolutionId}/comments/`, {
    comment,
    is_private: isPrivate
  });
  return response.data;
};

/**
 * Obtener comentarios de una resolución
 * @param {number} resolutionId - ID de la resolución
 * @returns {Promise<Array>} Comentarios de la resolución
 */
export const getResolutionComments = async (resolutionId) => {
  const response = await api.get(`${PAYROLL_ENDPOINTS.RESOLUTIONS}/${resolutionId}/comments/`);
  return response.data;
};

// ========== MÉTRICAS Y REPORTES ==========

/**
 * Obtener métricas de resoluciones
 * @param {Object} filters - Filtros para las métricas
 * @returns {Promise<Object>} Métricas de resoluciones
 */
export const getResolutionMetrics = async (filters = {}) => {
  const response = await api.get(`${PAYROLL_ENDPOINTS.RESOLUTIONS}/metrics/`, { params: filters });
  return response.data;
};

/**
 * Generar reporte de resoluciones
 * @param {Object} reportConfig - Configuración del reporte
 * @returns {Promise<Object>} Reporte generado
 */
export const generateResolutionReport = async (reportConfig) => {
  const response = await api.post(`${PAYROLL_ENDPOINTS.RESOLUTIONS}/generate-report/`, reportConfig);
  return response.data;
};

/**
 * Exportar resoluciones a Excel
 * @param {Object} exportConfig - Configuración de exportación
 * @returns {Promise<Blob>} Archivo Excel
 */
export const exportResolutionsToExcel = async (exportConfig = {}) => {
  const response = await api.get(`${PAYROLL_ENDPOINTS.RESOLUTIONS}/export/`, {
    params: exportConfig,
    responseType: 'blob'
  });
  return response.data;
};

// ========== PLANTILLAS DE RESOLUCIÓN ==========

/**
 * Obtener plantillas de resolución disponibles
 * @param {string} incidentType - Tipo de incidencia (opcional)
 * @returns {Promise<Array>} Plantillas disponibles
 */
export const getResolutionTemplates = async (incidentType = null) => {
  const params = incidentType ? { incident_type: incidentType } : {};
  const response = await api.get(`${PAYROLL_ENDPOINTS.RESOLUTIONS}/templates/`, { params });
  return response.data;
};

/**
 * Crear resolución desde plantilla
 * @param {number} incidentId - ID de la incidencia
 * @param {number} templateId - ID de la plantilla
 * @param {Object} customData - Datos personalizados
 * @returns {Promise<Object>} Resolución creada
 */
export const createResolutionFromTemplate = async (incidentId, templateId, customData = {}) => {
  const response = await api.post(`${PAYROLL_ENDPOINTS.RESOLUTIONS}/from-template/`, {
    incident_id: incidentId,
    template_id: templateId,
    custom_data: customData
  });
  return response.data;
};
