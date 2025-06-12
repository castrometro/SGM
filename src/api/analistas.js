import api from "./config";

export const obtenerAnalistasPerformance = async () => {
  const res = await api.get("/bi-analistas/");
  return res.data;
};

export const obtenerDashboardData = async (periodo = "current_month") => {
  const res = await api.get(`/dashboard/?periodo=${periodo}`);
  return res.data;
};

export const obtenerAnalistasDetallado = async () => {
  const res = await api.get("/analistas-detallado/");
  return res.data;
};

export const obtenerClientesDisponibles = async (analistaId) => {
  const res = await api.get(`/clientes-disponibles/${analistaId}/`);
  return res.data;
};

export const obtenerClientesAsignados = async (analistaId) => {
  const res = await api.get(`/clientes-asignados/${analistaId}/`);
  return res.data;
};

export const asignarClienteAnalista = async (analistaId, clienteId) => {
  const res = await api.post("/asignaciones/", {
    usuario: analistaId,
    cliente: clienteId
  });
  return res.data;
};

export const removerAsignacion = async (analistaId, clienteId) => {
  const res = await api.delete(`/asignaciones/${analistaId}/${clienteId}/`);
  return res.data;
};

export const obtenerEstadisticasAnalista = async (analistaId) => {
  const res = await api.get(`/analistas-detallado/${analistaId}/estadisticas/`);
  return res.data;
};

export const actualizarAnalista = async (analistaId, datosAnalista) => {
  const res = await api.put(`/usuarios/${analistaId}/`, datosAnalista);
  return res.data;
};

export const crearAnalista = async (datosAnalista) => {
  const res = await api.post("/usuarios/", datosAnalista);
  return res.data;
};

export const cambiarEstadoAnalista = async (analistaId, activo) => {
  const res = await api.patch(`/usuarios/${analistaId}/`, { is_active: activo });
  return res.data;
};

export const obtenerRendimientoAnalista = async (analistaId, periodo = 'month') => {
  const res = await api.get(`/analistas-detallado/${analistaId}/rendimiento/?periodo=${periodo}`);
  return res.data;
};
