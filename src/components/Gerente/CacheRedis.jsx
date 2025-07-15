// src/components/Gerente/CacheRedis.jsx
import { useState, useEffect } from 'react';
import { 
  obtenerEstadoCache, 
  limpiarCache, 
  cargarCierreACache,
  obtenerMetricasCache 
} from '../../api/gerente';
import { 
  Database, 
  Trash2, 
  RefreshCw, 
  HardDrive, 
  Clock, 
  Zap,
  BarChart3,
  AlertTriangle,
  CheckCircle,
  Activity,
  Download,
  Settings
} from 'lucide-react';

const CacheRedis = () => {
  const [estadoCache, setEstadoCache] = useState(null);
  const [metricas, setMetricas] = useState(null);
  const [loading, setLoading] = useState(true);
  const [operaciones, setOperaciones] = useState({});
  const [error, setError] = useState('');
  const [filtroTipo, setFiltroTipo] = useState('');
  const [mostrarDetalles, setMostrarDetalles] = useState({});

  useEffect(() => {
    cargarDatosCache();
    
    // Auto-refresh cada 15 segundos
    const interval = setInterval(cargarDatosCache, 15000);
    return () => clearInterval(interval);
  }, []);

  const cargarDatosCache = async () => {
    try {
      const [cacheData, metricsData] = await Promise.all([
        obtenerEstadoCache(),
        obtenerMetricasCache()
      ]);
      
      setEstadoCache(cacheData);
      setMetricas(metricsData);
      setError('');
    } catch (err) {
      console.error('Error cargando datos de cache:', err);
      setError('Error al cargar el estado del cache Redis');
    } finally {
      setLoading(false);
    }
  };

  const handleLimpiarCache = async (tipo, clienteId = null) => {
    const operacionKey = clienteId ? `${tipo}_${clienteId}` : tipo;
    
    try {
      setOperaciones(prev => ({ ...prev, [operacionKey]: 'limpiando' }));
      
      await limpiarCache({
        tipo: tipo,
        cliente_id: clienteId
      });
      
      await cargarDatosCache(); // Recargar datos
      
    } catch (err) {
      console.error('Error limpiando cache:', err);
      setError(`Error al limpiar cache ${tipo}`);
    } finally {
      setOperaciones(prev => ({ ...prev, [operacionKey]: null }));
    }
  };

  const handleCargarCierre = async (clienteId, mes, ano) => {
    const operacionKey = `cargar_${clienteId}_${mes}_${ano}`;
    
    try {
      setOperaciones(prev => ({ ...prev, [operacionKey]: 'cargando' }));
      
      await cargarCierreACache({
        cliente_id: clienteId,
        mes: mes,
        ano: ano
      });
      
      await cargarDatosCache(); // Recargar datos
      
    } catch (err) {
      console.error('Error cargando cierre a cache:', err);
      setError('Error al cargar cierre en cache');
    } finally {
      setOperaciones(prev => ({ ...prev, [operacionKey]: null }));
    }
  };

  const formatearTamano = (bytes) => {
    if (!bytes) return '0 B';
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  };

  const formatearTiempo = (segundos) => {
    if (!segundos) return 'N/A';
    if (segundos < 60) return `${segundos}s`;
    if (segundos < 3600) return `${Math.floor(segundos / 60)}m`;
    return `${Math.floor(segundos / 3600)}h ${Math.floor((segundos % 3600) / 60)}m`;
  };

  const getTipoColor = (tipo) => {
    const colors = {
      'esf': 'bg-blue-100 text-blue-800 border-blue-200',
      'eri': 'bg-green-100 text-green-800 border-green-200',
      'kpis': 'bg-purple-100 text-purple-800 border-purple-200',
      'clasificaciones': 'bg-orange-100 text-orange-800 border-orange-200',
      'general': 'bg-gray-100 text-gray-800 border-gray-200'
    };
    return colors[tipo] || 'bg-gray-100 text-gray-800 border-gray-200';
  };

  const getEstadoSalud = (porcentajeUso) => {
    if (porcentajeUso > 90) return { color: 'text-red-500', icon: AlertTriangle, estado: 'Crítico' };
    if (porcentajeUso > 70) return { color: 'text-yellow-500', icon: AlertTriangle, estado: 'Advertencia' };
    return { color: 'text-green-500', icon: CheckCircle, estado: 'Saludable' };
  };

  // Filtrar datos por tipo
  const datosFiltrados = estadoCache?.datos_por_tipo ? 
    Object.entries(estadoCache.datos_por_tipo).filter(([tipo]) => 
      !filtroTipo || tipo === filtroTipo
    ) : [];

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 text-white p-6">
        <div className="flex justify-center items-center h-64">
          <RefreshCw className="w-8 h-8 animate-spin" />
          <span className="ml-2">Cargando estado del cache Redis...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-3xl font-bold mb-2">Gestión Cache Redis</h1>
            <p className="text-gray-400">Monitoreo y administración del sistema de caché</p>
          </div>
          <button
            onClick={cargarDatosCache}
            disabled={loading}
            className="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-800 px-4 py-2 rounded-lg flex items-center"
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Actualizar
          </button>
        </div>

        {/* Resumen General */}
        {estadoCache && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-gray-800 p-4 rounded-lg">
              <div className="flex items-center">
                <Database className="w-8 h-8 text-blue-500" />
                <div className="ml-3">
                  <p className="text-sm text-gray-400">Claves Totales</p>
                  <p className="text-2xl font-bold">{estadoCache.total_claves || 0}</p>
                </div>
              </div>
            </div>
            <div className="bg-gray-800 p-4 rounded-lg">
              <div className="flex items-center">
                <HardDrive className="w-8 h-8 text-green-500" />
                <div className="ml-3">
                  <p className="text-sm text-gray-400">Memoria Usada</p>
                  <p className="text-2xl font-bold">{formatearTamano(estadoCache.memoria_usada)}</p>
                </div>
              </div>
            </div>
            <div className="bg-gray-800 p-4 rounded-lg">
              <div className="flex items-center">
                <Clock className="w-8 h-8 text-purple-500" />
                <div className="ml-3">
                  <p className="text-sm text-gray-400">Uptime</p>
                  <p className="text-2xl font-bold">{formatearTiempo(estadoCache.uptime_segundos)}</p>
                </div>
              </div>
            </div>
            <div className="bg-gray-800 p-4 rounded-lg">
              <div className="flex items-center">
                {(() => {
                  const salud = getEstadoSalud(estadoCache.porcentaje_memoria || 0);
                  const IconComponent = salud.icon;
                  return (
                    <>
                      <IconComponent className={`w-8 h-8 ${salud.color}`} />
                      <div className="ml-3">
                        <p className="text-sm text-gray-400">Estado</p>
                        <p className={`text-lg font-bold ${salud.color}`}>{salud.estado}</p>
                      </div>
                    </>
                  );
                })()}
              </div>
            </div>
          </div>
        )}

        {/* Métricas de Rendimiento */}
        {metricas && (
          <div className="bg-gray-800 p-6 rounded-lg mb-6">
            <h3 className="text-lg font-semibold mb-4 flex items-center">
              <BarChart3 className="w-5 h-5 mr-2" />
              Métricas de Rendimiento
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-gray-700 p-4 rounded">
                <p className="text-sm text-gray-400 mb-1">Hit Rate</p>
                <div className="flex items-center">
                  <div className="flex-1 bg-gray-600 rounded-full h-2 mr-3">
                    <div 
                      className="bg-green-500 h-2 rounded-full"
                      style={{ width: `${metricas.hit_rate || 0}%` }}
                    ></div>
                  </div>
                  <span className="text-sm font-bold">{metricas.hit_rate?.toFixed(1) || 0}%</span>
                </div>
              </div>
              <div className="bg-gray-700 p-4 rounded">
                <p className="text-sm text-gray-400 mb-1">Operaciones/seg</p>
                <p className="text-xl font-bold flex items-center">
                  <Activity className="w-4 h-4 mr-1" />
                  {metricas.ops_por_segundo || 0}
                </p>
              </div>
              <div className="bg-gray-700 p-4 rounded">
                <p className="text-sm text-gray-400 mb-1">Conectados</p>
                <p className="text-xl font-bold">{metricas.clientes_conectados || 0}</p>
              </div>
            </div>
          </div>
        )}

        {/* Filtros */}
        <div className="bg-gray-800 p-4 rounded-lg mb-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center">
              <Settings className="w-5 h-5 mr-2" />
              <h3 className="text-lg font-semibold">Gestión por Tipo de Cache</h3>
            </div>
            <select
              value={filtroTipo}
              onChange={(e) => setFiltroTipo(e.target.value)}
              className="bg-gray-700 border border-gray-600 rounded px-3 py-2"
            >
              <option value="">Todos los tipos</option>
              <option value="esf">ESF</option>
              <option value="eri">ERI</option>
              <option value="kpis">KPIs</option>
              <option value="clasificaciones">Clasificaciones</option>
              <option value="general">General</option>
            </select>
          </div>

          {/* Acciones Globales */}
          <div className="flex flex-wrap gap-3">
            <button
              onClick={() => handleLimpiarCache('todo')}
              disabled={operaciones['todo']}
              className="bg-red-600 hover:bg-red-700 disabled:bg-red-800 px-4 py-2 rounded flex items-center"
            >
              {operaciones['todo'] ? (
                <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <Trash2 className="w-4 h-4 mr-2" />
              )}
              Limpiar Todo el Cache
            </button>
            <button
              onClick={() => handleLimpiarCache('expirados')}
              disabled={operaciones['expirados']}
              className="bg-yellow-600 hover:bg-yellow-700 disabled:bg-yellow-800 px-4 py-2 rounded flex items-center"
            >
              {operaciones['expirados'] ? (
                <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <Clock className="w-4 h-4 mr-2" />
              )}
              Limpiar Expirados
            </button>
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="bg-red-600 text-white p-4 rounded-lg mb-6 flex items-center">
            <AlertTriangle className="w-5 h-5 mr-2" />
            {error}
          </div>
        )}

        {/* Datos por Tipo */}
        <div className="space-y-4">
          {datosFiltrados.map(([tipo, datos]) => (
            <div key={tipo} className="bg-gray-800 rounded-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center">
                  <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium border ${getTipoColor(tipo)}`}>
                    {tipo.toUpperCase()}
                  </span>
                  <div className="ml-4">
                    <p className="text-sm text-gray-400">
                      {datos.total_claves} claves • {formatearTamano(datos.memoria_usada)}
                    </p>
                  </div>
                </div>
                <div className="flex space-x-2">
                  <button
                    onClick={() => setMostrarDetalles(prev => ({
                      ...prev,
                      [tipo]: !prev[tipo]
                    }))}
                    className="bg-gray-600 hover:bg-gray-700 px-3 py-1 rounded text-sm"
                  >
                    {mostrarDetalles[tipo] ? 'Ocultar' : 'Ver'} Detalles
                  </button>
                  <button
                    onClick={() => handleLimpiarCache(tipo)}
                    disabled={operaciones[tipo]}
                    className="bg-red-600 hover:bg-red-700 disabled:bg-red-800 px-3 py-1 rounded text-sm flex items-center"
                  >
                    {operaciones[tipo] ? (
                      <RefreshCw className="w-3 h-3 mr-1 animate-spin" />
                    ) : (
                      <Trash2 className="w-3 h-3 mr-1" />
                    )}
                    Limpiar
                  </button>
                </div>
              </div>

              {/* Detalles expandidos */}
              {mostrarDetalles[tipo] && datos.clientes && (
                <div className="border-t border-gray-700 pt-4 mt-4">
                  <h4 className="text-sm font-medium text-gray-300 mb-3">Datos por Cliente</h4>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                    {Object.entries(datos.clientes).map(([clienteId, clienteData]) => (
                      <div key={clienteId} className="bg-gray-700 p-3 rounded">
                        <div className="flex justify-between items-start mb-2">
                          <div>
                            <p className="font-medium text-sm">{clienteData.nombre}</p>
                            <p className="text-xs text-gray-400">
                              {clienteData.claves} claves • {formatearTamano(clienteData.memoria)}
                            </p>
                          </div>
                          <button
                            onClick={() => handleLimpiarCache(tipo, clienteId)}
                            disabled={operaciones[`${tipo}_${clienteId}`]}
                            className="bg-red-500 hover:bg-red-600 disabled:bg-red-700 p-1 rounded text-xs"
                          >
                            {operaciones[`${tipo}_${clienteId}`] ? (
                              <RefreshCw className="w-3 h-3 animate-spin" />
                            ) : (
                              <Trash2 className="w-3 h-3" />
                            )}
                          </button>
                        </div>
                        
                        {clienteData.ultimo_cierre && (
                          <div className="text-xs text-gray-400 mb-2">
                            Último cierre: {clienteData.ultimo_cierre.mes}/{clienteData.ultimo_cierre.ano}
                          </div>
                        )}
                        
                        <div className="flex space-x-1">
                          <button
                            onClick={() => handleCargarCierre(
                              clienteId, 
                              clienteData.ultimo_cierre?.mes || new Date().getMonth() + 1,
                              clienteData.ultimo_cierre?.ano || new Date().getFullYear()
                            )}
                            disabled={operaciones[`cargar_${clienteId}_${clienteData.ultimo_cierre?.mes}_${clienteData.ultimo_cierre?.ano}`]}
                            className="bg-blue-500 hover:bg-blue-600 disabled:bg-blue-700 px-2 py-1 rounded text-xs flex items-center"
                          >
                            {operaciones[`cargar_${clienteId}_${clienteData.ultimo_cierre?.mes}_${clienteData.ultimo_cierre?.ano}`] ? (
                              <RefreshCw className="w-3 h-3 animate-spin" />
                            ) : (
                              <Download className="w-3 h-3" />
                            )}
                            <span className="ml-1">Cargar</span>
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Sin datos */}
        {datosFiltrados.length === 0 && !loading && (
          <div className="text-center py-12">
            <Database className="w-16 h-16 mx-auto text-gray-600 mb-4" />
            <h3 className="text-lg font-medium text-gray-300 mb-2">No hay datos de cache</h3>
            <p className="text-gray-400">
              {filtroTipo ? 
                `No se encontraron datos para el tipo "${filtroTipo}"` :
                'El cache está vacío o no se pudieron cargar los datos'
              }
            </p>
          </div>
        )}

        {/* Auto-refresh indicator */}
        <div className="fixed bottom-4 right-4 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-xs text-gray-400">
          <RefreshCw className="w-3 h-3 inline mr-1" />
          Actualización automática cada 15s
        </div>
      </div>
    </div>
  );
};

export default CacheRedis;
