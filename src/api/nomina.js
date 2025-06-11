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
  return res.data;
};

export const procesarLibroRemuneraciones = async (libroId) => {
  const res = await api.post(
    `/nomina/libros-remuneraciones/${libroId}/procesar/`
  );
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
export const descargarPlantillaMovimientosMes = () => {
  return `${api.defaults.baseURL}/nomina/plantilla-movimientos-mes/`;
};

// Plantillas para archivos del analista
export const descargarPlantillaFiniquitos = () => {
  return `${api.defaults.baseURL}/nomina/plantilla-finiquitos/`;
};

export const descargarPlantillaIncidencias = () => {
  return `${api.defaults.baseURL}/nomina/plantilla-incidencias/`;
};

export const descargarPlantillaIngresos = () => {
  return `${api.defaults.baseURL}/nomina/plantilla-ingresos/`;
};

// Funciones para archivos del analista
export const subirArchivoAnalista = async (cierreId, tipoArchivo, formData) => {
  const response = await api.post(`/nomina/archivos-analista/subir/${cierreId}/${tipoArchivo}/`, formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
  return response.data;
};

export const obtenerEstadoArchivoAnalista = async (cierreId, tipoArchivo) => {
  const response = await api.get(`/nomina/archivos-analista/?cierre=${cierreId}&tipo_archivo=${tipoArchivo}`);
  return response.data;
};

export const reprocesarArchivoAnalista = async (archivoId) => {
  const response = await api.post(`/nomina/archivos-analista/${archivoId}/reprocesar/`);
  return response.data;
};
//esto se cacheará en redis
export const obtenerClasificacionesCliente = async (clienteId) => {
  const response = await api.get(`/nomina/conceptos-remuneracion/?cliente_id=${clienteId}`);
  return response.data; // Devuelve array de { nombre_concepto, clasificacion, hashtags }
};
//--------------------------

export const guardarConceptosRemuneracion = async (
  clienteId,
  conceptos,
  cierreId = null
) => {
  const payload = {
    cliente_id: clienteId,
    conceptos,
  };
  if (cierreId) {
    payload.cierre_id = cierreId;
  }
  const response = await api.post(`/nomina/conceptos/`, payload);
  return response.data;
};

export const eliminarConceptoRemuneracion = async (clienteId, nombreConcepto) => {
  const encoded = encodeURIComponent(nombreConcepto);
  const res = await api.delete(
    `/nomina/conceptos/${clienteId}/${encoded}/eliminar/`
  );
  return res.data;
};

export const obtenerConceptosRemuneracionPorCierre = async (cierreId) => {
  const response = await api.get(`/nomina/conceptos/cierre/${cierreId}/`);
  return response.data;
};

export const descargarPlantillaNovedades = () => {
  return `${api.defaults.baseURL}/nomina/plantilla-novedades/`;
};

// Funciones específicas para archivos de novedades
export const subirArchivoNovedades = async (cierreId, formData) => {
  const response = await api.post(`/nomina/archivos-novedades/subir/${cierreId}/`, formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
  return response.data;
};

export const obtenerEstadoArchivoNovedades = async (cierreId) => {
  const response = await api.get(`/nomina/archivos-novedades/estado/${cierreId}/`);
  return response.data;
};

export const reprocesarArchivoNovedades = async (archivoId) => {
  const response = await api.post(`/nomina/archivos-novedades/${archivoId}/reprocesar/`);
  return response.data;
};

// Funciones para clasificación de headers en novedades
export const obtenerHeadersNovedades = async (archivoId) => {
  const response = await api.get(`/nomina/archivos-novedades/${archivoId}/headers/`);
  return response.data;
};

export const mapearHeadersNovedades = async (archivoId, mapeos) => {
  const response = await api.post(`/nomina/archivos-novedades/${archivoId}/clasificar_headers/`, {
    mapeos
  });
  return response.data;
};

export const procesarFinalNovedades = async (archivoId) => {
  const response = await api.post(`/nomina/archivos-novedades/${archivoId}/procesar_final/`);
  return response.data;
};

export const obtenerConceptosRemuneracionNovedades = async (clienteId) => {
  const response = await api.get(`/nomina/conceptos-remuneracion-novedades/?cliente=${clienteId}`);
  return response.data;
};