// src/api/payroll/files.js
import { api, PAYROLL_ENDPOINTS, FILE_TYPES } from './config';

/**
 * API para gestión de archivos de nómina (Payroll Files)
 * Sistema modular para upload, procesamiento y gestión de archivos
 */

// ========== PLANTILLAS DE ARCHIVOS ==========

/**
 * Descargar plantilla de libro de remuneraciones
 * @returns {string} URL de descarga de la plantilla
 */
export const downloadPayrollBookTemplate = () => {
  return `${api.defaults.baseURL}${PAYROLL_ENDPOINTS.TEMPLATES}/payroll-book/`;
};

/**
 * Descargar plantilla de movimientos del mes
 * @returns {string} URL de descarga de la plantilla
 */
export const downloadMonthlyMovementsTemplate = () => {
  return `${api.defaults.baseURL}${PAYROLL_ENDPOINTS.TEMPLATES}/monthly-movements/`;
};

/**
 * Descargar plantilla de novedades
 * @returns {string} URL de descarga de la plantilla
 */
export const downloadNoveltiesTemplate = () => {
  return `${api.defaults.baseURL}${PAYROLL_ENDPOINTS.TEMPLATES}/novelties/`;
};

/**
 * Descargar plantilla de finiquitos
 * @returns {string} URL de descarga de la plantilla
 */
export const downloadSettlementsTemplate = () => {
  return `${api.defaults.baseURL}${PAYROLL_ENDPOINTS.TEMPLATES}/settlements/`;
};

/**
 * Descargar plantilla de incidencias
 * @returns {string} URL de descarga de la plantilla
 */
export const downloadIncidentsTemplate = () => {
  return `${api.defaults.baseURL}${PAYROLL_ENDPOINTS.TEMPLATES}/incidents/`;
};

/**
 * Descargar plantilla de ingresos
 * @returns {string} URL de descarga de la plantilla
 */
export const downloadEntriesTemplate = () => {
  return `${api.defaults.baseURL}${PAYROLL_ENDPOINTS.TEMPLATES}/entries/`;
};

// ========== LIBRO DE REMUNERACIONES ==========

/**
 * Subir libro de remuneraciones
 * @param {number} closureId - ID del cierre
 * @param {File} file - Archivo a subir
 * @returns {Promise<Object>} Resultado del upload
 */
export const uploadPayrollBook = async (closureId, file) => {
  console.log('🌐 API uploadPayrollBook LLAMADA:', {
    timestamp: new Date().toISOString(),
    closureId,
    fileName: file.name,
    fileSize: file.size,
    stackTrace: new Error().stack.split('\n').slice(0, 8).join('\n')
  });

  const formData = new FormData();
  formData.append("closure", closureId);
  formData.append("file", file);

  const response = await api.post(`${PAYROLL_ENDPOINTS.FILES}/payroll-books/`, formData, {
    headers: {
      "Content-Type": "multipart/form-data"
    }
  });
  
  console.log('🌐 API uploadPayrollBook RESPUESTA:', {
    timestamp: new Date().toISOString(),
    status: response.status,
    data: response.data
  });
  
  return response.data;
};

/**
 * Obtener estado del libro de remuneraciones
 * @param {number} closureId - ID del cierre
 * @returns {Promise<Object>} Estado del libro
 */
export const getPayrollBookStatus = async (closureId) => {
  const response = await api.get(`${PAYROLL_ENDPOINTS.FILES}/payroll-books/status/${closureId}/`);
  return response.data;
};

/**
 * Procesar libro de remuneraciones
 * @param {number} bookId - ID del libro
 * @returns {Promise<Object>} Resultado del procesamiento
 */
export const processPayrollBook = async (bookId) => {
  const response = await api.post(`${PAYROLL_ENDPOINTS.FILES}/payroll-books/${bookId}/process/`);
  return response.data;
};

/**
 * Eliminar libro de remuneraciones
 * @param {number} bookId - ID del libro
 * @returns {Promise<Object>} Confirmación de eliminación
 */
export const deletePayrollBook = async (bookId) => {
  const response = await api.delete(`${PAYROLL_ENDPOINTS.FILES}/payroll-books/${bookId}/`);
  return response.data;
};

// ========== MOVIMIENTOS MENSUALES ==========

/**
 * Obtener estado de movimientos del mes
 * @param {number} closureId - ID del cierre
 * @returns {Promise<Object>} Estado de movimientos
 */
export const getMonthlyMovementsStatus = async (closureId) => {
  const response = await api.get(`${PAYROLL_ENDPOINTS.FILES}/monthly-movements/status/${closureId}/`);
  return response.data;
};

/**
 * Subir movimientos del mes
 * @param {number} closureId - ID del cierre
 * @param {FormData} formData - Datos del formulario con el archivo
 * @returns {Promise<Object>} Resultado del upload
 */
export const uploadMonthlyMovements = async (closureId, formData) => {
  const response = await api.post(`${PAYROLL_ENDPOINTS.FILES}/monthly-movements/upload/${closureId}/`, formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
  return response.data;
};

/**
 * Eliminar movimientos del mes
 * @param {number} movementId - ID del movimiento
 * @returns {Promise<Object>} Confirmación de eliminación
 */
export const deleteMonthlyMovements = async (movementId) => {
  const response = await api.delete(`${PAYROLL_ENDPOINTS.FILES}/monthly-movements/${movementId}/`);
  return response.data;
};

// ========== ARCHIVOS DEL ANALISTA ==========

/**
 * Subir archivo del analista
 * @param {number} closureId - ID del cierre
 * @param {string} fileType - Tipo de archivo (usar FILE_TYPES)
 * @param {FormData} formData - Datos del formulario con el archivo
 * @returns {Promise<Object>} Resultado del upload
 */
export const uploadAnalystFile = async (closureId, fileType, formData) => {
  const response = await api.post(`${PAYROLL_ENDPOINTS.FILES}/analyst-files/upload/${closureId}/${fileType}/`, formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
  return response.data;
};

/**
 * Obtener estado de archivo del analista
 * @param {number} closureId - ID del cierre
 * @param {string} fileType - Tipo de archivo
 * @returns {Promise<Object>} Estado del archivo
 */
export const getAnalystFileStatus = async (closureId, fileType) => {
  const response = await api.get(`${PAYROLL_ENDPOINTS.FILES}/analyst-files/`, {
    params: { closure: closureId, file_type: fileType }
  });
  return response.data;
};

/**
 * Reprocesar archivo del analista
 * @param {number} fileId - ID del archivo
 * @returns {Promise<Object>} Resultado del reprocesamiento
 */
export const reprocessAnalystFile = async (fileId) => {
  const response = await api.post(`${PAYROLL_ENDPOINTS.FILES}/analyst-files/${fileId}/reprocess/`);
  return response.data;
};

/**
 * Eliminar archivo del analista
 * @param {number} fileId - ID del archivo
 * @returns {Promise<Object>} Confirmación de eliminación
 */
export const deleteAnalystFile = async (fileId) => {
  const response = await api.delete(`${PAYROLL_ENDPOINTS.FILES}/analyst-files/${fileId}/`);
  return response.data;
};

// ========== ARCHIVOS DE NOVEDADES ==========

/**
 * Subir archivo de novedades
 * @param {number} closureId - ID del cierre
 * @param {FormData} formData - Datos del formulario con el archivo
 * @returns {Promise<Object>} Resultado del upload
 */
export const uploadNoveltiesFile = async (closureId, formData) => {
  const response = await api.post(`${PAYROLL_ENDPOINTS.FILES}/novelties/upload/${closureId}/`, formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
  return response.data;
};

/**
 * Obtener estado de archivo de novedades
 * @param {number} closureId - ID del cierre
 * @returns {Promise<Object>} Estado del archivo
 */
export const getNoveltiesFileStatus = async (closureId) => {
  const response = await api.get(`${PAYROLL_ENDPOINTS.FILES}/novelties/status/${closureId}/`);
  return response.data;
};

/**
 * Reprocesar archivo de novedades
 * @param {number} fileId - ID del archivo
 * @returns {Promise<Object>} Resultado del reprocesamiento
 */
export const reprocessNoveltiesFile = async (fileId) => {
  const response = await api.post(`${PAYROLL_ENDPOINTS.FILES}/novelties/${fileId}/reprocess/`);
  return response.data;
};

/**
 * Eliminar archivo de novedades
 * @param {number} fileId - ID del archivo
 * @returns {Promise<Object>} Confirmación de eliminación
 */
export const deleteNoveltiesFile = async (fileId) => {
  const response = await api.delete(`${PAYROLL_ENDPOINTS.FILES}/novelties/${fileId}/`);
  return response.data;
};

// ========== GESTIÓN DE HEADERS EN NOVEDADES ==========

/**
 * Obtener headers de archivo de novedades
 * @param {number} fileId - ID del archivo
 * @returns {Promise<Array>} Headers del archivo
 */
export const getNoveltiesFileHeaders = async (fileId) => {
  const response = await api.get(`${PAYROLL_ENDPOINTS.FILES}/novelties/${fileId}/headers/`);
  return response.data;
};

/**
 * Mapear headers de novedades
 * @param {number} fileId - ID del archivo
 * @param {Array} mappings - Mapeos de headers
 * @returns {Promise<Object>} Resultado del mapeo
 */
export const mapNoveltiesHeaders = async (fileId, mappings) => {
  const payload = mappings.map(m => ({
    ...m,
    concept_book_id: m.concept_book_id ?? null,
  }));
  const response = await api.post(
    `${PAYROLL_ENDPOINTS.FILES}/novelties/${fileId}/map-headers/`,
    { mappings: payload }
  );
  return response.data;
};

/**
 * Procesamiento final de novedades
 * @param {number} fileId - ID del archivo
 * @returns {Promise<Object>} Resultado del procesamiento
 */
export const processFinalNovelties = async (fileId) => {
  const response = await api.post(`${PAYROLL_ENDPOINTS.FILES}/novelties/${fileId}/process-final/`);
  return response.data;
};

// ========== CONCEPTOS DE REMUNERACIÓN ==========

/**
 * Obtener conceptos de libro de remuneraciones
 * @param {number} clientId - ID del cliente
 * @param {string} period - Período
 * @returns {Promise<Array>} Conceptos del período
 */
export const getPayrollBookConcepts = async (clientId, period) => {
  const response = await api.get(`${PAYROLL_ENDPOINTS.FILES}/payroll-books/concepts/${clientId}/${period}/`);
  return response.data;
};

/**
 * Obtener conceptos de remuneración para novedades
 * @param {number} clientId - ID del cliente
 * @returns {Promise<Array>} Conceptos disponibles
 */
export const getRemunerationConceptsForNovelties = async (clientId) => {
  const response = await api.get(`${PAYROLL_ENDPOINTS.FILES}/remuneration-concepts-novelties/`, {
    params: { client: clientId }
  });
  return response.data;
};

// ========== LOGS DE UPLOAD ==========

/**
 * Obtener estado del upload log
 * @param {number} uploadLogId - ID del upload log
 * @returns {Promise<Object>} Estado del upload
 */
export const getUploadLogStatus = async (uploadLogId) => {
  const response = await api.get(`${PAYROLL_ENDPOINTS.UPLOAD_LOGS}/${uploadLogId}/status/`);
  return response.data;
};

// ========== PROGRESO Y CLASIFICACIONES ==========

/**
 * Obtener progreso de clasificación de todos los sets
 * @param {number} closureId - ID del cierre
 * @returns {Promise<Object>} Progreso de clasificación
 */
export const getAllSetsClassificationProgress = async (closureId) => {
  const response = await api.get(`${PAYROLL_ENDPOINTS.FILES}/classification/progress-all-sets/${closureId}/`);
  return response.data;
};

/**
 * Obtener progreso de clasificación de remuneraciones
 * @param {number} closureId - ID del cierre
 * @returns {Promise<Object>} Progreso de clasificación
 */
export const getRemunerationClassificationProgress = async (closureId) => {
  const response = await api.get(`${PAYROLL_ENDPOINTS.FILES}/payroll-books/classification-progress/${closureId}/`);
  return response.data;
};
