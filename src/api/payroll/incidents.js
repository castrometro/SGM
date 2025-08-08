// src/api/payroll/incidents.js
import { api, PAYROLL_ENDPOINTS, INCIDENT_STATES } from './config';

/**
 * API para gestión de incidencias de nómina (Payroll Incidents)
 * Sistema mejorado y modular para el manejo de incidencias
 */

// ========== OPERACIONES BÁSICAS DE INCIDENCIAS ==========

/**
 * Obtener incidencias de un cierre
 * @param {number} closureId - ID del cierre
 * @param {Object} filters - Filtros opcionales
 * @returns {Promise<Array>} Lista de incidencias
 */
export const getClosureIncidents = async (closureId, filters = {}) => {
  console.log("🔍 [API] getClosureIncidents - Iniciando con:", { closureId, filters });
  
  const params = { closure: closureId, ...filters };
  console.log("🔍 [API] getClosureIncidents - Parámetros de la petición:", params);
  
  try {
    const response = await api.get(PAYROLL_ENDPOINTS.INCIDENTS, { params });
    console.log("✅ [API] getClosureIncidents - Respuesta exitosa:", response.data);
    return response.data;
  } catch (error) {
    console.error("❌ [API] getClosureIncidents - Error:", error);
    throw error;
  }
};

/**
 * Generar incidencias para un cierre
 * @param {number} closureId - ID del cierre
 * @param {Array} selectedClassifications - Clasificaciones seleccionadas (opcional)
 * @returns {Promise<Object>} Resultado de la generación
 */
export const generateClosureIncidents = async (closureId, selectedClassifications = null) => {
  const payload = { closure_id: closureId };
  
  if (selectedClassifications && selectedClassifications.length > 0) {
    payload.selected_classifications = selectedClassifications;
  }
  
  const response = await api.post(`${PAYROLL_ENDPOINTS.INCIDENTS}/generate/${closureId}/`, payload);
  return response.data;
};

/**
 * Obtener una incidencia específica
 * @param {number} incidentId - ID de la incidencia
 * @returns {Promise<Object>} Datos de la incidencia
 */
export const getIncident = async (incidentId) => {
  const response = await api.get(`${PAYROLL_ENDPOINTS.INCIDENTS}/${incidentId}/`);
  return response.data;
};

/**
 * Limpiar incidencias de un cierre (función de debug)
 * @param {number} closureId - ID del cierre
 * @returns {Promise<Object>} Confirmación de limpieza
 */
export const clearClosureIncidents = async (closureId) => {
  const response = await api.delete(`${PAYROLL_ENDPOINTS.INCIDENTS}/clear/${closureId}/`);
  return response.data;
};

/**
 * Vista previa de incidencias (sin guardar)
 * @param {number} closureId - ID del cierre
 * @returns {Promise<Array>} Vista previa de incidencias
 */
export const previewClosureIncidents = async (closureId) => {
  const response = await api.get(`${PAYROLL_ENDPOINTS.INCIDENTS}/preview/${closureId}/`);
  return response.data;
};

// ========== GESTIÓN DE ESTADOS DE INCIDENCIAS ==========

/**
 * Cambiar estado de una incidencia
 * @param {number} incidentId - ID de la incidencia
 * @param {string} state - Nuevo estado (usar INCIDENT_STATES)
 * @returns {Promise<Object>} Incidencia actualizada
 */
export const changeIncidentState = async (incidentId, state) => {
  const response = await api.patch(`${PAYROLL_ENDPOINTS.INCIDENTS}/${incidentId}/change-state/`, {
    state
  });
  return response.data;
};

/**
 * Asignar usuario a una incidencia
 * @param {number} incidentId - ID de la incidencia
 * @param {number} userId - ID del usuario
 * @returns {Promise<Object>} Incidencia actualizada
 */
export const assignUserToIncident = async (incidentId, userId) => {
  const response = await api.patch(`${PAYROLL_ENDPOINTS.INCIDENTS}/${incidentId}/assign-user/`, {
    user_id: userId
  });
  return response.data;
};

/**
 * Aprobar incidencia (flujo de conversación)
 * @param {number} incidentId - ID de la incidencia
 * @param {string} comment - Comentario de aprobación
 * @returns {Promise<Object>} Resultado de la aprobación
 */
export const approveIncident = async (incidentId, comment = '') => {
  const response = await api.post(`${PAYROLL_ENDPOINTS.INCIDENTS}/${incidentId}/approve/`, {
    comment
  });
  return response.data;
};

/**
 * Rechazar incidencia (flujo de conversación)
 * @param {number} incidentId - ID de la incidencia
 * @param {string} comment - Comentario de rechazo
 * @returns {Promise<Object>} Resultado del rechazo
 */
export const rejectIncident = async (incidentId, comment) => {
  const response = await api.post(`${PAYROLL_ENDPOINTS.INCIDENTS}/${incidentId}/reject/`, {
    comment
  });
  return response.data;
};

/**
 * Crear consulta sobre incidencia (supervisor)
 * @param {number} incidentId - ID de la incidencia
 * @param {string} comment - Comentario de consulta
 * @returns {Promise<Object>} Resultado de la consulta
 */
export const consultIncident = async (incidentId, comment) => {
  const response = await api.post(`${PAYROLL_ENDPOINTS.INCIDENTS}/${incidentId}/consult/`, {
    comment
  });
  return response.data;
};

// ========== RESÚMENES Y ESTADÍSTICAS ==========

/**
 * Obtener resumen de incidencias de un cierre
 * @param {number} closureId - ID del cierre
 * @returns {Promise<Object>} Resumen de incidencias
 */
export const getIncidentsSummary = async (closureId) => {
  console.log("🔍 [API] getIncidentsSummary - Iniciando para cierre:", closureId);
  
  try {
    const response = await api.get(`${PAYROLL_ENDPOINTS.INCIDENTS}/summary/${closureId}/`);
    console.log("✅ [API] getIncidentsSummary - Respuesta exitosa:", response.data);
    return response.data;
  } catch (error) {
    console.error("❌ [API] getIncidentsSummary - Error:", error);
    throw error;
  }
};

/**
 * Obtener estado de incidencias de un cierre
 * @param {number} closureId - ID del cierre
 * @returns {Promise<Object>} Estado de incidencias
 */
export const getClosureIncidentsState = async (closureId) => {
  console.log("🔍 [API] getClosureIncidentsState - Iniciando para cierre:", closureId);
  
  try {
    const response = await api.get(`${PAYROLL_ENDPOINTS.INCIDENTS}/state/${closureId}/`);
    console.log("✅ [API] getClosureIncidentsState - Respuesta exitosa:", response.data);
    return response.data;
  } catch (error) {
    console.error("❌ [API] getClosureIncidentsState - Error:", error);
    throw error;
  }
};

/**
 * Obtener progreso de incidencias
 * @param {number} closureId - ID del cierre
 * @returns {Promise<Object>} Progreso de incidencias
 */
export const getIncidentsProgress = async (closureId) => {
  const response = await api.get(`${PAYROLL_ENDPOINTS.INCIDENTS}/progress/${closureId}/`);
  return response.data;
};

/**
 * Obtener estadísticas generales de incidencias
 * @param {Object} filters - Filtros opcionales
 * @returns {Promise<Object>} Estadísticas de incidencias
 */
export const getIncidentsStatistics = async (filters = {}) => {
  const response = await api.get(PAYROLL_ENDPOINTS.INCIDENTS, { 
    params: { ...filters, stats: true } 
  });
  return response.data;
};

// ========== INCIDENCIAS ASIGNADAS AL USUARIO ==========

/**
 * Obtener incidencias que requieren mi atención (según turnos de conversación)
 * @returns {Promise<Array>} Incidencias de mi turno
 */
export const getMyTurnIncidents = async () => {
  const response = await api.get(`${PAYROLL_ENDPOINTS.INCIDENTS}/my-turn/`);
  return response.data;
};

// ========== FUNCIONES DE DESARROLLO ==========

/**
 * ⚠️ DESARROLLO ÚNICAMENTE - Limpiar incidencias para testing
 * @param {number} closureId - ID del cierre
 * @returns {Promise<Object>} Confirmación de limpieza
 */
export const devClearIncidents = async (closureId) => {
  const response = await api.post(`${PAYROLL_ENDPOINTS.INCIDENTS}/dev-clear/${closureId}/`);
  return response.data;
};

// ========== EXPORTACIÓN Y UTILIDADES ==========

/**
 * Exportar incidencias a Excel
 * @param {number} closureId - ID del cierre
 * @returns {Promise<Blob>} Archivo Excel
 */
export const exportIncidentsToExcel = async (closureId) => {
  const response = await api.get(`${PAYROLL_ENDPOINTS.INCIDENTS}/export/${closureId}/`, {
    responseType: 'blob'
  });
  return response.data;
};

/**
 * Obtener categorías de incidencias disponibles
 * @returns {Promise<Array>} Categorías de incidencias
 */
export const getIncidentCategories = async () => {
  const response = await api.get(`${PAYROLL_ENDPOINTS.INCIDENTS}/categories/`);
  return response.data;
};

/**
 * Lanzar generación de incidencias desde el cierre
 * @param {number} closureId - ID del cierre
 * @returns {Promise<Object>} Resultado del lanzamiento
 */
export const launchIncidentsGeneration = async (closureId) => {
  const response = await api.post(`${PAYROLL_ENDPOINTS.CLOSURES}/${closureId}/launch-incidents-generation/`);
  return response.data;
};
