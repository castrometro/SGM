// src/api/payroll/clientes_payroll.js
import api from "../config";

/**
 * APIs específicas para la gestión de clientes en el módulo de Payroll
 * Estas APIs están diseñadas para no interferir con las APIs de contabilidad
 */

// ==================== RESUMEN DE CLIENTES PAYROLL ====================

/**
 * Obtiene el resumen de payroll de un cliente específico
 * Incluye información de empleados, última nómina, estado actual, etc.
 * TODO: Implementar endpoint real en Django
 */
export const obtenerResumenPayrollCliente = async (clienteId) => {
  try {
    const response = await api.get(`/payroll/clientes/${clienteId}/resumen/`);
    return response.data;
  } catch (error) {
    // Si el endpoint no existe (404), devolver datos simulados
    if (error.response?.status === 404) {
      console.warn(`⚠️  Endpoint /payroll/clientes/${clienteId}/resumen/ no implementado. Devolviendo datos simulados.`);
      
      // Datos simulados que coinciden con la estructura esperada
      return {
        ultimo_cierre: "2025-01",
        estado_cierre_actual: "pendiente",
        estado_ultimo_cierre: "pendiente",
        total_empleados: 25,
        empleados_activos: 23,
        empleados_inactivos: 2,
        nominas_pendientes: 1,
        ultimo_proceso: "2025-01-15",
        proxima_nomina: "2025-02-15"
      };
    }
    
    // Si es otro tipo de error, re-lanzarlo
    throw error;
  }
};

/**
 * Obtiene estadísticas generales de payroll para un cliente
 * Útil para dashboards y vistas ejecutivas
 */
export const obtenerEstadisticasPayrollCliente = async (clienteId) => {
  try {
    const response = await api.get(`/payroll/clientes/${clienteId}/estadisticas/`);
    return response.data;
  } catch (error) {
    // Si el endpoint no existe (404), devolver datos simulados
    if (error.response?.status === 404) {
      console.warn(`⚠️  Endpoint /payroll/clientes/${clienteId}/estadisticas/ no implementado. Devolviendo datos simulados.`);
      
      return {
        resumen_anual: {
          total_nominas: 12,
          empleados_promedio: 24,
          gasto_nomina_total: 2850000,
          incremento_anual: 5.2
        },
        ultimo_trimestre: {
          nominas_procesadas: 3,
          empleados_nuevos: 2,
          empleados_retirados: 1,
          variacion_gasto: 2.1
        }
      };
    }
    throw error;
  }
};

// ==================== EMPLEADOS POR CLIENTE ====================

/**
 * Obtiene la lista de empleados de un cliente específico
 * Incluye filtros y paginación
 */
export const obtenerEmpleadosCliente = async (clienteId, params = {}) => {
  try {
    const response = await api.get(`/payroll/clientes/${clienteId}/empleados/`, {
      params: {
        page: 1,
        page_size: 50,
        search: '',
        estado: 'activo',
        ...params
      }
    });
    return response.data;
  } catch (error) {
    // Si el endpoint no existe (404), devolver datos simulados
    if (error.response?.status === 404) {
      console.warn(`⚠️  Endpoint /payroll/clientes/${clienteId}/empleados/ no implementado. Devolviendo datos simulados.`);
      
      return {
        count: 25,
        next: null,
        previous: null,
        results: [
          {
            id: 1,
            nombre: "Juan Pérez",
            email: "juan.perez@empresa.com",
            cargo: "Desarrollador Senior",
            estado: "activo",
            fecha_ingreso: "2023-01-15",
            salario_base: 1200000
          },
          {
            id: 2,
            nombre: "María González",
            email: "maria.gonzalez@empresa.com",
            cargo: "Contadora",
            estado: "activo",
            fecha_ingreso: "2022-11-10",
            salario_base: 1100000
          },
          {
            id: 3,
            nombre: "Carlos Rodríguez",
            email: "carlos.rodriguez@empresa.com",
            cargo: "Analista",
            estado: "activo",
            fecha_ingreso: "2024-03-20",
            salario_base: 950000
          }
        ]
      };
    }
    throw error;
  }
};

/**
 * Obtiene el detalle de un empleado específico de un cliente
 */
export const obtenerEmpleadoCliente = async (clienteId, empleadoId) => {
  const response = await api.get(`/payroll/clientes/${clienteId}/empleados/${empleadoId}/`);
  return response.data;
};

/**
 * Crea un nuevo empleado para un cliente
 */
export const crearEmpleadoCliente = async (clienteId, datosEmpleado) => {
  const response = await api.post(`/payroll/clientes/${clienteId}/empleados/`, datosEmpleado);
  return response.data;
};

/**
 * Actualiza un empleado existente de un cliente
 */
export const actualizarEmpleadoCliente = async (clienteId, empleadoId, datosEmpleado) => {
  const response = await api.put(`/payroll/clientes/${clienteId}/empleados/${empleadoId}/`, datosEmpleado);
  return response.data;
};

/**
 * Desactiva un empleado (no lo elimina, lo marca como inactivo)
 */
export const desactivarEmpleadoCliente = async (clienteId, empleadoId) => {
  const response = await api.patch(`/payroll/clientes/${clienteId}/empleados/${empleadoId}/desactivar/`);
  return response.data;
};

// ==================== NÓMINAS Y CIERRES PAYROLL ====================

/**
 * Obtiene los cierres de nómina de un cliente
 */
export const obtenerCierresPayrollCliente = async (clienteId, params = {}) => {
  try {
    const response = await api.get(`/payroll/clientes/${clienteId}/cierres/`, {
      params: {
        page: 1,
        page_size: 20,
        ...params
      }
    });
    return response.data;
  } catch (error) {
    // Si el endpoint no existe (404), devolver datos simulados
    if (error.response?.status === 404) {
      console.warn(`⚠️  Endpoint /payroll/clientes/${clienteId}/cierres/ no implementado. Devolviendo datos simulados.`);
      
      return {
        count: 6,
        next: null,
        previous: null,
        cliente: {
          id: parseInt(clienteId),
          nombre: "Cliente de Prueba Payroll",
          rut: "12345678-9"
        },
        results: [
          {
            id: 1,
            periodo: "2025-01",
            estado: "pendiente",
            fecha_creacion: "2025-01-31T10:00:00Z",
            fecha_finalizacion: null,
            total_empleados: 25,
            usuario_responsable: "analista@payroll.com",
            observaciones: "Cierre en proceso",
            puede_finalizar: false,
            en_proceso: true
          },
          {
            id: 2,
            periodo: "2024-12",
            estado: "completado",
            fecha_creacion: "2024-12-31T10:00:00Z",
            fecha_finalizacion: "2025-01-05T15:30:00Z",
            total_empleados: 24,
            usuario_responsable: "analista@payroll.com",
            observaciones: "Cierre completado sin observaciones",
            puede_finalizar: false,
            en_proceso: false
          },
          {
            id: 3,
            periodo: "2024-11",
            estado: "finalizado",
            fecha_creacion: "2024-11-30T10:00:00Z",
            fecha_finalizacion: "2024-12-10T14:20:00Z",
            total_empleados: 23,
            usuario_responsable: "supervisor@payroll.com",
            observaciones: "Cierre mensual completado",
            puede_finalizar: false,
            en_proceso: false
          },
          {
            id: 4,
            periodo: "2024-10",
            estado: "procesando",
            fecha_creacion: "2024-10-31T10:00:00Z",
            fecha_finalizacion: null,
            total_empleados: 23,
            usuario_responsable: "analista@payroll.com",
            observaciones: "Revisión de liquidaciones pendiente",
            puede_finalizar: false,
            en_proceso: true
          },
          {
            id: 5,
            periodo: "2024-09",
            estado: "sin_incidencias",
            fecha_creacion: "2024-09-30T10:00:00Z",
            fecha_finalizacion: null,
            total_empleados: 22,
            usuario_responsable: "analista@payroll.com",
            observaciones: "Listo para finalizar",
            puede_finalizar: true,
            en_proceso: false
          },
          {
            id: 6,
            periodo: "2024-08",
            estado: "finalizado",
            fecha_creacion: "2024-08-31T10:00:00Z",
            fecha_finalizacion: "2024-09-15T16:45:00Z",
            total_empleados: 22,
            usuario_responsable: "supervisor@payroll.com",
            observaciones: "Cierre histórico",
            puede_finalizar: false,
            en_proceso: false
          }
        ]
      };
    }
    throw error;
  }
};

/**
 * Obtiene el detalle de un cierre de nómina específico
 */
export const obtenerCierrePayrollDetalle = async (clienteId, cierreId) => {
  const response = await api.get(`/payroll/cierres/${cierreId}/`);
  return response.data;
};

// ==================== SERVICIOS PAYROLL ====================

/**
 * Obtiene los servicios de payroll contratados por un cliente
 */
export const obtenerServiciosPayrollCliente = async (clienteId) => {
  try {
    const response = await api.get(`/payroll/clientes/${clienteId}/servicios/`);
    return response.data;
  } catch (error) {
    // Si el endpoint no existe (404), devolver datos simulados
    if (error.response?.status === 404) {
      console.warn(`⚠️  Endpoint /payroll/clientes/${clienteId}/servicios/ no implementado. Devolviendo datos simulados.`);
      
      return [
        {
          id: 1,
          nombre: "Procesamiento de Nómina",
          tipo: "payroll",
          estado: "activo",
          fecha_contratacion: "2023-01-15",
          descripcion: "Procesamiento mensual de nómina completa"
        },
        {
          id: 2,
          nombre: "Liquidaciones",
          tipo: "liquidaciones",
          estado: "activo",
          fecha_contratacion: "2023-01-15",
          descripcion: "Cálculo y emisión de liquidaciones finales"
        },
        {
          id: 3,
          nombre: "Reportes RRHH",
          tipo: "rrhh",
          estado: "activo",
          fecha_contratacion: "2023-06-01",
          descripcion: "Informes y reportes de recursos humanos"
        }
      ];
    }
    throw error;
  }
};

/**
 * Obtiene el estado actual de los procesos de payroll del cliente
 */
export const obtenerEstadoProcesosPayrollCliente = async (clienteId) => {
  const response = await api.get(`/payroll/clientes/${clienteId}/estado-procesos/`);
  return response.data;
};

/**
 * Crea un nuevo cierre de nómina para un cliente
 */
export const crearCierrePayrollCliente = async (clienteId, datosCierre) => {
  const response = await api.post(`/payroll/clientes/${clienteId}/cierres/`, datosCierre);
  return response.data;
};

// ==================== FUNCIONES ESPECÍFICAS PARA CREAR CIERRE ====================

/**
 * Obtiene un cierre mensual específico de payroll (para verificar si existe)
 * Equivalente a obtenerCierreMensual de contabilidad
 */
export const obtenerCierreMensualPayroll = async (clienteId, periodo) => {
  try {
    // Buscar cierre por cliente y período usando query parameters
    const response = await api.get(`/payroll/cierres/`, {
      params: {
        cliente: clienteId,
        periodo: periodo
      }
    });
    
    // Si encontramos cierres, devolver el primero (debería ser único por cliente+período)
    if (response.data && response.data.length > 0) {
      return response.data[0];
    }
    
    // No existe cierre para este período
    return null;
  } catch (error) {
    console.error('Error buscando cierre payroll:', error);
    throw error;
  }
};

/**
 * Crea un nuevo cierre mensual de payroll
 * Equivalente a crearCierreMensual de contabilidad
 */
export const crearCierreMensualPayroll = async (clienteId, periodo) => {
  try {
    console.log('🚀 Creando cierre payroll:', { clienteId, periodo });
    
    const response = await api.post(`/payroll/cierres/`, {
      cliente: parseInt(clienteId),
      periodo: periodo
    });
    
    console.log('✅ Cierre creado exitosamente:', response.data);
    return response.data;
  } catch (error) {
    console.error('❌ Error creando cierre payroll:', error);
    throw error;
  }
};

// ==================== FUNCIONES DE UTILIDAD ====================

/**
 * Registra actividad del usuario en el módulo de payroll para tracking
 */
export const registrarActividadPayroll = async (clienteId, accion, detalles = {}) => {
  const response = await api.post(`/payroll/clientes/${clienteId}/registrar-actividad/`, {
    accion,
    detalles,
    timestamp: new Date().toISOString()
  });
  return response.data;
};

/**
 * Exporta datos de payroll del cliente en formato Excel/CSV
 */
export const exportarDatosPayrollCliente = async (clienteId, formato = 'excel', filtros = {}) => {
  const response = await api.post(`/payroll/clientes/${clienteId}/exportar/`, {
    formato,
    filtros
  }, {
    responseType: 'blob' // Para descargar archivos
  });
  return response.data;
};
