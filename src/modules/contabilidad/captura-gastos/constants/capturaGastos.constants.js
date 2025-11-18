// src/modules/contabilidad/captura-gastos/constants/capturaGastos.constants.js

/**
 * Estados del procesamiento
 */
export const PROCESSING_STATUS = {
  IDLE: 'idle',
  UPLOADING: 'uploading',
  PROCESSING: 'processing',
  SUCCESS: 'success',
  ERROR: 'error'
};

/**
 * Tipos de resultado
 */
export const RESULT_TYPES = {
  SUCCESS: 'success',
  WARNING: 'warning',
  ERROR: 'error'
};

/**
 * Configuración de archivos
 */
export const FILE_CONFIG = {
  MAX_SIZE_MB: 10,
  ACCEPTED_FORMATS: '.xlsx,.xls',
  SUPPORTED_TEXT: 'Formatos soportados: .xlsx, .xls'
};

/**
 * Mensajes de la aplicación
 */
export const MESSAGES = {
  NO_FILE: 'Por favor selecciona un archivo Excel',
  UPLOADING: 'Subiendo archivo...',
  PROCESSING: 'Procesando gastos...',
  SUCCESS: 'Archivo procesado exitosamente',
  ERROR_GENERIC: 'Error al procesar el archivo',
  VALIDATION_ERROR: 'Error de validación',
  FILE_TOO_LARGE: `El archivo excede el tamaño máximo de ${FILE_CONFIG.MAX_SIZE_MB}MB`
};

/**
 * Configuración de validación de cuentas
 */
export const VALIDATION_PATTERNS = {
  CUENTA_CONTABLE: /^\d{4,7}(-\d{3})?$/,
  SOLO_NUMEROS: /^\d+$/
};

/**
 * Nombres de cuentas globales requeridas
 */
export const CUENTAS_GLOBALES = {
  IVA: 'cuentaIVA',
  GASTO: 'cuentaGasto',
  PROVEEDORES: 'cuentaProveedores'
};

/**
 * Colores del tema
 */
export const THEME_COLORS = {
  PRIMARY: 'purple',
  SUCCESS: 'green',
  WARNING: 'yellow',
  ERROR: 'red',
  INFO: 'blue'
};
