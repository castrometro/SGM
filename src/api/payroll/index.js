// src/api/payroll/index.js

/**
 * Payroll API - Sistema modular para gestión de nómina
 * Versión mejorada y reestructurada de la API de nómina
 * 
 * Módulos disponibles:
 * - closures: Gestión de cierres de nómina
 * - incidents: Sistema de incidencias
 * - analysis: Análisis de datos y variaciones
 * - files: Gestión de archivos y uploads
 * - discrepancies: Sistema de discrepancias
 * - resolutions: Gestión de resoluciones
 * - reports: Generación de reportes
 * - concepts: Conceptos y clasificaciones
 * - config: Configuración general
 */

// Exportar módulos principales
export * as closures from './closures';
export * as incidents from './incidents';
export * as analysis from './analysis';
export * as files from './files';
export * as discrepancies from './discrepancies';
export * as resolutions from './resolutions';
export * as reports from './reports';
export * as concepts from './concepts';

// Exportar configuración
export * from './config';

// Funciones de utilidad generales
import { api } from './config';

/**
 * Obtener estado general del sistema de payroll
 * @param {number} clientId - ID del cliente
 * @returns {Promise<Object>} Estado general del sistema
 */
export const getSystemStatus = async (clientId) => {
  const response = await api.get(`/payroll/system-status/${clientId}/`);
  return response.data;
};

/**
 * Obtener información del usuario actual
 * @returns {Promise<Object>} Información del usuario
 */
export const getCurrentUser = async () => {
  const response = await api.get('/payroll/current-user/');
  return response.data;
};

/**
 * Obtener configuración general de payroll
 * @returns {Promise<Object>} Configuración del sistema
 */
export const getPayrollConfiguration = async () => {
  const response = await api.get('/payroll/configuration/');
  return response.data;
};

/**
 * Ping de conectividad
 * @returns {Promise<Object>} Estado de conectividad
 */
export const ping = async () => {
  const response = await api.get('/payroll/ping/');
  return response.data;
};

/**
 * Obtener versión de la API
 * @returns {Promise<Object>} Información de versión
 */
export const getApiVersion = async () => {
  const response = await api.get('/payroll/version/');
  return response.data;
};

// Exportar como default un objeto con todos los módulos
export default {
  closures: require('./closures'),
  incidents: require('./incidents'),
  analysis: require('./analysis'),
  files: require('./files'),
  discrepancies: require('./discrepancies'),
  resolutions: require('./resolutions'),
  reports: require('./reports'),
  concepts: require('./concepts'),
  config: require('./config'),
  // Funciones utilitarias
  getSystemStatus,
  getCurrentUser,
  getPayrollConfiguration,
  ping,
  getApiVersion,
};
