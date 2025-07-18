// frontend/src/utils/activityLogger.js

/**
 * Helper para registrar actividades de usuario en las tarjetas de nómina
 * Proporciona métodos convenientes para llamar a las APIs de logging
 */

const API_BASE = '/api/nomina/activity-log';

class ActivityLogger {
  constructor(cierreId, tarjeta) {
    this.cierreId = cierreId;
    this.tarjeta = tarjeta;
    this.sessionStartTime = null;
  }

  /**
   * Método base para enviar requests de logging
   */
  async _sendLogRequest(endpoint, data) {
    try {
      const response = await fetch(`${API_BASE}/${endpoint}/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': this._getCSRFToken(),
        },
        body: JSON.stringify({
          cierre_id: this.cierreId,
          tarjeta: this.tarjeta,
          ...data
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        console.error('Error en logging:', errorData);
        return { success: false, error: errorData.error };
      }

      const result = await response.json();
      return { success: true, data: result };
    } catch (error) {
      console.error('Error enviando log:', error);
      return { success: false, error: error.message };
    }
  }

  /**
   * Obtiene el token CSRF
   */
  _getCSRFToken() {
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
      const [name, value] = cookie.trim().split('=');
      if (name === 'csrftoken') {
        return value;
      }
    }
    return '';
  }

  // === ACTIVIDADES DE MODAL ===

  /**
   * Registra apertura de modal
   */
  async logModalOpen(modalType, context = {}) {
    return await this._sendLogRequest('modal', {
      action: 'open',
      modal_type: modalType,
      context: context
    });
  }

  /**
   * Registra cierre de modal
   */
  async logModalClose(modalType, actionTaken = null) {
    return await this._sendLogRequest('modal', {
      action: 'close',
      modal_type: modalType,
      action_taken: actionTaken
    });
  }

  // === ACTIVIDADES DE ARCHIVO ===

  /**
   * Registra selección de archivo
   */
  async logFileSelect(fileName, fileSize = null) {
    return await this._sendLogRequest('file', {
      action: 'select',
      archivo_nombre: fileName,
      archivo_size: fileSize
    });
  }

  /**
   * Registra validación de archivo
   */
  async logFileValidate(fileName, errors = []) {
    return await this._sendLogRequest('file', {
      action: 'validate',
      archivo_nombre: fileName,
      errores: errors
    });
  }

  /**
   * Registra descarga de plantilla
   */
  async logDownloadTemplate(templateType) {
    return await this._sendLogRequest('file', {
      action: 'download_template',
      template_type: templateType
    });
  }

  // === ACTIVIDADES DE CLASIFICACIÓN ===

  /**
   * Registra visualización de clasificación
   */
  async logViewClassification(headersCount = null, classifiedCount = null) {
    return await this._sendLogRequest('classification', {
      action: 'view',
      headers_count: headersCount,
      classified_count: classifiedCount
    });
  }

  /**
   * Registra mapeo de concepto
   */
  async logConceptMap(headerName, conceptoId, conceptoNombre) {
    return await this._sendLogRequest('classification', {
      action: 'map_concept',
      header_name: headerName,
      concepto_id: conceptoId,
      concepto_nombre: conceptoNombre
    });
  }

  /**
   * Registra desmapeo de concepto
   */
  async logConceptUnmap(headerName) {
    return await this._sendLogRequest('classification', {
      action: 'unmap_concept',
      header_name: headerName
    });
  }

  /**
   * Registra guardado de clasificación
   */
  async logSaveClassification(savedCount, totalCount) {
    return await this._sendLogRequest('classification', {
      action: 'save',
      saved_count: savedCount,
      total_count: totalCount
    });
  }

  // === ACTIVIDADES DE SESIÓN ===

  /**
   * Registra inicio de sesión de trabajo
   */
  async logSessionStart() {
    this.sessionStartTime = Date.now();
    return await this._sendLogRequest('session', {
      action: 'start'
    });
  }

  /**
   * Registra fin de sesión de trabajo
   */
  async logSessionEnd() {
    const durationSeconds = this.sessionStartTime 
      ? Math.floor((Date.now() - this.sessionStartTime) / 1000) 
      : null;
    
    return await this._sendLogRequest('session', {
      action: 'end',
      duration_seconds: durationSeconds
    });
  }

  /**
   * Registra cambio de estado
   */
  async logStateChange(oldState, newState, trigger = null) {
    return await this._sendLogRequest('session', {
      action: 'state_change',
      old_state: oldState,
      new_state: newState,
      trigger: trigger
    });
  }

  /**
   * Registra inicio de polling
   */
  async logPollingStart(intervalSeconds = 30) {
    return await this._sendLogRequest('session', {
      action: 'polling_start',
      interval_seconds: intervalSeconds
    });
  }

  /**
   * Registra detención de polling
   */
  async logPollingStop(reason = null) {
    return await this._sendLogRequest('session', {
      action: 'polling_stop',
      reason: reason
    });
  }

  /**
   * Registra actualización de progreso
   */
  async logProgressUpdate(progressPercentage, stepDescription) {
    return await this._sendLogRequest('session', {
      action: 'progress_update',
      progress_percentage: progressPercentage,
      step_description: stepDescription
    });
  }

  // === MÉTODOS DE CONVENIENCIA ===

  /**
   * Registra toda la secuencia de apertura de modal de upload
   */
  async logUploadModalSequence(modalType, file = null) {
    const results = [];
    
    // Apertura de modal
    results.push(await this.logModalOpen(modalType, { 
      trigger: 'user_click' 
    }));
    
    // Selección de archivo (si se proporciona)
    if (file) {
      results.push(await this.logFileSelect(file.name, file.size));
    }
    
    return results;
  }

  /**
   * Registra secuencia completa de clasificación
   */
  async logClassificationSequence(headers, mappings) {
    const results = [];
    
    // Visualización inicial
    results.push(await this.logViewClassification(
      headers.length, 
      mappings.length
    ));
    
    // Mapeos individuales
    for (const mapping of mappings) {
      results.push(await this.logConceptMap(
        mapping.header,
        mapping.conceptoId,
        mapping.conceptoNombre
      ));
    }
    
    // Guardado final
    results.push(await this.logSaveClassification(
      mappings.length,
      headers.length
    ));
    
    return results;
  }

  /**
   * Auto-manejo de sesión (registra inicio al crear, fin al destruir)
   */
  startAutoSession() {
    this.logSessionStart();
    
    // Registrar fin de sesión cuando se cierre la ventana
    window.addEventListener('beforeunload', () => {
      this.logSessionEnd();
    });
    
    // También cuando se navegue away del componente
    return () => {
      this.logSessionEnd();
    };
  }
}

// === FACTORY FUNCTIONS ===

/**
 * Crea un logger para una tarjeta específica
 */
export function createActivityLogger(cierreId, tarjeta) {
  return new ActivityLogger(cierreId, tarjeta);
}

/**
 * Hook de React para usar ActivityLogger
 */
export function useActivityLogger(cierreId, tarjeta) {
  const [logger] = useState(() => new ActivityLogger(cierreId, tarjeta));
  
  useEffect(() => {
    // Auto-iniciar sesión
    const cleanup = logger.startAutoSession();
    
    // Cleanup cuando se desmonte el componente
    return cleanup;
  }, [logger]);
  
  return logger;
}

// === UTILIDADES ===

/**
 * Obtiene logs de actividad para un cierre y tarjeta
 */
export async function getActivityLogs(cierreId, tarjeta, limit = 100) {
  try {
    const response = await fetch(
      `${API_BASE}/${cierreId}/${tarjeta}/?limit=${limit}`,
      {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        }
      }
    );
    
    if (!response.ok) {
      throw new Error('Error obteniendo logs');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error obteniendo activity logs:', error);
    return { success: false, error: error.message };
  }
}

/**
 * Formatea timestamp para mostrar
 */
export function formatLogTimestamp(timestamp) {
  return new Date(timestamp).toLocaleString('es-CL', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  });
}

export default ActivityLogger;
