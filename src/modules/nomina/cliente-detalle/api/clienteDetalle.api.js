// src/modules/nomina/cliente-detalle/api/clienteDetalle.api.js
import api from "../../../../api/config";

/**
 * 📡 API de Detalle de Cliente para Nómina
 * Funciones para comunicarse con el backend
 */

/**
 * Obtener un cliente específico por ID
 */
export const obtenerCliente = async (id) => {
  const response = await api.get(`/clientes/${id}/`);
  return response.data;
};

/**
 * Obtener resumen básico de nómina para un cliente
 */
export const obtenerResumenNomina = async (clienteId) => {
  console.log('🔍 obtenerResumenNomina - Solicitando para cliente:', clienteId);
  const response = await api.get(`/nomina/cierres/resumen/${clienteId}/`);
  console.log('✅ obtenerResumenNomina - Respuesta:', response.data);
  return response.data;
};

/**
 * Obtener KPIs agregados de nómina para un cliente
 * Usa el endpoint existente de obtenerKpisNominaCliente del API legacy
 */
export const obtenerKpisNominaCliente = async (clienteId) => {
  console.log('🔍 obtenerKpisNominaCliente - Solicitando para cliente:', clienteId);
  
  try {
    // Primero intentamos obtener directamente el último cierre finalizado
    const cierresResponse = await api.get(`/nomina/cierres/`, {
      params: {
        cliente: clienteId,
        estado: 'finalizado',
        ordering: '-periodo'
      }
    });
    
    const cierres = cierresResponse.data.results || cierresResponse.data;
    if (!cierres || cierres.length === 0) {
      console.warn('⚠️ obtenerKpisNominaCliente - No hay cierres finalizados');
      return { tieneCierre: false, clienteId, kpis: {}, raw: {}, motivo: 'sin_cierres' };
    }

    const cierre = cierres[0]; // El más reciente
    const cierreId = cierre.id;
    const periodo = cierre.periodo;
    
    console.log('🔍 obtenerKpisNominaCliente - Obteniendo informe para cierre:', cierreId);
    const informeResponse = await api.get(`/nomina/cierres/${cierreId}/informe/`);
    const informe = informeResponse.data;
    
    console.log('✅ obtenerKpisNominaCliente - Informe obtenido:', {
      source: informe.source,
      periodo: informe.periodo,
      tiene_datos: !!informe.datos_cierre
    });
    
    return {
      tieneCierre: true,
      clienteId,
      periodo,
      estado_cierre: cierre.estado,
      source: informe.source,
      kpis: informe.datos_cierre?.kpis || {},
      raw: { informe }
    };
  } catch (error) {
    console.error('❌ obtenerKpisNominaCliente - Error:', error);
    throw error;
  }
};

/**
 * Obtener usuario actual
 */
export const obtenerUsuario = async () => {
  const response = await api.get("/usuarios/me/");
  return response.data;
};
