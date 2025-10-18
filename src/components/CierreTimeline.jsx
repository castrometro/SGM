// src/components/CierreTimeline.jsx
/**
 * Componente para visualizar el timeline de actividades de un cierre
 * 
 * Muestra un historial completo de todos los eventos que ocurrieron:
 * - Uploads de archivos
 * - Eliminaciones
 * - Procesamientos Celery
 * - Errores
 * - Validaciones
 */

import React, { useState, useEffect } from 'react';
import api from '../api/config';
import './CierreTimeline.css';

const CierreTimeline = ({ cierreId, onClose }) => {
  const [timeline, setTimeline] = useState([]);
  const [resumen, setResumen] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [cliente, setCliente] = useState('');
  const [periodo, setPeriodo] = useState('');

  useEffect(() => {
    cargarTimeline();
  }, [cierreId]);

  const cargarTimeline = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await api.get(`/nomina/cierre/${cierreId}/timeline/`);
      
      setTimeline(response.data.timeline);
      setResumen(response.data.resumen);
      setCliente(response.data.cliente);
      setPeriodo(response.data.periodo);
      
      console.log('✅ Timeline cargado:', response.data);
    } catch (err) {
      console.error('❌ Error cargando timeline:', err);
      setError(err.response?.data?.error || 'Error al cargar el historial');
    } finally {
      setLoading(false);
    }
  };

  const exportarTXT = async () => {
    try {
      const response = await api.get(`/nomina/cierre/${cierreId}/log/export/txt/`, {
        responseType: 'blob'
      });

      // Descargar archivo
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `cierre_${cierreId}_log.txt`);
      document.body.appendChild(link);
      link.click();
      link.remove();

      console.log('✅ Log exportado como TXT');
    } catch (err) {
      console.error('❌ Error exportando log:', err);
      alert('Error al exportar el log');
    }
  };

  const getEventoIcon = (evento, resultado) => {
    if (resultado === 'error') return '❌';
    if (resultado === 'timeout') return '⏱️';
    
    if (evento.includes('upload_iniciado')) return '📤';
    if (evento.includes('upload_completado')) return '✅';
    if (evento.includes('archivo_validado')) return '🔍';
    if (evento.includes('eliminado')) return '🗑️';
    if (evento.includes('procesamiento')) return '⚙️';
    if (evento.includes('analisis')) return '📊';
    if (evento.includes('clasificacion')) return '🏷️';
    if (evento.includes('exitoso')) return '✅';
    if (evento.includes('error')) return '❌';
    
    return '📝';
  };

  const formatearFecha = (timestamp) => {
    const fecha = new Date(timestamp);
    return fecha.toLocaleString('es-CL', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  const formatearEvento = (evento) => {
    return evento
      .replace(/_/g, ' ')
      .replace(/\b\w/g, l => l.toUpperCase());
  };

  if (loading) {
    return (
      <div className="cierre-timeline-overlay">
        <div className="cierre-timeline-modal">
          <div className="loading-container">
            <div className="spinner"></div>
            <p>Cargando historial del cierre...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="cierre-timeline-overlay">
        <div className="cierre-timeline-modal">
          <div className="error-container">
            <h3>❌ Error</h3>
            <p>{error}</p>
            <button onClick={onClose} className="btn-close">Cerrar</button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="cierre-timeline-overlay" onClick={onClose}>
      <div className="cierre-timeline-modal" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="timeline-header">
          <div>
            <h2>📋 Historial del Cierre</h2>
            <p className="timeline-subtitle">
              <strong>Cliente:</strong> {cliente} | <strong>Período:</strong> {periodo}
            </p>
          </div>
          <button onClick={onClose} className="btn-close-x">✕</button>
        </div>

        {/* Resumen */}
        <div className="timeline-resumen">
          <div className="resumen-card">
            <div className="resumen-icon">📊</div>
            <div className="resumen-data">
              <div className="resumen-value">{resumen.total_eventos || 0}</div>
              <div className="resumen-label">Total Eventos</div>
            </div>
          </div>
          
          <div className="resumen-card success">
            <div className="resumen-icon">✅</div>
            <div className="resumen-data">
              <div className="resumen-value">{resumen.uploads_exitosos || 0}</div>
              <div className="resumen-label">Uploads Exitosos</div>
            </div>
          </div>
          
          <div className="resumen-card error">
            <div className="resumen-icon">❌</div>
            <div className="resumen-data">
              <div className="resumen-value">{resumen.errores || 0}</div>
              <div className="resumen-label">Errores</div>
            </div>
          </div>
          
          <div className="resumen-card warning">
            <div className="resumen-icon">🗑️</div>
            <div className="resumen-data">
              <div className="resumen-value">{resumen.eliminaciones || 0}</div>
              <div className="resumen-label">Eliminaciones</div>
            </div>
          </div>
        </div>

        {/* Timeline */}
        <div className="timeline-container">
          {timeline.length === 0 ? (
            <div className="timeline-empty">
              <p>📭 No hay actividad registrada para este cierre</p>
            </div>
          ) : (
            <div className="timeline-list">
              {timeline.map((evento, index) => (
                <div 
                  key={evento.id} 
                  className={`timeline-item ${evento.resultado === 'error' ? 'timeline-item-error' : ''}`}
                >
                  <div className="timeline-marker">
                    <span className="timeline-icon">
                      {getEventoIcon(evento.evento, evento.resultado)}
                    </span>
                  </div>
                  
                  <div className="timeline-content">
                    <div className="timeline-time">
                      {formatearFecha(evento.timestamp)}
                    </div>
                    
                    <div className="timeline-info">
                      <div className="timeline-title">
                        <strong>{formatearEvento(evento.evento)}</strong>
                        <span className="timeline-seccion">{evento.seccion}</span>
                      </div>
                      
                      <div className="timeline-usuario">
                        👤 {evento.usuario}
                      </div>
                      
                      {evento.datos && Object.keys(evento.datos).length > 0 && (
                        <details className="timeline-detalles">
                          <summary>Ver detalles</summary>
                          <pre>{JSON.stringify(evento.datos, null, 2)}</pre>
                        </details>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Footer con acciones */}
        <div className="timeline-footer">
          <button onClick={exportarTXT} className="btn-export">
            📥 Exportar como TXT
          </button>
          <button onClick={onClose} className="btn-secondary">
            Cerrar
          </button>
        </div>
      </div>
    </div>
  );
};

export default CierreTimeline;
