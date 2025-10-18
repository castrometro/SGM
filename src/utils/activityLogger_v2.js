// src/utils/activityLogger_v2.js
/**
 * Activity Logger V2 - Sistema Unificado
 * 
 * Diseño:
 * - API simplificada para usar desde cualquier componente
 * - Compatible con el backend ActivityEvent V2
 * - Sin estado complejo, solo funciones puras
 * - Fácil de habilitar/deshabilitar
 */

import api from '../api/config';

// 🔧 Configuración
const CONFIG = {
  enabled: true,  // ← Activar/desactivar logging
  endpoint: '/nomina/activity-log/log/',
  debug: true,  // Logs en consola para debugging
};

/**
 * Función principal para registrar actividad
 */
export async function logActivity({
  clienteId,
  cierreId = '',      // ✅ NUEVO: ID del cierre
  eventType = 'nomina',
  action,
  resourceType = 'general',
  resourceId = '',
  details = {},
  sessionId = ''
}) {
  if (!CONFIG.enabled) {
    if (CONFIG.debug) {
      console.log(`🔍 [ActivityV2] ${eventType}.${action}`, { resourceType, details });
    }
    return { success: true, disabled: true };
  }

  if (!clienteId || !action) {
    console.warn('⚠️ [ActivityV2] clienteId y action son requeridos');
    return { success: false, error: 'Faltan parámetros' };
  }

  const payload = {
    cliente_id: clienteId,
    cierre_id: cierreId || resourceId,  // ✅ Enviar cierre_id al backend
    event_type: eventType,
    action: action,
    resource_type: resourceType,
    resource_id: String(cierreId || resourceId),  // ✅ Usar cierreId como resourceId si está disponible
    details: details,
    session_id: sessionId || generateSessionId(),
  };

  try {
    if (CONFIG.debug) {
      console.log('📤 [ActivityV2]', payload);
    }

    const response = await api.post(CONFIG.endpoint, payload);

    if (CONFIG.debug) {
      console.log('✅ [ActivityV2] OK');
    }

    return response.data;
  } catch (error) {
    console.error('❌ [ActivityV2]', error.message);
    return { success: false, error: error.message };
  }
}

/**
 * Hook para componentes funcionales
 */
export function useActivityLogger(clienteId, cierreId = '') {
  const log = async (action, resourceType = 'general', details = {}) => {
    return logActivity({
      clienteId,
      cierreId,      // ✅ Pasar cierreId
      eventType: 'nomina',
      action,
      resourceType,
      resourceId: cierreId,  // ✅ Usar cierreId como resourceId
      details,
    });
  };

  return { log };
}

/**
 * Clase para componentes de clase
 */
export class ActivityLogger {
  constructor(clienteId, cierreId = '') {
    this.clienteId = clienteId;
    this.cierreId = cierreId;      // ✅ Guardar cierreId
    this.resourceId = cierreId;     // ✅ Mantener compatibilidad
  }

  async log(action, resourceType = 'general', details = {}) {
    return logActivity({
      clienteId: this.clienteId,
      cierreId: this.cierreId,      // ✅ Pasar cierreId
      eventType: 'nomina',
      action,
      resourceType,
      resourceId: this.cierreId,    // ✅ Usar cierreId como resourceId
      details,
    });
  }

  async logModalOpen(tarjeta, details = {}) {
    return this.log('modal_opened', tarjeta, details);
  }

  async logModalClose(tarjeta, details = {}) {
    return this.log('modal_closed', tarjeta, details);
  }

  async logFileSelect(tarjeta, filename, filesize) {
    return this.log('file_selected', tarjeta, { filename, filesize });
  }

  async logFileUpload(tarjeta, filename) {
    return this.log('file_upload', tarjeta, { filename });
  }

  async logSessionStart() {
    return this.log('session_started', 'cierre');
  }

  async logSessionEnd(duration) {
    return this.log('session_ended', 'cierre', { duration_seconds: duration });
  }

  async logPollingStart(interval) {
    return this.log('polling_started', 'cierre', { interval_seconds: interval });
  }

  async logPollingStop(reason) {
    return this.log('polling_stopped', 'cierre', { reason });
  }
}

export function createActivityLogger(clienteId, cierreId) {
  return new ActivityLogger(clienteId, cierreId);  // ✅ Pasar cierreId en lugar de resourceId
}

let sessionIdCache = null;
function generateSessionId() {
  if (!sessionIdCache) {
    sessionIdCache = `s_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }
  return sessionIdCache;
}

export function enableActivityLogging() {
  CONFIG.enabled = true;
  console.log('✅ Activity V2 ON');
}

export function disableActivityLogging() {
  CONFIG.enabled = false;
  console.log('⛔ Activity V2 OFF');
}

export default {
  logActivity,
  useActivityLogger,
  ActivityLogger,
  createActivityLogger,
  enableActivityLogging,
  disableActivityLogging,
};
