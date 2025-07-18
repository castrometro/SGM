import api from "./config";

export const obtenerClientesAsignados = async () => {
  const response = await api.get("/clientes/asignados/");
  return response.data;
};

export const obtenerTodosLosClientes = async () => {
  const response = await api.get("/clientes/");
  return response.data;
};

export const obtenerClientesPorArea = async () => {
  const response = await api.get("/clientes-por-area/");
  return response.data;
};


export const obtenerCliente = async (id) => {
  const response = await api.get(`/clientes/${id}/`);
  return response.data;
};

export const obtenerResumenContable = async (clienteId) => {
  const res = await api.get(`/contabilidad/clientes/${clienteId}/resumen/`);
  return res.data;
};

export const obtenerServiciosCliente = async (clienteId) => {
  const usuario = JSON.parse(localStorage.getItem("usuario"));

  const endpoint =
    usuario.tipo_usuario === "analista"
      ? `/clientes/${clienteId}/servicios-area/`
      : `/clientes/${clienteId}/servicios/`;

  const res = await api.get(endpoint);
  return res.data;
};