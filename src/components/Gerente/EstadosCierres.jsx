// src/components/Gerente/EstadosCierres.jsx
import { useState, useEffect } from 'react';
import { obtenerEstadosCierres, forzarRecalculoCierre } from '../../api/gerente';
import { 
  AlertCircle, 
  CheckCircle, 
  Clock, 
  RefreshCw, 
  TrendingUp, 
  Users, 
  Calendar,
  BarChart3,
  Settings,
  Eye,
  Search
} from 'lucide-react';

const EstadosCierres = () => {
  const [cierres, setCierres] = useState([]);
  const [resumen, setResumen] = useState(null);
  const [loading, setLoading] = useState(true);
  const [recalculando, setRecalculando] = useState({});
  const [error, setError] = useState('');
  const [filtroEstado, setFiltroEstado] = useState('');
  const [busquedaCliente, setBusquedaCliente] = useState('');
  // Removed filtroArea - el backend ya filtra por área del gerente

  useEffect(() => {
    cargarEstadosCierres();
    
    // Auto-refresh cada 30 segundos
    const interval = setInterval(cargarEstadosCierres, 30000);
    return () => clearInterval(interval);
  }, []);

  const cargarEstadosCierres = async () => {
    try {
      const data = await obtenerEstadosCierres();
      // El backend ahora devuelve la lista directamente
      setCierres(data || []);
      
      // Calcular resumen del frontend basado en los datos
      const resumenCalculado = {
        total: data?.length || 0,
        completados: data?.filter(c => ['completo', 'finalizado', 'cerrado', 'terminado'].includes(c.estado)).length || 0,
        en_proceso: data?.filter(c => ['procesando', 'clasificacion', 'generando_reportes'].includes(c.estado)).length || 0,
        error: data?.filter(c => c.estado === 'error').length || 0,
        pendiente: data?.filter(c => c.estado === 'pendiente').length || 0
      };
      setResumen(resumenCalculado);
      setError('');
    } catch (err) {
      console.error('Error cargando estados de cierres:', err);
      setError('Error al cargar los estados de cierres');
    } finally {
      setLoading(false);
    }
  };

  const handleForzarRecalculo = async (cierreId) => {
    try {
      setRecalculando(prev => ({ ...prev, [cierreId]: true }));
      await forzarRecalculoCierre(cierreId);
      await cargarEstadosCierres(); // Recargar datos
    } catch (err) {
      console.error('Error forzando recálculo:', err);
      setError('Error al forzar el recálculo del cierre');
    } finally {
      setRecalculando(prev => ({ ...prev, [cierreId]: false }));
    }
  };

  const getEstadoColor = (estado) => {
    const colors = {
      'pendiente': 'bg-yellow-100 text-yellow-800 border-yellow-200',
      'procesando': 'bg-blue-100 text-blue-800 border-blue-200',
      'clasificacion': 'bg-blue-100 text-blue-800 border-blue-200',
      'incidencias': 'bg-orange-100 text-orange-800 border-orange-200',
      'sin_incidencias': 'bg-emerald-100 text-emerald-800 border-emerald-200',
      'generando_reportes': 'bg-purple-100 text-purple-800 border-purple-200',
      'en_revision': 'bg-indigo-100 text-indigo-800 border-indigo-200',
      'rechazado': 'bg-red-100 text-red-800 border-red-200',
      'aprobado': 'bg-green-100 text-green-800 border-green-200',
      'finalizado': 'bg-green-500 text-green-800 border-green-500',
      'completo': 'bg-green-100 text-green-800 border-green-200',
      'error': 'bg-red-100 text-red-800 border-red-200',
      'cancelado': 'bg-gray-100 text-gray-800 border-gray-200'
    };
    return colors[estado] || 'bg-gray-100 text-gray-800 border-gray-200';
  };

  const getEstadoIcon = (estado) => {
    switch (estado) {
      case 'finalizado':
      case 'completo':
      case 'aprobado':
        return <CheckCircle className="w-4 h-4" />;
      case 'error':
      case 'rechazado':
        return <AlertCircle className="w-4 h-4" />;
      case 'procesando':
      case 'clasificacion':
      case 'generando_reportes':
        return <RefreshCw className="w-4 h-4 animate-spin" />;
      default:
        return <Clock className="w-4 h-4" />;
    }
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

  const cierresFiltrados = cierres.filter(cierre => {
    const matchEstado = !filtroEstado || cierre.estado === filtroEstado;
    const matchCliente = !busquedaCliente || 
      cierre.cliente_nombre.toLowerCase().includes(busquedaCliente.toLowerCase());
    // Removed area filter - backend handles area-based filtering
    return matchEstado && matchCliente;
  });

  // Removed areas extraction - no longer needed
  const estados = [...new Set(cierres.map(c => c.estado))].filter(Boolean);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 text-white p-6">
        <div className="flex justify-center items-center h-64">
          <RefreshCw className="w-8 h-8 animate-spin" />
          <span className="ml-2">Cargando estados de cierres...</span>
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
            <h1 className="text-3xl font-bold mb-2">Estados de Cierres Contables</h1>
            <p className="text-gray-400">Monitoreo en tiempo real de procesos de cierre</p>
          </div>
          <button
            onClick={cargarEstadosCierres}
            disabled={loading}
            className="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-800 px-4 py-2 rounded-lg flex items-center"
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Actualizar
          </button>
        </div>

        {/* Resumen de Estados */}
        {resumen && (
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4 mb-6">
            <div className="bg-gray-800 p-4 rounded-lg">
              <div className="flex items-center">
                <BarChart3 className="w-8 h-8 text-blue-500" />
                <div className="ml-3">
                  <p className="text-sm text-gray-400">Total Cierres</p>
                  <p className="text-2xl font-bold">{resumen.total || 0}</p>
                </div>
              </div>
            </div>
            <div className="bg-gray-800 p-4 rounded-lg">
              <div className="flex items-center">
                <CheckCircle className="w-8 h-8 text-green-500" />
                <div className="ml-3">
                  <p className="text-sm text-gray-400">Completados</p>
                  <p className="text-2xl font-bold">{resumen.completados || 0}</p>
                </div>
              </div>
            </div>
            <div className="bg-gray-800 p-4 rounded-lg">
              <div className="flex items-center">
                <RefreshCw className="w-8 h-8 text-blue-400" />
                <div className="ml-3">
                  <p className="text-sm text-gray-400">En Proceso</p>
                  <p className="text-2xl font-bold">{resumen.en_proceso || 0}</p>
                </div>
              </div>
            </div>
            <div className="bg-gray-800 p-4 rounded-lg">
              <div className="flex items-center">
                <AlertCircle className="w-8 h-8 text-red-500" />
                <div className="ml-3">
                  <p className="text-sm text-gray-400">Con Errores</p>
                  <p className="text-2xl font-bold">{resumen.error || 0}</p>
                </div>
              </div>
            </div>
            <div className="bg-gray-800 p-4 rounded-lg">
              <div className="flex items-center">
                <Clock className="w-8 h-8 text-yellow-500" />
                <div className="ml-3">
                  <p className="text-sm text-gray-400">Pendientes</p>
                  <p className="text-2xl font-bold">{resumen.pendiente || 0}</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Filtros */}
        <div className="bg-gray-800 p-4 rounded-lg mb-6">
          <div className="flex items-center mb-4">
            <Settings className="w-5 h-5 mr-2" />
            <h3 className="text-lg font-semibold">Filtros</h3>
            <button
              onClick={() => {
                setFiltroEstado('');
                setBusquedaCliente('');
                // Removed filtroArea reset
              }}
              className="ml-auto text-sm text-blue-400 hover:text-blue-300"
            >
              Limpiar filtros
            </button>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Estado</label>
              <select
                value={filtroEstado}
                onChange={(e) => setFiltroEstado(e.target.value)}
                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2"
              >
                <option value="">Todos los estados</option>
                {estados.map(estado => (
                  <option key={estado} value={estado}>
                    {estado.charAt(0).toUpperCase() + estado.slice(1).replace('_', ' ')}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Buscar Cliente</label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="Nombre del cliente..."
                  value={busquedaCliente}
                  onChange={(e) => setBusquedaCliente(e.target.value)}
                  className="w-full bg-gray-700 border border-gray-600 rounded pl-10 pr-3 py-2 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
            <div className="flex items-end">
              <div className="text-sm text-gray-400">
                Mostrando {cierresFiltrados.length} de {cierres.length} cierres
                <br />
                <span className="text-xs text-blue-400">
                  Filtrado por área del gerente
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="bg-red-600 text-white p-4 rounded-lg mb-6 flex items-center">
            <AlertCircle className="w-5 h-5 mr-2" />
            {error}
          </div>
        )}

        {/* Lista de Cierres */}
        <div className="space-y-4">
          {cierresFiltrados.map((cierre) => (
            <div key={cierre.id} className="bg-gray-800 rounded-lg p-6">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center mb-2">
                    <h3 className="text-lg font-semibold mr-3">
                      {cierre.cliente_nombre}
                    </h3>
                    <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium border ${getEstadoColor(cierre.estado)}`}>
                      {getEstadoIcon(cierre.estado)}
                      <span className="ml-1 capitalize">
                        {cierre.estado.replace('_', ' ')}
                      </span>
                    </span>
                    {cierre.area_nombre && (
                      <span className="ml-2 inline-flex items-center px-2 py-1 rounded text-xs bg-gray-700 text-gray-300">
                        <Users className="w-3 h-3 mr-1" />
                        {cierre.area_nombre}
                      </span>
                    )}
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                    <div>
                      <p className="text-gray-400 mb-1">Período</p>
                      <p className="font-medium flex items-center">
                        <Calendar className="w-4 h-4 mr-1" />
                        {cierre.periodo}
                      </p>
                    </div>
                    <div>
                      <p className="text-gray-400 mb-1">Iniciado</p>
                      <p className="font-medium">
                        {formatearFecha(cierre.fecha_creacion)}
                      </p>
                    </div>
                    <div>
                      <p className="text-gray-400 mb-1">
                        {['finalizado', 'completo', 'aprobado'].includes(cierre.estado) ? 'Completado' : 'Última actualización'}
                      </p>
                      <p className="font-medium">
                        {formatearFecha(cierre.fecha_finalizacion || cierre.fecha_cierre)}
                      </p>
                    </div>
                  </div>

                  {cierre.tiempo_en_estado_dias !== null && (
                    <div className="mt-2">
                      <p className="text-gray-400 text-sm mb-1">Tiempo en estado actual</p>
                      <p className="text-sm font-medium flex items-center">
                        <TrendingUp className="w-4 h-4 mr-1" />
                        {cierre.tiempo_en_estado_dias} días
                      </p>
                    </div>
                  )}

                  {cierre.ultima_actividad && (
                    <div className="mt-3">
                      <p className="text-gray-400 text-sm mb-1">Última actividad</p>
                      <p className="text-xs text-gray-400">{formatearFecha(cierre.ultima_actividad)}</p>
                    </div>
                  )}
                </div>

                <div className="flex flex-col space-y-2 ml-4">
                  {(cierre.estado === 'error' || cierre.estado === 'cancelado') && (
                    <button
                      onClick={() => handleForzarRecalculo(cierre.id)}
                      disabled={recalculando[cierre.id]}
                      className="bg-yellow-600 hover:bg-yellow-700 disabled:bg-yellow-800 px-3 py-2 rounded text-sm font-medium flex items-center"
                    >
                      {recalculando[cierre.id] ? (
                        <RefreshCw className="w-4 h-4 mr-1 animate-spin" />
                      ) : (
                        <RefreshCw className="w-4 h-4 mr-1" />
                      )}
                      Recalcular
                    </button>
                  )}
                  <button className="bg-gray-600 hover:bg-gray-700 px-3 py-2 rounded text-sm font-medium flex items-center">
                    <Eye className="w-4 h-4 mr-1" />
                    Ver Detalle
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Sin resultados */}
        {cierresFiltrados.length === 0 && !loading && (
          <div className="text-center py-12">
            <BarChart3 className="w-16 h-16 mx-auto text-gray-600 mb-4" />
            <h3 className="text-lg font-medium text-gray-300 mb-2">No se encontraron cierres</h3>
            <p className="text-gray-400">
              {filtroEstado || busquedaCliente ? 
                'Intenta ajustar los filtros para ver más resultados' : 
                'No hay cierres registrados en el sistema'
              }
            </p>
          </div>
        )}

        {/* Auto-refresh indicator */}
        <div className="fixed bottom-4 right-4 bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-xs text-gray-400">
          <RefreshCw className="w-3 h-3 inline mr-1" />
          Actualización automática cada 30s
        </div>
      </div>
    </div>
  );
};

export default EstadosCierres;
