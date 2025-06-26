import { useState, useEffect } from 'react';
import { X } from 'lucide-react';

const getSeverityColor = (severidad) => {
  const colors = {
    critica: 'text-red-400',
    alta: 'text-orange-400',
    media: 'text-yellow-400',
    baja: 'text-blue-400'
  };
  return colors[severidad] || 'text-gray-400';
};

const ModalIncidenciasConsolidadas = ({ abierto, onClose, incidencias }) => {
  if (!abierto) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 rounded-xl max-w-4xl w-full max-h-[90vh] flex flex-col shadow-xl">
        {/* Header */}
        <div className="p-4 border-b border-gray-700 flex justify-between items-center">
          <h3 className="text-lg font-semibold text-white">Incidencias Detectadas</h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white transition-colors"
          >
            <X size={20} />
          </button>
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
                  className="bg-gray-800 rounded-lg p-4 border border-gray-700"
                >
                  <div className="flex items-center gap-2 mb-2">
                    <span className={`font-semibold ${getSeverityColor(incidencia.severidad)}`}>
                      {incidencia.severidad?.toUpperCase() || 'DESCONOCIDA'}
                    </span>
                    <span className="text-gray-400">•</span>
                    <span className="text-white">
                      {incidencia.mensaje_usuario || 'Sin mensaje'}
                    </span>
                  </div>

                  {/* Detalles */}
                  <div className="mt-3 space-y-2 text-sm">
                    <div className="text-gray-300">
                      <span className="text-gray-400">Elementos afectados:</span> {incidencia.cantidad_afectada || 0}
                    </div>
                    
                    {incidencia.detalle_muestra && incidencia.detalle_muestra.length > 0 && (
                      <div className="mt-2">
                        <div className="text-gray-400 mb-1">Ejemplos:</div>
                        <ul className="list-disc list-inside space-y-1 text-white bg-gray-700 p-2 rounded">
                          {incidencia.detalle_muestra.slice(0, 5).map((detalle, idx) => (
                            <li key={idx} className="text-sm">
                              {typeof detalle === 'object' ? 
                                (detalle.codigo ? `${detalle.codigo} - ${detalle.nombre || detalle.descripcion || ''}` : JSON.stringify(detalle)) 
                                : detalle}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Estadísticas adicionales */}
                    {incidencia.estadisticas_adicionales && Object.keys(incidencia.estadisticas_adicionales).length > 0 && (
                      <div className="mt-3">
                        <div className="text-gray-400 mb-2">Estadísticas:</div>
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
                      </div>
                    )}

                    {/* Acción sugerida */}
                    {incidencia.accion_sugerida && (
                      <div className="mt-3 p-2 bg-blue-900/30 border border-blue-700 rounded">
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
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ModalIncidenciasConsolidadas;
