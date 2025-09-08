// src/api/contabilidad.js
import api from "./config";

// ==================== RESUMEN CONTABLE ====================
export const obtenerResumenContable = async (clienteId) => {
  const response = await api.get(
    `/contabilidad/clientes/${clienteId}/resumen/`,
  );
  return response.data;
};

// ==================== PLANTILLAS ====================
export const descargarPlantillaTipoDocumento = () => {
  return `${api.defaults.baseURL}/contabilidad/plantilla-tipo-doc/`;
};

export const descargarPlantillaNombresEnIngles = () => {
  return `${api.defaults.baseURL}/contabilidad/plantilla-nombres-en-ingles/`;
};

// Nueva: descarga Excel con cuentas sin nombre en inglés para un cliente
export const descargarCuentasSinNombreIngles = (clienteId) => {
  return `${api.defaults.baseURL}/contabilidad/nombre-ingles/${clienteId}/exportar-sin-nombre/`;
};

// Descarga autenticada (XHR) del Excel de cuentas sin nombre en inglés y dispara descarga en el navegador
export const descargarCuentasSinNombreInglesFile = async (clienteId, nombreArchivo = null) => {
  const url = `/contabilidad/nombre-ingles/${clienteId}/exportar-sin-nombre/`;
  const res = await api.get(url, { responseType: 'blob' });
  const blob = res.data;
  const contentDisposition = res.headers['content-disposition'];
  let filename = nombreArchivo || 'cuentas_sin_nombre_ingles.xlsx';
  if (!nombreArchivo && contentDisposition) {
    const match = contentDisposition.match(/filename="?([^";]+)"?/i);
    if (match) filename = match[1];
  }
  const blobUrl = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = blobUrl;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(blobUrl);
  return { filename };
};

export const descargarPlantillaClasificacionBulk = () => {
  return `${api.defaults.baseURL}/contabilidad/plantilla-clasificacion-bulk/`;
};

// ==================== TIPO DE DOCUMENTO ====================
export const obtenerEstadoTipoDocumento = async (clienteId) => {
  const res = await api.get(
    `/contabilidad/tipo-documento/${clienteId}/estado/`,
  );
  return typeof res.data === "string" ? res.data : res.data.estado;
};

export const subirTipoDocumento = async (formData) => {
  const res = await api.post(
    "/contabilidad/tipo-documento/subir-archivo/",
    formData,
  );
  return res.data;
};

export const obtenerTiposDocumentoCliente = async (clienteId) => {
  const res = await api.get(`/contabilidad/tipo-documento/${clienteId}/list/`);
  return res.data;
};

export const registrarVistaTiposDocumento = async (clienteId, cierreId = null) => {
  const params = cierreId ? `?cierre_id=${cierreId}` : '';
  const res = await api.post(
    `/contabilidad/tipo-documento/${clienteId}/registrar-vista/${params}`,
  );
  return res.data;
};

// ==================== LOGGING DE ACTIVIDADES CRUD ====================
export const registrarActividadTarjeta = async (
  clienteId, 
  tarjeta, 
  accion, 
  descripcion, 
  detalles = null,
  cierreId = null
) => {
  const data = {
    cliente_id: clienteId,
    tarjeta: tarjeta,
    accion: accion,
    descripcion: descripcion,
    detalles: detalles || {},
  };
  
  if (cierreId) {
    data.cierre_id = cierreId;
  }
  
  const res = await api.post("/contabilidad/registrar-actividad/", data);
  return res.data;
};

export const registrarVistaClasificaciones = async (
  clienteId,
  uploadId = null,
  cierreId = null,
) => {
  const params = cierreId ? `?cierre_id=${cierreId}` : '';
  const res = await api.post(
    `/contabilidad/clasificacion/${clienteId}/registrar-vista/${params}`,
    {
      upload_log_id: uploadId,
    },
  );
  return res.data;
};

export const registrarVistaSetsClasificacion = async (clienteId) => {
  const res = await api.post(
    `/contabilidad/clasificacion/${clienteId}/registrar-vista-sets/`,
  );
  return res.data;
};

export const eliminarTodosTiposDocumento = async (clienteId) => {
  const res = await api.post(
    `/contabilidad/tipo-documento/${clienteId}/eliminar-todos/`,
  );
  return res.data;
};

export const crearTipoDocumento = async (clienteId, tipoDocumento) => {
  const res = await api.post("/contabilidad/tipos-documento/", {
    cliente: clienteId,
    ...tipoDocumento,
  });
  return res.data;
};

export const actualizarTipoDocumento = async (id, tipoDocumento) => {
  const res = await api.patch(
    `/contabilidad/tipos-documento/${id}/`,
    tipoDocumento,
  );
  return res.data;
};

export const eliminarTipoDocumento = async (id) => {
  const res = await api.delete(`/contabilidad/tipos-documento/${id}/`);
  return res.data;
};

// ==================== LIBRO MAYOR ====================
export const subirLibroMayor = async (clienteId, archivo, cierreId = null) => {
  const formData = new FormData();
  formData.append("cliente_id", clienteId);
  formData.append("archivo", archivo);
  if (cierreId) formData.append("cierre_id", cierreId);

  const res = await api.post(
    "/contabilidad/libro-mayor/subir-archivo/",
    formData,
  );
  return res.data;
};

export const obtenerLibrosMayor = async (cierreId) => {
  const res = await api.get("/contabilidad/libromayor-archivo/", {
    params: { cierre: cierreId },
  });
  return res.data;
};

export const obtenerMovimientosIncompletos = async (cierreId) => {
  const res = await api.get(
    `/contabilidad/libro-mayor/incompletos/${cierreId}/`
  );
  return res.data;
};

export const eliminarLibroMayor = async (libroId) => {
  // Ajuste: endpoint correcto del ViewSet es libromayor-archivo
  const res = await api.delete(`/contabilidad/libromayor-archivo/${libroId}/`);
  return res.data;
};

export const reprocesarConExcepciones = async (cierreId) => {
  const res = await api.post('/contabilidad/libro-mayor/reprocesar-con-excepciones/', {
    cierre_id: cierreId
  });
  return res.data;
};

export const obtenerHistorialReprocesamiento = async (cierreId) => {
  const res = await api.get(`/contabilidad/libro-mayor/${cierreId}/historial-reprocesamiento/`);
  return res.data;
};

export const cambiarIteracionPrincipal = async (cierreId, iteracion) => {
  const res = await api.post('/contabilidad/libro-mayor/cambiar-iteracion-principal/', {
    cierre_id: cierreId,
    iteracion: iteracion
  });
  return res.data;
};

// ==================== CUENTAS ====================
export const obtenerCuentasCliente = async (clienteId) => {
  const res = await api.get(`/contabilidad/cuentas/`, {
    params: { cliente: clienteId },
  });
  return res.data;
};

// ==================== CIERRES ====================
export const obtenerCierresCliente = async (clienteId) => {
  const res = await api.get(`/contabilidad/cierres/`, {
    params: { cliente: clienteId },
  });
  return res.data;
};

export const obtenerCierrePorId = async (cierreId) => {
  const res = await api.get(`/contabilidad/cierres/${cierreId}/`);
  return res.data;
};

export const obtenerCierreMensual = async (clienteId, periodo) => {
  const res = await api.get(`/contabilidad/cierres/`, {
    params: { cliente: clienteId, periodo },
  });
  return res.data.length > 0 ? res.data[0] : null;
};

export const crearCierreMensual = async (clienteId, periodo) => {
  const res = await api.post(`/contabilidad/cierres/`, {
    cliente: Number(clienteId),
    periodo,
    estado: "pendiente",
  });
  return res.data;
};

export const obtenerProgresoClasificacionTodosLosSets = async (cierreId) => {
  const res = await api.get(
    `/contabilidad/clasificacion/${cierreId}/progreso_todos_los_sets/`,
  );
  return res.data;
};

export const obtenerProgresoClasificacionPorSet = async (cierreId, setId) => {
  const res = await api.get(
    `/contabilidad/clasificacion/${cierreId}/progreso/`,
    {
      params: { set_id: setId },
    },
  );
  return res.data;
};

export const obtenerCuentasPendientes = async (cierreId) => {
  const res = await api.get(
    `/contabilidad/clasificacion/${cierreId}/cuentas_pendientes/`,
  );
  return res.data;
};

// ==================== FINALIZACIÓN DE CIERRES ====================
export const finalizarCierre = async (cierreId) => {
  const res = await api.post(`/contabilidad/cierres/${cierreId}/finalizar/`);
  return res.data;
};

export const actualizarEstadoCierre = async (cierreId) => {
  const res = await api.post(`/contabilidad/cierres/${cierreId}/actualizar-estado/`);
  return res.data;
};

export const obtenerEstadoFinalizacion = async (cierreId) => {
  const res = await api.get(`/contabilidad/cierres/${cierreId}/estado-finalizacion/`);
  return res.data;
};

export const obtenerProgresoTarea = async (taskId) => {
  const res = await api.get(`/contabilidad/tareas/${taskId}/progreso/`);
  return res.data;
};

// ==================== CLASIFICACIONES - SETS ====================
export const obtenerSetsClasificacion = async (clienteId) => {
  const res = await api.get(`/contabilidad/clasificaciones-set/`, {
    params: { cliente: clienteId },
  });
  return res.data;
};

export const crearSetClasificacion = async (clienteId, data) => {
  const res = await api.post(`/contabilidad/clasificaciones-set/`, {
    cliente: clienteId,
    ...data,
  });
  return res.data;
};

export const eliminarSetClasificacion = async (setClasId) => {
  const res = await api.delete(
    `/contabilidad/clasificaciones-set/${setClasId}/`,
  );
  return res.data;
};

// ==================== CLASIFICACIONES - OPCIONES ====================
export const obtenerOpcionesClasificacion = async (setClasId) => {
  const res = await api.get(`/contabilidad/clasificaciones-opcion/`, {
    params: { set_clas: setClasId },
  });
  return res.data;
};

export const crearOpcionClasificacion = async (setClasId, data) => {
  const res = await api.post(`/contabilidad/clasificaciones-opcion/`, {
    set_clas: setClasId,
    ...data,
  });
  return res.data;
};

export const eliminarOpcionClasificacion = async (opcionClasId) => {
  const res = await api.delete(
    `/contabilidad/clasificaciones-opcion/${opcionClasId}/`,
  );
  return res.data;
};

// ==================== CLASIFICACIONES - UTILIDADES ====================
export const obtenerClasificacionCompleta = async (clienteId) => {
  const sets = await obtenerSetsClasificacion(clienteId);
  const completa = [];
  for (const set of sets) {
    const opciones = await obtenerOpcionesClasificacion(set.id);
    completa.push({ ...set, opciones });
  }
  return completa;
};

export const obtenerCuentasPendientesPorSet = async (clienteId, setId) => {
  const res = await api.get(
    `/contabilidad/clientes/${clienteId}/sets/${setId}/cuentas_pendientes/`,
  );
  return res.data;
};

// ==================== CLASIFICACIONES - CUENTAS INDIVIDUALES ====================
export const clasificarCuenta = async (cuentaId, setClasId, opcionId) => {
  const res = await api.post(`/contabilidad/clasificaciones/`, {
    cuenta: cuentaId,
    set_clas: setClasId,
    opcion: opcionId,
  });
  return res.data;
};

// Función alternativa para clasificar cuenta usando endpoint específico
export const clasificarCuentaEspecifico = async (
  cuentaId,
  setClasId,
  opcionId,
) => {
  const res = await api.post(`/contabilidad/clasificacion/clasificar/`, {
    cuenta_id: cuentaId,
    set_clas_id: setClasId,
    opcion_id: opcionId,
  });
  return res.data;
};

export const obtenerClasificacionesCuenta = async (clienteId) => {
  const res = await api.get(`/contabilidad/clasificaciones/`, {
    params: { cuenta__cliente: clienteId },
  });
  return res.data;
};

export const crearClasificacionCuenta = async (data) => {
  const res = await api.post(`/contabilidad/clasificaciones/`, data);
  return res.data;
};

export const actualizarClasificacionCuenta = async (id, data) => {
  const res = await api.patch(`/contabilidad/clasificaciones/${id}/`, data);
  return res.data;
};

export const eliminarClasificacionCuenta = async (id) => {
  const res = await api.delete(`/contabilidad/clasificaciones/${id}/`);
  return res.data;
};

export const eliminarTodasClasificacionesCuenta = async (clienteId) => {
  const clasificaciones = await obtenerClasificacionesCuenta(clienteId);
  const promesas = clasificaciones.map((clasificacion) =>
    eliminarClasificacionCuenta(clasificacion.id),
  );
  await Promise.all(promesas);
  return { mensaje: `${clasificaciones.length} clasificaciones eliminadas` };
};
// ==================== MOVIMIENTOS ====================
export const obtenerMovimientosResumen = async (
  cierreId,
  {
    setId = undefined,
    opcionId = undefined,
    page = undefined,
    page_size = undefined,
    search = undefined,
    cuenta = undefined,
    auxiliar = undefined,
    centro_costo = undefined,
    fecha_desde = undefined,
    fecha_hasta = undefined,
  } = {},
) => {
  const params = {};
  
  // Solo agregar parámetros que realmente tienen valor
  if (setId !== undefined) params.set_id = setId;
  if (opcionId !== undefined) params.opcion_id = opcionId;
  if (page !== undefined) params.page = page;
  if (page_size !== undefined) params.page_size = page_size;
  if (search !== undefined) params.search = search;
  if (cuenta !== undefined) params.cuenta = cuenta;
  if (auxiliar !== undefined) params.auxiliar = auxiliar;
  if (centro_costo !== undefined) params.centro_costo = centro_costo;
  if (fecha_desde !== undefined) params.fecha_desde = fecha_desde;
  if (fecha_hasta !== undefined) params.fecha_hasta = fecha_hasta;

  const res = await api.get(
    `/contabilidad/cierres/${cierreId}/movimientos-resumen/`,
    { params },
  );
  // Devolver siempre el array de movimientos, ya sea con paginación o sin ella
  if (Array.isArray(res.data)) {
    return res.data;
  } else if (res.data.results && Array.isArray(res.data.results)) {
    return res.data.results;
  }
  // Fallback a la data original
  return res.data;
};

export const obtenerMovimientosCuenta = async (cierreId, cuentaId, params = {}) => {
  const res = await api.get(
    `/contabilidad/cierres/${cierreId}/cuentas/${cuentaId}/movimientos/`,
    { params }
  );
  return res.data;
};

// ==================== NOMBRES EN INGLÉS ====================
export const obtenerEstadoNombresIngles = async (clienteId) => {
  const res = await api.get(`/contabilidad/nombre-ingles/${clienteId}/estado/`);
  // Devolver siempre el objeto completo para que el caller evalúe ready/estado/total
  return res.data;
};

export const obtenerNombresEnIngles = async (clienteId) => {
  const res = await api.get(`/contabilidad/nombre-ingles/${clienteId}/list/`);
  return res.data;
};

export const subirNombresIngles = async (formData) => {
  const res = await api.post(
    "/contabilidad/nombre-ingles/subir-archivo/",
    formData,
  );
  return res.data;
};

export const eliminarNombresEnIngles = async (clienteId) => {
  const res = await api.post(
    `/contabilidad/nombre-ingles/${clienteId}/eliminar-todos/`,
  );
  return res.data;
};

// ==================== NOMBRES EN INGLÉS CRUD ====================
export const obtenerNombresInglesCliente = async (clienteId, registrarActividad = false) => {
  const params = registrarActividad ? '?registrar_actividad=true' : '';
  const res = await api.get(
    `/contabilidad/nombre-ingles/${clienteId}/list/${params}`,
  );
  // El backend devuelve { cliente, total, nombres }, necesitamos solo el array nombres
  return res.data.nombres || [];
};

export const registrarVistaNombresIngles = async (clienteId, cierreId = null) => {
  const params = cierreId ? `?cierre_id=${cierreId}` : '';
  const res = await api.post(
    `/contabilidad/nombre-ingles/${clienteId}/registrar-vista/${params}`,
  );
  return res.data;
};

export const crearNombreIngles = async (data) => {
  const res = await api.post("/contabilidad/nombres-ingles/", data);
  return res.data;
};

export const actualizarNombreIngles = async (id, data) => {
  const res = await api.patch(`/contabilidad/nombres-ingles/${id}/`, data);
  return res.data;
};

export const eliminarNombreIngles = async (id) => {
  const res = await api.delete(`/contabilidad/nombres-ingles/${id}/`);
  return res.data;
};

export const eliminarTodosNombresIngles = async (clienteId) => {
  const res = await api.post(
    `/contabilidad/nombre-ingles/${clienteId}/eliminar-todos/`,
  );
  return res.data;
};

// ==================== CLASIFICACIONES PERSISTENTES (BASE DE DATOS) ====================
// Estas funciones trabajan directamente con la base de datos persistente
// a diferencia de las funciones de archivo temporal que dependen del uploadId

export const obtenerClasificacionesPersistentes = async (clienteId) => {
  console.log('🌐 API: obtenerClasificacionesPersistentes con clienteId:', clienteId);
  const res = await api.get("/contabilidad/clasificaciones/", {
    params: { cuenta__cliente: clienteId },
  });
  console.log('✅ API: obtenerClasificacionesPersistentes respuesta:', res.data.length, 'registros');
  
  // Debug: Log de la primera clasificación para verificar estructura
  if (res.data.length > 0) {
    console.log('🔍 Primera clasificación persistente:', res.data[0]);
  }
  
  return res.data;
};

export const obtenerClasificacionesPersistentesDetalladas = async (clienteId) => {
  const res = await api.get(`/contabilidad/clientes/${clienteId}/clasificaciones/detalladas/`);
  return res.data;
};

export const registrarVistaClasificacionesPersistentes = async (clienteId, cierreId = null) => {
  const params = cierreId ? `?cierre_id=${cierreId}` : '';
  const res = await api.post(
    `/contabilidad/clientes/${clienteId}/clasificaciones/registrar-vista/${params}`
  );
  return res.data;
};

export const actualizarClasificacionPersistente = async (cuentaCodigo, data) => {
  const clienteId = data.cliente || data.cliente_id;
  const res = await api.patch(`/contabilidad/clasificaciones/registro-completo/${cuentaCodigo}/?cliente=${clienteId}`, data);
  return res.data;
};

export const eliminarClasificacionPersistente = async (cuentaCodigo, clienteId) => {
  const res = await api.delete(`/contabilidad/clasificaciones/registro-completo/${cuentaCodigo}/delete/?cliente=${clienteId}`);
  return res.data;
};

export const crearClasificacionPersistente = async (data) => {
  const res = await api.post("/contabilidad/clasificaciones/registro-completo/", data);
  return res.data;
};

export const obtenerEstadisticasClasificacionesPersistentes = async (clienteId) => {
  const res = await api.get(`/contabilidad/clientes/${clienteId}/clasificaciones/estadisticas/`);
  return res.data;
};

// ==================== BULK CLASIFICACIONES ====================
export const obtenerEstadoClasificaciones = async (clienteId) => {
  const res = await api.get(
    `/contabilidad/clasificacion/${clienteId}/estado/`,
  );
  return res.data;
};

export const subirClasificacionBulk = async (formData) => {
  const res = await api.post(
    "/contabilidad/clasificacion-bulk/subir-archivo/",
    formData,
  );
  return res.data;
};

export const obtenerBulkClasificaciones = async (clienteId) => {
  const res = await api.get(`/contabilidad/clientes/${clienteId}/uploads/`, {
    params: { tipo: "clasificacion" },
  });
  return res.data.uploads;
};

export const eliminarBulkClasificacion = async (uploadId) => {
  const res = await api.delete(`/contabilidad/clasificacion-bulk/${uploadId}/`);
  return res.data;
};

export const eliminarTodosBulkClasificacion = async (clienteId) => {
  const res = await api.post(
    "/contabilidad/clasificacion-bulk/eliminar-todos/",
    {
      cliente_id: clienteId,
    },
  );
  return res.data;
};

export const reprocesarBulkClasificacionUpload = async (uploadId) => {
  const res = await api.post(
    `/contabilidad/clasificacion-bulk/${uploadId}/reprocesar/`,
  );
  return res.data;
};

// ==================== CLASIFICACIÓN ARCHIVO (RAW DATA) - OBSOLETO ====================
// REDISEÑADO: Estas funciones son obsoletas porque ClasificacionCuentaArchivo fue eliminado
// Usar las funciones de AccountClassification (clasificaciones persistentes) en su lugar

/**
 * @deprecated Usar obtenerClasificacionesPersistentesDetalladas en su lugar
 */
export const obtenerClasificacionesArchivo = async (uploadId) => {
  console.warn('⚠️ obtenerClasificacionesArchivo es obsoleta. Usar obtenerClasificacionesPersistentesDetalladas');
  // Redirigir a la nueva función que trabaja con AccountClassification
  const res = await api.get("/contabilidad/clasificaciones/", {
    params: { upload_log: uploadId },
  });
  return res.data;
};

/**
 * @deprecated Usar crearClasificacionPersistente en su lugar
 */
export const crearClasificacionArchivo = async (data) => {
  console.warn('⚠️ crearClasificacionArchivo es obsoleta. Usar crearClasificacionPersistente');
  // Redirigir a AccountClassification
  const res = await api.post("/contabilidad/clasificaciones/", data);
  return res.data;
};

/**
 * @deprecated Usar actualizarClasificacionPersistente en su lugar
 */
export const actualizarClasificacionArchivo = async (id, data) => {
  console.warn('⚠️ actualizarClasificacionArchivo es obsoleta. Usar actualizarClasificacionPersistente');
  const res = await api.patch(`/contabilidad/clasificaciones/${id}/`, data);
  return res.data;
};

/**
 * @deprecated Usar eliminarClasificacionPersistente en su lugar
 */
export const eliminarClasificacionArchivo = async (id) => {
  console.warn('⚠️ eliminarClasificacionArchivo es obsoleta. Usar eliminarClasificacionPersistente');
  const res = await api.delete(`/contabilidad/clasificaciones/${id}/`);
  return res.data;
};

/**
 * @deprecated Esta función usaba el modelo obsoleto ClasificacionCuentaArchivo
 */
export const clasificacionBulkArchivo = async (registroIds, setNombre, valorClasificacion) => {
  console.warn('⚠️ clasificacionBulkArchivo es obsoleta. El bulk se maneja automáticamente en el procesamiento');
  throw new Error('Función obsoleta: clasificacionBulkArchivo ya no es necesaria con el nuevo flujo');
};

/**
 * @deprecated Esta función es obsoleta, el mapeo se hace automáticamente
 */
export const procesarMapeoClasificaciones = async (uploadId) => {
  console.warn('⚠️ procesarMapeoClasificaciones es obsoleta. El mapeo es automático');
  // En el nuevo flujo, esto se hace automáticamente cuando se sube el libro mayor
  return { mensaje: 'El mapeo se hace automáticamente cuando se sube el libro mayor' };
};

/**
 * @deprecated Usar obtenerClasificacionesPersistentes en su lugar
 */
export const obtenerClasificacionesArchivoCliente = async (
  clienteId,
  procesado = null,
) => {
  console.warn('⚠️ obtenerClasificacionesArchivoCliente es obsoleta. Usar obtenerClasificacionesPersistentes');
  return obtenerClasificacionesPersistentes(clienteId);
};

/**
 * @deprecated Usar obtenerEstadisticasClasificacionesPersistentes en su lugar
 */
export const obtenerEstadisticasClasificacionArchivo = async (uploadId) => {
  console.warn('⚠️ obtenerEstadisticasClasificacionArchivo es obsoleta. Usar obtenerEstadisticasClasificacionesPersistentes');
  // Redirigir a estadísticas persistentes
  // Nota: uploadId debe convertirse a clienteId para la nueva función
  throw new Error('Esta función requiere adaptación: debe proporcionar clienteId en lugar de uploadId');
};

// ==================== NUEVAS FUNCIONES PARA REDISEÑO ====================

/**
 * Obtiene clasificaciones por upload_log (tanto temporales como con FK)
 * Reemplaza la funcionalidad de obtenerClasificacionesArchivo
 */
export const obtenerClasificacionesPorUpload = async (uploadId) => {
  console.log('🌐 API: obtenerClasificacionesPorUpload con uploadId:', uploadId);
  const res = await api.get("/contabilidad/clasificaciones/", {
    params: { upload_log: uploadId },
  });
  console.log('✅ API: obtenerClasificacionesPorUpload respuesta:', res.data.length, 'registros');
  return res.data;
};

/**
 * Obtiene clasificaciones temporales (sin FK a cuenta) para un cliente
 */
export const obtenerClasificacionesTemporales = async (clienteId) => {
  console.log('🌐 API: obtenerClasificacionesTemporales con clienteId:', clienteId);
  const res = await api.get("/contabilidad/clasificaciones/", {
    params: { 
      cliente: clienteId,
      cuenta__isnull: true  // Solo temporales
    },
  });
  console.log('✅ API: obtenerClasificacionesTemporales respuesta:', res.data.length, 'registros');
  return res.data;
};

/**
 * Migra clasificaciones temporales a FK después de subir libro mayor
 */
export const migrarClasificacionesTemporalesAFK = async (uploadLogId, cierreId = null) => {
  const data = { upload_log_id: uploadLogId };
  if (cierreId) {
    data.cierre_id = cierreId;
  }
  const res = await api.post("/contabilidad/clasificaciones/migrar-temporales-fk/", data);
  return res.data;
};

// ==================== NOMBRES EN INGLÉS UPLOADS ====================
export const obtenerNombresInglesUploads = async (clienteId) => {
  const res = await api.get("/contabilidad/nombres-ingles-upload/", {
    params: { cliente: clienteId },
  });
  return res.data;
};

export const subirNombresInglesUpload = async (
  clienteId,
  cierreId,
  archivo,
) => {
  const formData = new FormData();
  formData.append("cliente_id", clienteId);
  if (cierreId) {
    formData.append("cierre", cierreId);
  }
  formData.append("archivo", archivo);

  const res = await api.post("/contabilidad/nombres-ingles-upload/", formData);
  return res.data;
};

export const eliminarNombresInglesUpload = async (uploadId) => {
  const res = await api.delete(
    `/contabilidad/nombres-ingles-upload/${uploadId}/`,
  );
  return res.data;
};

export const eliminarTodosNombresInglesUpload = async (
  clienteId,
  cierreId = null,
) => {
  const data = { cliente_id: clienteId };
  if (cierreId) {
    data.cierre_id = cierreId;
  }

  const res = await api.post(
    "/contabilidad/nombres-ingles-upload/eliminar-todos/",
    data,
  );
  return res.data;
};

export const reprocesarNombresInglesUpload = async (uploadId) => {
  const res = await api.post(
    `/contabilidad/nombres-ingles-upload/${uploadId}/reprocesar/`,
  );
  return res.data;
};

// ==================== LOGS Y ACTIVIDAD ====================
export const obtenerLogsUpload = async (
  tipoUpload,
  uploadId = null,
  clienteId = null,
) => {
  const params = { tipo_upload: tipoUpload };
  if (uploadId) params.upload_id = uploadId;
  if (clienteId) params.cliente_id = clienteId;

  const res = await api.get("/contabilidad/activity-logs/", { params });
  return res.data;
};

// ==================== FUNCIONES PARA SETS DE CLASIFICACIÓN ====================
export const obtenerSetsCliente = async (clienteId) => {
  const res = await api.get("/contabilidad/clasificaciones-set/", {
    params: { cliente: clienteId },
  });
  return res.data;
};

export const crearSet = async (clienteId, nombre) => {
  const res = await api.post("/contabilidad/clasificaciones-set/", {
    cliente: clienteId,
    nombre: nombre,
  });
  return res.data;
};

export const actualizarSet = async (setId, nombre) => {
  const res = await api.put(`/contabilidad/clasificaciones-set/${setId}/`, {
    nombre: nombre,
  });
  return res.data;
};

export const eliminarSet = async (setId) => {
  const res = await api.delete(`/contabilidad/clasificaciones-set/${setId}/`);
  return res.data;
};

// ==================== FUNCIONES PARA OPCIONES DE CLASIFICACIÓN ====================
export const obtenerOpcionesSet = async (setId) => {
  const res = await api.get("/contabilidad/clasificaciones-opcion/", {
    params: { set_clas: setId },
  });
  return res.data;
};

export const crearOpcion = async (setId, datos) => {
  // datos puede ser: { valor: "...", valor_en: "...", descripcion: "...", descripcion_en: "..." }
  const datosCompletos = {
    set_clas: setId,
    ...datos,
  };
  
  console.log('📤 API crearOpcion - Enviando al backend:', {
    setId,
    datosOriginales: datos,
    datosCompletos,
    esBilingue: !!(datos.valor && datos.valor_en),
    camposEnviados: Object.keys(datosCompletos)
  });
  
  const res = await api.post("/contabilidad/clasificaciones-opcion/", datosCompletos);
  
  console.log('📥 API crearOpcion - Respuesta del backend:', {
    status: res.status,
    data: res.data,
    tieneValorEn: !!res.data.valor_en,
    datosCompletos: JSON.stringify(res.data, null, 2)
  });
  
  return res.data;
};

export const actualizarOpcion = async (opcionId, datos, setClasId = null) => {
  // datos puede ser: { valor: "...", valor_en: "...", descripcion: "...", descripcion_en: "..." }
  const dataToSend = { ...datos };
  
  // Si se proporciona setClasId, incluirlo (requerido para PATCH en algunos casos)
  if (setClasId) {
    dataToSend.set_clas = setClasId;
  }
  
  // Usar PATCH en lugar de PUT para enviar solo los campos que cambian
  const res = await api.patch(
    `/contabilidad/clasificaciones-opcion/${opcionId}/`,
    dataToSend,
  );
  return res.data;
};

export const eliminarOpcion = async (opcionId) => {
  const res = await api.delete(
    `/contabilidad/clasificaciones-opcion/${opcionId}/`,
  );
  return res.data;
};

// ==================== UPLOAD LOG ====================
export const obtenerEstadoUploadLog = async (uploadLogId) => {
  const res = await api.get(`/contabilidad/upload-log/${uploadLogId}/estado/`);
  return res.data;
};

export const obtenerHistorialUploads = async (
  clienteId,
  tipo = null,
  limit = 20,
) => {
  const params = { limit };
  if (tipo) params.tipo = tipo;

  const res = await api.get(`/contabilidad/clientes/${clienteId}/uploads/`, {
    params,
  });
  return res.data;
};

export const obtenerIncidenciasConsolidadas = async (cierreId) => {
  const res = await api.get(`/contabilidad/libro-mayor/${cierreId}/incidencias-consolidadas/`);
  return res.data;
};

export const obtenerIncidenciasConsolidadasOptimizado = async (cierreId, forzarActualizacion = false) => {
  const params = {};
  if (forzarActualizacion) {
    params.forzar_actualizacion = 'true';
    params.usar_cache = 'false'; // También desactivar caché
  }
  
  const res = await api.get(`/contabilidad/libro-mayor/${cierreId}/incidencias-optimizado/`, {
    params
  });
  return res.data;
};

export const obtenerHistorialIncidencias = async (cierreId) => {
  const res = await api.get(`/contabilidad/libro-mayor/${cierreId}/historial-incidencias/`);
  return res.data;
};

export const obtenerCuentasDetalleIncidencia = async (cierreId, tipoIncidencia) => {
  const res = await api.get(`/contabilidad/libro-mayor/${cierreId}/incidencias/${tipoIncidencia}/detalle/`);
  return res.data;
};

export const marcarCuentaNoAplica = async (cierreId, codigoCuenta, tipoExcepcion, motivo = '', setId = null) => {
  const payload = {
    cierre_id: cierreId,
    codigo_cuenta: codigoCuenta,
    tipo_excepcion: tipoExcepcion,
    motivo: motivo
  };
  
  const esClasificacion = tipoExcepcion === 'CUENTA_NO_CLAS' || tipoExcepcion === 'CUENTA_NO_CLASIFICADA';
  if (esClasificacion) {
    if (setId === null || setId === undefined || setId === '') {
      throw new Error('set_clasificacion_id es requerido para excepciones de clasificación');
    }
    // Normalizar a número si es string numérico
    const normalizado = isNaN(Number(setId)) ? setId : Number(setId);
    payload.set_clasificacion_id = normalizado;
  } else if (setId) {
    // Para otros tipos, solo enviar si existe
    payload.set_clasificacion_id = setId;
  }
  
  const res = await api.post('/contabilidad/libro-mayor/marcar-no-aplica/', payload);
  return res.data;
};

export const eliminarExcepcionNoAplica = async (cierreId, codigoCuenta, tipoExcepcion, setId = null) => {
  try {
    // Para clasificaciones (CUENTA_NO_CLAS, CUENTA_NO_CLASIFICADA) usar el endpoint específico
    if ((tipoExcepcion === 'CUENTA_NO_CLAS' || tipoExcepcion === 'CUENTA_NO_CLASIFICADA') && setId) {
      const res = await api.delete('/contabilidad/libro-mayor/excepciones/clasificacion/eliminar/', {
        data: {
          cierre_id: cierreId,
          codigo_cuenta: codigoCuenta,
          set_clasificacion_id: setId
        }
      });
      return res.data;
    }
    
    // Para otros tipos de excepciones (DOC_NULL, etc.), usar el método original
    const res = await api.get(`/contabilidad/libro-mayor/excepciones/${codigoCuenta}/`, {
      params: { cierre_id: cierreId }
    });
    
    const excepciones = res.data.excepciones || [];
    
    // Mapear tipos de incidencia a tipos de excepción del backend
    const mapeoTipos = {
      'DOC_NULL': 'movimientos_tipodoc_nulo',
      'DOC_NO_REC': 'tipos_doc_no_reconocidos',
      'CUENTA_INGLES': 'cuentas_sin_nombre_ingles',
    };
    
    const tipoBackend = mapeoTipos[tipoExcepcion];
    const excepcionAEliminar = excepciones.find(exc => exc.tipo_excepcion === tipoBackend);
    
    if (!excepcionAEliminar) {
      throw new Error(`No se encontró la excepción de tipo "${tipoExcepcion}" para la cuenta ${codigoCuenta}`);
    }
    
    // Eliminar la excepción usando su ID
    const deleteRes = await api.delete(`/contabilidad/libro-mayor/excepciones/${excepcionAEliminar.id}/eliminar/`);
    return deleteRes.data;
    
  } catch (error) {
    if (error.response?.status === 404) {
      throw new Error(`Cuenta ${codigoCuenta} no encontrada o no tiene excepciones`);
    }
    throw new Error(`Error al eliminar excepción: ${error.response?.data?.error || error.message}`);
  }
};

// ==================== GESTIÓN DE CACHÉ ====================
export const obtenerEstadoCache = async () => {
  const res = await api.get('/contabilidad/cache/incidencias/estado/');
  return res.data;
};

export const limpiarCacheIncidencias = async (cierreId = null, limpiarTodo = false) => {
  const data = {};
  if (cierreId) data.cierre_id = cierreId;
  if (limpiarTodo) data.limpiar_todo = true;
  
  const res = await api.post('/contabilidad/cache/incidencias/limpiar/', data);
  return res.data;
};

export const obtenerIncidenciasConsolidadasLibroMayor = async (cierreId) => {
  const res = await api.get(`/contabilidad/libro-mayor/${cierreId}/incidencias-consolidadas/`);
  return res.data;
};

// ==================== CRUD REGISTROS INDIVIDUALES PERSISTENTES ====================
// APIs para manejar registros individuales (cuenta + sus clasificaciones)

export const crearRegistroClasificacionPersistente = async (data) => {
  // Crear una nueva cuenta con sus clasificaciones
  const res = await api.post("/contabilidad/cuentas/crear/", data);
  return res.data;
};

export const actualizarRegistroClasificacionPersistente = async (cuentaId, data) => {
  // Actualizar una cuenta y sus clasificaciones
  const res = await api.patch(`/contabilidad/cuentas/${cuentaId}/actualizar/`, data);
  return res.data;
};

export const eliminarRegistroClasificacionPersistente = async (cuentaId) => {
  // Eliminar una cuenta y todas sus clasificaciones
  const res = await api.delete(`/contabilidad/cuentas/${cuentaId}/eliminar/`);
  return res.data;
};

export const clasificacionMasivaPersistente = async (cuentaIds, setId, opcionId) => {
  const res = await api.post("/contabilidad/cuentas/clasificacion-masiva/", {
    cuenta_ids: cuentaIds,
    set_clas_id: setId,
    opcion_id: opcionId
  });
  return res.data;
};
