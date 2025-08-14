import { useMemo } from 'react';

/**
 * Hook para obtener estadísticas y información específica de payroll
 */
export const usePayrollInfo = (usuario) => {
  return useMemo(() => {
    const tienePayroll = usuario?.areas?.some(area => area.nombre === "Payroll");
    
    if (!tienePayroll) {
      return null;
    }

    // Aquí podrías agregar lógica para obtener estadísticas de payroll
    // Por ahora retornamos información básica
    return {
      tieneAcceso: true,
      totalEmpleados: 0, // Se actualizará con datos reales
      nominasPendientes: 0, // Se actualizará con datos reales
      ultimoProceso: null, // Se actualizará con datos reales
      estadisticas: {
        empleadosActivos: 0,
        cierresDelMes: 0,
        procesosEnCurso: 0
      }
    };
  }, [usuario]);
};

/**
 * Hook para determinar qué acciones de payroll puede realizar el usuario
 */
export const usePayrollPermissions = (usuario) => {
  return useMemo(() => {
    const tienePayroll = usuario?.areas?.some(area => area.nombre === "Payroll");
    
    if (!tienePayroll) {
      return {
        puedeVerEmpleados: false,
        puedeProcesarNomina: false,
        puedeConfigurar: false,
        puedeVerReportes: false
      };
    }

    const tipoUsuario = usuario.tipo_usuario;

    return {
      puedeVerEmpleados: true,
      puedeProcesarNomina: ['analista', 'supervisor', 'gerente'].includes(tipoUsuario),
      puedeConfigurar: ['gerente'].includes(tipoUsuario),
      puedeVerReportes: ['supervisor', 'gerente'].includes(tipoUsuario),
      puedeVerAnalytics: ['gerente'].includes(tipoUsuario),
      puedeGestionarEmpleados: ['gerente'].includes(tipoUsuario)
    };
  }, [usuario]);
};
