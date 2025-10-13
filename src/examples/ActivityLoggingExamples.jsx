// Ejemplo de uso del nuevo sistema de Activity Logging V2

import React, { useEffect, useRef } from 'react';
import { ActivityLogger, ActivityConfig, useActivitySession } from '../utils/activityLogger_v2';

// === 1. CONFIGURACIÓN INICIAL (Una sola vez en la app) ===

// En tu App.js o index.js
ActivityConfig.enable();  // ← Habilitar logging
ActivityConfig.setDebug(true);  // ← Para desarrollo

// === 2. USO EN COMPONENTES - SÚPER SIMPLE ===

const LibroRemuneracionesCard = ({ cierreId, onUpload }) => {
  // Auto-logging de sesión (opcional)
  useActivitySession(cierreId, 'libro_remuneraciones');
  
  const handleFileSelect = async (event) => {
    const file = event.target.files[0];
    if (!file) return;
    
    // Log automático
    await ActivityLogger.fileSelect(cierreId, 'libro_remuneraciones', file.name, file.size);
    
    try {
      await onUpload(file);
      // Log de éxito
      await ActivityLogger.fileUpload(cierreId, 'libro_remuneraciones', file.name, true);
    } catch (error) {
      // Log de error
      await ActivityLogger.error(cierreId, 'libro_remuneraciones', 'upload_failed', error.message);
    }
  };
  
  const handleDownloadTemplate = async () => {
    // Log de descarga
    await ActivityLogger.downloadTemplate(cierreId, 'libro_remuneraciones', 'plantilla_libro');
    
    // ... resto de la lógica
  };
  
  return (
    <div>
      <input type="file" onChange={handleFileSelect} />
      <button onClick={handleDownloadTemplate}>Descargar Plantilla</button>
    </div>
  );
};

// === 3. USO CON HOC (Aún más automático) ===

import { withActivityLogging } from '../utils/activityLogger_v2';

const SimpleCard = ({ cierreId, logActivity }) => {
  const handleClick = () => {
    // Helper inyectado automáticamente
    logActivity('button_click', { button: 'process' });
    
    // ... lógica del componente
  };
  
  return <button onClick={handleClick}>Procesar</button>;
};

// Wrap con logging automático
export default withActivityLogging(SimpleCard, 'simple_section');

// === 4. MODAL CON LOGGING ===

const ClasificacionModal = ({ cierreId, isOpen, onClose }) => {
  useEffect(() => {
    if (isOpen) {
      ActivityLogger.modalOpen(cierreId, 'clasificacion', 'headers_modal', {
        headers_count: 25
      });
    }
  }, [isOpen]);
  
  const handleClose = (actionTaken = null) => {
    ActivityLogger.modalClose(cierreId, 'clasificacion', 'headers_modal', actionTaken);
    onClose();
  };
  
  const handleConceptMap = (headerName, conceptId, conceptName) => {
    ActivityLogger.conceptMap(cierreId, headerName, conceptId, conceptName);
    // ... resto de lógica
  };
  
  return (
    <Modal isOpen={isOpen} onClose={() => handleClose('cancel')}>
      {/* Contenido del modal */}
      <button onClick={() => handleClose('save')}>Guardar</button>
    </Modal>
  );
};

// === 5. CONTROL DINÁMICO ===

// En consola del navegador o en respuesta a eventos
ActivityConfig.toggle();  // Habilitar/deshabilitar on-the-fly
ActivityConfig.flushBatch();  // Forzar envío inmediato

// === 6. LOGGING PERSONALIZADO ===

import { logActivity } from '../utils/activityLogger_v2';

const CustomComponent = ({ cierreId }) => {
  const handleCustomAction = () => {
    // Log completamente personalizado
    logActivity(cierreId, 'custom_section', 'special_action', {
      custom_field: 'custom_value',
      timestamp: Date.now(),
      user_data: { preference: 'advanced' }
    });
  };
  
  return <button onClick={handleCustomAction}>Acción Especial</button>;
};

// === 7. MÚLTIPLES EVENTOS EN SECUENCIA ===

const ComplexWorkflow = ({ cierreId }) => {
  const handleComplexFlow = async () => {
    // Secuencia de eventos
    await ActivityLogger.sessionStart(cierreId, 'complex_workflow');
    
    await ActivityLogger.modalOpen(cierreId, 'complex_workflow', 'step1_modal');
    // ... lógica paso 1
    await ActivityLogger.modalClose(cierreId, 'complex_workflow', 'step1_modal', 'continue');
    
    await ActivityLogger.stateChange(cierreId, 'complex_workflow', 'step1', 'step2');
    // ... lógica paso 2
    
    await ActivityLogger.sessionEnd(cierreId, 'complex_workflow');
  };
  
  return <button onClick={handleComplexFlow}>Flujo Complejo</button>;
};

export {
  LibroRemuneracionesCard,
  ClasificacionModal, 
  CustomComponent,
  ComplexWorkflow
};