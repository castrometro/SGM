// src/modules/contabilidad/clientes/api/clientes.api.js
import api from "../../../../api/config";

/**
 * 📡 API de Clientes para Contabilidad
 * Funciones para comunicarse con el backend
 */

/**
 * Obtener clientes asignados al usuario actual (Analistas)
 */
export const obtenerClientesAsignados = async () => {
  const response = await api.get("/clientes/asignados/");
  return response.data;
};

/**
 * Obtener todos los clientes (uso limitado)
 */
export const obtenerTodosLosClientes = async () => {
  const response = await api.get("/clientes/");
  return response.data;
};

/**
 * Obtener clientes por área del usuario (Gerentes y Supervisores)
 */
export const obtenerClientesPorArea = async () => {
  const response = await api.get("/clientes-por-area/");
  return response.data;
};

/**
 * Obtener un cliente específico por ID
 */
export const obtenerCliente = async (id) => {
  const response = await api.get(`/clientes/${id}/`);
  return response.data;
};

/**
 * Obtener resumen de contabilidad para un cliente
 */
export const obtenerResumenContabilidad = async (clienteId) => {
  console.log('🔍 obtenerResumenContabilidad - Solicitando para cliente:', clienteId);
  const response = await api.get(`/cierres/resumen/${clienteId}/`);
  console.log('✅ obtenerResumenContabilidad - Respuesta:', response.data);
  return response.data;
};

/**
 * Obtener usuario actual
 */
export const obtenerUsuario = async () => {
  const response = await api.get("/usuarios/me/");
  return response.data;
};
