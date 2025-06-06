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

//----------LIBRO MAYOR----------//
export const subirLibroMayor = async (cierreId, archivo) => {
  const formData = new FormData();
  formData.append("cierre", cierreId);
  formData.append("archivo", archivo);

  const res = await api.post(`/contabilidad/libromayor/`, formData, {
    headers: { "Content-Type": "multipart/form-data" }
  });
  return res.data;
};


export const obtenerLibrosMayor = async (cierreId) => {
  const res = await api.get(`/contabilidad/libromayor/`, {
    params: { cierre: cierreId }
  });
  return res.data;
};



//----------CIERRE MENSUAL----------//
export const obtenerCierreMensual = async (clienteId, periodo) => {
  const res = await api.get(`/contabilidad/cierres/`, {
    params: { cliente: clienteId, periodo }
  });
  // Devuelve el primero si existe, o null
  return res.data.length > 0 ? res.data[0] : null;
};

export const crearCierreMensual = async (clienteId, periodo) => {
  const res = await api.post(`/contabilidad/cierres/`, {
    cliente: Number(clienteId),
    periodo,
    estado: "pendiente"
  });
  return res.data;
};

export const obtenerCierrePorId = async (cierreId) => {
  const res = await api.get(`/contabilidad/cierres/${cierreId}/`);
  return res.data; // { id, cliente, periodo, estado, ... }
}


//----------CLASIFICACION-PROGRESO----------//
export const obtenerProgresoClasificacionTodosLosSets = async (cierreId) => {
  // Llama al action /contabilidad/clasificacion/<cierre_id>/progreso_todos_los_sets/
  const res = await api.get(`/contabilidad/clasificacion/${cierreId}/progreso_todos_los_sets/`);
  return res.data; // { sets_progreso: [...], total_sets: N }
};

// Progreso de clasificación para un set específico (opcional, según endpoint DRF)
export const obtenerProgresoClasificacionPorSet = async (cierreId, setId) => {
  // Si tu endpoint soporta query param ?set_id=... (modifica el backend como sugerí)
  const res = await api.get(`/contabilidad/clasificacion/${cierreId}/progreso/`, {
    params: { set_id: setId }
  });
  return res.data;
};



//----------CLASIFICACION----------//
// 1. Cuentas pendientes de clasificar para un cierre (por cliente)
export const obtenerCuentasPendientes = async (cierreId) => {
  const res = await api.get(`/contabilidad/clasificacion/${cierreId}/cuentas_pendientes/`);
  return res.data; // [{ id, codigo, nombre }]
};

// 2. Sets de clasificación de un cliente
export const obtenerSetsClasificacion = async (clienteId) => {
  const res = await api.get(`/contabilidad/clasificaciones-set/`, {
    params: { cliente: clienteId }
  });
  return res.data; // [{ id, nombre, ... }]
};

// 3. Opciones de un set de clasificación
export const obtenerOpcionesClasificacion = async (setClasId) => {
  const res = await api.get(`/contabilidad/clasificaciones-opcion/`, {
    params: { set_clas: setClasId }
  });
  return res.data;
};


// 4. Guardar clasificación de cuenta
export const clasificarCuenta = async (cuentaId, setClasId, opcionId) => {
  const res = await api.post(`/contabilidad/clasificacion/clasificar/`, {
    cuenta_id: cuentaId,
    set_clas_id: setClasId,
    opcion_id: opcionId,
  });
  return res.data; // { ok: true, id: ..., creado: true/false }
};

// 5. Guardar un nuevo set de clasificación
// POST /contabilidad/clasificaciones-set/
export const crearSetClasificacion = async (clienteId, data) => {
  // data: { nombre: "nombre del set" }
  const res = await api.post(`/contabilidad/clasificaciones-set/`, {
    ...data,
    cliente: clienteId
  });
  return res.data; // { id, nombre, ... }
};

// 6. Guardar una nueva opción de clasificación
// POST /contabilidad/clasificaciones-opcion/
export const crearOpcionClasificacion = async (setClasId, data) => {
  // data: { valor: "nombre de la opción" }
  const res = await api.post(`/contabilidad/clasificaciones-opcion/`, {
    ...data,
    set_clas: setClasId
  });
  return res.data; // { id, valor, ... }
};

// 7. Eliminar un set de clasificación
export const eliminarSetClasificacion = async (setClasId) => {
  const res = await api.delete(`/contabilidad/clasificaciones-set/${setClasId}/`);
  return res.data; // { ok: true }
};
// 8. Eliminar una opción de clasificación
export const eliminarOpcionClasificacion = async (opcionClasId) => {
  const res = await api.delete(`/contabilidad/clasificaciones-opcion/${opcionClasId}/`);
  return res.data; // { ok: true }
};

// Cuentas pendientes de clasificar para un cliente y set específico
export const obtenerCuentasPendientesPorSet = async (clienteId, setId) => {
  const res = await api.get(`/contabilidad/clientes/${clienteId}/sets/${setId}/cuentas_pendientes/`);
  return res.data; // { cuentas_faltantes: [...] }
};

//Cierres//

// 9. Obtener cierres de un cliente
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
  const res = await api.post(`/contabilidad/nombres-ingles/`, formData, {
    headers: { "Content-Type": "multipart/form-data" }
  });
  return res.data; // { ok: true }
};

// Resumen de movimientos por cuenta para un cierre
export const obtenerMovimientosResumen = async (cierreId) => {
  const res = await api.get(
    `/contabilidad/cierres/${cierreId}/movimientos-resumen/`
  );
  return res.data;
};

// Detalle de movimientos para una cuenta específica
export const obtenerMovimientosCuenta = async (cierreId, cuentaId) => {
  const res = await api.get(
    `/contabilidad/cierres/${cierreId}/cuentas/${cuentaId}/movimientos/`
  );
  return res.data;
};
