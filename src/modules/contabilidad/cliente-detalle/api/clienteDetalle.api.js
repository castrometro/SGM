// src/modules/contabilidad/cliente-detalle/api/clienteDetalle.api.js
import api from "../../../../api/config";

/**
 * 📡 API de Detalle de Cliente para Contabilidad
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
 * Obtener resumen básico de contabilidad para un cliente
 */
export const obtenerResumenContabilidad = async (clienteId) => {
  console.log('🔍 obtenerResumenContabilidad - Solicitando para cliente:', clienteId);
  const response = await api.get(`/contabilidad/cierres/resumen/${clienteId}/`);
  console.log('✅ obtenerResumenContabilidad - Respuesta:', response.data);
  return response.data;
};

/**
 * Obtener KPIs agregados de contabilidad para un cliente
 */
export const obtenerKpisContabilidadCliente = async (clienteId) => {
  console.log('🔍 obtenerKpisContabilidadCliente - Solicitando para cliente:', clienteId);
  
  try {
    // Obtener el último cierre finalizado
    const cierresResponse = await api.get(`/contabilidad/cierres/`, {
      params: {
        cliente: clienteId,
        estado: 'finalizado',
        ordering: '-periodo'
      }
    });
    
    const cierres = cierresResponse.data.results || cierresResponse.data;
    if (!cierres || cierres.length === 0) {
      console.warn('⚠️ obtenerKpisContabilidadCliente - No hay cierres finalizados');
      return { tieneCierre: false, clienteId, kpis: {}, raw: {}, motivo: 'sin_cierres' };
    }

    const cierre = cierres[0]; // El más reciente
    const cierreId = cierre.id;
    const periodo = cierre.periodo;
    
    console.log('🔍 obtenerKpisContabilidadCliente - Obteniendo informe para cierre:', cierreId);
    const informeResponse = await api.get(`/contabilidad/cierres/${cierreId}/informe/`);
    const informe = informeResponse.data;
    
    console.log('✅ obtenerKpisContabilidadCliente - Informe obtenido:', {
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
    console.error('❌ obtenerKpisContabilidadCliente - Error:', error);
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
