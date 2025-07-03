import { useState, useEffect } from 'react';
import { obtenerEstadoCache, limpiarCacheIncidencias } from '../../api/contabilidad';

const CacheDebugPanel = ({ visible, onClose }) => {
  const [cacheInfo, setCacheInfo] = useState(null);
  const [loading, setLoading] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(null);

  const cargarEstadoCache = async () => {
    setLoading(true);
    try {
      const data = await obtenerEstadoCache();
      setCacheInfo(data);
      setLastUpdate(new Date().toLocaleTimeString());
    } catch (error) {
      console.error('Error cargando estado del caché:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleLimpiarCache = async (cierreId = null, limpiarTodo = false) => {
    try {
      const resultado = await limpiarCacheIncidencias(cierreId, limpiarTodo);
      alert(`✅ ${resultado.mensaje}\nClaves eliminadas: ${resultado.keys_eliminadas}`);
      await cargarEstadoCache(); // Recargar después de limpiar
    } catch (error) {
      console.error('Error limpiando caché:', error);
      alert(`❌ Error: ${error.response?.data?.error || error.message}`);
    }
  };

  useEffect(() => {
    if (visible) {
      cargarEstadoCache();
    }
  }, [visible]);

  if (!visible) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 rounded-xl max-w-4xl w-full max-h-[90vh] flex flex-col shadow-xl">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-700">
          <div className="flex items-center gap-3">
            <h2 className="text-xl font-semibold text-white">🐛 Debug - Estado del Caché Redis</h2>
            {lastUpdate && (
              <span className="text-xs text-gray-400">Actualizado: {lastUpdate}</span>
            )}
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white transition-colors"
          >
            ✕
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {loading ? (
            <div className="text-center py-8">
              <div className="text-blue-400">🔄 Cargando información del caché...</div>
            </div>
          ) : cacheInfo ? (
            <>
              {/* Redis Info */}
              <div className="bg-gray-800 rounded-lg p-4">
                <h3 className="text-lg font-semibold text-white mb-3">📊 Información de Redis</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <div className="text-gray-400">Versión</div>
                    <div className="text-white font-mono">{cacheInfo.redis_info?.version || 'N/A'}</div>
                  </div>
                  <div>
                    <div className="text-gray-400">Memoria Usada</div>
                    <div className="text-white font-mono">{cacheInfo.redis_info?.used_memory || 'N/A'}</div>
                  </div>
                  <div>
                    <div className="text-gray-400">Clientes Conectados</div>
                    <div className="text-white font-mono">{cacheInfo.redis_info?.connected_clients || 'N/A'}</div>
                  </div>
                  <div>
                    <div className="text-gray-400">Total de Claves</div>
                    <div className="text-white font-mono">{cacheInfo.redis_info?.total_keys || 'N/A'}</div>
                  </div>
                </div>
              </div>

              {/* Cache de Incidencias */}
              <div className="bg-gray-800 rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-lg font-semibold text-white">🔑 Caché de Incidencias</h3>
                  <div className="space-x-2">
                    <button
                      onClick={cargarEstadoCache}
                      className="bg-blue-600 hover:bg-blue-700 text-white text-xs px-3 py-1 rounded transition-colors"
                    >
                      🔄 Actualizar
                    </button>
                    <button
                      onClick={() => handleLimpiarCache(null, true)}
                      className="bg-red-600 hover:bg-red-700 text-white text-xs px-3 py-1 rounded transition-colors"
                    >
                      🧹 Limpiar Todo
                    </button>
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-4 mb-4 text-sm">
                  <div>
                    <div className="text-gray-400">Total Claves</div>
                    <div className="text-white font-mono text-lg">{cacheInfo.incidencias_cache?.total_keys || 0}</div>
                  </div>
                  <div>
                    <div className="text-gray-400">Memoria Total</div>
                    <div className="text-white font-mono text-lg">{cacheInfo.incidencias_cache?.total_memory_human || '0KB'}</div>
                  </div>
                  <div>
                    <div className="text-gray-400">Timestamp</div>
                    <div className="text-white font-mono text-xs">{new Date(cacheInfo.timestamp).toLocaleString()}</div>
                  </div>
                </div>

                {/* Lista de Claves */}
                {cacheInfo.incidencias_cache?.keys && cacheInfo.incidencias_cache.keys.length > 0 ? (
                  <div className="space-y-2 max-h-64 overflow-y-auto">
                    <div className="text-gray-300 font-semibold text-sm border-b border-gray-700 pb-2">
                      Claves en Caché ({cacheInfo.incidencias_cache.keys.length})
                    </div>
                    {cacheInfo.incidencias_cache.keys.map((key, index) => (
                      <div key={index} className="bg-gray-900 rounded p-2 text-xs">
                        <div className="flex items-center justify-between">
                          <div className="font-mono text-blue-300 flex-1 mr-4 truncate">
                            {key.key}
                          </div>
                          <div className="flex items-center gap-2 text-gray-400">
                            <span>{key.ttl_human}</span>
                            <span>{key.memory_human}</span>
                            <button
                              onClick={() => {
                                // Extraer cierre_id de la clave si es posible
                                const match = key.key.match(/_(\d+)_/);
                                const cierreId = match ? parseInt(match[1]) : null;
                                if (cierreId) {
                                  handleLimpiarCache(cierreId);
                                }
                              }}
                              className="bg-red-600 hover:bg-red-700 text-white px-1 py-0.5 rounded"
                              title="Limpiar caché para este cierre"
                            >
                              🗑️
                            </button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-4 text-gray-400">
                    📭 No hay claves de incidencias en caché
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="text-center py-8 text-gray-400">
              ❌ Error cargando información del caché
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-gray-700">
          <div className="text-xs text-gray-400">
            💡 Tip: El caché se actualiza automáticamente cada 5 minutos. Usa "Forzar Actualización" en el modal de incidencias para bypass del caché.
          </div>
        </div>
      </div>
    </div>
  );
};

export default CacheDebugPanel;
