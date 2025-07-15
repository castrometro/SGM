// src/components/Gerente/LogsActividad.jsx
import { useState, useEffect } from 'react';
import { 
  obtenerLogsActividad, 
  obtenerEstadisticasActividad, 
  obtenerUsuariosActividad,
  obtenerUsuariosConectados
} from '../../api/gerente';
import { 
  Search, Filter, Calendar, User, FileText, Activity, RefreshCw, 
  Users, Clock, BarChart3, Wifi, WifiOff, Eye, TrendingUp 
} from 'lucide-react';

const LogsActividad = () => {
  const [logs, setLogs] = useState([]);
  const [estadisticas, setEstadisticas] = useState(null);
  const [usuarios, setUsuarios] = useState([]);
  const [usuariosConectados, setUsuariosConectados] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  // Estados de filtros
  const [filtros, setFiltros] = useState({
    cliente_id: '',
    usuario_id: '',
    tarjeta: '',
    accion: '',
    fecha_desde: '',
    fecha_hasta: '',
    page: 1,
    page_size: 10 // Reducido para el dashboard
  });
  
  const [paginacion, setPaginacion] = useState({
    count: 0,
    total_pages: 0,
    current_page: 1,
    has_next: false,
    has_previous: false
  });

  // Opciones para filtros
  const tiposTarjeta = [
    { value: '', label: 'Todas las tarjetas' },
    { value: 'tipo_documento', label: 'Tipos de Documento' },
    { value: 'libro_mayor', label: 'Libro Mayor' },
    { value: 'clasificacion', label: 'Clasificaciones' },
    { value: 'nombres_ingles', label: 'Nombres en Inglés' },
    { value: 'revision', label: 'Revisión' },
    { value: 'movimientos_cuenta', label: 'Movimientos por Cuenta' }
  ];

  const tiposAccion = [
    { value: '', label: 'Todas las acciones' },
    { value: 'view_data', label: 'Ver Datos' },
    { value: 'manual_create', label: 'Crear Manual' },
    { value: 'manual_edit', label: 'Editar Manual' },
    { value: 'manual_delete', label: 'Eliminar Manual' },
    { value: 'upload_excel', label: 'Subir Excel' },
    { value: 'process_complete', label: 'Proceso Completado' }
  ];

  useEffect(() => {
    cargarDatos();
  }, [filtros]);

  // Auto-refresh para usuarios conectados cada 30 segundos
  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const conectadosData = await obtenerUsuariosConectados();
        setUsuariosConectados(conectadosData.usuarios_conectados || []);
      } catch (err) {
        console.error('Error actualizando usuarios conectados:', err);
        // No mostrar error en el auto-refresh, solo log
      }
    }, 30000); // 30 segundos

    return () => clearInterval(interval);
  }, []);

  const cargarDatos = async () => {
    try {
      setLoading(true);
      
      // Cargar datos con manejo individual de errores
      let logsData = { results: [], count: 0, total_pages: 0, current_page: 1, has_next: false, has_previous: false };
      let statsData = null;
      let usuariosData = usuarios.length > 0 ? usuarios : [];
      let conectadosData = { usuarios_conectados: [] };

      // Intentar cargar logs
      try {
        logsData = await obtenerLogsActividad(filtros);
      } catch (err) {
        console.error('Error cargando logs:', err);
      }

      // Intentar cargar estadísticas
      try {
        statsData = await obtenerEstadisticasActividad('semana');
      } catch (err) {
        console.error('Error cargando estadísticas:', err);
        // Datos de fallback para mostrar el widget
        statsData = {
          resumen: {
            total_actividades: 0,
            usuarios_activos: 0,
            clientes_trabajados: 0,
            periodo: 'semana'
          }
        };
      }

      // Intentar cargar usuarios si no están cargados
      if (usuarios.length === 0) {
        try {
          usuariosData = await obtenerUsuariosActividad();
        } catch (err) {
          console.error('Error cargando usuarios:', err);
        }
      }

      // Intentar cargar usuarios conectados
      try {
        conectadosData = await obtenerUsuariosConectados();
        console.log('=== DEBUG: Usuarios conectados ===');
        console.log('Respuesta completa:', conectadosData);
        console.log('Usuarios conectados:', conectadosData.usuarios_conectados);
        console.log('Debug info:', conectadosData.debug);
        console.log('====================================');
      } catch (err) {
        console.error('Error cargando usuarios conectados:', err);
        console.error('Error details:', err.response?.data);
      }

      // Procesar logs con validación de fechas
      const logsConFechasValidadas = (logsData.results || []).map(log => ({
        ...log,
        // Asegurar que timestamp esté disponible, priorizar timestamp sobre fecha_creacion
        timestamp: log.timestamp || log.fecha_creacion || null
      }));
      
      // Debug de fechas para identificar problemas
      console.log('=== DEBUG: Fechas en logs ===');
      logsConFechasValidadas.slice(0, 3).forEach((log, index) => {
        console.log(`Log ${index + 1}:`, {
          id: log.id,
          timestamp: log.timestamp,
          fecha_creacion: log.fecha_creacion,
          timestamp_type: typeof log.timestamp,
          usuario: log.usuario_nombre
        });
      });
      console.log('============================');
      
      setLogs(logsConFechasValidadas);
      setPaginacion({
        count: logsData.count || 0,
        total_pages: logsData.total_pages || 0,
        current_page: logsData.current_page || 1,
        has_next: logsData.has_next || false,
        has_previous: logsData.has_previous || false
      });

      // Procesar estadísticas
      setEstadisticas(statsData);

      // Procesar usuarios
      if (usuarios.length === 0) {
        setUsuarios(usuariosData);
      }

      // Procesar usuarios conectados
      setUsuariosConectados(conectadosData.usuarios_conectados || []);

      // Limpiar error si todo va bien
      setError('');

    } catch (err) {
      console.error('Error general cargando datos:', err);
      setError('Error al cargar los datos de actividad');
    } finally {
      setLoading(false);
    }
  };

  const handleFiltroChange = (campo, valor) => {
    setFiltros(prev => ({
      ...prev,
      [campo]: valor,
      page: 1 // Reset page when filtering
    }));
  };

  const handlePageChange = (newPage) => {
    setFiltros(prev => ({ ...prev, page: newPage }));
  };

  const limpiarFiltros = () => {
    setFiltros({
      cliente_id: '',
      usuario_id: '',
      tarjeta: '',
      accion: '',
      fecha_desde: '',
      fecha_hasta: '',
      page: 1,
      page_size: 10
    });
  };

  const formatearFecha = (fecha) => {
    // Validar que la fecha no sea null, undefined o inválida
    if (!fecha) {
      return 'Sin fecha';
    }
    
    try {
      const fechaObj = new Date(fecha);
      
      // Verificar que la fecha sea válida
      if (isNaN(fechaObj.getTime())) {
        return 'Fecha inválida';
      }
      
      return fechaObj.toLocaleString('es-CL', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch (error) {
      console.warn('Error formateando fecha:', fecha, error);
      return 'Error en fecha';
    }
  };

  const getTarjetaColor = (tarjeta) => {
    const colors = {
      'tipo_documento': 'bg-blue-100 text-blue-800',
      'libro_mayor': 'bg-green-100 text-green-800',
      'clasificacion': 'bg-purple-100 text-purple-800',
      'nombres_ingles': 'bg-yellow-100 text-yellow-800',
      'revision': 'bg-red-100 text-red-800',
      'movimientos_cuenta': 'bg-indigo-100 text-indigo-800'
    };
    return colors[tarjeta] || 'bg-gray-100 text-gray-800';
  };

  const getAccionIcon = (accion) => {
    if (accion.includes('view')) return <Search className="w-4 h-4" />;
    if (accion.includes('create')) return <FileText className="w-4 h-4" />;
    if (accion.includes('upload')) return <Activity className="w-4 h-4" />;
    return <User className="w-4 h-4" />;
  };

  if (loading && logs.length === 0) {
    return (
      <div className="min-h-screen bg-gray-900 text-white p-6">
        <div className="flex justify-center items-center h-64">
          <RefreshCw className="w-8 h-8 animate-spin" />
          <span className="ml-2">Cargando dashboard de actividad...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold mb-2">Dashboard de Actividad del Sistema</h1>
          <p className="text-gray-400">Monitoreo en tiempo real y auditoría de actividades</p>
        </div>

        {/* Dashboard Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* Columna Izquierda: KPIs y Usuarios Conectados */}
          <div className="lg:col-span-1 space-y-6">
            
            {/* Widget 1: KPIs Principales */}
            <div className="bg-gray-800 rounded-lg p-6">
              <div className="flex items-center mb-4">
                <BarChart3 className="w-6 h-6 text-blue-500 mr-2" />
                <h3 className="text-lg font-semibold">Métricas de la Semana</h3>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-400">
                    {estadisticas?.resumen?.total_actividades || 0}
                  </div>
                  <div className="text-sm text-gray-400">Actividades</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-400">
                    {estadisticas?.resumen?.usuarios_activos || 0}
                  </div>
                  <div className="text-sm text-gray-400">Usuarios Activos</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-purple-400">
                    {estadisticas?.resumen?.clientes_trabajados || 0}
                  </div>
                  <div className="text-sm text-gray-400">Clientes</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-orange-400">
                    {Math.round((estadisticas?.resumen?.total_actividades || 0) / 7)}
                  </div>
                  <div className="text-sm text-gray-400">Promedio/día</div>
                </div>
              </div>
              {!estadisticas && (
                <div className="mt-3 text-xs text-gray-500 text-center">
                  ⚠️ Conectando con el servidor...
                </div>
              )}
            </div>

            {/* Widget 2: Usuarios Conectados Ahora */}
            <div className="bg-gray-800 rounded-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center">
                  <Users className="w-6 h-6 text-green-500 mr-2" />
                  <h3 className="text-lg font-semibold">Usuarios Conectados</h3>
                </div>
                <div className="flex items-center gap-2">
                  <div className="flex items-center text-green-400">
                    <Wifi className="w-4 h-4 mr-1" />
                    <span className="text-sm font-medium">{usuariosConectados.length} online</span>
                  </div>
                  <button
                    onClick={async () => {
                      try {
                        const debug = await obtenerUsuariosConectados();
                        const debugInfo = `
                            === DEBUG USUARIOS CONECTADOS ===
                            Total sesiones Django: ${debug.debug?.total_sessions || 0}
                            Usuarios en sesiones: ${debug.debug?.session_user_ids || []}
                            Usuarios con actividad reciente: ${debug.debug?.recent_activity_users || []}
                            Total combinado: ${debug.debug?.connected_user_ids || []}
                            Filtrados finales: ${debug.debug?.filtered_users || 0}

                            USUARIOS DETECTADOS:
                            ${debug.usuarios_conectados?.map(u => 
                            `- ${u.nombre} (${u.tipo_conexion}) - hace ${u.minutos_desde_actividad || '?'}min`
                            ).join('\n') || 'Ninguno'}
                            ================================`;
                        alert(debugInfo);
                      } catch (err) {
                        alert(`Error: ${err.message}`);
                      }
                    }}
                    className="text-xs text-gray-400 hover:text-gray-300 px-2 py-1 border border-gray-600 rounded"
                  >
                    🐛
                  </button>
                </div>
              </div>
              
              <div className="space-y-3 max-h-64 overflow-y-auto">
                {usuariosConectados.length === 0 ? (
                  <div className="text-center py-4 text-gray-400">
                    <WifiOff className="w-8 h-8 mx-auto mb-2" />
                    <p>No hay usuarios conectados</p>
                  </div>
                ) : (
                  usuariosConectados.map((usuario) => (
                    <div key={usuario.id} className="flex items-center justify-between p-3 bg-gray-700 rounded-lg">
                      <div>
                        <div className="font-medium text-sm">{usuario.nombre}</div>
                        <div className="text-xs text-gray-400">{usuario.rol}</div>
                        {usuario.tipo_conexion && (
                          <div className="text-xs text-blue-400">
                            🔗 {usuario.tipo_conexion}
                          </div>
                        )}
                        {usuario.cliente_actual && (
                          <div className="text-xs text-green-400">
                            📊 {usuario.cliente_actual}
                          </div>
                        )}
                      </div>
                      <div className="text-right">
                        <div className="flex items-center text-green-400 text-xs">
                          <div className="w-2 h-2 bg-green-400 rounded-full mr-1"></div>
                          {usuario.minutos_desde_actividad !== null && usuario.minutos_desde_actividad <= 10 ? 
                            'Activo ahora' : 
                            'Online'
                          }
                        </div>
                        {usuario.minutos_desde_actividad !== null && (
                          <div className="text-xs text-gray-500">
                            hace {usuario.minutos_desde_actividad}min
                          </div>
                        )}
                        {usuario.ultima_actividad && !usuario.minutos_desde_actividad && (
                          <div className="text-xs text-gray-500">
                            {new Date(usuario.ultima_actividad).toLocaleTimeString('es-CL', {
                              hour: '2-digit',
                              minute: '2-digit'
                            })}
                          </div>
                        )}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>

          {/* Columna Derecha: Tabla de Logs Compacta */}
          <div className="lg:col-span-2">
            <div className="bg-gray-800 rounded-lg overflow-hidden">
              
              {/* Header de la tabla con filtros compactos */}
              <div className="p-4 border-b border-gray-700">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center">
                    <Activity className="w-6 h-6 text-blue-500 mr-2" />
                    <h3 className="text-lg font-semibold">Actividad Reciente</h3>
                  </div>
                  <button
                    onClick={cargarDatos}
                    disabled={loading}
                    className="flex items-center px-3 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-800 rounded text-sm"
                  >
                    <RefreshCw className={`w-4 h-4 mr-1 ${loading ? 'animate-spin' : ''}`} />
                    Actualizar
                  </button>
                </div>
                
                {/* Filtros en línea */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
                  <select
                    value={filtros.usuario_id}
                    onChange={(e) => handleFiltroChange('usuario_id', e.target.value)}
                    className="bg-gray-700 border border-gray-600 rounded px-3 py-2 text-sm"
                  >
                    <option value="">Todos los usuarios</option>
                    {usuarios.map(usuario => (
                      <option key={usuario.id} value={usuario.id}>
                        {usuario.nombre} {usuario.apellido}
                      </option>
                    ))}
                  </select>

                  <select
                    value={filtros.tarjeta}
                    onChange={(e) => handleFiltroChange('tarjeta', e.target.value)}
                    className="bg-gray-700 border border-gray-600 rounded px-3 py-2 text-sm"
                  >
                    {tiposTarjeta.map(tipo => (
                      <option key={tipo.value} value={tipo.value}>
                        {tipo.label}
                      </option>
                    ))}
                  </select>

                  <input
                    type="date"
                    value={filtros.fecha_desde}
                    onChange={(e) => handleFiltroChange('fecha_desde', e.target.value)}
                    className="bg-gray-700 border border-gray-600 rounded px-3 py-2 text-sm"
                  />

                  <button
                    onClick={limpiarFiltros}
                    className="text-sm text-blue-400 hover:text-blue-300 px-3 py-2 border border-gray-600 rounded"
                  >
                    Limpiar
                  </button>
                </div>
              </div>

              {/* Error */}
              {error && (
                <div className="bg-red-600 text-white p-3 text-sm">
                  {error}
                </div>
              )}

              {/* Tabla compacta */}
              <div className="overflow-x-auto max-h-96 overflow-y-auto">
                <table className="w-full text-sm">
                  <thead className="bg-gray-700 sticky top-0">
                    <tr>
                      <th className="px-3 py-2 text-left font-medium">Hora</th>
                      <th className="px-3 py-2 text-left font-medium">Usuario</th>
                      <th className="px-3 py-2 text-left font-medium">Acción</th>
                      <th className="px-3 py-2 text-left font-medium">Cliente</th>
                      <th className="px-3 py-2 text-left font-medium">Tarjeta</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-700">
                    {logs.map((log) => (
                      <tr key={log.id} className="hover:bg-gray-750">
                        <td className="px-3 py-2">
                          <div className="text-xs">
                            {log.timestamp ? formatearFecha(log.timestamp).split(' ')[1] || 'Sin hora' : 'Sin hora'}
                          </div>
                          <div className="text-xs text-gray-400">
                            {log.timestamp ? formatearFecha(log.timestamp).split(' ')[0] || 'Sin fecha' : 'Sin fecha'}
                          </div>
                        </td>
                        <td className="px-3 py-2">
                          <div className="font-medium text-xs">{log.usuario_nombre}</div>
                          <div className="text-xs text-gray-400">{log.usuario_email}</div>
                        </td>
                        <td className="px-3 py-2">
                          <div className="flex items-center text-xs">
                            {getAccionIcon(log.accion)}
                            <span className="ml-1">{log.accion}</span>
                          </div>
                        </td>
                        <td className="px-3 py-2 text-xs">
                          {log.cliente_nombre}
                        </td>
                        <td className="px-3 py-2">
                          <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getTarjetaColor(log.tarjeta)}`}>
                            {log.tarjeta}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Paginación compacta */}
              {paginacion.total_pages > 1 && (
                <div className="bg-gray-750 px-4 py-3 flex items-center justify-between text-sm">
                  <div className="text-gray-400">
                    {paginacion.count} resultados
                  </div>
                  <div className="flex space-x-2">
                    <button
                      onClick={() => handlePageChange(paginacion.current_page - 1)}
                      disabled={!paginacion.has_previous}
                      className="px-2 py-1 bg-gray-600 hover:bg-gray-500 disabled:bg-gray-800 disabled:text-gray-500 rounded text-xs"
                    >
                      ‹
                    </button>
                    <span className="px-2 py-1 text-xs">
                      {paginacion.current_page}/{paginacion.total_pages}
                    </span>
                    <button
                      onClick={() => handlePageChange(paginacion.current_page + 1)}
                      disabled={!paginacion.has_next}
                      className="px-2 py-1 bg-gray-600 hover:bg-gray-500 disabled:bg-gray-800 disabled:text-gray-500 rounded text-xs"
                    >
                      ›
                    </button>
                  </div>
                </div>
              )}

              {/* Sin resultados */}
              {logs.length === 0 && !loading && (
                <div className="text-center py-8">
                  <FileText className="w-12 h-12 mx-auto text-gray-600 mb-3" />
                  <h4 className="text-gray-300 mb-2">No hay actividad reciente</h4>
                  <p className="text-gray-400 text-sm">Ajusta los filtros para ver más resultados</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LogsActividad;
