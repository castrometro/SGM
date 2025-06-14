// src/api/contabilidad.js
import api from "./config";

// Trae el resumen contable de un cliente
export const obtenerResumenContable = async (clienteId) => {
  const response = await api.get(`/contabilidad/clientes/${clienteId}/resumen/`);
  return response.data;
};

//---------Plantillas---------//
// Devuelve la URL para descargar la plantilla oficial de tipo de documento
export const descargarPlantillaTipoDocumento = () => {
  return `${api.defaults.baseURL}/contabilidad/plantilla-tipo-doc/`;
};

export const descargarPlantillaNombresEnIngles = () => {
  return `${api.defaults.baseURL}/contabilidad/plantilla-nombres-en-ingles/`;
};

// Plantilla Excel para bulk de clasificaciones
export const descargarPlantillaClasificacionBulk = () => {
  return `${api.defaults.baseURL}/contabilidad/plantilla-clasificacion-bulk/`;
};

//-----Tipo de documento-----//
// Consulta el estado del tipo de documento para un cliente
export const obtenerEstadoTipoDocumento = async (clienteId) => {
  const res = await api.get(`/contabilidad/tipo-documento/${clienteId}/estado/`);
  // Si tu backend devuelve {estado: "pendiente"} o "pendiente", soporta ambos
  return typeof res.data === "string" ? res.data : res.data.estado;
};

// Sube un archivo de tipo de documento para el cliente (ruta nueva)
export const subirTipoDocumento = async (formData) => {
  const res = await api.post("/contabilidad/tipo-documento/subir-archivo/", formData);
  return res.data;
};

export const obtenerTiposDocumentoCliente = async (clienteId) => {
  const res = await api.get(`/contabilidad/tipo-documento/${clienteId}/list/`);
  return res.data;
};

export const eliminarTodosTiposDocumento = async (clienteId) => {
  const res = await api.post(`/contabilidad/tipo-documento/${clienteId}/eliminar-todos/`);
  return res.data;
};

// CRUD individual para tipos de documento
export const crearTipoDocumento = async (clienteId, tipoDocumento) => {
  const res = await api.post("/contabilidad/tipos-documento/", {
    cliente: clienteId,
    ...tipoDocumento
  });
  return res.data;
};

export const actualizarTipoDocumento = async (id, tipoDocumento) => {
  const res = await api.patch(`/contabilidad/tipos-documento/${id}/`, tipoDocumento);
  return res.data;
};

export const eliminarTipoDocumento = async (id) => {
  const res = await api.delete(`/contabilidad/tipos-documento/${id}/`);
  return res.data;
};

//----------LIBRO MAYOR----------//
export const subirLibroMayor = async (cierreId, archivo) => {
  const formData = new FormData();
  formData.append("cierre", cierreId);
  formData.append("archivo", archivo);

  const res = await api.post("/contabilidad/libromayor/", formData);
  return res.data;
};

export const obtenerLibrosMayor = async (cierreId) => {
  const res = await api.get("/contabilidad/libromayor/", {
    params: { cierre: cierreId }
  });
  return res.data;
};

export const eliminarLibroMayor = async (libroId) => {
  const res = await api.delete(`/contabilidad/libromayor/${libroId}/`);
  return res.data;
};

//----------CLASIFICACIONES----------//

// 1. Obtener sets de clasificación de un cliente específico
export const obtenerSetsClasificacion = async (clienteId) => {
  const res = await api.get(`/contabilidad/clasificaciones-set/`, {
    params: { cliente: clienteId }
  });
  return res.data; // [{ id, nombre, descripcion, idioma }]
};

// 2. Obtener opciones de un set de clasificación específico
export const obtenerOpcionesClasificacion = async (setClasId) => {
  const res = await api.get(`/contabilidad/clasificaciones-opcion/`, {
    params: { set_clas: setClasId }
  });
  return res.data; // [{ id, valor, descripcion, parent }]
};

// 3. Obtener una "clasificación completa" de un cliente (sets con sus opciones)
export const obtenerClasificacionCompleta = async (clienteId) => {
  const sets = await obtenerSetsClasificacion(clienteId);
  const completa = [];
  for (const set of sets) {
    const opciones = await obtenerOpcionesClasificacion(set.id);
    completa.push({ ...set, opciones });
  }
  return completa;
};

// 4. Crear un nuevo set de clasificación
export const crearSetClasificacion = async (clienteId, nombre, descripcion, idioma = "es") => {
  // POST /contabilidad/clasificaciones-set/
  const res = await api.post(`/contabilidad/clasificaciones-set/`, {
    cliente: clienteId,
    nombre,
    descripcion,
    idioma
  });
  return res.data; // { id, cliente, nombre, descripcion, idioma }
};

// 5. Crear una nueva opción en un set
export const crearOpcionClasificacion = async (setClasId, valor, descripcion, parentId = null) => {
  // POST /contabilidad/clasificaciones-opcion/
  const res = await api.post(`/contabilidad/clasificaciones-opcion/`, {
    set_clas: setClasId,
    valor,
    descripcion,
    parent: parentId
  });
  return res.data; // { id, set_clas, valor, descripcion, parent }
};

// 6. Eliminar un set de clasificación
export const eliminarSetClasificacion = async (setClasId) => {
  const res = await api.delete(`/contabilidad/clasificaciones-set/${setClasId}/`);
  return res.data; // { ok: true }
};

// 7. Eliminar una opción de clasificación
export const eliminarOpcionClasificacion = async (opcionClasId) => {
  const res = await api.delete(`/contabilidad/clasificaciones-opcion/${opcionClasId}/`);
  return res.data; // { ok: true }
};

// AccountClassification (Clasificaciones de cuentas individuales)
export const obtenerClasificacionesCuenta = async (clienteId) => {
  const res = await api.get(`/contabilidad/clasificaciones/`, {
    params: { cuenta__cliente: clienteId }
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
  // Primero obtenemos todas las clasificaciones del cliente
  const clasificaciones = await obtenerClasificacionesCuenta(clienteId);
  
  // Eliminamos cada una
  const promesas = clasificaciones.map(clasificacion => 
    eliminarClasificacionCuenta(clasificacion.id)
  );
  
  await Promise.all(promesas);
  return { mensaje: `${clasificaciones.length} clasificaciones eliminadas` };
};

// Cuentas pendientes de clasificar para un cliente y set específico
export const obtenerCuentasPendientesPorSet = async (clienteId, setId) => {
  const res = await api.get(`/contabilidad/clientes/${clienteId}/sets/${setId}/cuentas_pendientes/`);
  return res.data; // { cuentas_faltantes: [...] }
};

//Cierres//

// Obtener cierres de un cliente
export const obtenerCierresCliente = async (clienteId) => {
  const res = await api.get(`/contabilidad/cierres/`, {
    params: { cliente: clienteId }
  });
  return res.data; // [{ id, periodo, estado, ... }]
};

//----------NOMBRES EN INGLES----------//

export const eliminarNombresEnIngles = async (clienteId, cierreId) => {
  const res = await api.delete(`/contabilidad/nombres-ingles/${clienteId}/${cierreId}/`);
  return res.data; // { ok: true }
}

export const obtenerEstadoNombresIngles = async (clienteId, cierreId) => {
  const params = new URLSearchParams({ cliente_id: clienteId, estado: 1 });
  if (cierreId) params.append("cierre_id", cierreId);
  const res = await api.get(`/contabilidad/nombres-ingles/?${params}`);
  return res.data;
}

export const obtenerNombresEnInglesCliente = async (clienteId, cierreId) => {
  const params = new URLSearchParams({ cliente_id: clienteId, list: 1 });
  if (cierreId) params.append("cierre_id", cierreId);
  const res = await api.get(`/contabilidad/nombres-ingles/?${params}`);
  return res.data;
};

export const obtenerNombresEnIngles = async (cierreId) => {
  const res = await api.get(`/contabilidad/nombres-ingles/${cierreId}/`);
  return res.data; // { id, cliente, cierre, nombres: [...] }
}

export const subirNombresIngles = async (formData) => {
  const res = await api.post("/contabilidad/nombres-ingles/", formData);
  return res.data;
}

// ---------- MOVIMIENTOS ---------- //

export const obtenerMovimientosResumen = async (
  cierreId,
  { page = 1, page_size = 50, search = "", cuenta = "", auxiliar = "", centro_costo = "" } = {}
) => {
  const params = { page, page_size };
  if (search) params.search = search;
  if (cuenta) params.cuenta = cuenta;
  if (auxiliar) params.auxiliar = auxiliar;
  if (centro_costo) params.centro_costo = centro_costo;

  const res = await api.get(`/contabilidad/cierres/${cierreId}/movimientos-resumen/`, { params });
  return res.data;
};

export const obtenerMovimientosCuenta = async (cierreId, cuentaId) => {
  const res = await api.get(`/contabilidad/cierres/${cierreId}/cuentas/${cuentaId}/movimientos/`);
  return res.data;
};

//----------BULK CLASIFICACIONES----------//

export const subirClasificacionBulk = async (formData) => {
  const res = await api.post("/contabilidad/clasificacion-bulk/", formData);
  return res.data;
};

// Obtener lista de bulk uploads de clasificaciones para un cliente
export const obtenerBulkClasificaciones = async (clienteId) => {
  const res = await api.get("/contabilidad/clasificacion-bulk/", {
    params: { cliente: clienteId }
  });
  return res.data;
};

export const eliminarBulkClasificacion = async (uploadId) => {
  const res = await api.delete(`/contabilidad/clasificacion-bulk/${uploadId}/`);
  return res.data;
};

export const eliminarTodosBulkClasificacion = async (clienteId) => {
  const res = await api.post("/contabilidad/clasificacion-bulk/eliminar-todos/", {
    cliente_id: clienteId
  });
  return res.data;
};

export const reprocesarBulkClasificacionUpload = async (uploadId) => {
  const res = await api.post(`/contabilidad/clasificacion-bulk/${uploadId}/reprocesar/`);
  return res.data;
};

export const obtenerLogsUpload = async (tipoUpload, uploadId = null, clienteId = null) => {
  const params = { tipo_upload: tipoUpload };
  if (uploadId) params.upload_id = uploadId;
  if (clienteId) params.cliente_id = clienteId;
  
  const res = await api.get('/contabilidad/activity-logs/', { params });
  return res.data;
};

//----------NOMBRES EN INGLES UPLOADS----------//

export const obtenerNombresInglesUploads = async (clienteId) => {
  const res = await api.get("/contabilidad/nombres-ingles-upload/", {
    params: { cliente: clienteId }
  });
  return res.data;
};

export const subirNombresInglesUpload = async (clienteId, cierreId, archivo) => {
  const formData = new FormData();
  formData.append("cliente", clienteId);
  if (cierreId) {
    formData.append("cierre", cierreId);
  }
  formData.append("archivo", archivo);

  const res = await api.post("/contabilidad/nombres-ingles-upload/", formData);
  return res.data;
};

export const eliminarNombresInglesUpload = async (uploadId) => {
  const res = await api.delete(`/contabilidad/nombres-ingles-upload/${uploadId}/`);
  return res.data;
};

export const eliminarTodosNombresInglesUpload = async (clienteId, cierreId = null) => {
  const data = { cliente_id: clienteId };
  if (cierreId) {
    data.cierre_id = cierreId;
  }
  
  const res = await api.post("/contabilidad/nombres-ingles-upload/eliminar-todos/", data);
  return res.data;
};

export const reprocesarNombresInglesUpload = async (uploadId) => {
  const res = await api.post(`/contabilidad/nombres-ingles-upload/${uploadId}/reprocesar/`);
  return res.data;
};
