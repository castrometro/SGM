// src/utils/activityLogger_v2.js
/**
 * Activity Logger V2 - Sistema Simplificado
 * 
 * Principios:
 * - Un solo punto de entrada
 * - Configuración mínima  
 * - Sin dependencias complejas
 * - Fácil de usar en cualquier componente
 */

// 🔧 Configuración global
const CONFIG = {
  enabled: false,  // ← Principal switch on/off
  endpoint: '/api/activity/',
  batchMode: true,  // Enviar en lotes para mejor performance
  batchSize: 10,
  batchTimeout: 5000, // 5 segundos
  debug: false,
};

// 🗂️ Buffer para modo batch
let eventBuffer = [];
let batchTimer = null;

/**
 * Logger principal - Función global única
 */
export function logActivity(cierreId, seccion, evento, datos = {}) {
  // Si está deshabilitado, solo debug
  if (!CONFIG.enabled) {
    if (CONFIG.debug) {
      console.log(`🔍 [ActivityLogger] ${seccion}:${evento}`, datos);
    }
    return Promise.resolve({ success: true, offline: true });
  }

  const eventData = {
    cierre_id: cierreId,
    modulo: 'nomina',  // Por defecto nómina
    seccion: seccion,
    evento: evento,
    datos: datos,
    timestamp: new Date().toISOString(),
    session_id: getSessionId(),
  };

  if (CONFIG.batchMode) {
    return addToBatch(eventData);
  } else {
    return sendEvent(eventData);
  }
}

/**
 * Funciones específicas de conveniencia
 */
export const ActivityLogger = {
  // Archivos
  fileSelect: (cierreId, seccion, filename, size) => 
    logActivity(cierreId, seccion, 'file_select', { filename, size }),
    
  fileUpload: (cierreId, seccion, filename, success = true) =>
    logActivity(cierreId, seccion, 'file_upload', { filename, success }),
    
  downloadTemplate: (cierreId, seccion, templateType) =>
    logActivity(cierreId, seccion, 'download_template', { templateType }),

  // Modales  
  modalOpen: (cierreId, seccion, modalType, context = {}) =>
    logActivity(cierreId, seccion, 'modal_open', { modalType, ...context }),
    
  modalClose: (cierreId, seccion, modalType, action = null) =>
    logActivity(cierreId, seccion, 'modal_close', { modalType, action }),

  // Estados
  stateChange: (cierreId, seccion, fromState, toState) =>
    logActivity(cierreId, seccion, 'state_change', { fromState, toState }),
    
  // Clasificación
  conceptMap: (cierreId, headerName, conceptId, conceptName) =>
    logActivity(cierreId, 'clasificacion', 'concept_map', { 
      headerName, conceptId, conceptName 
    }),
    
  // Sesión
  sessionStart: (cierreId, seccion) =>
    logActivity(cierreId, seccion, 'session_start', { startTime: Date.now() }),
    
  sessionEnd: (cierreId, seccion, duration = null) =>
    logActivity(cierreId, seccion, 'session_end', { 
      duration: duration || calculateSessionDuration() 
    }),

  // Error
  error: (cierreId, seccion, errorType, errorMessage) =>
    logActivity(cierreId, seccion, 'error', { errorType, errorMessage }),
};

/**
 * Hook de React para logging automático de sesión
 */
export function useActivitySession(cierreId, seccion) {
  React.useEffect(() => {
    if (!cierreId || !seccion) return;

    // Log session start
    ActivityLogger.sessionStart(cierreId, seccion);
    const startTime = Date.now();

    // Log session end on unmount
    return () => {
      const duration = Date.now() - startTime;
      ActivityLogger.sessionEnd(cierreId, seccion, duration);
    };
  }, [cierreId, seccion]);
}

/**
 * HOC para logging automático de componentes
 */
export function withActivityLogging(WrappedComponent, seccion) {
  return function ActivityLoggedComponent(props) {
    const { cierreId, ...otherProps } = props;
    
    useActivitySession(cierreId, seccion);
    
    return React.createElement(WrappedComponent, {
      ...otherProps,
      cierreId,
      // Inyectar helper de logging
      logActivity: (evento, datos) => logActivity(cierreId, seccion, evento, datos),
    });
  };
}

/**
 * Configuración y control
 */
export const ActivityConfig = {
  enable: () => {
    CONFIG.enabled = true;
    console.log('✅ Activity Logging habilitado');
  },
  
  disable: () => {
    CONFIG.enabled = false;
    console.log('❌ Activity Logging deshabilitado');
  },
  
  toggle: () => {
    CONFIG.enabled = !CONFIG.enabled;
    console.log(`🔄 Activity Logging ${CONFIG.enabled ? 'habilitado' : 'deshabilitado'}`);
  },
  
  setBatchMode: (enabled) => {
    CONFIG.batchMode = enabled;
  },
  
  setDebug: (enabled) => {
    CONFIG.debug = enabled;
  },
  
  flushBatch: () => {
    if (eventBuffer.length > 0) {
      sendBatch();
    }
  }
};

// === IMPLEMENTACIÓN INTERNA ===

function addToBatch(eventData) {
  eventBuffer.push(eventData);
  
  // Enviar si el buffer está lleno
  if (eventBuffer.length >= CONFIG.batchSize) {
    return sendBatch();
  }
  
  // O programar envío por timeout
  if (batchTimer) {
    clearTimeout(batchTimer);
  }
  
  batchTimer = setTimeout(() => {
    if (eventBuffer.length > 0) {
      sendBatch();
    }
  }, CONFIG.batchTimeout);
  
  return Promise.resolve({ success: true, batched: true });
}

async function sendBatch() {
  if (eventBuffer.length === 0) return;
  
  const batch = [...eventBuffer];
  eventBuffer = [];
  
  if (batchTimer) {
    clearTimeout(batchTimer);
    batchTimer = null;
  }
  
  try {
    const response = await fetch(CONFIG.endpoint + 'batch/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCSRFToken(),
      },
      body: JSON.stringify({ events: batch }),
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    
    return { success: true, count: batch.length };
  } catch (error) {
    console.warn('Error enviando batch de actividades:', error);
    return { success: false, error: error.message };
  }
}

async function sendEvent(eventData) {
  try {
    const response = await fetch(CONFIG.endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCSRFToken(),
      },
      body: JSON.stringify(eventData),
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    
    return { success: true };
  } catch (error) {
    console.warn('Error enviando actividad:', error);
    return { success: false, error: error.message };
  }
}

function getSessionId() {
  // Generar o recuperar session ID simple
  let sessionId = sessionStorage.getItem('activity_session_id');
  if (!sessionId) {
    sessionId = 'sess_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now();
    sessionStorage.setItem('activity_session_id', sessionId);
  }
  return sessionId;
}

function getCSRFToken() {
  const cookies = document.cookie.split(';');
  for (let cookie of cookies) {
    const [name, value] = cookie.trim().split('=');
    if (name === 'csrftoken') {
      return value;
    }
  }
  return '';
}

function calculateSessionDuration() {
  // Implementación simple - se puede mejorar
  return Date.now() - (parseInt(sessionStorage.getItem('session_start_time')) || Date.now());
}

// Auto-inicialización
if (typeof window !== 'undefined') {
  // Guardar timestamp de inicio de sesión
  if (!sessionStorage.getItem('session_start_time')) {
    sessionStorage.setItem('session_start_time', Date.now().toString());
  }
  
  // Flush batch antes de cerrar página
  window.addEventListener('beforeunload', () => {
    if (eventBuffer.length > 0) {
      navigator.sendBeacon(
        CONFIG.endpoint + 'batch/',
        JSON.stringify({ events: eventBuffer })
      );
    }
  });
}