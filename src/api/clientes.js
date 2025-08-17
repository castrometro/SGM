import api from "./config";
import { obtenerClientesConEstadoCierre } from "./contabilidad";

export const obtenerClientesAsignados = async () => {
  const response = await api.get("/clientes/asignados/");
  return response.data;
};

export const obtenerClientesAsignadosContabilidad = async () => {
  const clientes = await obtenerClientesAsignados();
  return await obtenerClientesConEstadoCierre(clientes);
};

export const obtenerTodosLosClientes = async () => {
  const response = await api.get("/clientes/");
  return response.data;
};

export const obtenerClientesPorArea = async () => {
  const response = await api.get("/clientes-por-area/");
  return response.data;
};

export const obtenerClientesPorAreaContabilidad = async () => {
  const clientes = await obtenerClientesPorArea();
  return await obtenerClientesConEstadoCierre(clientes);
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