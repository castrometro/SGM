// src/api/nomina.js
import api from "./config";

export const obtenerResumenNomina = async (clienteId) => {
  const response = await api.get(`/nomina/cierres/resumen/${clienteId}/`);
  return response.data;
};


export const obtenerCierreMensual = async (clienteId, periodo) => {
  // Normaliza siempre el periodo

  const res = await api.get(`/nomina/cierres/`, { params: { cliente: clienteId, periodo: periodo } });
  return res.data.length > 0 ? res.data[0] : null;
};

export const crearCierreMensual = async (clienteId, periodo, checklist) => {
  
  const payload = {
    cliente: Number(clienteId),
    periodo: periodo,  
    checklist,
  };
  const res = await api.post("/nomina/cierres/", payload);
  return res.data;
};


export const obtenerCierreNominaPorId = async (cierreId) => {
  const res = await api.get(`/nomina/cierres/${cierreId}/`);
  return res.data;
};
export const actualizarCierreNomina = async (cierreId, data) => {
  const res = await api.put(`/nomina/cierres/${cierreId}/`, data);
  return res.data;
};
export const eliminarCierreNomina = async (cierreId) => {
  const res = await api.delete(`/nomina/cierres/${cierreId}/`);
  return res.data;
};
export const obtenerIncidenciasCierre = async (cierreId) => {
  const res = await api.get(`/nomina/cierres/${cierreId}/incidencias/`);
  return res.data;
};
export const obtenerCierresCliente = async (clienteId) => {
  const res = await api.get(`/nomina/cierres/`, { params: { cliente: clienteId } });
  return res.data;
}

export const subirLibroRemuneraciones = async (cierreId, archivo) => {
  const formData = new FormData();
  formData.append("cierre", cierreId); // el nombre debe calzar con tu serializer
  formData.append("archivo", archivo);
  // Si necesitas user/otros campos, también agrégalos aquí

  const res = await api.post("/nomina/libros-remuneraciones/", formData, {
    headers: {
      "Content-Type": "multipart/form-data"
    }
  });
  return res.data;
};
export const obtenerEstadoLibroRemuneraciones = async (cierreId) => {
  const res = await api.get(`/nomina/libros-remuneraciones/estado/${cierreId}/`);
  console.log("Estado Libro Remuneraciones:", res.data);
  return res.data;
};
export const obtenerConceptosLibroRemuneraciones = async (clienteId, periodo) => {
  const response = await api.get(`/nomina/libro_remuneraciones/conceptos/${clienteId}/${periodo}/`);
  return response.data;
};

export const guardarClasificacionesLibroRemuneraciones = async (cierreId, clasificaciones) => {
  const response = await api.post(`/nomina/libro_remuneraciones/clasificar/${cierreId}/`, { clasificaciones });
  return response.data;
};
export const obtenerProgresoClasificacionRemu = async (cierreId) => {
  const response = await api.get(`/nomina/libro_remuneraciones/progreso_clasificacion/${cierreId}/`);
  return response.data;
};
export const obtenerEstadoMovimientosMes = async (cierreId) => {
  const response = await api.get(`/nomina/movimientos/estado/${cierreId}/`);
  return response.data;
};

export const subirMovimientosMes = async (cierreId, formData) => {
  const response = await api.post(`/nomina/movimientos/subir/${cierreId}/`, formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
  return response.data;
};
export const obtenerProgresoClasificacionTodosLosSets = async (cierreId) => {
  const response = await api.get(`/nomina/clasificacion/progreso_todos_sets/${cierreId}/`);
  return response.data;
};
export const obtenerProgresoIncidencias = async (cierreId) => {
  const response = await api.get(`/nomina/incidencias/progreso/${cierreId}/`);
  return response.data;
};

export const descargarPlantillaLibroRemuneraciones = () => {
  return `${api.defaults.baseURL}/nomina/plantilla-libro-remuneraciones/`;
};


//esto se cacheará en redis
export const obtenerClasificacionesCliente = async (clienteId) => {
  const response = await api.get(`/nomina/conceptos-remuneracion/?cliente_id=${clienteId}`);
  return response.data; // Devuelve array de { nombre_concepto, clasificacion, hashtags }
};
//--------------------------

export const guardarConceptosRemuneracion = async (clienteId, conceptos) => {
  const response = await api.post(`/nomina/conceptos/`, {
    cliente_id: clienteId,
    conceptos: conceptos,
  });
  return response.data;
};
