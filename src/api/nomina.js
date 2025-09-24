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

// Obtener informe completo de un cierre finalizado (solo lectura, sin cálculos)
export const obtenerInformeCierre = async (cierreId) => {
  const res = await api.get(`/nomina/cierres/${cierreId}/informe/`);
  return res.data; // { id, cierre_id, cliente, periodo, fecha_generacion, estado_cierre, datos_cierre }
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

// Solicitar recarga de archivos (reactiva la etapa de carga/clasificación)
export const solicitarRecargaArchivos = async (cierreId, motivo) => {
  const res = await api.post(`/nomina/cierres/${cierreId}/solicitar-recarga-archivos/`, {
    motivo,
  });
  return res.data;
};

// Solicitar recarga (analista) → deja el cierre en 'recarga_solicitud_pendiente'
export const solicitarRecargaArchivosAnalista = async (cierreId, motivo) => {
  const res = await api.post(`/nomina/cierres/${cierreId}/solicitar-recarga-archivos-analista/`, { motivo });
  return res.data;
};

// Aprobar recarga (supervisor) → pasa a 'requiere_recarga_archivos' y sube version_datos
export const aprobarRecargaArchivos = async (cierreId) => {
  const res = await api.post(`/nomina/cierres/${cierreId}/aprobar-recarga-archivos/`);
  return res.data;
};

// Consolidar datos de Talana (Libro + Novedades)
export const consolidarDatosTalana = async (cierreId, opciones = {}) => {
  // Permite pasar modo de consolidación u opciones futuras
  const payload = {};
  if (opciones?.modo) payload.modo = opciones.modo;
  const res = await api.post(`/nomina/cierres/${cierreId}/consolidar-datos/`, payload);
  return res.data;
};

// Consultar estado de tarea Celery
export const consultarEstadoTarea = async (cierreId, taskId) => {
  const res = await api.get(`/nomina/cierres/${cierreId}/task-status/${taskId}/`);
  return res.data;
};

// Estado de cache (informe/consolidados) para un cierre
export const obtenerEstadoCacheCierre = async (cierreId) => {
  const res = await api.get(`/nomina/cierres/${cierreId}/estado-cache/`);
  const data = res.data;
  try {
    const bloques = data?.informe_metadata?.bloques || data?.informe_metadata?.blocks || null;
    const bloquesKeys = bloques ? Object.keys(bloques) : null;
    console.log("🧠 [CACHE] Estado cache para cierre:", cierreId, {
      informe_en_cache: data?.informe_en_cache,
      consolidados_en_cache: data?.consolidados_en_cache,
      bloques_disponibles: bloquesKeys,
      stats: data?.stats,
    });
  } catch (e) {
    console.log("🧠 [CACHE] Estado cache (raw) para cierre:", cierreId, data);
  }
  return data;
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
  const data = response.data;
  // Log amigable sobre uso de caché del período anterior si viene expuesto por el backend
  const usadoCachePrev = data?.prev_period_cache_used ?? data?.diagnosticos?.prev_period_cache_used;
  if (typeof usadoCachePrev !== 'undefined') {
    console.log("🧠 [CACHE] Generación de incidencias - ¿Usó caché del período anterior?:", usadoCachePrev);
  }
  return data;
};

// Limpiar incidencias de un cierre (función de debug)
export const limpiarIncidenciasCierre = async (cierreId) => {
  const response = await api.delete(`/nomina/incidencias/limpiar/${cierreId}/`);
  return response.data;
};

// Finalizar cierre (cuando no hay incidencias o todas están resueltas)
export const finalizarCierre = async (cierreId) => {
  // Intenta rutas conocidas en orden de preferencia para máxima compatibilidad
  const rutas = [
    `/nomina/cierres/${cierreId}/finalizar/`, // oficial (detail=True)
    `/nomina/cierres/finalizar/${cierreId}/`, // compat 1
    `/nomina/incidencias/finalizar/${cierreId}/`, // compat 2 histórica
  ];

  let ultimaError;
  for (const path of rutas) {
    try {
      const response = await api.post(path);
      return response.data;
    } catch (err) {
      ultimaError = err;
      const status = err?.response?.status;
      // En 404/405 probamos siguiente ruta; en 500 también probamos por si es endpoint inválido en esa versión
      if (![404, 405, 500].includes(status)) {
        throw err;
      }
      // Continúa a siguiente ruta
    }
  }
  // Si llegamos aquí, todas fallaron
  throw ultimaError || new Error('No fue posible finalizar el cierre: todas las rutas fallaron');
};

// Utilidad: esperar una tarea Celery hasta finalizar (SUCCESS/FAILURE/REVOKED)
export const esperarTarea = async (cierreId, taskId, { intervalMs = 2000, timeoutMs = 0 } = {}) => {
  const inicio = Date.now();
  // eslint-disable-next-line no-constant-condition
  while (true) {
    const estado = await consultarEstadoTarea(cierreId, taskId);
    const status = estado?.estado || estado?.status || estado?.state;
    if (["SUCCESS", "FAILURE", "REVOKED"].includes(String(status || '').toUpperCase())) {
      return estado;
    }
    if (timeoutMs > 0 && Date.now() - inicio > timeoutMs) {
      const e = new Error(`Timeout esperando tarea ${taskId}`);
      e.partial = estado;
      throw e;
    }
    await new Promise((r) => setTimeout(r, intervalMs));
  }
};

// Utilidad: esperar a que el cierre termine de consolidar según su estado en BD
// Condición de término: estado_consolidacion === 'consolidado' OR estado === 'datos_consolidados'
export const esperarConsolidacionCierre = async (
  cierreId,
  { intervalMs = 3000, timeoutMs = 0 } = {}
) => {
  const inicio = Date.now();
  // eslint-disable-next-line no-constant-condition
  while (true) {
    try {
      const cierre = await obtenerCierreNominaPorId(cierreId);
      const estadoConsol = cierre?.estado_consolidacion;
      const estado = cierre?.estado;
      if (estadoConsol === 'consolidado' || estado === 'datos_consolidados') {
        return cierre;
      }
      // Si el backend marca explícitamente error
      if (estadoConsol === 'error_consolidacion') {
        const e = new Error('Consolidación fallida (estado_consolidacion=error_consolidacion)');
        e.cierre = cierre;
        throw e;
      }
    } catch (err) {
      // Si falla la lectura del cierre, reintentar salvo que se supere el timeout
      if (timeoutMs > 0 && Date.now() - inicio > timeoutMs) throw err;
    }
    if (timeoutMs > 0 && Date.now() - inicio > timeoutMs) {
      const e = new Error('Timeout esperando consolidación del cierre');
      throw e;
    }
    await new Promise((r) => setTimeout(r, intervalMs));
  }
};

// Azúcar: finalizar cierre y esperar a que complete si retorna task_id
export const finalizarCierreYEsperar = async (cierreId, { intervalMs = 2000, timeoutMs = 0 } = {}) => {
  const res = await finalizarCierre(cierreId);
  const taskId = res?.task_id || res?.taskId || res?.celery_task_id;
  if (!taskId) return res; // si el backend finaliza sin background, devolver respuesta directa
  const estadoFinal = await esperarTarea(cierreId, taskId, { intervalMs, timeoutMs });
  return { inicio: res, fin: estadoFinal };
};

// Azúcar: consolidar datos y esperar a que finalice
export const consolidarDatosTalanaYEsperar = async (cierreId, opciones = {}, { intervalMs = 2000, timeoutMs = 0 } = {}) => {
  const res = await consolidarDatosTalana(cierreId, opciones);
  const taskId = res?.task_id || res?.taskId || res?.celery_task_id;
  const chainId = res?.chain_id || res?.chainId;

  // 1) Si hay taskId, podemos consultar estado de la tarea orquestadora
  //    PERO este "SUCCESS" puede ocurrir al inicio (cuando lanza la chain).
  //    Por robustez, siempre complementamos esperando el estado del cierre.
  if (taskId) {
    try {
      await esperarTarea(cierreId, taskId, { intervalMs, timeoutMs });
    } catch (e) {
      // Si la tarea falla temprano, igual continuamos a verificar estado del cierre para mostrar info real
    }
  }

  // 2) Si el backend expone un chainId, no necesariamente refleja el último eslabón.
  //    La fuente de verdad será el estado del cierre en BD.
  const cierreFinal = await esperarConsolidacionCierre(cierreId, {
    intervalMs: Math.max(2000, intervalMs),
    timeoutMs,
  });

  return { inicio: res, cierre: cierreFinal };
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
  // Permitir enviar como FormData (para adjuntos) o como JSON simple
  if (typeof FormData !== 'undefined' && resolucionData instanceof FormData) {
    // Asegurar que incluya la incidencia
    if (!resolucionData.has('incidencia')) {
      resolucionData.append('incidencia', incidenciaId);
    }
    const response = await api.post('/nomina/resoluciones-incidencias/', resolucionData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  }
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

// ========== RECONCILIACIÓN (recargas Talana) ==========

// KPIs de reconciliación por cierre (vigentes_actualizadas, supervisor_pendiente, unificadas, etc.)
export const obtenerResumenReconciliacion = async (cierreId) => {
  const response = await api.get(`/nomina/cierres/${cierreId}/resumen-reconciliacion/`);
  return response.data;
};

// Aprobar todas las incidencias resueltas por analista (acción masiva)
export const marcarTodasComoJustificadas = async (cierreId, comentario = 'Aprobación masiva por supervisor') => {
  const response = await api.post(`/nomina/cierres/${cierreId}/marcar-todas-como-justificadas/`, {
    comentario,
  });
  return response.data;
};

// Confirmar desaparición individual (incidencia marcada como 'resolucion_supervisor_pendiente')
export const confirmarDesaparicionIncidencia = async (incidenciaId, comentario = '') => {
  const response = await api.post(`/nomina/incidencias/${incidenciaId}/confirmar-desaparicion/`, {
    comentario,
  });
  return response.data;
};

// Confirmar todas las desapariciones de un cierre
export const confirmarDesaparicionesCierre = async (cierreId, comentario = '') => {
  const response = await api.post(`/nomina/incidencias/confirmar-desapariciones/${cierreId}/`, {
    comentario,
  });
  return response.data;
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

// Movimientos Personal V3 (detalle completo con normalización)
export const obtenerMovimientosPersonalV3 = async (cierreId) => {
  const response = await api.get(`/nomina/cierres/${cierreId}/movimientos/v3/detalle/`);
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
export const generarIncidenciasTotalesVariacion = async (cierreId) => {
  // Preferimos GET (actual backend), con fallback a POST por compatibilidad histórica
  try {
    const respGet = await api.get(`/nomina/cierres/${cierreId}/incidencias/totales-variacion/`);
    return respGet.data;
  } catch (errGet) {
    // Si GET no está permitido en alguna versión antigua, probamos POST
    if (errGet?.response?.status === 405 || errGet?.response?.status === 404) {
      console.warn('[API] GET no permitido/encontrado, intentando POST (modo compat) ...');
      const respPost = await api.post(`/nomina/cierres/${cierreId}/incidencias/totales-variacion/`);
      return respPost.data;
    }
    throw errGet;
  }
};
