// src/api/payroll/config.js
import api from "../config";

/**
 * Configuración base para la API de Payroll
 * Version mejorada y modular de la API de Nómina
 */

// Configuración de endpoints base
export const PAYROLL_ENDPOINTS = {
  BASE: '/payroll',
  CLOSURES: '/payroll/closures',
  INCIDENTS: '/payroll/incidents',
  ANALYSIS: '/payroll/analysis',
  FILES: '/payroll/files',
  REPORTS: '/payroll/reports',
  DISCREPANCIES: '/payroll/discrepancies',
  RESOLUTIONS: '/payroll/resolutions',
  UPLOAD_LOGS: '/payroll/upload-logs',
  TEMPLATES: '/payroll/templates',
};

// Configuración de estados de cierre
export const CLOSURE_STATES = {
  PENDING: 'pending',
  IN_PROGRESS: 'in_progress',
  REVIEW: 'review',
  COMPLETED: 'completed',
  REJECTED: 'rejected',
};

// Configuración de estados de incidencias
export const INCIDENT_STATES = {
  PENDING: 'pending',
  IN_PROGRESS: 'in_progress',
  RESOLVED: 'resolved',
  APPROVED: 'approved',
  REJECTED: 'rejected',
};

// Configuración de tipos de archivos
export const FILE_TYPES = {
  PAYROLL_BOOK: 'payroll_book',
  MONTHLY_MOVEMENTS: 'monthly_movements',
  ANALYST_FILES: 'analyst_files',
  NOVELTIES: 'novelties',
  SETTLEMENTS: 'settlements',
  INCIDENTS: 'incidents',
  ENTRIES: 'entries',
};

// Configuración de tolerancias por defecto
export const DEFAULT_TOLERANCES = {
  SALARY_VARIATION: 30, // Porcentaje
  AMOUNT_THRESHOLD: 1000, // Monto mínimo para alertas
};

export { api };
