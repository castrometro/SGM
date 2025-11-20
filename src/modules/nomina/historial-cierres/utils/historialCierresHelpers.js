// src/modules/nomina/historial-cierres/utils/historialCierresHelpers.js

/**
 * Normaliza una cadena removiendo acentos y convirtiendo a minúsculas
 */
const normalizar = (str) => {
  if (!str) return '';
  return str.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
};

/**
 * Valida que el usuario tenga acceso al área de Nómina
 */
export const validarAccesoNomina = (userData) => {
  if (!userData || !userData.areas) return false;
  
  return userData.areas.some(area => {
    const areaNombre = typeof area === 'string' ? area : area.nombre;
    return normalizar(areaNombre) === 'nomina';
  });
};

/**
 * Helper para determinar si un cierre puede ser finalizado
 */
export const puedeFinalizarse = (cierre) => {
  return cierre.estado === 'sin_incidencias';
};

/**
 * Filtra cierres por estado
 */
export const filtrarCierresPorEstado = (cierres, filtroEstado) => {
  if (filtroEstado === "todos") return cierres;
  
  if (filtroEstado === "procesando") {
    return cierres.filter(c => c.estado === 'procesando' || c.estado === 'generando_reportes');
  }
  
  if (filtroEstado === "finalizado") {
    return cierres.filter(c => 
      c.estado === 'finalizado' || c.estado === 'completado' || c.estado === 'sin_incidencias'
    );
  }
  
  return cierres.filter(c => c.estado === filtroEstado);
};

/**
 * Calcula estadísticas de cierres
 */
export const calcularEstadisticas = (cierres) => {
  return {
    total: cierres.length,
    finalizados: cierres.filter(c => 
      c.estado === 'finalizado' || c.estado === 'completado'
    ).length,
    enProceso: cierres.filter(c => 
      c.estado === 'procesando' || c.estado === 'generando_reportes'
    ).length,
    conIncidencias: cierres.filter(c => 
      c.estado === 'con_incidencias'
    ).length,
  };
};
