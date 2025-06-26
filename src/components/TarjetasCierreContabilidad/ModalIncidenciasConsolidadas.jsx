import { useState, useEffect } from 'react';
import { X, RefreshCw, ChevronRight, ChevronDown, CheckCircle } from 'lucide-react';
import { reprocesarConExcepciones, obtenerCuentasDetalleIncidencia, marcarCuentaNoAplica } from '../../api/contabilidad';

const getSeverityColor = (severidad) => {
  const colors = {
    critica: 'text-red-400',
    alta: 'text-orange-400',
    media: 'text-yellow-400',
    baja: 'text-blue-400'
  };
  return colors[severidad] || 'text-gray-400';
};

const ModalIncidenciasConsolidadas = ({ abierto, onClose, incidencias, cierreId, onReprocesar }) => {
  const [expandida, setExpandida] = useState(null);
  const [cuentasDetalle, setCuentasDetalle] = useState({});
  const [cargandoDetalle, setCargandoDetalle] = useState(false);
  const [reprocesando, setReprocesando] = useState(false);

  if (!abierto) return null;

  const handleReprocesar = async () => {
    if (!cierreId) return;
    
    setReprocesando(true);
    try {
      await reprocesarConExcepciones(cierreId);
      alert('Reprocesamiento completado. Las incidencias se actualizarán.');
      if (onReprocesar) onReprocesar();
      onClose();
    } catch (error) {
      console.error('Error en reprocesamiento:', error);
      alert('Error al reprocesar: ' + (error.response?.data?.error || error.message));
    } finally {
      setReprocesando(false);
    }
  };

  const handleExpandir = async (index, tipoIncidencia) => {
    if (expandida === index) {
      setExpandida(null);
      return;
    }

    setExpandida(index);
    
    if (!cuentasDetalle[tipoIncidencia] && cierreId) {
      setCargandoDetalle(true);
      try {
        const detalle = await obtenerCuentasDetalleIncidencia(cierreId, tipoIncidencia);
        setCuentasDetalle(prev => ({
          ...prev,
          [tipoIncidencia]: detalle
        }));
      } catch (error) {
        console.error('Error cargando detalle:', error);
      } finally {
        setCargandoDetalle(false);
      }
    }
  };

  const handleMarcarNoAplica = async (codigoCuenta, tipoIncidencia, motivo = '') => {
    try {
      await marcarCuentaNoAplica(cierreId, codigoCuenta, tipoIncidencia, motivo);
      
      // Actualizar el estado local
      setCuentasDetalle(prev => ({
        ...prev,
        [tipoIncidencia]: {
          ...prev[tipoIncidencia],
          cuentas: prev[tipoIncidencia].cuentas.map(cuenta =>
            cuenta.codigo === codigoCuenta
              ? { ...cuenta, tiene_excepcion: true }
              : cuenta
          )
        }
      }));
    } catch (error) {
      console.error('Error marcando cuenta como no aplica:', error);
      alert('Error al marcar la cuenta. Intente nuevamente.');
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 rounded-xl max-w-4xl w-full max-h-[90vh] flex flex-col shadow-xl">
        {/* Header */}
        <div className="p-4 border-b border-gray-700 flex justify-between items-center">
          <h3 className="text-lg font-semibold text-white">Incidencias Detectadas</h3>
          <div className="flex items-center gap-3">
            <button
              onClick={handleReprocesar}
              disabled={reprocesando}
              className="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-800 disabled:opacity-50 text-white px-3 py-1 rounded text-sm flex items-center gap-2 transition-colors"
            >
              <RefreshCw size={16} className={reprocesando ? 'animate-spin' : ''} />
              {reprocesando ? 'Reprocesando...' : 'Reprocesar'}
            </button>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-white transition-colors"
            >
              <X size={20} />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-4 overflow-y-auto flex-1">
          {!incidencias || incidencias.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-gray-400 text-lg">No se encontraron incidencias.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {incidencias.map((incidencia, index) => (
                <div
                  key={index}
                  className="bg-gray-800 rounded-lg border border-gray-700"
                >
                  {/* Header de la incidencia */}
                  <div className="p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className={`font-semibold ${getSeverityColor(incidencia.severidad)}`}>
                          {incidencia.severidad?.toUpperCase() || 'DESCONOCIDA'}
                        </span>
                        <span className="text-gray-400">•</span>
                        <span className="text-white">
                          {incidencia.mensaje_usuario || 'Sin mensaje'}
                        </span>
                      </div>
                      
                      {/* Botón expandir */}
                      <button
                        onClick={() => handleExpandir(index, incidencia.tipo_incidencia)}
                        className="flex items-center gap-2 text-blue-400 hover:text-blue-300 transition-colors"
                      >
                        <span className="text-sm">Ver detalles</span>
                        {expandida === index ? 
                          <ChevronDown size={16} /> : 
                          <ChevronRight size={16} />
                        }
                      </button>
                    </div>

                    {/* Información básica */}
                    <div className="mt-3 space-y-2 text-sm">
                      <div className="text-gray-300">
                        <span className="text-gray-400">Elementos afectados:</span> {incidencia.cantidad_afectada || 0}
                      </div>
                      
                      {/* Estadísticas adicionales */}
                      {incidencia.estadisticas_adicionales && Object.keys(incidencia.estadisticas_adicionales).length > 0 && (
                        <div className="grid grid-cols-2 gap-2 text-xs bg-gray-700 p-2 rounded">
                          {Object.entries(incidencia.estadisticas_adicionales).map(([key, value]) => (
                            <div key={key} className="text-gray-300">
                              <span className="text-gray-400">{key.replace(/_/g, ' ')}:</span> {' '}
                              <span className="text-white">
                                {typeof value === 'number' ? value.toLocaleString() : value}
                              </span>
                            </div>
                          ))}
                        </div>
                      )}

                      {/* Acción sugerida */}
                      {incidencia.accion_sugerida && (
                        <div className="p-2 bg-blue-900/30 border border-blue-700 rounded">
                          <div className="text-blue-300 text-sm">
                            💡 <span className="font-medium">Acción sugerida:</span>
                          </div>
                          <div className="text-blue-200 text-sm mt-1">
                            {incidencia.accion_sugerida}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Panel expandido con detalle de cuentas */}
                  {expandida === index && (
                    <div className="border-t border-gray-700 p-4 bg-gray-700/50">
                      {cargandoDetalle ? (
                        <div className="text-center text-gray-400 py-4">
                          Cargando detalles...
                        </div>
                      ) : cuentasDetalle[incidencia.tipo_incidencia] ? (
                        <div>
                          <h4 className="text-white font-medium mb-3">
                            Cuentas afectadas ({cuentasDetalle[incidencia.tipo_incidencia].cuentas?.length || 0})
                          </h4>
                          <div className="space-y-2 max-h-60 overflow-y-auto">
                            {cuentasDetalle[incidencia.tipo_incidencia].cuentas?.map((cuenta, idx) => (
                              <div 
                                key={idx}
                                className="bg-gray-800 p-3 rounded border border-gray-600 flex items-center justify-between"
                              >
                                <div className="flex-1">
                                  <div className="text-white font-medium">
                                    {cuenta.codigo} - {cuenta.nombre}
                                  </div>
                                  {cuenta.descripcion && (
                                    <div className="text-gray-400 text-sm mt-1">
                                      {cuenta.descripcion}
                                    </div>
                                  )}
                                  {cuenta.monto > 0 && (
                                    <div className="text-green-400 text-sm">
                                      Monto: ${cuenta.monto.toLocaleString()}
                                    </div>
                                  )}
                                </div>
                                
                                <div className="ml-4">
                                  {cuenta.tiene_excepcion ? (
                                    <div className="flex items-center gap-2 text-green-400">
                                      <CheckCircle size={16} />
                                      <span className="text-sm">No aplica</span>
                                    </div>
                                  ) : (
                                    <button
                                      onClick={() => handleMarcarNoAplica(cuenta.codigo, incidencia.tipo_incidencia)}
                                      className="px-3 py-1 bg-orange-600 hover:bg-orange-700 text-white text-sm rounded transition-colors"
                                    >
                                      Marcar "No aplica"
                                    </button>
                                  )}
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      ) : (
                        <div className="text-gray-400 text-center py-4">
                          No se pudo cargar el detalle de las cuentas
                        </div>
                      )}
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

export default ModalIncidenciasConsolidadas;
