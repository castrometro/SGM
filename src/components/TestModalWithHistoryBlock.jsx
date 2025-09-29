/**
 * Test utility para verificar el comportamiento del hook useModalHistoryBlock
 * Este archivo puede ser usado para pruebas manuales del comportamiento del modal
 */

import { useState } from 'react';
import useModalHistoryBlock from '../hooks/useModalHistoryBlock';

const TestModalWithHistoryBlock = () => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [log, setLog] = useState([]);

  const addLog = (message) => {
    setLog(prev => [...prev, `${new Date().toLocaleTimeString()}: ${message}`]);
  };

  const { closeModal, isBlocking } = useModalHistoryBlock(
    isModalOpen,
    () => {
      addLog('Modal cerrado desde hook');
      setIsModalOpen(false);
    },
    {
      preventNavigation: true,
      onNavigationAttempt: (event) => {
        addLog('Intento de navegación detectado - modal abierto');
      }
    }
  );

  const openModal = () => {
    setIsModalOpen(true);
    addLog('Modal abierto');
  };

  const closeModalDirectly = () => {
    closeModal();
    addLog('Modal cerrado directamente');
  };

  const clearLog = () => {
    setLog([]);
  };

  if (!isModalOpen) {
    return (
      <div style={{ padding: '20px', fontFamily: 'monospace' }}>
        <h2>Test: Modal History Block</h2>
        <button onClick={openModal} style={{ marginRight: '10px', padding: '10px' }}>
          Abrir Modal
        </button>
        <button onClick={clearLog} style={{ padding: '10px' }}>
          Limpiar Log
        </button>
        
        <div style={{ marginTop: '20px' }}>
          <h3>Log de eventos:</h3>
          <div style={{ border: '1px solid #ccc', padding: '10px', height: '200px', overflow: 'auto' }}>
            {log.map((entry, index) => (
              <div key={index}>{entry}</div>
            ))}
          </div>
        </div>
        
        <div style={{ marginTop: '20px', fontSize: '14px', color: '#666' }}>
          <strong>Instrucciones:</strong>
          <ul>
            <li>1. Abrir modal</li>
            <li>2. Intentar usar botón "atrás" del navegador</li>
            <li>3. Verificar que el modal se cierre y no haya navegación</li>
          </ul>
        </div>
      </div>
    );
  }

  return (
    <div style={{ 
      position: 'fixed', 
      top: 0, 
      left: 0, 
      right: 0, 
      bottom: 0, 
      backgroundColor: 'rgba(0,0,0,0.7)',
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      fontFamily: 'monospace'
    }}>
      <div style={{ 
        backgroundColor: 'white', 
        padding: '30px', 
        borderRadius: '8px',
        minWidth: '400px'
      }}>
        <h2>Modal de Prueba</h2>
        <p>Estado de bloqueo: <strong>{isBlocking ? 'ACTIVO' : 'INACTIVO'}</strong></p>
        <p>Ahora presiona el botón "atrás" de tu navegador para probar el comportamiento.</p>
        
        <div style={{ marginTop: '20px' }}>
          <button onClick={closeModalDirectly} style={{ marginRight: '10px', padding: '10px' }}>
            Cerrar Modal
          </button>
        </div>
        
        <div style={{ marginTop: '20px', fontSize: '12px' }}>
          <strong>Hash actual:</strong> {window.location.hash}
        </div>
      </div>
    </div>
  );
};

export default TestModalWithHistoryBlock;