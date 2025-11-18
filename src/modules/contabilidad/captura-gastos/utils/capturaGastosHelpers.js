// src/modules/contabilidad/captura-gastos/utils/capturaGastosHelpers.js
import { VALIDATION_PATTERNS, CUENTAS_GLOBALES } from '../constants/capturaGastos.constants';

/**
 * Normaliza texto removiendo acentos y convirtiendo a minúsculas
 */
export const normalizar = (texto) => {
  if (!texto) return '';
  return texto
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '');
};

/**
 * Valida que el usuario tenga acceso al área de Contabilidad
 */
export const validarAccesoContabilidad = (usuario) => {
  if (!usuario || !usuario.areas || !Array.isArray(usuario.areas)) {
    return false;
  }

  return usuario.areas.some(area => {
    const areaNombre = typeof area === 'string' ? area : area.nombre;
    return normalizar(areaNombre) === 'contabilidad';
  });
};

/**
 * Valida formato de cuenta contable
 * @param {string} cuenta - Número de cuenta
 * @returns {boolean}
 */
export const validarCuentaContable = (cuenta) => {
  if (!cuenta) return false;
  
  const cuentaLimpia = cuenta.toString().trim();
  return VALIDATION_PATTERNS.CUENTA_CONTABLE.test(cuentaLimpia);
};

/**
 * Valida que todas las cuentas globales sean correctas
 * @param {Object} cuentas - Objeto con las cuentas globales
 * @returns {Object} - { valido: boolean, errores: string[] }
 */
export const validarCuentasGlobales = (cuentas) => {
  const errores = [];
  
  Object.entries(CUENTAS_GLOBALES).forEach(([key, fieldName]) => {
    const cuenta = cuentas[fieldName];
    if (!cuenta) {
      errores.push(`Falta la cuenta: ${key}`);
    } else if (!validarCuentaContable(cuenta)) {
      errores.push(`Formato inválido en cuenta ${key}: ${cuenta}`);
    }
  });

  return {
    valido: errores.length === 0,
    errores
  };
};

/**
 * Formatea número de cuenta contable
 * @param {string} cuenta - Número de cuenta
 * @returns {string} - Cuenta formateada
 */
export const formatearCuenta = (cuenta) => {
  if (!cuenta) return '';
  
  const cuentaStr = cuenta.toString().trim();
  
  // Si ya tiene guión, retornar como está
  if (cuentaStr.includes('-')) {
    return cuentaStr;
  }
  
  // Si tiene 7 dígitos sin guión, agregar guión
  if (cuentaStr.length === 7 && VALIDATION_PATTERNS.SOLO_NUMEROS.test(cuentaStr)) {
    return `${cuentaStr.substring(0, 4)}-${cuentaStr.substring(4)}`;
  }
  
  return cuentaStr;
};

/**
 * Descarga un blob como archivo
 * @param {Blob} blob - Blob a descargar
 * @param {string} filename - Nombre del archivo
 */
export const descargarBlob = (blob, filename) => {
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
};

/**
 * Extrae headers de Excel desde los resultados
 * @param {Object} resultados - Resultados del procesamiento
 * @returns {Array<string>} - Lista de headers
 */
export const extraerHeadersExcel = (resultados) => {
  if (!resultados || !resultados.headers_excel) {
    return [];
  }
  return resultados.headers_excel;
};

/**
 * Extrae centros de costo detectados
 * @param {Object} resultados - Resultados del procesamiento
 * @returns {Array<string>} - Lista de centros de costo
 */
export const extraerCentrosCosto = (resultados) => {
  if (!resultados || !resultados.centros_costo_detectados) {
    return [];
  }
  return resultados.centros_costo_detectados;
};

/**
 * Procesa mensaje de error de la API
 * @param {Error} error - Error de axios
 * @returns {string} - Mensaje de error procesado
 */
export const procesarErrorAPI = (error) => {
  if (error.response?.data?.error) {
    return error.response.data.error;
  }
  
  if (error.response?.data?.message) {
    return error.response.data.message;
  }
  
  if (error.message) {
    return error.message;
  }
  
  return 'Error desconocido al procesar el archivo';
};
