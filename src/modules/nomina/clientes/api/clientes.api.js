// src/modules/nomina/clientes/api/clientes.api.js
import api from "../../../../api/config";

/**
 * 📡 API de Clientes para Nómina
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
 * Obtener resumen de nómina para un cliente
 */
export const obtenerResumenNomina = async (clienteId) => {
  console.log('🔍 obtenerResumenNomina - Solicitando para cliente:', clienteId);
  const response = await api.get(`/nomina/cierres/resumen/${clienteId}/`);
  console.log('✅ obtenerResumenNomina - Respuesta:', response.data);
  return response.data;
};

/**
 * Obtener usuario actual
 */
export const obtenerUsuario = async () => {
  const response = await api.get("/usuarios/me/");
  return response.data;
};
