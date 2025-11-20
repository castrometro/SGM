// src/modules/contabilidad/cierre-detalle/api/cierreDetalle.api.js
import api from "../../../../api/config";

// Re-export all functions from the original contabilidad API for convenience
export * from "../../../../api/contabilidad";

// ============ FUNCIONES DE CLIENTES ============
export const obtenerCliente = async (id) => {
  const response = await api.get(`/clientes/${id}/`);
  return response.data;
};

export const obtenerServiciosCliente = async (clienteId) => {
  const usuario = JSON.parse(localStorage.getItem("usuario"));
  const endpoint =
    usuario.tipo_usuario === "analista"
      ? `/clientes/${clienteId}/servicios-area/`
      : `/clientes/${clienteId}/servicios/`;
  const res = await api.get(endpoint);
  return res.data;
};


// ============ FUNCIONES DE CONTABILIDAD ============

export const obtenerResumenContable = async (clienteId) => {
  console.log('🔍 obtenerResumenContable - Solicitando para cliente:', clienteId);
  const response = await api.get(`/contabilidad/clientes/${clienteId}/resumen/`);
  console.log('🔍 obtenerResumenContable - Respuesta recibida:', response.data);
  return response.data;
};

// ==================== CIERRES ====================
export const obtenerCierresCliente = async (clienteId) => {
  const res = await api.get(`/contabilidad/cierres/`, {
    params: { cliente: clienteId },
  });
  return res.data;
};

export const obtenerCierrePorId = async (cierreId) => {
  console.log('🔍 obtenerCierrePorId - Solicitando cierre:', cierreId);
  const res = await api.get(`/contabilidad/cierres/${cierreId}/`);
  console.log('🔍 obtenerCierrePorId - Respuesta recibida:', res.data);
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

// ==================== TIPO DE DOCUMENTO ====================
export const obtenerEstadoTipoDocumento = async (clienteId) => {
  const res = await api.get(`/contabilidad/tipo-documento/${clienteId}/estado/`);
  return typeof res.data === "string" ? res.data : res.data.estado;
};

export const subirTipoDocumento = async (formData) => {
  const res = await api.post("/contabilidad/tipo-documento/subir-archivo/", formData);
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

// ==================== LIBRO MAYOR ====================
export const subirLibroMayor = async (clienteId, archivo, cierreId = null) => {
  const formData = new FormData();
  formData.append("cliente_id", clienteId);
  formData.append("archivo", archivo);
  if (cierreId) formData.append("cierre_id", cierreId);

  const res = await api.post("/contabilidad/libro-mayor/subir-archivo/", formData);
  return res.data;
};

export const obtenerLibrosMayor = async (cierreId) => {
  const res = await api.get("/contabilidad/libromayor-archivo/", {
    params: { cierre: cierreId },
  });
  return res.data;
};

export const obtenerMovimientosIncompletos = async (cierreId) => {
  const res = await api.get(`/contabilidad/libro-mayor/incompletos/${cierreId}/`);
  return res.data;
};

export const eliminarLibroMayor = async (libroId) => {
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

// ==================== CLASIFICACIONES ====================
export const obtenerProgresoClasificacionTodosLosSets = async (cierreId) => {
  const res = await api.get(
    `/contabilidad/clasificacion/${cierreId}/progreso_todos_los_sets/`,
  );
  return res.data;
};

export const obtenerProgresoClasificacionPorSet = async (cierreId, setId) => {
  const res = await api.get(
    `/contabilidad/clasificacion/${cierreId}/progreso/`,
    { params: { set_id: setId } },
  );
  return res.data;
};

export const obtenerCuentasPendientes = async (cierreId) => {
  const res = await api.get(
    `/contabilidad/clasificacion/${cierreId}/cuentas_pendientes/`,
  );
  return res.data;
};

// ==================== NOMBRES EN INGLÉS ====================
export const obtenerEstadoNombresIngles = async (clienteId) => {
  const res = await api.get(`/contabilidad/nombre-ingles/${clienteId}/estado/`);
  return res.data;
};

export const obtenerCuentasSinNombreIngles = async (clienteId) => {
  const res = await api.get(`/contabilidad/nombre-ingles/${clienteId}/sin-nombre/`);
  return res.data;
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

// ==================== TIPO DE DOCUMENTO - CRUD ====================
export const eliminarTodosTiposDocumento = async (clienteId) => {
  const res = await api.post(`/contabilidad/tipo-documento/${clienteId}/eliminar-todos/`);
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
  const res = await api.patch(`/contabilidad/tipos-documento/${id}/`, tipoDocumento);
  return res.data;
};

export const eliminarTipoDocumento = async (id) => {
  const res = await api.delete(`/contabilidad/tipos-documento/${id}/`);
  return res.data;
};

// ==================== CLASIFICACIONES - BULK ====================
export const subirClasificacionBulk = async (formData) => {
  const res = await api.post("/contabilidad/clasificacion-bulk/subir-archivo/", formData);
  return res.data;
};

export const obtenerEstadoUploadLog = async (uploadLogId) => {
  const res = await api.get(`/contabilidad/upload-log/${uploadLogId}/estado/`);
  return res.data;
};

// ==================== CLASIFICACIONES - SETS ====================
export const obtenerSetsClasificacion = async (clienteId) => {
  const res = await api.get(`/contabilidad/clasificaciones-set/`, {
    params: { cliente: clienteId },
  });
  return res.data;
};

// ==================== NOMBRES EN INGLÉS - CRUD ====================
export const subirNombresEnIngles = async (formData) => {
  const res = await api.post("/contabilidad/nombre-ingles/subir-archivo/", formData);
  return res.data;
};

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

// ==================== INCIDENCIAS ====================
export const obtenerIncidenciasConsolidadas = async (cierreId) => {
  const res = await api.get(`/contabilidad/libro-mayor/${cierreId}/incidencias-consolidadas/`);
  return res.data;
};

export const obtenerIncidenciasConsolidadasOptimizado = async (cierreId, forzarActualizacion = false) => {
  const params = {};
  if (forzarActualizacion) {
    params.forzar_actualizacion = 'true';
    params.usar_cache = 'false';
  }
  
  const res = await api.get(`/contabilidad/libro-mayor/${cierreId}/incidencias-optimizado/`, {
    params
  });
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
  
  if (esClasificacion && setId) {
    payload.set_clasificacion_id = setId;
    const res = await api.post('/contabilidad/libro-mayor/excepciones/clasificacion/crear/', payload);
    return res.data;
  } else {
    const res = await api.post('/contabilidad/libro-mayor/excepciones/crear/', payload);
    return res.data;
  }
};

export const eliminarExcepcionNoAplica = async (cierreId, codigoCuenta, tipoExcepcion, setId = null) => {
  try {
    if ((tipoExcepcion === 'CUENTA_NO_CLAS' || tipoExcepcion === 'CUENTA_NO_CLASIFICADA') && setId) {
      const res = await api.delete('/contabilidad/libro-mayor/excepciones/clasificacion/eliminar/', {
        data: {
          cierre_id: cierreId,
          codigo_cuenta: codigoCuenta,
          set_clasificacion_id: setId
        }
      });
      return res.data;
    } else {
      const res = await api.delete('/contabilidad/libro-mayor/excepciones/eliminar/', {
        data: {
          cierre_id: cierreId,
          codigo_cuenta: codigoCuenta,
          tipo_excepcion: tipoExcepcion
        }
      });
      return res.data;
    }
  } catch (error) {
    console.error('Error eliminando excepción:', error);
    throw error;
  }
};

// ==================== LOGGING DE ACTIVIDADES ====================
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


