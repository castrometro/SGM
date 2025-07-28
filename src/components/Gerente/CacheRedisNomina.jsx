// src/components/Gerente/CacheRedisNomina.jsx
import { useState, useEffect } from 'react';
import { 
  obtenerEstadoCacheNomina, 
  limpiarCacheNomina, 
  cargarCierreACacheNomina,
  obtenerMetricasCacheNomina 
} from '../../api/gerenteNomina';
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

const CacheRedisNomina = () => {
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
        obtenerEstadoCacheNomina(),
        obtenerMetricasCacheNomina()
      ]);
      
      setEstadoCache(cacheData);
      setMetricas(metricsData);
      setError('');
    } catch (err) {
      console.error('Error cargando datos de cache de nómina:', err);
      setError('Error al cargar el estado del cache Redis de nómina');
    } finally {
      setLoading(false);
    }
  };

  const handleLimpiarCache = async (tipo, clienteId = null) => {
    const operacionKey = clienteId ? `${tipo}_${clienteId}` : tipo;
    
    try {
      setOperaciones(prev => ({ ...prev, [operacionKey]: 'limpiando' }));
      
      await limpiarCacheNomina({
        tipo: tipo,
        cliente_id: clienteId
      });
      
      await cargarDatosCache(); // Recargar datos
      
    } catch (err) {
      console.error('Error limpiando cache de nómina:', err);
      setError(`Error al limpiar cache ${tipo} de nómina`);
    } finally {
      setOperaciones(prev => ({ ...prev, [operacionKey]: null }));
    }
  };

  const handleCargarCierre = async (clienteId, periodo) => {
    const operacionKey = `cargar_${clienteId}_${periodo}`;
    
    try {
      setOperaciones(prev => ({ ...prev, [operacionKey]: 'cargando' }));
      
      await cargarCierreACacheNomina(clienteId, periodo);
      
      await cargarDatosCache(); // Recargar datos
      
    } catch (err) {
      console.error('Error cargando cierre de nómina a cache:', err);
      setError('Error al cargar cierre de nómina en cache');
    } finally {
      setOperaciones(prev => ({ ...prev, [operacionKey]: null }));
    }
  };

  const formatBytes = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatearFecha = (fecha) => {
    if (!fecha) return 'N/A';
    return new Date(fecha).toLocaleString('es-CL', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getHealthColor = (health) => {
    switch (health) {
      case 'healthy': return 'text-green-500';
      case 'warning': return 'text-yellow-500';
      case 'critical': return 'text-red-500';
      default: return 'text-gray-500';
    }
  };

  const getHealthIcon = (health) => {
    switch (health) {
      case 'healthy': return <CheckCircle className="w-5 h-5" />;
      case 'warning': return <AlertTriangle className="w-5 h-5" />;
      case 'critical': return <AlertTriangle className="w-5 h-5" />;
      default: return <Database className="w-5 h-5" />;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 text-white p-6">
        <div className="flex justify-center items-center h-64">
          <RefreshCw className="w-8 h-8 animate-spin" />
          <span className="ml-2">Cargando estado del cache de nómina...</span>
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
            <h1 className="text-3xl font-bold mb-2">Cache Redis - Nómina</h1>
            <p className="text-gray-400">Gestión y monitoreo del cache Redis para nómina</p>
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

        {/* Error */}
        {error && (
          <div className="bg-red-600 text-white p-4 rounded-lg mb-6 flex items-center">
            <AlertTriangle className="w-5 h-5 mr-2" />
            {error}
          </div>
        )}

        {/* Métricas Generales */}
        {metricas && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-gray-800 p-4 rounded-lg">
              <div className="flex items-center">
                <div className={getHealthColor(metricas.health)}>
                  {getHealthIcon(metricas.health)}
                </div>
                <div className="ml-3">
                  <p className="text-sm text-gray-400">Estado General</p>
                  <p className="text-lg font-bold capitalize">{metricas.health || 'N/A'}</p>
                </div>
              </div>
            </div>
            <div className="bg-gray-800 p-4 rounded-lg">
              <div className="flex items-center">
                <HardDrive className="w-8 h-8 text-blue-500" />
                <div className="ml-3">
                  <p className="text-sm text-gray-400">Memoria Usada</p>
                  <p className="text-lg font-bold">{formatBytes(metricas.memoria_usada || 0)}</p>
                </div>
              </div>
            </div>
            <div className="bg-gray-800 p-4 rounded-lg">
              <div className="flex items-center">
                <Activity className="w-8 h-8 text-green-500" />
                <div className="ml-3">
                  <p className="text-sm text-gray-400">Conexiones</p>
                  <p className="text-lg font-bold">{metricas.conexiones_activas || 0}</p>
                </div>
              </div>
            </div>
            <div className="bg-gray-800 p-4 rounded-lg">
              <div className="flex items-center">
                <Clock className="w-8 h-8 text-purple-500" />
                <div className="ml-3">
                  <p className="text-sm text-gray-400">Uptime</p>
                  <p className="text-lg font-bold">{metricas.uptime_hours || 0}h</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Estadísticas de Cache */}
        {estadoCache && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            <div className="bg-gray-800 p-6 rounded-lg">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold">Estadísticas de Nómina</h3>
                <BarChart3 className="w-5 h-5 text-blue-500" />
              </div>
              
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-400">Total de Claves:</span>
                  <span className="font-medium">{estadoCache.total_keys || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Cierres en Cache:</span>
                  <span className="font-medium">{estadoCache.cierres_nomina || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Planillas:</span>
                  <span className="font-medium">{estadoCache.planillas || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Empleados:</span>
                  <span className="font-medium">{estadoCache.empleados || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Remuneraciones:</span>
                  <span className="font-medium">{estadoCache.remuneraciones || 0}</span>
                </div>
              </div>
            </div>

            <div className="bg-gray-800 p-6 rounded-lg">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold">Rendimiento</h3>
                <Zap className="w-5 h-5 text-yellow-500" />
              </div>
              
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-400">Hit Rate:</span>
                  <span className="font-medium">{metricas?.hit_rate ? `${metricas.hit_rate}%` : 'N/A'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Comandos/seg:</span>
                  <span className="font-medium">{metricas?.ops_per_sec || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Última Actualización:</span>
                  <span className="font-medium text-sm">{formatearFecha(estadoCache.ultima_actualizacion)}</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Filtros */}
        <div className="bg-gray-800 p-4 rounded-lg mb-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center">
              <Settings className="w-5 h-5 mr-2" />
              <h3 className="text-lg font-semibold">Gestión de Cache</h3>
            </div>
            <select
              value={filtroTipo}
              onChange={(e) => setFiltroTipo(e.target.value)}
              className="bg-gray-700 border border-gray-600 rounded px-3 py-2"
            >
              <option value="">Todos los tipos</option>
              <option value="nomina">Nómina</option>
              <option value="planillas">Planillas</option>
              <option value="empleados">Empleados</option>
              <option value="remuneraciones">Remuneraciones</option>
            </select>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <button
              onClick={() => handleLimpiarCache('todos')}
              disabled={operaciones['todos'] === 'limpiando'}
              className="bg-red-600 hover:bg-red-700 disabled:bg-red-800 px-4 py-2 rounded-lg flex items-center justify-center"
            >
              {operaciones['todos'] === 'limpiando' ? (
                <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <Trash2 className="w-4 h-4 mr-2" />
              )}
              Limpiar Todo
            </button>
            
            <button
              onClick={() => handleLimpiarCache('nomina')}
              disabled={operaciones['nomina'] === 'limpiando'}
              className="bg-orange-600 hover:bg-orange-700 disabled:bg-orange-800 px-4 py-2 rounded-lg flex items-center justify-center"
            >
              {operaciones['nomina'] === 'limpiando' ? (
                <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <Trash2 className="w-4 h-4 mr-2" />
              )}
              Limpiar Nómina
            </button>

            <button
              onClick={() => handleLimpiarCache('planillas')}
              disabled={operaciones['planillas'] === 'limpiando'}
              className="bg-purple-600 hover:bg-purple-700 disabled:bg-purple-800 px-4 py-2 rounded-lg flex items-center justify-center"
            >
              {operaciones['planillas'] === 'limpiando' ? (
                <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <Trash2 className="w-4 h-4 mr-2" />
              )}
              Limpiar Planillas
            </button>

            <button
              onClick={() => handleLimpiarCache('empleados')}
              disabled={operaciones['empleados'] === 'limpiando'}
              className="bg-yellow-600 hover:bg-yellow-700 disabled:bg-yellow-800 px-4 py-2 rounded-lg flex items-center justify-center"
            >
              {operaciones['empleados'] === 'limpiando' ? (
                <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <Trash2 className="w-4 h-4 mr-2" />
              )}
              Limpiar Empleados
            </button>
          </div>
        </div>

        {/* Lista de Cierres en Cache */}
        {estadoCache?.cierres_detalle && estadoCache.cierres_detalle.length > 0 && (
          <div className="bg-gray-800 rounded-lg">
            <div className="p-4 border-b border-gray-700">
              <h3 className="text-lg font-semibold">Cierres de Nómina en Cache</h3>
            </div>
            
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-700">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                      Cliente
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                      Período
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                      Tamaño
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                      Última Actualización
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                      Acciones
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-700">
                  {estadoCache.cierres_detalle
                    .filter(cierre => !filtroTipo || cierre.tipo === filtroTipo)
                    .map((cierre, index) => (
                    <tr key={index} className="hover:bg-gray-700">
                      <td className="px-4 py-4 whitespace-nowrap text-sm font-medium">
                        {cierre.cliente_nombre}
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap text-sm">
                        {cierre.periodo}
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap text-sm">
                        {formatBytes(cierre.size || 0)}
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap text-sm text-gray-400">
                        {formatearFecha(cierre.last_access)}
                      </td>
                      <td className="px-4 py-4 whitespace-nowrap text-sm">
                        <div className="flex space-x-2">
                          <button
                            onClick={() => handleLimpiarCache('cierre', cierre.cliente_id)}
                            disabled={operaciones[`cierre_${cierre.cliente_id}`] === 'limpiando'}
                            className="bg-red-600 hover:bg-red-700 disabled:bg-red-800 px-2 py-1 rounded text-xs flex items-center"
                          >
                            {operaciones[`cierre_${cierre.cliente_id}`] === 'limpiando' ? (
                              <RefreshCw className="w-3 h-3 animate-spin" />
                            ) : (
                              <Trash2 className="w-3 h-3" />
                            )}
                          </button>
                          <button
                            onClick={() => handleCargarCierre(cierre.cliente_id, cierre.periodo)}
                            disabled={operaciones[`cargar_${cierre.cliente_id}_${cierre.periodo}`] === 'cargando'}
                            className="bg-green-600 hover:bg-green-700 disabled:bg-green-800 px-2 py-1 rounded text-xs flex items-center"
                          >
                            {operaciones[`cargar_${cierre.cliente_id}_${cierre.periodo}`] === 'cargando' ? (
                              <RefreshCw className="w-3 h-3 animate-spin" />
                            ) : (
                              <Download className="w-3 h-3" />
                            )}
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
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

export default CacheRedisNomina;
