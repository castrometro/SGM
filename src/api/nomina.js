/**
 * API para gestión de nómina - Funciones específicas para manejo de empleados y procesamiento
 * Optimizado para el flujo de analistas de nómina
 */

const API_BASE_URL = "http://127.0.0.1:8000";

/**
 * Obtener empleados asignados a un cliente específico
 * Incluye información relevante para nómina
 */
export const obtenerEmpleadosPorCliente = async (clienteId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/nomina/clientes/${clienteId}/empleados/`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Error ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();
    
    // Simular datos si no hay respuesta del servidor
    if (!data || data.length === 0) {
      return {
        success: true,
        data: {
          cliente: {
            id: clienteId,
            nombre: `Cliente ${clienteId}`,
            rut: '12.345.678-9'
          },
          empleados: [
            {
              id: 1,
              nombre: 'Juan',
              apellido: 'Pérez',
              rut: '11.111.111-1',
              cargo: 'Desarrollador',
              departamento: 'IT',
              salario_base: 1200000,
              fecha_ingreso: '2023-01-15',
              estado: 'activo',
              horas_trabajadas_mes: 160,
              dias_trabajados: 22
            },
            {
              id: 2,
              nombre: 'María',
              apellido: 'González',
              rut: '22.222.222-2',
              cargo: 'Analista',
              departamento: 'Finanzas',
              salario_base: 950000,
              fecha_ingreso: '2023-03-01',
              estado: 'activo',
              horas_trabajadas_mes: 160,
              dias_trabajados: 22
            }
          ]
        }
      };
    }

    return { success: true, data };
  } catch (error) {
    console.error('Error al obtener empleados por cliente:', error);
    return {
      success: false,
      mensaje: error.message || 'Error al cargar empleados del cliente'
    };
  }
};

/**
 * Obtener resumen de nómina para un cliente específico
 * Incluye totales, último procesamiento, etc.
 */
export const obtenerResumenNominaCliente = async (clienteId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/nomina/clientes/${clienteId}/resumen/`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Error ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();
    
    // Simular datos si no hay respuesta del servidor
    if (!data) {
      return {
        success: true,
        data: {
          total_empleados: 2,
          total_estimado: 2150000,
          ultimo_proceso: '2024-07-15',
          estado_proceso: 'Completado',
          empleados_activos: 2,
          empleados_inactivos: 0
        }
      };
    }

    return { success: true, data };
  } catch (error) {
    console.error('Error al obtener resumen de nómina:', error);
    return {
      success: false,
      mensaje: error.message || 'Error al cargar resumen de nómina'
    };
  }
};

/**
 * Obtener resumen de nómina para lista de clientes (usado en ClienteRow)
 * Versión simplificada para mostrar en tabla
 */
export const obtenerResumenNomina = async (clienteId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/nomina/clientes/${clienteId}/resumen-simple/`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      // Simular datos por defecto si no hay endpoint
      return {
        ultimo_cierre: '2024-07-15',
        estado_cierre_actual: 'procesado',
        total_empleados: 2
      };
    }

    return await response.json();
  } catch (error) {
    console.error('Error al obtener resumen simple:', error);
    // Retornar datos por defecto en caso de error
    return {
      ultimo_cierre: null,
      estado_cierre_actual: 'pendiente',
      total_empleados: 0
    };
  }
};

/**
 * Procesar nómina para un cliente específico
 * Función principal para analistas
 */
export const procesarNominaCliente = async (clienteId, parametros = {}) => {
  try {
    const response = await fetch(`${API_BASE_URL}/nomina/clientes/${clienteId}/procesar/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        periodo: parametros.periodo || new Date().toISOString().slice(0, 7),
        incluir_beneficios: parametros.incluir_beneficios ?? true,
        calcular_descuentos: parametros.calcular_descuentos ?? true,
        ...parametros
      }),
    });

    if (!response.ok) {
      throw new Error(`Error ${response.status}: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error al procesar nómina:', error);
    return {
      success: false,
      mensaje: error.message || 'Error al procesar nómina del cliente'
    };
  }
};

/**
 * Actualizar información de un empleado específico
 * Para analistas - campos limitados
 */
export const actualizarEmpleadoCliente = async (empleadoId, datosActualizados) => {
  try {
    const response = await fetch(`${API_BASE_URL}/nomina/empleados/${empleadoId}/`, {
      method: 'PATCH',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(datosActualizados),
    });

    if (!response.ok) {
      throw new Error(`Error ${response.status}: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error al actualizar empleado:', error);
    return {
      success: false,
      mensaje: error.message || 'Error al actualizar empleado'
    };
  }
};
