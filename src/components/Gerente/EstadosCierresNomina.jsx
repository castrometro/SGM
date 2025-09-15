// src/components/Gerente/EstadosCierresNomina.jsx
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { obtenerEstadosCierresNomina, forzarRecalculoCierreNomina } from '../../api/gerenteNomina';
import { obtenerCliente } from '../../api/clientes';
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

const EstadosCierresNomina = () => {
  const navigate = useNavigate();
  const [cierres, setCierres] = useState([]);
  const [resumen, setResumen] = useState(null);
  const [loading, setLoading] = useState(true);
  const [recalculando, setRecalculando] = useState({});
  const [error, setError] = useState('');
  const [filtroEstado, setFiltroEstado] = useState('');
  const [busquedaCliente, setBusquedaCliente] = useState('');

  useEffect(() => {
    cargarEstadosCierres();
    
    // Auto-refresh cada 30 segundos
    const interval = setInterval(cargarEstadosCierres, 30000);
    return () => clearInterval(interval);
  }, []);

  const cargarEstadosCierres = async () => {
    try {
      const data = await obtenerEstadosCierresNomina();
      console.log('=== DEBUG: Datos de nómina cargados ===');
      console.log('Total cierres:', data?.length || 0);
      
      // Procesar los datos para enriquecer con información de clientes
      const cierresEnriquecidos = await Promise.all(
        (data || []).map(async (cierre) => {
          try {
            // Obtener información del cliente usando la API
            const clienteData = await obtenerCliente(cierre.cliente);
            
            return {
              ...cierre,
              cliente_nombre: clienteData?.nombre || `Cliente ${cierre.cliente}`,
              cliente_id: cierre.cliente,
              // Mapear campos para compatibilidad
              usuario_id: cierre.usuario_analista,
              area_nombre: 'Nómina' // Siempre es nómina
            };
          } catch (error) {
            console.error(`Error obteniendo cliente ${cierre.cliente}:`, error);
            return {
              ...cierre,
              cliente_nombre: `Cliente ${cierre.cliente}`,
              cliente_id: cierre.cliente,
              usuario_id: cierre.usuario_analista,
              area_nombre: 'Nómina'
            };
          }
        })
      );
      
      setCierres(cierresEnriquecidos);
      
      // Calcular resumen del frontend basado en los datos enriquecidos
      const resumenCalculado = {
        total: cierresEnriquecidos?.length || 0,
        completados: cierresEnriquecidos?.filter(c => ['finalizado'].includes(c.estado)).length || 0,
        en_proceso: cierresEnriquecidos?.filter(c => [
          'cargando_archivos', 
          'archivos_completos',
          'verificacion_datos', 
          'datos_consolidados',
          'validacion_final'
        ].includes(c.estado)).length || 0,
        con_discrepancias: cierresEnriquecidos?.filter(c => ['con_discrepancias'].includes(c.estado)).length || 0,
        con_incidencias: cierresEnriquecidos?.filter(c => ['con_incidencias'].includes(c.estado)).length || 0,
        pendiente: cierresEnriquecidos?.filter(c => c.estado === 'pendiente').length || 0
      };
      setResumen(resumenCalculado);
      setError('');
    } catch (err) {
      console.error('Error cargando estados de cierres de nómina:', err);
      setError('Error al cargar los estados de cierres de nómina');
    } finally {
      setLoading(false);
    }
  };  const handleForzarRecalculo = async (cierreId) => {
    try {
      setRecalculando(prev => ({ ...prev, [cierreId]: true }));
      await forzarRecalculoCierreNomina(cierreId);
      await cargarEstadosCierres(); // Recargar datos
    } catch (err) {
      console.error('Error forzando recálculo:', err);
      setError('Error al forzar el recálculo del cierre de nómina');
    } finally {
      setRecalculando(prev => ({ ...prev, [cierreId]: false }));
    }
  };

  const handleVerDetalle = (cierreId) => {
    // Navegar al detalle del cierre de nómina
    navigate(`/menu/nomina/cierres/${cierreId}`);
  };

  const obtenerNombreCliente = (cierre) => {
    // Los datos ya están enriquecidos con el nombre del cliente
    return cierre.cliente_nombre || `Cliente ${cierre.cliente_id || cierre.cliente}`;
  };

  const getEstadoColor = (estado) => {
    const colors = {
      'pendiente': 'bg-yellow-100 text-yellow-800 border-yellow-200',
      'cargando_archivos': 'bg-blue-100 text-blue-800 border-blue-200',
      'archivos_completos': 'bg-blue-100 text-blue-800 border-blue-200',
      'verificacion_datos': 'bg-purple-100 text-purple-800 border-purple-200',
      'verificado_sin_discrepancias': 'bg-emerald-100 text-emerald-800 border-emerald-200',
      'datos_consolidados': 'bg-green-100 text-green-800 border-green-200',
      'con_discrepancias': 'bg-orange-100 text-orange-800 border-orange-200',
      'con_incidencias': 'bg-red-100 text-red-800 border-red-200',
      'incidencias_resueltas': 'bg-emerald-100 text-emerald-800 border-emerald-200',
      'requiere_recarga_archivos': 'bg-amber-100 text-amber-800 border-amber-200',
      'validacion_final': 'bg-indigo-100 text-indigo-800 border-indigo-200',
      'finalizado': 'bg-green-500 text-white border-green-500'
    };
    return colors[estado] || 'bg-gray-100 text-gray-800 border-gray-200';
  };

  const getEstadoIcon = (estado) => {
    switch (estado) {
      case 'finalizado':
        return <CheckCircle className="w-4 h-4" />;
      case 'con_discrepancias':
      case 'con_incidencias':
      case 'requiere_recarga_archivos':
        return <AlertCircle className="w-4 h-4" />;
      case 'cargando_archivos':
      case 'verificacion_datos':
      case 'validacion_final':
        return <RefreshCw className="w-4 h-4 animate-spin" />;
      case 'archivos_completos':
      case 'verificado_sin_discrepancias':
      case 'datos_consolidados':
      case 'incidencias_resueltas':
        return <CheckCircle className="w-4 h-4" />;
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
    const nombreCliente = obtenerNombreCliente(cierre);
    const matchCliente = !busquedaCliente || 
      nombreCliente.toLowerCase().includes(busquedaCliente.toLowerCase());
    return matchEstado && matchCliente;
  });

  const estados = [...new Set(cierres.map(c => c.estado))].filter(Boolean);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 text-white p-6">
        <div className="flex justify-center items-center h-64">
          <RefreshCw className="w-8 h-8 animate-spin" />
          <span className="ml-2">Cargando estados de cierres de nómina...</span>
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
            <h1 className="text-3xl font-bold mb-2">Estados de Cierres de Nómina</h1>
            <p className="text-gray-400">Monitoreo en tiempo real de procesos de cierre de nómina</p>
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
          <div className="grid grid-cols-1 md:grid-cols-6 gap-4 mb-6">
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
                  <p className="text-sm text-gray-400">Finalizados</p>
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
                <AlertCircle className="w-8 h-8 text-orange-500" />
                <div className="ml-3">
                  <p className="text-sm text-gray-400">Con Discrepancias</p>
                  <p className="text-2xl font-bold">{resumen.con_discrepancias || 0}</p>
                </div>
              </div>
            </div>
            <div className="bg-gray-800 p-4 rounded-lg">
              <div className="flex items-center">
                <AlertCircle className="w-8 h-8 text-red-500" />
                <div className="ml-3">
                  <p className="text-sm text-gray-400">Con Incidencias</p>
                  <p className="text-2xl font-bold">{resumen.con_incidencias || 0}</p>
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
                      {obtenerNombreCliente(cierre)}
                    </h3>
                    <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium border ${getEstadoColor(cierre.estado)}`}>
                      {getEstadoIcon(cierre.estado)}
                      <span className="ml-1 capitalize">
                        {cierre.estado.replace('_', ' ')}
                      </span>
                    </span>
                    {cierre.usuario_analista && (
                      <span className="ml-2 inline-flex items-center px-2 py-1 rounded text-xs bg-gray-700 text-gray-300">
                        <Users className="w-3 h-3 mr-1" />
                        {cierre.usuario_analista.username || cierre.usuario_analista}
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
                        {['finalizado'].includes(cierre.estado) ? 'Finalizado' : 'Última actualización'}
                      </p>
                      <p className="font-medium">
                        {formatearFecha(cierre.fecha_finalizacion || cierre.fecha_creacion)}
                      </p>
                    </div>
                  </div>

                  {/* Información adicional específica de nómina */}
                  {cierre.estado_incidencias && cierre.estado_incidencias !== 'pendiente' && (
                    <div className="mt-2">
                      <p className="text-gray-400 text-sm mb-1">Estado de Incidencias</p>
                      <p className="text-sm font-medium flex items-center">
                        <TrendingUp className="w-4 h-4 mr-1" />
                        {cierre.estado_incidencias.replace('_', ' ')}
                        {cierre.total_incidencias > 0 && (
                          <span className="ml-2 text-xs bg-red-100 text-red-800 px-2 py-1 rounded">
                            {cierre.total_incidencias} incidencias
                          </span>
                        )}
                      </p>
                    </div>
                  )}

                  {cierre.estado_consolidacion && cierre.estado_consolidacion !== 'pendiente' && (
                    <div className="mt-2">
                      <p className="text-gray-400 text-sm mb-1">Estado de Consolidación</p>
                      <p className="text-sm font-medium flex items-center">
                        <BarChart3 className="w-4 h-4 mr-1" />
                        {cierre.estado_consolidacion.replace('_', ' ')}
                        {cierre.estado_consolidacion === 'consolidando' && (
                          <span className="ml-2 inline-flex items-center gap-1 text-yellow-300 text-xs bg-yellow-900/40 border border-yellow-700 px-2 py-0.5 rounded-full">
                            <svg className="animate-spin h-3 w-3" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"></path>
                            </svg>
                            en progreso
                          </span>
                        )}
                      </p>
                    </div>
                  )}
                </div>

                <div className="flex flex-col space-y-2 ml-4">
                  {(['con_discrepancias', 'con_incidencias', 'requiere_recarga_archivos'].includes(cierre.estado)) && (
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
                      {cierre.estado === 'requiere_recarga_archivos' ? 'Recargar' : 'Reprocesar'}
                    </button>
                  )}
                  <button 
                    onClick={() => handleVerDetalle(cierre.id)}
                    className="bg-gray-600 hover:bg-gray-700 px-3 py-2 rounded text-sm font-medium flex items-center"
                  >
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
            <h3 className="text-lg font-medium text-gray-300 mb-2">No se encontraron cierres de nómina</h3>
            <p className="text-gray-400">
              {filtroEstado || busquedaCliente ? 
                'Intenta ajustar los filtros para ver más resultados' : 
                'No hay cierres de nómina registrados en el sistema'
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

export default EstadosCierresNomina;
