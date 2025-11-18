// src/modules/contabilidad/captura-gastos/api/capturaGastos.api.js
import api from '../../../../api/config';

/**
 * Leer headers del archivo Excel para detectar centros de costo
 * @param {File} archivo - Archivo Excel
 * @returns {Promise} Headers y centros de costo detectados
 */
export const leerHeadersExcel = async (archivo) => {
  const formData = new FormData();
  formData.append('archivo', archivo);

  const response = await api.post('/contabilidad/rindegastos/leer-headers/', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });

  return response.data;
};

/**
 * Iniciar procesamiento (Step 1) - Procesar archivo con parámetros
 * @param {File} archivo - Archivo Excel
 * @param {Object} mapeoCC - Mapeo de centros de costo
 * @param {Object} cuentasGlobales - Cuentas globales {cuentaIVA, cuentaGasto, cuentaProveedores}
 * @returns {Promise} Task ID y estado inicial
 */
export const iniciarProcesamiento = async (archivo, mapeoCC = {}, cuentasGlobales = {}) => {
  const formData = new FormData();
  formData.append('archivo', archivo);
  
  // Backend espera 'parametros_contables' como JSON string
  const payloadParam = {
    cuentasGlobales: {
      iva: cuentasGlobales.cuentaIVA || '',
      proveedores: cuentasGlobales.cuentaProveedores || '',
      gasto_default: cuentasGlobales.cuentaGasto || ''
    },
    mapeoCC: mapeoCC || {}
  };
  
  console.log('[RG API] Enviando parametros_contables:', payloadParam);
  formData.append('parametros_contables', JSON.stringify(payloadParam));
  
  // Fallback: campos individuales para compatibilidad
  formData.append('cuentaIva', cuentasGlobales.cuentaIVA || '');
  formData.append('cuentaProveedores', cuentasGlobales.cuentaProveedores || '');
  formData.append('cuentaGasto', cuentasGlobales.cuentaGasto || '');
  formData.append('cuenta_iva', cuentasGlobales.cuentaIVA || '');
  formData.append('cuenta_proveedores', cuentasGlobales.cuentaProveedores || '');
  formData.append('cuenta_gasto', cuentasGlobales.cuentaGasto || '');

  const response = await api.post('/contabilidad/rindegastos/step1/iniciar/', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });

  return response.data;
};

/**
 * Consultar estado del procesamiento (Step 1)
 * @param {string} taskId - ID de la tarea
 * @returns {Promise} Estado actual del procesamiento
 */
export const consultarEstado = async (taskId) => {
  const response = await api.get(`/contabilidad/rindegastos/step1/estado/${taskId}/`);
  return response.data;
};

/**
 * Descargar archivo procesado (Step 1)
 * @param {string} taskId - ID de la tarea
 * @returns {Promise<Blob>} Archivo Excel procesado
 */
export const descargarProcesado = async (taskId) => {
  const response = await api.get(`/contabilidad/rindegastos/step1/descargar/${taskId}/`, {
    responseType: 'blob',
  });
  return response.data;
};
