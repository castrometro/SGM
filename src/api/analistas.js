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
