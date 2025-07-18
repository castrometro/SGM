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

// Actualizar estado automático del cierre
export const actualizarEstadoCierreNomina = async (cierreId) => {
  const res = await api.post(`/nomina/cierres/${cierreId}/actualizar-estado/`);
  return res.data;
};

// ========== SISTEMA DE INCIDENCIAS ==========

// Obtener incidencias de un cierre
export const obtenerIncidenciasCierre = async (cierreId, filtros = {}) => {
  const params = { cierre: cierreId, ...filtros };
  const response = await api.get('/nomina/incidencias/', { params });
  return response.data;
};

// Generar incidencias para un cierre
export const generarIncidenciasCierre = async (cierreId) => {
  const response = await api.post(`/nomina/incidencias/generar/${cierreId}/`);
  return response.data;
};

// Obtener resumen de incidencias de un cierre
export const obtenerResumenIncidencias = async (cierreId) => {
  const response = await api.get(`/nomina/incidencias/resumen/${cierreId}/`);
  return response.data;
};

// Cambiar estado de una incidencia
export const cambiarEstadoIncidencia = async (incidenciaId, estado) => {
  const response = await api.patch(`/nomina/incidencias/${incidenciaId}/cambiar_estado/`, {
    estado
  });
  return response.data;
};

// Asignar usuario a una incidencia
export const asignarUsuarioIncidencia = async (incidenciaId, usuarioId) => {
  const response = await api.patch(`/nomina/incidencias/${incidenciaId}/asignar_usuario/`, {
    usuario_id: usuarioId
  });
  return response.data;
};

// Obtener una incidencia específica
export const obtenerIncidencia = async (incidenciaId) => {
  const response = await api.get(`/nomina/incidencias/${incidenciaId}/`);
  return response.data;
};

// Vista previa de incidencias (sin guardar)
export const previewIncidenciasCierre = async (cierreId) => {
  const response = await api.get(`/nomina/incidencias/preview/${cierreId}/`);
  return response.data;
};

// ⚠️ DESARROLLO ÚNICAMENTE - Limpiar incidencias para testing
export const devLimpiarIncidencias = async (cierreId) => {
  const response = await api.post(`/nomina/incidencias/dev-clear/${cierreId}/`);
  return response.data;
};

// ========== ANÁLISIS DE DATOS ==========

// Iniciar análisis de datos del cierre
export const iniciarAnalisisDatos = async (cierreId, toleranciaVariacion = 30) => {
  const response = await api.post(`/nomina/incidencias/analizar-datos/${cierreId}/`, {
    tolerancia_variacion: toleranciaVariacion
  });
  return response.data;
};

// Obtener análisis de datos de un cierre
export const obtenerAnalisisDatos = async (cierreId) => {
  const response = await api.get(`/nomina/analisis-datos/`, {
    params: { cierre: cierreId }
  });
  return response.data;
};

// Obtener incidencias de variación salarial
export const obtenerIncidenciasVariacion = async (cierreId, filtros = {}) => {
  const params = { cierre: cierreId, ...filtros };
  const response = await api.get('/nomina/incidencias-variacion/', { params });
  return response.data;
};

// Justificar incidencia de variación salarial
export const justificarIncidenciaVariacion = async (incidenciaId, justificacion) => {
  const response = await api.post(`/nomina/incidencias-variacion/${incidenciaId}/justificar/`, {
    justificacion
  });
  return response.data;
};

// Aprobar incidencia de variación salarial
export const aprobarIncidenciaVariacion = async (incidenciaId, comentario = '') => {
  const response = await api.post(`/nomina/incidencias-variacion/${incidenciaId}/aprobar/`, {
    comentario
  });
  return response.data;
};

// Rechazar incidencia de variación salarial
export const rechazarIncidenciaVariacion = async (incidenciaId, comentario) => {
  const response = await api.post(`/nomina/incidencias-variacion/${incidenciaId}/rechazar/`, {
    comentario
  });
  return response.data;
};

// Obtener resumen de incidencias de variación salarial
export const obtenerResumenIncidenciasVariacion = async (cierreId) => {
  const response = await api.get(`/nomina/incidencias-variacion/resumen/${cierreId}/`);
  return response.data;
};

// Obtener resumen de incidencias de variación salarial
export const obtenerResumenVariaciones = async (cierreId) => {
  const response = await api.get(`/nomina/incidencias-variacion/resumen/${cierreId}/`);
  return response.data;
};

// ========== RESOLUCIONES DE INCIDENCIAS ==========

// Crear una nueva resolución para una incidencia
export const crearResolucionIncidencia = async (incidenciaId, resolucionData) => {
  const response = await api.post('/nomina/resoluciones-incidencias/', {
    incidencia_id: incidenciaId,
    ...resolucionData
  });
  return response.data;
};

// Obtener historial de resoluciones de una incidencia
export const obtenerHistorialIncidencia = async (incidenciaId) => {
  const response = await api.get(`/nomina/resoluciones-incidencias/historial/${incidenciaId}/`);
  return response.data;
};

// Obtener resoluciones de un usuario
export const obtenerResolucionesUsuario = async (usuarioId) => {
  const response = await api.get('/nomina/resoluciones-incidencias/', {
    params: { usuario: usuarioId }
  });
  return response.data;
};

// ========== ESTADO DE INCIDENCIAS EN CIERRES ==========

// Obtener estado de incidencias de un cierre
export const obtenerEstadoIncidenciasCierre = async (cierreId) => {
  const response = await api.get(`/nomina/cierres-incidencias/${cierreId}/estado_incidencias/`);
  return response.data;
};

// Lanzar generación de incidencias desde el cierre
export const lanzarGeneracionIncidencias = async (cierreId) => {
  const response = await api.post(`/nomina/cierres-incidencias/${cierreId}/lanzar_generacion_incidencias/`);
  return response.data;
};

// ========== FUNCIONES DE UTILIDAD ==========

// Obtener estadísticas generales de incidencias
export const obtenerEstadisticasIncidencias = async (filtros = {}) => {
  const response = await api.get('/nomina/incidencias/', { 
    params: { ...filtros, stats: true } 
  });
  return response.data;
};

// Exportar incidencias a Excel
export const exportarIncidenciasExcel = async (cierreId) => {
  const response = await api.get(`/nomina/incidencias/exportar/${cierreId}/`, {
    responseType: 'blob'
  });
  return response.data;
};

export const obtenerCierresCliente = async (clienteId) => {
  const res = await api.get(`/nomina/cierres/`, { params: { cliente: clienteId } });
  return res.data;
}

export const subirLibroRemuneraciones = async (cierreId, archivo) => {
  console.log('🌐 API subirLibroRemuneraciones LLAMADA:', {
    timestamp: new Date().toISOString(),
    cierreId,
    fileName: archivo.name,
    fileSize: archivo.size,
    stackTrace: new Error().stack.split('\n').slice(0, 8).join('\n')
  });

  const formData = new FormData();
  formData.append("cierre", cierreId); // el nombre debe calzar con tu serializer
  formData.append("archivo", archivo);
  // Si necesitas user/otros campos, también agrégalos aquí

  const res = await api.post("/nomina/libros-remuneraciones/", formData, {
    headers: {
      "Content-Type": "multipart/form-data"
    }
  });
  
  console.log('🌐 API subirLibroRemuneraciones RESPUESTA:', {
    timestamp: new Date().toISOString(),
    status: res.status,
    data: res.data
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
  const payload = mapeos.map(m => ({
    ...m,
    concepto_libro_id: m.concepto_libro_id ?? null,
  }));
  const response = await api.post(
    `/nomina/archivos-novedades/${archivoId}/clasificar_headers/`,
    { mapeos: payload }
  );
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

// ========== UPLOAD LOG NÓMINA ==========

// Obtener estado del upload log de nómina
export const obtenerEstadoUploadLogNomina = async (uploadLogId) => {
  const response = await api.get(`/nomina/upload-log/${uploadLogId}/estado/`);
  return response.data;
};

// ========== ELIMINACIÓN DE ARCHIVOS ==========

// Eliminar libro de remuneraciones
export const eliminarLibroRemuneraciones = async (libroId) => {
  const response = await api.delete(`/nomina/libros-remuneraciones/${libroId}/`);
  return response.data;
};

// Eliminar movimientos del mes  
export const eliminarMovimientosMes = async (movimientoId) => {
  const response = await api.delete(`/nomina/movimientos-mes/${movimientoId}/`);
  return response.data;
};

// Eliminar archivo del analista
export const eliminarArchivoAnalista = async (archivoId) => {
  const response = await api.delete(`/nomina/archivos-analista/${archivoId}/`);
  return response.data;
};

// Eliminar archivo de novedades
export const eliminarArchivoNovedades = async (archivoId) => {
  const response = await api.delete(`/nomina/archivos-novedades/${archivoId}/`);
  return response.data;
};

export const obtenerCategoriasIncidencias = async () => {
  const response = await api.get('/nomina/incidencias/categorias/');
  return response.data;
};

// Obtener todos los cierres de nómina (para vista gerencial)
export const obtenerCierresNomina = async () => {
  const res = await api.get('/nomina/cierres/');
  return res.data;
};

// ========== SISTEMA DE DISCREPANCIAS ==========

// Obtener discrepancias de un cierre
export const obtenerDiscrepanciasCierre = async (cierreId, filtros = {}) => {
  const params = { cierre: cierreId, ...filtros };
  const response = await api.get('/nomina/discrepancias/', { params });
  return response.data;
};

// Generar discrepancias para un cierre
export const generarDiscrepanciasCierre = async (cierreId) => {
  const response = await api.post(`/nomina/discrepancias/generar/${cierreId}/`);
  return response.data;
};

// Obtener resumen de discrepancias de un cierre
export const obtenerResumenDiscrepancias = async (cierreId) => {
  const response = await api.get(`/nomina/discrepancias/resumen/${cierreId}/`);
  return response.data;
};

// Obtener estado de discrepancias de un cierre
export const obtenerEstadoDiscrepanciasCierre = async (cierreId) => {
  const response = await api.get(`/nomina/cierres-discrepancias/${cierreId}/estado_verificacion/`);
  return response.data;
};

// Vista previa de discrepancias (sin guardar)
export const previewDiscrepanciasCierre = async (cierreId) => {
  const response = await api.get(`/nomina/discrepancias/preview/${cierreId}/`);
  return response.data;
};

// Limpiar discrepancias de un cierre
export const limpiarDiscrepanciasCierre = async (cierreId) => {
  const response = await api.delete(`/nomina/discrepancias/limpiar/${cierreId}/`);
  return response.data;
};
