// src/components/Gerente/LogsActividadNomina.jsx
import { useState, useEffect } from 'react';
import { 
  obtenerLogsActividadNomina, 
  obtenerLogsActividadPorCierre,
  obtenerLogsActividadPorTipo,
  obtenerEstadisticasActividadNomina, 
  obtenerUsuariosActividadNomina,
  obtenerUsuariosConectadosNomina,
  obtenerPeriodosDisponiblesNomina,
  obtenerEstadisticasRedisLogsNomina
} from '../../api/gerenteNomina';
import { 
  Search, Filter, Calendar, User, FileText, Activity, RefreshCw, 
  Users, Clock, BarChart3, Wifi, WifiOff, Eye, TrendingUp 
} from 'lucide-react';

const LogsActividadNomina = () => {
  const [logs, setLogs] = useState([]);
  const [logsOriginales, setLogsOriginales] = useState([]);
  const [estadisticas, setEstadisticas] = useState(null);
  const [usuarios, setUsuarios] = useState([]);
  const [clientes, setClientes] = useState([]);
  const [periodos, setPeriodos] = useState([]);
  const [usuariosConectados, setUsuariosConectados] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [dataSource, setDataSource] = useState(null);
  
  // Estados de filtros - Solo para frontend
  const [filtrosFrontend, setFiltrosFrontend] = useState({
    cliente_id: '',
    usuario_id: '',
    periodo: ''
  });

  // Filtros para backend - Solo para paginación
  const [filtrosBackend, setFiltrosBackend] = useState({
    page: 1,
    page_size: 100,
    force_redis: true
  });
  
  const [paginacion, setPaginacion] = useState({
    count: 0,
    total_pages: 0,
    current_page: 1,
    has_next: false,
    has_previous: false
  });

  useEffect(() => {
    cargarDatos();
  }, [filtrosBackend]);

  // Auto-refresh para usuarios conectados cada 30 segundos
  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const conectadosData = await obtenerUsuariosConectadosNomina();
        setUsuariosConectados(conectadosData.usuarios_conectados || []);
      } catch (err) {
        console.error('Error actualizando usuarios conectados:', err);
      }
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  const cargarDatos = async () => {
    try {
      setLoading(true);
      
      let logsData = { results: [], count: 0, total_pages: 0, current_page: 1, has_next: false, has_previous: false };
      let statsData = null;
      let usuariosData = usuarios.length > 0 ? usuarios : [];
      let conectadosData = { usuarios_conectados: [] };

      try {
        console.log('=== DEBUG: Obteniendo logs de actividad de nómina (archivos y cierres) ===');
        console.log('Filtros aplicados:', { ...filtrosBackend, ...filtrosFrontend });
        
        // Combinar filtros de frontend con backend para la nueva función
        const filtrosCombinados = {
          ...filtrosBackend,
          cierre_id: filtrosFrontend.periodo || '', // Mapear período a cierre_id si hay
          usuario_id: filtrosFrontend.usuario_id || '',
          tarjeta: 'general', // Por defecto buscar tarjeta general
        };
        
        logsData = await obtenerLogsActividadNomina(filtrosCombinados);
        setDataSource('nomina-files-activity');
        
        console.log('=== DEBUG: Respuesta de logs de nómina ===');
        console.log('Endpoints usados: /nomina/activity-log/file/ + cierres específicos');
        console.log('Total logs obtenidos:', logsData?.results?.length || 0);
        console.log('Fuentes de logs:', logsData?.results?.map(log => log.fuente) || []);
        
      } catch (err) {
        console.error('Error cargando logs de actividad de nómina:', err);
        setError('Error cargando logs de actividad de nómina');
      }

      try {
        if (usuarios.length === 0) {
          usuariosData = await obtenerUsuariosActividadNomina();
          setUsuarios(usuariosData);
        }
      } catch (err) {
        console.error('Error cargando usuarios de nómina:', err);
      }

      try {
        conectadosData = await obtenerUsuariosConectadosNomina();
        setUsuariosConectados(conectadosData.usuarios_conectados || []);
      } catch (err) {
        console.error('Error cargando usuarios conectados de nómina:', err);
      }

      try {
        if (periodos.length === 0) {
          const periodosData = await obtenerPeriodosDisponiblesNomina();
          setPeriodos(periodosData);
        }
      } catch (err) {
        console.error('Error cargando períodos de nómina:', err);
      }

      try {
        statsData = await obtenerEstadisticasActividadNomina('semana');
        setEstadisticas(statsData);
      } catch (err) {
        console.error('Error cargando estadísticas de nómina:', err);
      }

      // Procesar logs obtenidos (adaptar estructura para nómina)
      let logsResults = [];
      if (Array.isArray(logsData)) {
        // Si es un array directo
        logsResults = logsData;
      } else if (logsData?.results) {
        // Si viene con paginación
        logsResults = logsData.results;
      }

      console.log('=== DEBUG: Procesando logs de nómina ===');
      console.log('Logs procesados:', logsResults.length);
      
      // Adaptar estructura de datos de actividad de nómina para el frontend
      const logsAdaptados = logsResults.map(log => ({
        id: log.id || Date.now() + Math.random(),
        cliente_id: log.cierre_id || log.cliente_id || 'N/A',
        cliente_nombre: log.cliente_nombre || (log.cierre_id ? `Cierre ${log.cierre_id}` : 'Actividad General'),
        usuario_id: log.usuario_id || log.usuario || 'N/A',
        usuario_nombre: log.usuario_nombre || log.usuario || `Usuario ${log.usuario_id || 'N/A'}`,
        actividad: log.descripcion || log.actividad || log.accion || `${log.accion} en ${log.tarjeta}`,
        fecha: log.fecha || log.timestamp || new Date().toISOString(),
        periodo: log.periodo || 'N/A',
        detalles: log.detalles || {},
        tarjeta: log.tarjeta || log.tipo_actividad || 'general',
        estado: log.resultado || log.estado || 'completed',
        fuente: log.fuente || 'database',
        tipo_actividad: log.tipo_actividad || log.tarjeta || 'general',
        archivo_nombre: log.archivo_nombre || log.nombre_archivo || null,
        accion: log.accion || 'actividad',
        ip_address: log.ip_address || null
      }));

      setLogsOriginales(logsAdaptados);
      
      // Aplicar filtros de frontend
      const logsFiltrados = aplicarFiltrosFrontend(logsAdaptados, filtrosFrontend);
      setLogs(logsFiltrados);
      
      console.log('=== DEBUG: Logs finales ===');
      console.log('Logs originales:', logsAdaptados.length);
      console.log('Logs después de filtros:', logsFiltrados.length);
      
      // Actualizar paginación (adaptar a la nueva estructura)
      setPaginacion({
        count: logsAdaptados.length,
        total_pages: Math.ceil(logsAdaptados.length / (filtrosBackend.page_size || 50)),
        current_page: filtrosBackend.page || 1,
        has_next: logsAdaptados.length > (filtrosBackend.page * filtrosBackend.page_size),
        has_previous: (filtrosBackend.page || 1) > 1
      });

      // Extraer "clientes" únicos de los logs (en este caso, cierres únicos)
      const cierresUnicos = [...new Set(logsAdaptados
        .filter(log => log.cliente_nombre)
        .map(log => ({ id: log.cliente_id, nombre: log.cliente_nombre }))
        .map(JSON.stringify))]
        .map(JSON.parse);
      setClientes(cierresUnicos);

    } catch (err) {
      console.error('Error general cargando datos de nómina:', err);
      setError('Error al cargar los datos de actividad de nómina');
    } finally {
      setLoading(false);
    }
  };

  const aplicarFiltrosFrontend = (logs, filtros) => {
    return logs.filter(log => {
      const matchCliente = !filtros.cliente_id || log.cliente_id?.toString() === filtros.cliente_id;
      const matchUsuario = !filtros.usuario_id || log.usuario_id?.toString() === filtros.usuario_id;
      const matchPeriodo = !filtros.periodo || log.periodo === filtros.periodo;
      
      return matchCliente && matchUsuario && matchPeriodo;
    });
  };

  const handleFiltroChange = (campo, valor) => {
    const nuevos = { ...filtrosFrontend, [campo]: valor };
    setFiltrosFrontend(nuevos);
    
    // Aplicar filtros inmediatamente
    const logsFiltrados = aplicarFiltrosFrontend(logsOriginales, nuevos);
    setLogs(logsFiltrados);
  };

  const limpiarFiltros = () => {
    setFiltrosFrontend({
      cliente_id: '',
      usuario_id: '',
      periodo: ''
    });
    setLogs(logsOriginales);
  };

  const formatearFecha = (fecha) => {
    if (!fecha) return 'N/A';
    return new Date(fecha).toLocaleString('es-CL', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  const getAccionColor = (accion) => {
    const colors = {
      'crear': 'bg-green-100 text-green-800',
      'actualizar': 'bg-blue-100 text-blue-800',
      'eliminar': 'bg-red-100 text-red-800',
      'ver': 'bg-gray-100 text-gray-800',
      'procesar': 'bg-purple-100 text-purple-800',
      'validar': 'bg-yellow-100 text-yellow-800',
      'upload_excel': 'bg-green-100 text-green-800',
      'consolidar_datos': 'bg-blue-100 text-blue-800',
      'procesar_libro': 'bg-purple-100 text-purple-800',
      'actualizar_estado': 'bg-yellow-100 text-yellow-800',
      'header_analysis': 'bg-indigo-100 text-indigo-800',
      'classification_complete': 'bg-teal-100 text-teal-800'
    };
    return colors[accion] || 'bg-gray-100 text-gray-600';
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 text-white p-6">
        <div className="flex justify-center items-center h-64">
          <RefreshCw className="w-8 h-8 animate-spin" />
          <span className="ml-2">Cargando logs de actividad de nómina...</span>
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
            <h1 className="text-3xl font-bold mb-2">Logs y Actividad de Nómina</h1>
            <p className="text-gray-400">Monitoreo de actividades y auditoría del sistema de nómina</p>
          </div>
          <div className="flex items-center gap-2">
            {dataSource && (
              <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                dataSource === 'redis' ? 'bg-green-100 text-green-800' : 'bg-blue-100 text-blue-800'
              }`}>
                {dataSource === 'redis' ? 'Redis (Tiempo Real)' : 'PostgreSQL'}
              </span>
            )}
            <button
              onClick={cargarDatos}
              disabled={loading}
              className="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-800 px-4 py-2 rounded-lg flex items-center"
            >
              <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Actualizar
            </button>
          </div>
        </div>

        {/* Usuarios Conectados */}
        {usuariosConectados.length > 0 && (
          <div className="bg-gray-800 p-4 rounded-lg mb-6">
            <div className="flex items-center mb-3">
              <Wifi className="w-5 h-5 mr-2 text-green-500" />
              <h3 className="text-lg font-semibold">Usuarios Conectados en Nómina ({usuariosConectados.length})</h3>
            </div>
            <div className="flex flex-wrap gap-2">
              {usuariosConectados.map((usuario, index) => (
                <span key={index} className="bg-green-100 text-green-800 px-3 py-1 rounded-full text-sm font-medium flex items-center">
                  <div className="w-2 h-2 bg-green-500 rounded-full mr-2 animate-pulse"></div>
                  {usuario.username} - {usuario.area || 'N/A'}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Estadísticas */}
        {estadisticas && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-gray-800 p-4 rounded-lg">
              <div className="flex items-center">
                <Activity className="w-8 h-8 text-blue-500" />
                <div className="ml-3">
                  <p className="text-sm text-gray-400">Total Actividades</p>
                  <p className="text-2xl font-bold">{estadisticas.total_actividades || 0}</p>
                </div>
              </div>
            </div>
            <div className="bg-gray-800 p-4 rounded-lg">
              <div className="flex items-center">
                <Users className="w-8 h-8 text-green-500" />
                <div className="ml-3">
                  <p className="text-sm text-gray-400">Usuarios Activos</p>
                  <p className="text-2xl font-bold">{estadisticas.usuarios_activos || 0}</p>
                </div>
              </div>
            </div>
            <div className="bg-gray-800 p-4 rounded-lg">
              <div className="flex items-center">
                <FileText className="w-8 h-8 text-purple-500" />
                <div className="ml-3">
                  <p className="text-sm text-gray-400">Cierres Procesados</p>
                  <p className="text-2xl font-bold">{estadisticas.cierres_procesados || 0}</p>
                </div>
              </div>
            </div>
            <div className="bg-gray-800 p-4 rounded-lg">
              <div className="flex items-center">
                <TrendingUp className="w-8 h-8 text-yellow-500" />
                <div className="ml-3">
                  <p className="text-sm text-gray-400">Actividad Promedio</p>
                  <p className="text-2xl font-bold">{estadisticas.actividad_promedio || 0}</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Filtros */}
        <div className="bg-gray-800 p-4 rounded-lg mb-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center">
              <Filter className="w-5 h-5 mr-2" />
              <h3 className="text-lg font-semibold">Filtros</h3>
            </div>
            <button
              onClick={limpiarFiltros}
              className="text-sm text-blue-400 hover:text-blue-300"
            >
              Limpiar filtros
            </button>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Cliente</label>
              <select
                value={filtrosFrontend.cliente_id}
                onChange={(e) => handleFiltroChange('cliente_id', e.target.value)}
                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2"
              >
                <option value="">Todos los clientes</option>
                {clientes.map(cliente => (
                  <option key={cliente.id} value={cliente.id}>
                    {cliente.nombre}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Usuario</label>
              <select
                value={filtrosFrontend.usuario_id}
                onChange={(e) => handleFiltroChange('usuario_id', e.target.value)}
                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2"
              >
                <option value="">Todos los usuarios</option>
                {usuarios.map(usuario => (
                  <option key={usuario.id} value={usuario.id}>
                    {usuario.username} - {usuario.area}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">Período</label>
              <select
                value={filtrosFrontend.periodo}
                onChange={(e) => handleFiltroChange('periodo', e.target.value)}
                className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2"
              >
                <option value="">Todos los períodos</option>
                {periodos.map(periodo => (
                  <option key={periodo} value={periodo}>
                    {periodo}
                  </option>
                ))}
              </select>
            </div>
          </div>
          
          <div className="mt-4 text-sm text-gray-400">
            Mostrando {logs.length} de {logsOriginales.length} actividades
            {paginacion.count > logsOriginales.length && (
              <span className="ml-2 text-blue-400">
                (Total en sistema: {paginacion.count})
              </span>
            )}
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="bg-red-600 text-white p-4 rounded-lg mb-6">
            {error}
          </div>
        )}

        {/* Lista de Logs */}
        <div className="bg-gray-800 rounded-lg">
          <div className="p-4 border-b border-gray-700">
            <h3 className="text-lg font-semibold">Registro de Actividades</h3>
          </div>
          
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-700">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Fecha y Hora
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Usuario
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Cliente
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Acción
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Detalles
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700">
                {logs.map((log, index) => (
                  <tr key={index} className="hover:bg-gray-700">
                    <td className="px-4 py-4 whitespace-nowrap text-sm">
                      {formatearFecha(log.fecha)}
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap text-sm">
                      <div className="flex items-center">
                        <User className="w-4 h-4 mr-2 text-gray-400" />
                        <div>
                          <div className="font-medium">{log.usuario_nombre || 'N/A'}</div>
                          <div className="text-gray-400 text-xs">{log.area || 'N/A'}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap text-sm">
                      <div>
                        <div className="font-medium">{log.cliente_nombre || 'N/A'}</div>
                        {log.periodo && (
                          <div className="text-gray-400 text-xs">{log.periodo}</div>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getAccionColor(log.accion)}`}>
                        {log.accion}
                      </span>
                    </td>
                    <td className="px-4 py-4 text-sm text-gray-300">
                      <div>
                        <div className="font-medium">{log.actividad || log.descripcion || 'N/A'}</div>
                        {log.tarjeta && (
                          <div className="text-gray-400 text-xs mt-1">
                            Tarjeta: {log.tarjeta}
                          </div>
                        )}
                        {log.ip_address && (
                          <div className="text-gray-400 text-xs">
                            IP: {log.ip_address}
                          </div>
                        )}
                        {log.detalles && Object.keys(log.detalles).length > 0 && (
                          <div className="text-gray-400 text-xs mt-1">
                            Detalles: {JSON.stringify(log.detalles)}
                          </div>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {logs.length === 0 && !loading && (
            <div className="text-center py-12">
              <FileText className="w-16 h-16 mx-auto text-gray-600 mb-4" />
              <h3 className="text-lg font-medium text-gray-300 mb-2">No se encontraron registros</h3>
              <p className="text-gray-400">
                No hay actividades registradas con los filtros seleccionados
              </p>
            </div>
          )}
        </div>

        {/* Paginación */}
        {paginacion.total_pages > 1 && (
          <div className="flex justify-center items-center mt-6 space-x-2">
            <button
              onClick={() => setFiltrosBackend({...filtrosBackend, page: paginacion.current_page - 1})}
              disabled={!paginacion.has_previous}
              className="px-3 py-2 bg-gray-700 hover:bg-gray-600 disabled:bg-gray-800 disabled:opacity-50 rounded text-sm"
            >
              Anterior
            </button>
            <span className="text-sm text-gray-400">
              Página {paginacion.current_page} de {paginacion.total_pages}
            </span>
            <button
              onClick={() => setFiltrosBackend({...filtrosBackend, page: paginacion.current_page + 1})}
              disabled={!paginacion.has_next}
              className="px-3 py-2 bg-gray-700 hover:bg-gray-600 disabled:bg-gray-800 disabled:opacity-50 rounded text-sm"
            >
              Siguiente
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default LogsActividadNomina;
