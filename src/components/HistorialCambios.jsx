import { useState, useEffect } from 'react';
import { obtenerLogsUpload } from '../api/contabilidad';
import { History } from 'lucide-react';

const HistorialCambios = ({ tipoUpload, uploadId, clienteId, abierto, onClose }) => {
  const [logs, setLogs] = useState([]);
  const [cargando, setCargando] = useState(false);

  useEffect(() => {
    if (abierto) {
      cargarLogs();
    }
  }, [abierto, tipoUpload, uploadId, clienteId]);

  const cargarLogs = async () => {
    setCargando(true);
    try {
      const data = await obtenerLogsUpload(tipoUpload, uploadId, clienteId);
      setLogs(data);
    } catch (err) {
      console.error('Error al cargar logs:', err);
      setLogs([]);
    } finally {
      setCargando(false);
    }
  };

  const formatFecha = (fecha) => {
    if (!fecha) return '-';
    return new Date(fecha).toLocaleString('es-CL');
  };

  const formatAccion = (log) => {
    const accion = log.accion_display || log.accion;
    const acciones = {
      'Creación': { text: 'Creación', color: 'text-blue-400', icon: '📤' },
      'Eliminación': { text: 'Eliminación', color: 'text-red-400', icon: '🗑️' },
      'Reprocesamiento': { text: 'Reprocesamiento', color: 'text-yellow-400', icon: '🔄' },
      'Actualización': { text: 'Actualización', color: 'text-green-400', icon: '✏️' },
      'Visualización': { text: 'Visualización', color: 'text-gray-400', icon: '�️' }
    };
    const info = acciones[accion] || { text: accion, color: 'text-gray-400', icon: '📝' };
    return (
      <span className={info.color}>
        {info.icon} {info.text}
      </span>
    );
  };

  if (!abierto) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black bg-opacity-40 flex items-center justify-center">
      <div className="bg-gray-800 rounded-xl shadow-lg p-6 w-full max-w-4xl relative text-white">
        <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
          <History size={20} />
          Historial de Cambios - {tipoUpload}
        </h2>
        <button
          className="absolute top-3 right-3 text-gray-400 hover:text-red-500"
          onClick={onClose}
        >✕</button>
        
        <div className="overflow-y-auto" style={{ maxHeight: "500px" }}>
          {cargando ? (
            <div className="text-center py-10 text-gray-400">
              <div className="animate-spin inline-block w-6 h-6 border-2 border-current border-t-transparent rounded-full"></div>
              <div className="mt-2">Cargando historial...</div>
            </div>
          ) : logs.length === 0 ? (
            <div className="text-center py-10 text-gray-400">
              No hay cambios registrados.
            </div>
          ) : (
            <div className="space-y-3">
              {logs.map((log) => (
                <div 
                  key={log.id} 
                  className="bg-gray-700 p-4 rounded-lg border-l-4 border-blue-500"
                >
                  <div className="flex justify-between items-start mb-2">
                    <div className="font-semibold">{formatAccion(log)}</div>
                    <div className="text-xs text-gray-400">{formatFecha(log.fecha)}</div>
                  </div>
                  
                  {log.descripcion && (
                    <div className="text-sm text-gray-300 mb-1">
                      <strong>Descripción:</strong> {log.descripcion}
                    </div>
                  )}
                  
                  {log.metadata && Object.keys(log.metadata).length > 0 && (
                    <div className="text-sm text-gray-300 mb-1">
                      <strong>Detalles:</strong>
                      <div className="ml-2 mt-1 space-y-1">
                        {Object.entries(log.metadata).map(([key, value]) => (
                          <div key={key} className="text-xs">
                            <span className="text-gray-400">{key}:</span> {String(value)}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {log.ip_address && (
                    <div className="text-xs text-gray-500">
                      IP: {log.ip_address}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default HistorialCambios;
