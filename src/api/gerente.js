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
