// src/modules/contabilidad/cierre-detalle/api/cierreDetalle.api.js
import api from "../../../../api/config";

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
