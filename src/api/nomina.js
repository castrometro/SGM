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

// Consolidar datos de Talana (Libro + Novedades)
export const consolidarDatosTalana = async (cierreId) => {
  const res = await api.post(`/nomina/cierres/${cierreId}/consolidar-datos/`);
  return res.data;
};

// Consultar estado de tarea Celery
export const consultarEstadoTarea = async (cierreId, taskId) => {
  const res = await api.get(`/nomina/cierres/${cierreId}/task-status/${taskId}/`);
  return res.data;
};

// ========== SISTEMA DE INCIDENCIAS ==========

// Obtener incidencias de un cierre
export const obtenerIncidenciasCierre = async (cierreId, filtros = {}) => {
  console.log("🔍 [API] obtenerIncidenciasCierre - Iniciando con:", { cierreId, filtros });
  
  const params = { cierre: cierreId, ...filtros };
  console.log("🔍 [API] obtenerIncidenciasCierre - Parámetros de la petición:", params);
  
  try {
    const response = await api.get('/nomina/incidencias/', { params });
    console.log("🔍 [API] obtenerIncidenciasCierre - Respuesta completa:", response);
    console.log("🔍 [API] obtenerIncidenciasCierre - Datos recibidos:", response.data);
    console.log("🔍 [API] obtenerIncidenciasCierre - Status:", response.status);
    
    return response.data;
  } catch (error) {
    console.error("❌ [API] obtenerIncidenciasCierre - Error:", error);
    console.error("❌ [API] obtenerIncidenciasCierre - Error response:", error.response);
    throw error;
  }
};

// Generar incidencias para un cierre
export const generarIncidenciasCierre = async (cierreId, clasificacionesSeleccionadas = null) => {
  const payload = { cierre_id: cierreId };
  
  // Si se proporcionan clasificaciones específicas, incluirlas en el payload
  if (clasificacionesSeleccionadas && clasificacionesSeleccionadas.length > 0) {
    payload.clasificaciones_seleccionadas = clasificacionesSeleccionadas;
  }
  
  const response = await api.post(`/nomina/incidencias/generar/${cierreId}/`, payload);
  return response.data;
};

// Limpiar incidencias de un cierre (función de debug)
export const limpiarIncidenciasCierre = async (cierreId) => {
  const response = await api.delete(`/nomina/incidencias/limpiar/${cierreId}/`);
  return response.data;
};

// Finalizar cierre (cuando no hay incidencias o todas están resueltas)
export const finalizarCierre = async (cierreId) => {
  const response = await api.post(`/nomina/incidencias/finalizar/${cierreId}/`);
  return response.data;
};

// Obtener resumen de incidencias de un cierre
export const obtenerResumenIncidencias = async (cierreId) => {
  console.log("🔍 [API] obtenerResumenIncidencias - Iniciando para cierre:", cierreId);
  
  try {
    const response = await api.get(`/nomina/incidencias/resumen/${cierreId}/`);
    console.log("🔍 [API] obtenerResumenIncidencias - Respuesta completa:", response);
    console.log("🔍 [API] obtenerResumenIncidencias - Datos recibidos:", response.data);
    console.log("🔍 [API] obtenerResumenIncidencias - Status:", response.status);
    
    return response.data;
  } catch (error) {
    console.error("❌ [API] obtenerResumenIncidencias - Error:", error);
    console.error("❌ [API] obtenerResumenIncidencias - Error response:", error.response);
    throw error;
  }
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
    incidencia: incidenciaId,
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

// Obtener incidencias que requieren mi atención (según turnos de conversación)
export const obtenerIncidenciasMiTurno = async () => {
  const response = await api.get('/nomina/incidencias/mi-turno/');
  return response.data;
};

// ========== ESTADO DE INCIDENCIAS EN CIERRES ==========

// Obtener estado de incidencias de un cierre
export const obtenerEstadoIncidenciasCierre = async (cierreId) => {
  console.log("🔍 [API] obtenerEstadoIncidenciasCierre - Iniciando para cierre:", cierreId);
  
  try {
    const response = await api.get(`/nomina/cierres/${cierreId}/estado-incidencias/`);
    console.log("🔍 [API] obtenerEstadoIncidenciasCierre - Respuesta completa:", response);
    console.log("🔍 [API] obtenerEstadoIncidenciasCierre - Datos recibidos:", response.data);
    console.log("🔍 [API] obtenerEstadoIncidenciasCierre - Status:", response.status);
    
    return response.data;
  } catch (error) {
    console.error("❌ [API] obtenerEstadoIncidenciasCierre - Error:", error);
    console.error("❌ [API] obtenerEstadoIncidenciasCierre - Error response:", error.response);
    throw error;
  }
};

// Lanzar generación de incidencias desde el cierre
export const lanzarGeneracionIncidencias = async (cierreId) => {
  const response = await api.post(`/nomina/cierres-incidencias/${cierreId}/lanzar_generacion_incidencias/`);
  return response.data;
};

// Obtener análisis completo temporal (todas las comparaciones vs mes anterior)
export const obtenerAnalisisCompletoTemporal = async (cierreId) => {
  const response = await api.get(`/nomina/incidencias/analisis-completo/${cierreId}/`);
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

// === Resumen Nómina Consolidada ===

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

export const descargarPlantillaAusentismos = () => {
  return `${api.defaults.baseURL}/nomina/plantilla-ausentismos/`;
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
  try {
    const response = await api.get(`/nomina/archivos-analista/?cierre=${cierreId}&tipo_archivo=${tipoArchivo}`);
    // El endpoint retorna una lista, tomamos el primer elemento o null si está vacía
    const archivos = response.data;
    return Array.isArray(archivos) && archivos.length > 0 ? archivos[0] : null;
  } catch (error) {
    // Si hay error 404 o similar, retornamos null (no hay archivo aún)
    if (error.response?.status === 404) {
      return null;
    }
    throw error; // Re-lanzar otros errores
  }
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

// Limpiar discrepancias de un cierre
export const limpiarDiscrepanciasCierre = async (cierreId) => {
  const response = await api.delete(`/nomina/discrepancias/limpiar/${cierreId}/`);
  return response.data;
};

// ========================================
// 📋 VISUALIZACIÓN DE DATOS CONSOLIDADOS
// ========================================

// Detalle de nómina consolidada (empleados, headers, conceptos)
export const obtenerDetalleNominaConsolidada = async (cierreId) => {
  const response = await api.get(`/nomina/cierres/${cierreId}/nomina-consolidada/detalle/`);
  console.log("🔍 [API] obtenerDetalleNominaConsolidada - Respuesta completa:", response);
  return response.data;
};

// Libro de remuneraciones (compatibilidad con vistas existentes)
export const obtenerLibroRemuneraciones = async (cierreId) => {
  const response = await api.get(`/nomina/cierres/${cierreId}/libro-remuneraciones/`);
  return response.data;
};

// Obtener movimientos del mes (ingresos, ausencias, finiquitos)
export const obtenerMovimientosMes = async (cierreId) => {
  const response = await api.get(`/nomina/cierres/${cierreId}/movimientos/`);
  console.log("🔍 [API] obtenerMovimientosMes - Respuesta completa:", response);
  return response.data;
};

// Movimientos Personal V2 (simplificado: ingresos, finiquitos, ausentismos)
export const obtenerMovimientosPersonalV2 = async (cierreId) => {
  const response = await api.get(`/nomina/cierres/${cierreId}/movimientos/v2/resumen/`);
  return response.data;
};

// Resumen de nómina consolidada (NominaConsolidada)
export const obtenerResumenNominaConsolidada = async (cierreId) => {
  const response = await api.get(`/nomina/cierres/${cierreId}/nomina-consolidada/resumen/`);
  return response.data;
};

// ================== LIBRO REMUNERACIONES V2 (simplificado) ==================
// Resumen compacto: totales por categoría + conceptos agregados
export const obtenerLibroResumenV2 = async (cierreId) => {
  const response = await api.get(`/nomina/cierres/${cierreId}/libro/v2/resumen/`);
  return response.data;
};

// ========== APROBACIÓN Y RECHAZO DE INCIDENCIAS ==========

// Aprobar incidencia (flujo de conversación) - Nueva arquitectura unificada
export const aprobarIncidencia = async (incidenciaId, comentario = '') => {
  const response = await api.post('/nomina/resoluciones-incidencias/', {
    incidencia: incidenciaId,
    tipo_resolucion: 'aprobacion',
    comentario: comentario || 'Incidencia aprobada'
  });
  return response.data;
};

// Rechazar incidencia (flujo de conversación) - Nueva arquitectura unificada
export const rechazarIncidencia = async (incidenciaId, comentario) => {
  const response = await api.post('/nomina/resoluciones-incidencias/', {
    incidencia: incidenciaId,
    tipo_resolucion: 'rechazo',
    comentario
  });
  return response.data;
};

// Crear consulta sobre incidencia (supervisor) - Nueva arquitectura unificada
export const consultarIncidencia = async (incidenciaId, comentario) => {
  const response = await api.post('/nomina/resoluciones-incidencias/', {
    incidencia: incidenciaId,
    tipo_resolucion: 'consulta',
    comentario
  });
  return response.data;
};

// ========== FUNCIONES ESPECÍFICAS PARA ARCHIVOS DEL ANALISTA ==========

// Funciones para Ingresos
export const subirIngresos = async (cierreId, formData) => {
  return await subirArchivoAnalista(cierreId, 'ingresos', formData);
};

export const obtenerEstadoIngresos = async (cierreId) => {
  try {
    return await obtenerEstadoArchivoAnalista(cierreId, 'ingresos');
  } catch (error) {
    console.error('Error obteniendo estado de ingresos:', error);
    return null;
  }
};

export const eliminarIngresos = async (archivoId) => {
  return await eliminarArchivoAnalista(archivoId);
};

// Funciones para Finiquitos
export const subirFiniquitos = async (cierreId, formData) => {
  return await subirArchivoAnalista(cierreId, 'finiquitos', formData);
};

export const obtenerEstadoFiniquitos = async (cierreId) => {
  try {
    return await obtenerEstadoArchivoAnalista(cierreId, 'finiquitos');
  } catch (error) {
    console.error('Error obteniendo estado de finiquitos:', error);
    return null;
  }
};

export const eliminarFiniquitos = async (archivoId) => {
  return await eliminarArchivoAnalista(archivoId);
};

// Funciones para Ausentismos (backend usa 'incidencias')
export const subirAusentismos = async (cierreId, formData) => {
  return await subirArchivoAnalista(cierreId, 'incidencias', formData);
};

export const obtenerEstadoAusentismos = async (cierreId) => {
  try {
    return await obtenerEstadoArchivoAnalista(cierreId, 'incidencias');
  } catch (error) {
    console.error('Error obteniendo estado de ausentismos:', error);
    return null;
  }
};

export const eliminarAusentismos = async (archivoId) => {
  return await eliminarArchivoAnalista(archivoId);
};

// Funciones para Novedades (ya existen, pero agregamos las de manejo de estado)
// NOTA: La función procesarNovedades usa un endpoint incorrecto, usar procesarFinalNovedades
// export const procesarNovedades = async (novedadesId) => {
//   const response = await api.post(`/nomina/archivos-novedades/${novedadesId}/procesar/`);
//   return response.data;
// };
