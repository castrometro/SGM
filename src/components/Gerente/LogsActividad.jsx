// src/components/Gerente/LogsActividad.jsx
import { useState, useEffect } from 'react';
import { 
  obtenerLogsActividad, 
  obtenerEstadisticasActividad, 
  obtenerUsuariosActividad,
  obtenerUsuariosConectados,
  obtenerPeriodosDisponibles
} from '../../api/gerente';
import { 
  Search, Filter, Calendar, User, FileText, Activity, RefreshCw, 
  Users, Clock, BarChart3, Wifi, WifiOff, Eye, TrendingUp 
} from 'lucide-react';

const LogsActividad = () => {
  const [logs, setLogs] = useState([]);
  const [logsOriginales, setLogsOriginales] = useState([]); // Para almacenar logs sin filtrar
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
    page_size: 100, // Obtener más logs para filtrar en frontend
    force_redis: true // Forzar uso de Redis para actividad reciente
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
  }, [filtrosBackend]); // Solo recarga cuando cambian los filtros del backend

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

      // Intentar cargar logs - SIN FILTROS, obtener todo de Redis
      try {
        console.log('=== DEBUG: Obteniendo TODOS los logs de Redis ===');
        console.log('Filtros backend (solo paginación):', filtrosBackend);
        console.log('Filtros frontend (para filtrar localmente):', filtrosFrontend);
        console.log('===============================================');
        
        logsData = await obtenerLogsActividad(filtrosBackend);
        setDataSource(logsData.source || 'postgres'); // Mostrar fuente de datos
        
        console.log('=== DEBUG: Respuesta del backend ===');
        console.log('Fuente:', logsData.source);
        console.log('Total logs sin filtrar:', logsData.results?.length || 0);
        console.log('Count total:', logsData.count);
        console.log('==================================');
        
        // Debug info para mostrar que está usando Redis
        if (logsData.source === 'redis') {
          console.log('=== DEBUG: Usando Redis para todos los logs ===');
          console.log('Total logs en Redis:', logsData.count);
          console.log('Logs mostrados:', logsData.results?.length || 0);
          console.log('Páginas totales:', logsData.total_pages);
          console.log('============================================');
        }
      } catch (err) {
        console.error('Error cargando logs:', err);
        console.error('Error details:', err.response?.data);
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

      // Intentar cargar períodos si no están cargados
      if (periodos.length === 0) {
        try {
          const periodosData = await obtenerPeriodosDisponibles();
          setPeriodos(periodosData || []);
        } catch (err) {
          console.error('Error cargando períodos:', err);
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
          usuario: log.usuario_nombre,
          cliente_id: log.cliente_id,
          cliente_nombre: log.cliente_nombre
        });
      });
      console.log('============================');
      
      // APLICAR FILTROS EN FRONTEND
      const logsFiltrados = aplicarFiltrosFrontend(logsConFechasValidadas, filtrosFrontend);
      
      console.log('=== DEBUG: Filtrado Frontend ===');
      console.log('Logs sin filtrar:', logsConFechasValidadas.length);
      console.log('Logs después del filtro:', logsFiltrados.length);
      console.log('Filtros aplicados:', filtrosFrontend);
      
      // Debug específico del filtro de cliente
      if (filtrosFrontend.cliente_id) {
        console.log(`🔍 Filtro de cliente activo: "${filtrosFrontend.cliente_id}"`);
        console.log('Logs que coinciden con el cliente:');
        logsConFechasValidadas.forEach((log, index) => {
          const clienteIdLog = log.cliente_id || log.cliente_nombre;
          const matches = clienteIdLog === filtrosFrontend.cliente_id;
          console.log(`  Log ${index + 1}: cliente_id="${log.cliente_id}", cliente_nombre="${log.cliente_nombre}" → ${matches ? '✅ MATCH' : '❌ NO MATCH'}`);
        });
      }
      
      console.log('===============================');
      
      // Guardar logs originales para filtrado posterior
      setLogsOriginales(logsConFechasValidadas);
      setLogs(logsFiltrados);
      
      // Actualizar paginación con los logs filtrados
      setPaginacion({
        count: logsFiltrados.length,
        total_pages: Math.ceil(logsFiltrados.length / 10),
        current_page: 1,
        has_next: logsFiltrados.length > 10,
        has_previous: false
      });

      // Procesar estadísticas
      setEstadisticas(statsData);

      // Procesar usuarios
      if (usuarios.length === 0) {
        setUsuarios(usuariosData);
      }

      // Procesar usuarios conectados
      setUsuariosConectados(conectadosData.usuarios_conectados || []);

      // Extraer lista única de clientes desde los logs para el filtro
      const clientesMap = new Map();
      
      logsConFechasValidadas
        .filter(log => log.cliente_nombre && log.cliente_nombre.trim() !== '')
        .forEach(log => {
          const clienteId = log.cliente_id || log.cliente_nombre;
          if (!clientesMap.has(clienteId)) {
            clientesMap.set(clienteId, {
              id: clienteId,
              nombre: log.cliente_nombre
            });
          }
        });
      
      const clientesUnicos = Array.from(clientesMap.values());
      
      // Debug de clientes extraídos
      console.log('=== DEBUG: Clientes extraídos de logs ===');
      console.log('Logs con cliente_nombre:', logsConFechasValidadas.filter(log => log.cliente_nombre && log.cliente_nombre.trim() !== '').length);
      console.log('Clientes únicos encontrados:', clientesUnicos.length);
      clientesUnicos.forEach((cliente, index) => {
        console.log(`Cliente ${index + 1}:`, {
          id: cliente.id,
          nombre: cliente.nombre
        });
      });
      console.log('========================================');
      
      // Actualizar lista de clientes solo si hay nuevos clientes
      if (clientesUnicos.length > 0) {
        setClientes(prev => {
          const clientesExistentes = new Set(prev.map(c => c.id));
          const clientesNuevos = clientesUnicos.filter(c => !clientesExistentes.has(c.id));
          
          console.log('=== DEBUG: Actualización de clientes ===');
          console.log('Clientes existentes:', prev.length);
          console.log('Clientes nuevos a agregar:', clientesNuevos.length);
          console.log('Total después de actualizar:', prev.length + clientesNuevos.length);
          console.log('=======================================');
          
          return [...prev, ...clientesNuevos];
        });
      }

      // Limpiar error si todo va bien
      setError('');

    } catch (err) {
      console.error('Error general cargando datos:', err);
      setError('Error al cargar los datos de actividad');
    } finally {
      setLoading(false);
    }
  };

  // Función para aplicar filtros en el frontend
  const aplicarFiltrosFrontend = (logs, filtros) => {
    console.log('🔧 Aplicando filtros frontend...');
    console.log('Total logs de entrada:', logs.length);
    console.log('Filtros a aplicar:', filtros);
    
    return logs.filter(log => {
      // Filtro por cliente
      if (filtros.cliente_id && filtros.cliente_id !== '') {
        const clienteId = log.cliente_id || log.cliente_nombre;
        // Convertir ambos valores a string para comparar correctamente
        const clienteIdString = String(clienteId);
        const filtroClienteString = String(filtros.cliente_id);
        const match = clienteIdString === filtroClienteString;
        console.log(`🔍 Filtro cliente: "${filtroClienteString}" vs "${clienteIdString}" → ${match ? 'MATCH' : 'NO MATCH'}`);
        if (!match) {
          return false;
        }
      }

      // Filtro por usuario
      if (filtros.usuario_id && filtros.usuario_id !== '') {
        if (log.usuario_id !== parseInt(filtros.usuario_id)) {
          return false;
        }
      }

      // Filtro por período
      if (filtros.periodo && filtros.periodo !== '') {
        if (log.periodo_cierre !== filtros.periodo) {
          return false;
        }
      }

      return true;
    });
  };

  const handleFiltroChange = (campo, valor) => {
    setFiltrosFrontend(prev => ({
      ...prev,
      [campo]: valor
    }));
  };

  // Efecto para aplicar filtros cuando cambian los filtros del frontend
  useEffect(() => {
    if (logsOriginales.length > 0) {
      const logsFiltrados = aplicarFiltrosFrontend(logsOriginales, filtrosFrontend);
      
      console.log('=== DEBUG: Re-filtrado Frontend ===');
      console.log('Logs originales:', logsOriginales.length);
      console.log('Logs después del filtro:', logsFiltrados.length);
      console.log('Filtros aplicados:', filtrosFrontend);
      
      // Debug específico para el filtro de cliente
      if (filtrosFrontend.cliente_id) {
        console.log(`🔍 Re-filtro de cliente activo: "${filtrosFrontend.cliente_id}"`);
        console.log('Comparación detallada:');
        logsOriginales.forEach((log, index) => {
          const clienteIdLog = log.cliente_id || log.cliente_nombre;
          // Convertir ambos valores a string para comparar correctamente
          const clienteIdString = String(clienteIdLog);
          const filtroClienteString = String(filtrosFrontend.cliente_id);
          const matches = clienteIdString === filtroClienteString;
          console.log(`  Log ${index + 1}: cliente_id="${log.cliente_id}", cliente_nombre="${log.cliente_nombre}" → ${matches ? '✅ MATCH' : '❌ NO MATCH'}`);
        });
      }
      
      console.log('==================================');
      
      setLogs(logsFiltrados);
      
      // Actualizar paginación
      setPaginacion({
        count: logsFiltrados.length,
        total_pages: Math.ceil(logsFiltrados.length / 10),
        current_page: 1,
        has_next: logsFiltrados.length > 10,
        has_previous: false
      });
    }
  }, [filtrosFrontend, logsOriginales]);

  const handlePageChange = (newPage) => {
    setFiltrosBackend(prev => ({ ...prev, page: newPage }));
  };

  const limpiarFiltros = () => {
    setFiltrosFrontend({
      cliente_id: '',
      usuario_id: '',
      periodo: ''
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
      'incidencias': 'bg-red-100 text-red-800',
      'revision': 'bg-orange-100 text-orange-800',
      'movimientos_cuenta': 'bg-indigo-100 text-indigo-800',
      'movimientos_resumen': 'bg-cyan-100 text-cyan-800',
      'reportes': 'bg-pink-100 text-pink-800'
    };
    return colors[tarjeta] || 'bg-gray-100 text-gray-800';
  };

  const getCierreColor = (estado) => {
    const colors = {
      'pendiente': 'bg-yellow-100 text-yellow-800',
      'procesando': 'bg-blue-100 text-blue-800',
      'clasificacion': 'bg-purple-100 text-purple-800',
      'incidencias': 'bg-red-100 text-red-800',
      'sin_incidencias': 'bg-green-100 text-green-800',
      'generando_reportes': 'bg-indigo-100 text-indigo-800',
      'en_revision': 'bg-orange-100 text-orange-800',
      'rechazado': 'bg-red-200 text-red-900',
      'aprobado': 'bg-green-200 text-green-900',
      'finalizado': 'bg-gray-100 text-gray-800',
      'completo': 'bg-gray-200 text-gray-900'
    };
    return colors[estado] || 'bg-gray-100 text-gray-800';
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
          <div className="mt-2 flex items-center text-sm text-green-400">
            <span className="inline-block w-2 h-2 bg-green-400 rounded-full mr-2"></span>
            Mostrando todos los logs disponibles en Redis (tiempo real)
          </div>
        </div>

        {/* Dashboard Grid */}
        <div className="space-y-6">
          
          {/* Fila Superior: KPIs y Usuarios Conectados */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            
            {/* Widget 1: KPIs Principales */}
            <div className="bg-gray-800 rounded-lg p-6">
              <div className="flex items-center mb-4">
                <BarChart3 className="w-6 h-6 text-blue-500 mr-2" />
                <h3 className="text-lg font-semibold">Métricas</h3>
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
              {estadisticas && (
                <div className="mt-3 text-xs text-green-400 text-center">
                  ✅ Datos actualizados desde Redis
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

          {/* Bloque Inferior: Tabla de Logs de Actividad Reciente */}
          <div className="bg-gray-800 rounded-lg overflow-hidden">
            
            {/* Header de la tabla con filtros compactos */}
            <div className="p-4 border-b border-gray-700">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center">
                  <Activity className="w-6 h-6 text-blue-500 mr-2" />
                  <h3 className="text-lg font-semibold">Actividad Reciente - Redis</h3>
                  {dataSource && (
                    <span className={`ml-2 px-2 py-1 rounded text-xs ${
                      dataSource === 'redis' 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-blue-100 text-blue-800'
                    }`}>
                      {dataSource === 'redis' ? '⚡ Tiempo Real' : '🗄️ Base de Datos'}
                    </span>
                  )}
                  {!dataSource && (
                    <span className="ml-2 px-2 py-1 rounded text-xs bg-orange-100 text-orange-800">
                      🔄 Conectando con Redis...
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={cargarDatos}
                    disabled={loading}
                    className="flex items-center px-3 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-800 rounded text-sm"
                  >
                    <RefreshCw className={`w-4 h-4 mr-1 ${loading ? 'animate-spin' : ''}`} />
                    Actualizar
                  </button>
                  <button
                    onClick={() => {
                      const debugInfo = `
                        === DEBUG: Estado de Redis Logs ===
                        Fuente de datos: ${dataSource || 'No detectada'}
                        Total logs cargados: ${logs.length}
                        Paginación actual: ${paginacion.current_page}/${paginacion.total_pages}
                        Total disponible: ${paginacion.count}
                        
                        Filtros Frontend activos:
                        - Cliente: ${filtrosFrontend.cliente_id || 'Todos'}
                        - Usuario: ${filtrosFrontend.usuario_id || 'Todos'}
                        - Tarjeta: ${filtrosFrontend.tarjeta || 'Todas'}
                        - Cierre: ${filtrosFrontend.cierre || 'Todos'}
                        - Período: ${filtrosFrontend.periodo || 'Todos'}
                        - Fecha desde: ${filtrosFrontend.fecha_desde || 'Sin filtro'}
                        
                        Filtros Backend (solo paginación):
                        - Page: ${filtrosBackend.page}
                        - Page size: ${filtrosBackend.page_size}
                        - Force Redis: ${filtrosBackend.force_redis ? 'SÍ' : 'NO'}
                        
                        CLIENTES DISPONIBLES:
                        ${clientes.map(c => `- ID: "${c.id}" | Nombre: "${c.nombre}"`).join('\n')}
                        
                        LOGS SAMPLE (primeros 5):
                        ${logs.slice(0, 5).map(log => 
                          `- Usuario: ${log.usuario_nombre} | Cliente ID: "${log.cliente_id}" | Cliente Nombre: "${log.cliente_nombre}" | Acción: ${log.accion}`
                        ).join('\n')}
                        =====================================`;
                      alert(debugInfo);
                    }}
                    className="text-xs text-gray-400 hover:text-gray-300 px-2 py-1 border border-gray-600 rounded"
                  >
                    🔍 Debug Redis
                  </button>
                </div>
              </div>
              
              {/* Filtros en línea */}
              <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-3">
                <select
                  value={filtrosFrontend.usuario_id}
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
                  value={filtrosFrontend.cliente_id}
                  onChange={(e) => handleFiltroChange('cliente_id', e.target.value)}
                  className="bg-gray-700 border border-gray-600 rounded px-3 py-2 text-sm"
                >
                  <option value="">Todos los clientes</option>
                  {clientes.map(cliente => (
                    <option key={cliente.id} value={cliente.id}>
                      {cliente.nombre}
                    </option>
                  ))}
                </select>

                <select
                  value={filtrosFrontend.periodo}
                  onChange={(e) => handleFiltroChange('periodo', e.target.value)}
                  className="bg-gray-700 border border-gray-600 rounded px-3 py-2 text-sm"
                  title="Seleccionar período de cierre específico"
                >
                  <option value="">Todos los períodos</option>
                  {periodos.map(periodo => (
                    <option key={periodo.periodo} value={periodo.periodo}>
                      {periodo.periodo} ({periodo.total_actividades} logs)
                    </option>
                  ))}
                </select>

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
                    <th className="px-3 py-2 text-left font-medium">Cierre</th>
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
                        <div 
                          className="flex items-center text-xs cursor-help"
                          title={log.descripcion || 'Sin descripción'}
                        >
                          {getAccionIcon(log.accion)}
                          <span className="ml-1">{log.accion}</span>
                        </div>
                      </td>
                      <td className="px-3 py-2 text-xs">
                        {log.cliente_nombre}
                      </td>
                      <td className="px-3 py-2">
                        <span 
                          className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getTarjetaColor(log.tarjeta)}`}
                          title={`Tarjeta: ${log.tarjeta}`}
                        >
                          {log.tarjeta}
                        </span>
                      </td>
                      <td className="px-3 py-2">
                        {log.estado_cierre && (
                          <div className="flex flex-col">
                            <span 
                              className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getCierreColor(log.estado_cierre)}`}
                              title={`Estado: ${log.estado_cierre}${log.periodo_cierre ? ` - Período: ${log.periodo_cierre}` : ''}`}
                            >
                              {log.estado_cierre}
                            </span>
                            {log.periodo_cierre && (
                              <span className="text-xs text-gray-400 mt-1">
                                {log.periodo_cierre}
                              </span>
                            )}
                          </div>
                        )}
                        {!log.estado_cierre && (
                          <span className="text-xs text-gray-500">N/A</span>
                        )}
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
  );
};

export default LogsActividad;
