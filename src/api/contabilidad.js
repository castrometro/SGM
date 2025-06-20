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

export const registrarVistaTiposDocumento = async (clienteId) => {
  const res = await api.post(
    `/contabilidad/tipo-documento/${clienteId}/registrar-vista/`,
  );
  return res.data;
};

export const registrarVistaClasificaciones = async (
  clienteId,
  uploadId = null,
) => {
  const res = await api.post(
    `/contabilidad/clasificacion/${clienteId}/registrar-vista/`,
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
export const subirLibroMayor = async (cierreId, archivo) => {
  const formData = new FormData();
  formData.append("cierre", cierreId);
  formData.append("archivo", archivo);

  const res = await api.post("/contabilidad/libromayor/", formData);
  return res.data;
};

export const obtenerLibrosMayor = async (cierreId) => {
  const res = await api.get("/contabilidad/libromayor/", {
    params: { cierre: cierreId },
  });
  return res.data;
};

export const eliminarLibroMayor = async (libroId) => {
  const res = await api.delete(`/contabilidad/libromayor/${libroId}/`);
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
    page = 1,
    page_size = 50,
    search = "",
    cuenta = "",
    auxiliar = "",
    centro_costo = "",
  } = {},
) => {
  const params = { page, page_size };
  if (search) params.search = search;
  if (cuenta) params.cuenta = cuenta;
  if (auxiliar) params.auxiliar = auxiliar;
  if (centro_costo) params.centro_costo = centro_costo;

  const res = await api.get(
    `/contabilidad/cierres/${cierreId}/movimientos-resumen/`,
    { params },
  );
  return res.data;
};

export const obtenerMovimientosCuenta = async (cierreId, cuentaId) => {
  const res = await api.get(
    `/contabilidad/cierres/${cierreId}/cuentas/${cuentaId}/movimientos/`,
  );
  return res.data;
};

// ==================== NOMBRES EN INGLÉS ====================
export const obtenerEstadoNombresIngles = async (clienteId, cierreId) => {
  const res = await api.get(
    `/contabilidad/nombres-ingles-crud/${clienteId}/estado/`,
    {
      params: cierreId ? { cierre: cierreId } : {},
    },
  );
  return res.data;
};

export const obtenerNombresEnIngles = async (cierreId) => {
  const res = await api.get(`/contabilidad/nombres-ingles/${cierreId}/`);
  return res.data;
};

export const subirNombresIngles = async (formData) => {
  const res = await api.post(
    "/contabilidad/nombres-ingles-crud/subir-archivo/",
    formData,
  );
  return res.data;
};

export const eliminarNombresEnIngles = async (clienteId, cierreId) => {
  const res = await api.delete(
    `/contabilidad/nombres-ingles/${clienteId}/${cierreId}/`,
  );
  return res.data;
};

// ==================== NOMBRES EN INGLÉS CRUD ====================
export const obtenerNombresInglesCliente = async (clienteId) => {
  const res = await api.get(
    `/contabilidad/nombres-ingles-crud/${clienteId}/list/`,
  );
  return res.data;
};

export const registrarVistaNombresIngles = async (clienteId) => {
  const res = await api.post(
    `/contabilidad/nombres-ingles-crud/${clienteId}/registrar-vista/`,
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
    `/contabilidad/nombres-ingles-crud/${clienteId}/eliminar-todos/`,
  );
  return res.data;
};

// ==================== BULK CLASIFICACIONES ====================
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

// ==================== CLASIFICACIÓN ARCHIVO (RAW DATA) ====================
export const obtenerClasificacionesArchivo = async (uploadId) => {
  const res = await api.get("/contabilidad/clasificacion-archivo/", {
    params: { upload_log: uploadId },
  });
  return res.data;
};

export const crearClasificacionArchivo = async (data) => {
  const res = await api.post("/contabilidad/clasificacion-archivo/", data);
  return res.data;
};

export const actualizarClasificacionArchivo = async (id, data) => {
  const res = await api.patch(
    `/contabilidad/clasificacion-archivo/${id}/`,
    data,
  );
  return res.data;
};

export const eliminarClasificacionArchivo = async (id) => {
  const res = await api.delete(`/contabilidad/clasificacion-archivo/${id}/`);
  return res.data;
};

export const procesarMapeoClasificaciones = async (uploadId) => {
  const res = await api.post(
    "/contabilidad/clasificacion-archivo/procesar_mapeo/",
    {
      upload_log_id: uploadId,
    },
  );
  return res.data;
};

export const obtenerClasificacionesArchivoCliente = async (
  clienteId,
  procesado = null,
) => {
  const params = { cliente: clienteId };
  if (procesado !== null) {
    params.procesado = procesado;
  }
  const res = await api.get("/contabilidad/clasificacion-archivo/", { params });
  return res.data;
};

export const obtenerEstadisticasClasificacionArchivo = async (uploadId) => {
  const registros = await obtenerClasificacionesArchivo(uploadId);
  const total = registros.length;
  const procesados = registros.filter((r) => r.procesado).length;
  const conErrores = registros.filter((r) => r.errores_mapeo).length;
  const pendientes = total - procesados;

  return {
    total,
    procesados,
    pendientes,
    conErrores,
    registros,
  };
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

export const crearOpcion = async (setId, valor) => {
  const res = await api.post("/contabilidad/clasificaciones-opcion/", {
    set_clas: setId,
    valor: valor,
  });
  return res.data;
};

export const actualizarOpcion = async (opcionId, valor) => {
  const res = await api.put(
    `/contabilidad/clasificaciones-opcion/${opcionId}/`,
    {
      valor: valor,
    },
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
