// src/api/gerente.js
import api from "./config";

// ========== GESTIÓN DE CLIENTES ==========

export const obtenerClientesGerente = async () => {
  const res = await api.get('/gerente/clientes/');
  return res.data;
};

export const reasignarCliente = async (clienteId, nuevoAnalistaId, area) => {
  const res = await api.post('/gerente/clientes/reasignar/', {
    cliente_id: clienteId,
    nuevo_analista_id: nuevoAnalistaId,
    area: area
  });
  return res.data;
};

export const obtenerPerfilCompletoCliente = async (clienteId) => {
  const res = await api.get(`/gerente/clientes/${clienteId}/perfil-completo/`);
  return res.data;
};

// ==================== LOGS Y ACTIVIDAD ====================

export const obtenerLogsActividad = async (filtros = {}) => {
  const params = new URLSearchParams();
  
  if (filtros.cliente_id) params.append('cliente_id', filtros.cliente_id);
  if (filtros.usuario_id) params.append('usuario_id', filtros.usuario_id);
  if (filtros.tarjeta) params.append('tarjeta', filtros.tarjeta);
  if (filtros.accion) params.append('accion', filtros.accion);
  if (filtros.fecha_desde) params.append('fecha_desde', filtros.fecha_desde);
  if (filtros.fecha_hasta) params.append('fecha_hasta', filtros.fecha_hasta);
  if (filtros.page) params.append('page', filtros.page);
  if (filtros.page_size) params.append('page_size', filtros.page_size);
  
  const res = await api.get(`/contabilidad/gerente/logs-actividad/?${params}`);
  return res.data;
};

export const obtenerEstadisticasActividad = async (periodo = 'semana') => {
  const res = await api.get(`/contabilidad/gerente/estadisticas-actividad/?periodo=${periodo}`);
  return res.data;
};

export const obtenerUsuariosActividad = async () => {
  const res = await api.get('/contabilidad/gerente/usuarios-actividad/');
  return res.data;
};

// ==================== ESTADOS DE CIERRES ====================

export const obtenerEstadosCierres = async (filtros = {}) => {
  const params = new URLSearchParams();
  
  if (filtros.cliente_id) params.append('cliente_id', filtros.cliente_id);
  if (filtros.estado) params.append('estado', filtros.estado);
  if (filtros.usuario_id) params.append('usuario_id', filtros.usuario_id); // Cambio: analista_id -> usuario_id
  if (filtros.periodo) params.append('periodo', filtros.periodo);
  
  const res = await api.get(`/contabilidad/gerente/estados-cierres/?${params}`);
  return res.data;
};

export const obtenerMetricasCierres = async () => {
  const res = await api.get('/contabilidad/gerente/metricas-cierres/');
  return res.data;
};

// ==================== CACHE REDIS ====================

export const obtenerEstadoCache = async () => {
  const res = await api.get('/contabilidad/gerente/estado-cache/');
  return res.data;
};

export const obtenerCierresEnCache = async () => {
  const res = await api.get('/contabilidad/gerente/cierres-cache/');
  return res.data;
};

export const cargarCierreACache = async (clienteId, periodo) => {
  const res = await api.post('/contabilidad/gerente/cargar-cierre-cache/', {
    cliente_id: clienteId,
    periodo: periodo
  });
  return res.data;
};

export const limpiarCache = async (opciones = {}) => {
  const res = await api.post('/contabilidad/gerente/limpiar-cache/', opciones);
  return res.data;
};

export const obtenerMetricasCache = async () => {
  const res = await api.get('/contabilidad/gerente/metricas-cache/');
  return res.data;
};

// ==================== GESTIÓN DE USUARIOS Y CLIENTES ====================

export const obtenerUsuarios = async () => {
  const res = await api.get('/contabilidad/gerente/usuarios/');
  return res.data;
};

export const crearUsuario = async (datosUsuario) => {
  const res = await api.post('/contabilidad/gerente/usuarios/', datosUsuario);
  return res.data;
};

export const actualizarUsuario = async (userId, datosUsuario) => {
  const res = await api.put(`/contabilidad/gerente/usuarios/${userId}/`, datosUsuario);
  return res.data;
};

export const eliminarUsuario = async (userId) => {
  const res = await api.delete(`/contabilidad/gerente/usuarios/${userId}/eliminar/`);
  return res.data;
};

export const obtenerClientes = async () => {
  const res = await api.get('/contabilidad/gerente/clientes/');
  return res.data;
};

export const crearCliente = async (datosCliente) => {
  const res = await api.post('/contabilidad/gerente/clientes/', datosCliente);
  return res.data;
};

export const actualizarCliente = async (clienteId, datosCliente) => {
  const res = await api.put(`/contabilidad/gerente/actualizar-cliente/${clienteId}/`, datosCliente);
  return res.data;
};

export const eliminarCliente = async (clienteId) => {
  const res = await api.delete(`/contabilidad/gerente/eliminar-cliente/${clienteId}/`);
  return res.data;
};

export const obtenerAreas = async () => {
  const res = await api.get('/contabilidad/gerente/areas/');
  return res.data;
};

export const obtenerMetricasSistema = async () => {
  const res = await api.get('/contabilidad/gerente/metricas-sistema/');
  return res.data;
};

// ==================== FUNCIONES ADICIONALES ====================

export const forzarRecalculoCierre = async (cierreId) => {
  const res = await api.post(`/contabilidad/gerente/cierres/${cierreId}/recalcular/`);
  return res.data;
};

export const reasignarClienteMasivo = async (asignaciones) => {
  const res = await api.post('/contabilidad/gerente/reasignar-masivo/', {
    asignaciones: asignaciones
  });
  return res.data;
};

// ========== MÉTRICAS Y KPIs ==========

export const obtenerMetricasAvanzadas = async (filtros = {}) => {
  const res = await api.get('/gerente/metricas/', { params: filtros });
  return res.data;
};

export const obtenerKPIsEquipo = async (periodo = 'month') => {
  const res = await api.get(`/gerente/kpis/?periodo=${periodo}`);
  return res.data;
};

export const obtenerTendenciasCierres = async (meses = 6) => {
  const res = await api.get(`/gerente/tendencias-cierres/?meses=${meses}`);
  return res.data;
};

// ========== ANÁLISIS DE PORTAFOLIO ==========

export const obtenerAnalisisPortafolio = async (filtros = {}) => {
  const res = await api.get('/gerente/analisis-portafolio/', { params: filtros });
  return res.data;
};

export const obtenerSegmentacionClientes = async (tipoVista = 'valor') => {
  const res = await api.get(`/gerente/segmentacion-clientes/?vista=${tipoVista}`);
  return res.data;
};

export const obtenerTopClientes = async (categoria = 'valor', limite = 10) => {
  const res = await api.get(`/gerente/top-clientes/?categoria=${categoria}&limite=${limite}`);
  return res.data;
};

// ========== PLANIFICACIÓN Y PRONÓSTICOS ==========

export const obtenerCapacidadEquipo = async () => {
  const res = await api.get('/gerente/capacidad-equipo/');
  return res.data;
};

export const obtenerPronosticosCarga = async (meses = 3) => {
  const res = await api.get(`/gerente/pronosticos-carga/?meses=${meses}`);
  return res.data;
};

export const obtenerPlanificacionRecursos = async (periodo) => {
  const res = await api.get(`/gerente/planificacion-recursos/?periodo=${periodo}`);
  return res.data;
};

// ========== SISTEMA DE ALERTAS ==========

export const obtenerAlertas = async (filtros = {}) => {
  const res = await api.get('/gerente/alertas/', { params: filtros });
  return res.data;
};

export const marcarAlertaLeida = async (alertaId) => {
  const res = await api.patch(`/gerente/alertas/${alertaId}/marcar-leida/`);
  return res.data;
};

export const configurarAlertas = async (configuracion) => {
  const res = await api.post('/gerente/alertas/configurar/', configuracion);
  return res.data;
};

export const obtenerConfiguracionAlertas = async () => {
  const res = await api.get('/gerente/alertas/configuracion/');
  return res.data;
};

// ========== REPORTES ==========

export const generarReporte = async (tipoReporte, parametros = {}) => {
  const res = await api.post('/gerente/reportes/generar/', {
    tipo: tipoReporte,
    parametros
  });
  return res.data;
};

export const obtenerHistorialReportes = async (limite = 20) => {
  const res = await api.get(`/gerente/reportes/historial/?limite=${limite}`);
  return res.data;
};

export const descargarReporte = async (reporteId) => {
  const res = await api.get(`/gerente/reportes/${reporteId}/descargar/`, {
    responseType: 'blob'
  });
  return res.data;
};

// ========== GESTIÓN DE EQUIPOS ==========

export const obtenerRendimientoAnalistas = async (periodo = 'month') => {
  const res = await api.get(`/gerente/analistas/rendimiento/?periodo=${periodo}`);
  return res.data;
};

export const obtenerEstadisticasEquipo = async () => {
  const res = await api.get('/gerente/equipo/estadisticas/');
  return res.data;
};

export const asignarObjetivos = async (analistaId, objetivos) => {
  const res = await api.post(`/gerente/analistas/${analistaId}/objetivos/`, objetivos);
  return res.data;
};

export const evaluarRendimiento = async (analistaId, evaluacion) => {
  const res = await api.post(`/gerente/analistas/${analistaId}/evaluacion/`, evaluacion);
  return res.data;
};

// ==================== USUARIOS CONECTADOS ====================

export const obtenerUsuariosConectados = async () => {
  // Agregar timestamp para evitar cache
  const timestamp = new Date().getTime();
  const res = await api.get(`/contabilidad/gerente/usuarios-conectados/?t=${timestamp}`);
  return res.data;
};
