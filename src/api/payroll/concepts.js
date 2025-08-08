// src/api/payroll/concepts.js
import { api, PAYROLL_ENDPOINTS } from './config';

/**
 * API para gestión de conceptos de remuneración (Payroll Concepts)
 * Sistema para manejo de conceptos, clasificaciones y configuraciones
 */

// ========== CONCEPTOS DE REMUNERACIÓN ==========

/**
 * Obtener clasificaciones de un cliente (se cachea en Redis)
 * @param {number} clientId - ID del cliente
 * @returns {Promise<Array>} Array de conceptos con clasificaciones
 */
export const getClientClassifications = async (clientId) => {
  const response = await api.get(`${PAYROLL_ENDPOINTS.BASE}/remuneration-concepts/`, {
    params: { client_id: clientId }
  });
  return response.data; // Devuelve array de { concept_name, classification, hashtags }
};

/**
 * Guardar conceptos de remuneración
 * @param {number} clientId - ID del cliente
 * @param {Array} concepts - Lista de conceptos
 * @param {number} closureId - ID del cierre (opcional)
 * @returns {Promise<Object>} Conceptos guardados
 */
export const saveRemunerationConcepts = async (clientId, concepts, closureId = null) => {
  const payload = {
    client_id: clientId,
    concepts,
  };
  if (closureId) {
    payload.closure_id = closureId;
  }
  const response = await api.post(`${PAYROLL_ENDPOINTS.BASE}/concepts/`, payload);
  return response.data;
};

/**
 * Eliminar concepto de remuneración
 * @param {number} clientId - ID del cliente
 * @param {string} conceptName - Nombre del concepto
 * @returns {Promise<Object>} Confirmación de eliminación
 */
export const deleteRemunerationConcept = async (clientId, conceptName) => {
  const encoded = encodeURIComponent(conceptName);
  const response = await api.delete(
    `${PAYROLL_ENDPOINTS.BASE}/concepts/${clientId}/${encoded}/delete/`
  );
  return response.data;
};

/**
 * Obtener conceptos de remuneración por cierre
 * @param {number} closureId - ID del cierre
 * @returns {Promise<Array>} Conceptos del cierre
 */
export const getRemunerationConceptsByClosure = async (closureId) => {
  const response = await api.get(`${PAYROLL_ENDPOINTS.BASE}/concepts/closure/${closureId}/`);
  return response.data;
};

// ========== CONCEPTOS DE LIBRO DE REMUNERACIONES ==========

/**
 * Obtener conceptos del libro de remuneraciones
 * @param {number} clientId - ID del cliente
 * @param {string} period - Período en formato YYYY-MM
 * @returns {Promise<Array>} Conceptos del período
 */
export const getPayrollBookConcepts = async (clientId, period) => {
  const response = await api.get(`${PAYROLL_ENDPOINTS.BASE}/payroll-book/concepts/${clientId}/${period}/`);
  return response.data;
};

/**
 * Guardar clasificaciones del libro de remuneraciones
 * @param {number} closureId - ID del cierre
 * @param {Array} classifications - Clasificaciones
 * @returns {Promise<Object>} Clasificaciones guardadas
 */
export const savePayrollBookClassifications = async (closureId, classifications) => {
  const response = await api.post(`${PAYROLL_ENDPOINTS.BASE}/payroll-book/classify/${closureId}/`, { 
    classifications 
  });
  return response.data;
};

/**
 * Obtener progreso de clasificación de remuneraciones
 * @param {number} closureId - ID del cierre
 * @returns {Promise<Object>} Progreso de clasificación
 */
export const getRemunerationClassificationProgress = async (closureId) => {
  const response = await api.get(`${PAYROLL_ENDPOINTS.BASE}/payroll-book/classification-progress/${closureId}/`);
  return response.data;
};

// ========== CONCEPTOS PARA NOVEDADES ==========

/**
 * Obtener conceptos de remuneración para novedades
 * @param {number} clientId - ID del cliente
 * @returns {Promise<Array>} Conceptos disponibles para novedades
 */
export const getRemunerationConceptsForNovelties = async (clientId) => {
  const response = await api.get(`${PAYROLL_ENDPOINTS.BASE}/remuneration-concepts-novelties/`, {
    params: { client: clientId }
  });
  return response.data;
};

// ========== CLASIFICACIONES GENERALES ==========

/**
 * Obtener progreso de clasificación de todos los sets
 * @param {number} closureId - ID del cierre
 * @returns {Promise<Object>} Progreso general de clasificación
 */
export const getAllSetsClassificationProgress = async (closureId) => {
  const response = await api.get(`${PAYROLL_ENDPOINTS.BASE}/classification/progress-all-sets/${closureId}/`);
  return response.data;
};

// ========== TIPOS DE CONCEPTOS ==========

/**
 * Obtener tipos de conceptos disponibles
 * @returns {Promise<Array>} Tipos de conceptos
 */
export const getConceptTypes = async () => {
  const response = await api.get(`${PAYROLL_ENDPOINTS.BASE}/concept-types/`);
  return response.data;
};

/**
 * Crear nuevo tipo de concepto
 * @param {Object} conceptType - Datos del tipo de concepto
 * @returns {Promise<Object>} Tipo de concepto creado
 */
export const createConceptType = async (conceptType) => {
  const response = await api.post(`${PAYROLL_ENDPOINTS.BASE}/concept-types/`, conceptType);
  return response.data;
};

/**
 * Actualizar tipo de concepto
 * @param {number} typeId - ID del tipo
 * @param {Object} updateData - Datos a actualizar
 * @returns {Promise<Object>} Tipo actualizado
 */
export const updateConceptType = async (typeId, updateData) => {
  const response = await api.patch(`${PAYROLL_ENDPOINTS.BASE}/concept-types/${typeId}/`, updateData);
  return response.data;
};

/**
 * Eliminar tipo de concepto
 * @param {number} typeId - ID del tipo
 * @returns {Promise<Object>} Confirmación de eliminación
 */
export const deleteConceptType = async (typeId) => {
  const response = await api.delete(`${PAYROLL_ENDPOINTS.BASE}/concept-types/${typeId}/`);
  return response.data;
};

// ========== CONFIGURACIÓN DE CONCEPTOS POR CLIENTE ==========

/**
 * Obtener configuración de conceptos de un cliente
 * @param {number} clientId - ID del cliente
 * @returns {Promise<Object>} Configuración de conceptos
 */
export const getClientConceptConfiguration = async (clientId) => {
  const response = await api.get(`${PAYROLL_ENDPOINTS.BASE}/client-concept-config/${clientId}/`);
  return response.data;
};

/**
 * Actualizar configuración de conceptos de un cliente
 * @param {number} clientId - ID del cliente
 * @param {Object} configuration - Nueva configuración
 * @returns {Promise<Object>} Configuración actualizada
 */
export const updateClientConceptConfiguration = async (clientId, configuration) => {
  const response = await api.put(`${PAYROLL_ENDPOINTS.BASE}/client-concept-config/${clientId}/`, configuration);
  return response.data;
};

// ========== MAPEO AUTOMÁTICO DE CONCEPTOS ==========

/**
 * Sugerir clasificaciones automáticas basadas en histórico
 * @param {number} clientId - ID del cliente
 * @param {Array} concepts - Conceptos a clasificar
 * @returns {Promise<Array>} Sugerencias de clasificación
 */
export const suggestConceptClassifications = async (clientId, concepts) => {
  const response = await api.post(`${PAYROLL_ENDPOINTS.BASE}/suggest-classifications/`, {
    client_id: clientId,
    concepts
  });
  return response.data;
};

/**
 * Aplicar clasificaciones masivas
 * @param {number} clientId - ID del cliente
 * @param {Array} classifications - Clasificaciones a aplicar
 * @returns {Promise<Object>} Resultado de la aplicación
 */
export const applyBulkClassifications = async (clientId, classifications) => {
  const response = await api.post(`${PAYROLL_ENDPOINTS.BASE}/apply-bulk-classifications/`, {
    client_id: clientId,
    classifications
  });
  return response.data;
};

// ========== VALIDACIÓN DE CONCEPTOS ==========

/**
 * Validar consistencia de conceptos
 * @param {number} clientId - ID del cliente
 * @param {string} period - Período a validar
 * @returns {Promise<Object>} Resultado de la validación
 */
export const validateConceptConsistency = async (clientId, period) => {
  const response = await api.post(`${PAYROLL_ENDPOINTS.BASE}/validate-concepts/`, {
    client_id: clientId,
    period
  });
  return response.data;
};

/**
 * Obtener conceptos no clasificados
 * @param {number} clientId - ID del cliente
 * @param {number} closureId - ID del cierre (opcional)
 * @returns {Promise<Array>} Conceptos sin clasificar
 */
export const getUnclassifiedConcepts = async (clientId, closureId = null) => {
  const params = { client_id: clientId };
  if (closureId) params.closure_id = closureId;
  
  const response = await api.get(`${PAYROLL_ENDPOINTS.BASE}/unclassified-concepts/`, { params });
  return response.data;
};

// ========== HISTORIAL Y AUDITORÍA ==========

/**
 * Obtener historial de clasificaciones
 * @param {number} clientId - ID del cliente
 * @param {Object} filters - Filtros opcionales
 * @returns {Promise<Array>} Historial de clasificaciones
 */
export const getClassificationHistory = async (clientId, filters = {}) => {
  const response = await api.get(`${PAYROLL_ENDPOINTS.BASE}/classification-history/`, {
    params: { client_id: clientId, ...filters }
  });
  return response.data;
};

/**
 * Obtener cambios en conceptos entre períodos
 * @param {number} clientId - ID del cliente
 * @param {string} periodFrom - Período inicial
 * @param {string} periodTo - Período final
 * @returns {Promise<Object>} Cambios detectados
 */
export const getConceptChanges = async (clientId, periodFrom, periodTo) => {
  const response = await api.get(`${PAYROLL_ENDPOINTS.BASE}/concept-changes/`, {
    params: { 
      client_id: clientId, 
      period_from: periodFrom, 
      period_to: periodTo 
    }
  });
  return response.data;
};

// ========== EXPORTACIÓN E IMPORTACIÓN ==========

/**
 * Exportar configuración de conceptos
 * @param {number} clientId - ID del cliente
 * @returns {Promise<Blob>} Archivo de configuración
 */
export const exportConceptConfiguration = async (clientId) => {
  const response = await api.get(`${PAYROLL_ENDPOINTS.BASE}/export-concept-config/${clientId}/`, {
    responseType: 'blob'
  });
  return response.data;
};

/**
 * Importar configuración de conceptos
 * @param {number} clientId - ID del cliente
 * @param {File} configFile - Archivo de configuración
 * @returns {Promise<Object>} Resultado de la importación
 */
export const importConceptConfiguration = async (clientId, configFile) => {
  const formData = new FormData();
  formData.append('client_id', clientId);
  formData.append('config_file', configFile);
  
  const response = await api.post(`${PAYROLL_ENDPOINTS.BASE}/import-concept-config/`, formData, {
    headers: { "Content-Type": "multipart/form-data" }
  });
  return response.data;
};
