// src/utils/activityLogger.js
/**
 * ActivityLogger V1 - STUB DE TRANSICIÓN
 * 
 * Este archivo reemplaza temporalmente el sistema V1 para evitar errores
 * mientras migramos al sistema V2. Todas las funciones son stubs que no hacen nada.
 */

console.warn('⚠️ Usando ActivityLogger V1 stub - Migrar a V2');

// Stub class que no hace nada
class ActivityLoggerStub {
  constructor() {
    // No-op
  }

  async logModalOpen() { return Promise.resolve(); }
  async logModalClose() { return Promise.resolve(); }
  async logFileSelect() { return Promise.resolve(); }
  async logFileValidate() { return Promise.resolve(); }
  async logDownloadTemplate() { return Promise.resolve(); }
  async logViewClassification() { return Promise.resolve(); }
  async logConceptMap() { return Promise.resolve(); }
  async logSessionStart() { return Promise.resolve(); }
  async logSessionEnd() { return Promise.resolve(); }
  async logPollingStart() { return Promise.resolve(); }
  async logPollingStop() { return Promise.resolve(); }
  async logStateChange() { return Promise.resolve(); }
}

// Factory function stub
export function createActivityLogger(cierreId, tarjeta) {
  return new ActivityLoggerStub();
}

// Hook stub  
export function useActivityLogger(cierreId, tarjeta) {
  return new ActivityLoggerStub();
}

// Stub para otras funciones que puedan existir
export async function getActivityLogs() {
  return [];
}

export async function logActivity() {
  return Promise.resolve();
}