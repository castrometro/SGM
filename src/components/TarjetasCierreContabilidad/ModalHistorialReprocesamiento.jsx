import { useState, useEffect } from 'react';
import { X, Clock, User, CheckCircle, AlertCircle } from 'lucide-react';
import { obtenerHistorialReprocesamiento, cambiarIteracionPrincipal } from '../../api/contabilidad';

const ModalHistorialReprocesamiento = ({ abierto, onClose, cierreId }) => {
  const [historial, setHistorial] = useState([]);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState('');
  const [cambiandoIteracion, setCambiandoIteracion] = useState(null);

  useEffect(() => {
    if (abierto && cierreId) {
      cargarHistorial();
    }
  }, [abierto, cierreId]);

  const cargarHistorial = async () => {
    setCargando(true);
    setError('');
    
    try {
      const data = await obtenerHistorialReprocesamiento(cierreId);
      setHistorial(data.historial || []);
    } catch (err) {
      console.error('Error cargando historial:', err);
      setError('Error al cargar el historial de reprocesamiento');
    } finally {
      setCargando(false);
    }
  };

  const handleCambiarIteracionPrincipal = async (iteracion) => {
    if (cambiandoIteracion) return;
    
    const confirmar = window.confirm(
      `¿Cambiar a la iteración ${iteracion} como principal?\n\n` +
      'Esta será la versión que se muestra por defecto en las tarjetas.'
    );
    
    if (!confirmar) return;
    
    setCambiandoIteracion(iteracion);
    
    try {
      await cambiarIteracionPrincipal(cierreId, iteracion);
      await cargarHistorial(); // Recargar para actualizar estado
      alert(`Iteración ${iteracion} marcada como principal`);
    } catch (err) {
      console.error('Error cambiando iteración:', err);
      alert('Error al cambiar la iteración principal');
    } finally {
      setCambiandoIteracion(null);
    }
  };

  const formatearFecha = (fechaString) => {
    const fecha = new Date(fechaString);
    return fecha.toLocaleString('es-CL', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getEstadoColor = (estado) => {
    const colores = {
      'completado': 'text-green-400',
      'procesando': 'text-blue-400',
      'error': 'text-red-400',
      'subido': 'text-yellow-400'
    };
    return colores[estado] || 'text-gray-400';
  };

  if (!abierto) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 rounded-xl max-w-4xl w-full max-h-[80vh] flex flex-col shadow-xl">
        {/* Header */}
        <div className="p-4 border-b border-gray-700 flex justify-between items-center">
          <h3 className="text-lg font-semibold text-white">
            Historial de Reprocesamiento
          </h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        {/* Content */}
        <div className="p-4 overflow-y-auto flex-1">
          {cargando ? (
            <div className="text-center py-8">
              <div className="text-blue-400">Cargando historial...</div>
            </div>
          ) : error ? (
            <div className="text-center py-8">
              <div className="text-red-400">{error}</div>
              <button
                onClick={cargarHistorial}
                className="mt-2 text-blue-400 hover:text-blue-300 underline"
              >
                Reintentar
              </button>
            </div>
          ) : historial.length === 0 ? (
            <div className="text-center py-8">
              <div className="text-gray-400">No hay historial de reprocesamiento</div>
            </div>
          ) : (
            <div className="space-y-4">
              {historial.map((item, index) => (
                <div
                  key={index}
                  className={`bg-gray-800 rounded-lg border p-4 ${
                    item.es_principal ? 'border-blue-500 bg-blue-900/20' : 'border-gray-600'
                  }`}
                >
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <div className="text-lg font-semibold text-white">
                        Iteración {item.iteracion}
                      </div>
                      {item.es_principal && (
                        <div className="bg-blue-600 text-white text-xs px-2 py-1 rounded flex items-center gap-1">
                          <CheckCircle size={12} />
                          Principal
                        </div>
                      )}
                      <div className={`text-sm font-medium ${getEstadoColor(item.estado)}`}>
                        {item.estado.toUpperCase()}
                      </div>
                    </div>
                    
                    {!item.es_principal && item.estado === 'completado' && (
                      <button
                        onClick={() => handleCambiarIteracionPrincipal(item.iteracion)}
                        disabled={cambiandoIteracion === item.iteracion}
                        className="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-800 text-white text-xs px-2 py-1 rounded transition-colors"
                      >
                        {cambiandoIteracion === item.iteracion ? 'Cambiando...' : 'Marcar principal'}
                      </button>
                    )}
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                    <div>
                      <div className="text-gray-400 mb-1 flex items-center gap-1">
                        <Clock size={14} />
                        Fecha
                      </div>
                      <div className="text-white">{formatearFecha(item.fecha)}</div>
                    </div>
                    
                    <div>
                      <div className="text-gray-400 mb-1 flex items-center gap-1">
                        <User size={14} />
                        Usuario
                      </div>
                      <div className="text-white">{item.usuario}</div>
                    </div>
                    
                    <div>
                      <div className="text-gray-400 mb-1">Motivo</div>
                      <div className="text-white">{item.motivo}</div>
                    </div>
                  </div>

                  {/* Estadísticas */}
                  {item.estadisticas && (
                    <div className="mt-3 p-3 bg-gray-700/50 rounded">
                      <div className="text-sm font-medium text-gray-300 mb-2">
                        Estadísticas del procesamiento
                      </div>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
                        <div>
                          <div className="text-yellow-400">Incidencias</div>
                          <div className="text-white font-medium">
                            {item.estadisticas.incidencias || 0}
                          </div>
                        </div>
                        <div>
                          <div className="text-blue-400">Elementos afectados</div>
                          <div className="text-white font-medium">
                            {item.estadisticas.elementos_afectados || 0}
                          </div>
                        </div>
                        {item.estadisticas.procesamiento?.movimientos && (
                          <div>
                            <div className="text-green-400">Movimientos</div>
                            <div className="text-white font-medium">
                              {item.estadisticas.procesamiento.movimientos.toLocaleString()}
                            </div>
                          </div>
                        )}
                        {item.estadisticas.procesamiento?.cuentas_nuevas && (
                          <div>
                            <div className="text-purple-400">Cuentas nuevas</div>
                            <div className="text-white font-medium">
                              {item.estadisticas.procesamiento.cuentas_nuevas}
                            </div>
                          </div>
                        )}
                      </div>
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

export default ModalHistorialReprocesamiento;
