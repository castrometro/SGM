// src/api/supervisores.js
import api from "./config";

export const obtenerMisAnalistas = async () => {
  const response = await api.get("/usuarios/mis-analistas/");
  return response.data;
};

export const obtenerClientesSupervisionados = async () => {
  const response = await api.get("/usuarios/clientes-supervisados/");
  return response.data;
};

export const asignarSupervisor = async (analistaId, supervisorId) => {
  const response = await api.post(`/usuarios/${analistaId}/asignar-supervisor/`, {
    supervisor_id: supervisorId
  });
  return response.data;
};

export const obtenerSupervisoresDisponibles = async () => {
  const response = await api.get("/usuarios/", {
    params: {
      tipo_usuario: 'supervisor'
    }
  });
  return response.data;
};