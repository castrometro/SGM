/**
 * Utilidades para el manejo de estados de incidencias
 * Basado en los estados reales del modelo Django
 */

// Estados basados en models.py EstadoIncidencia
export const ESTADOS_INCIDENCIA = {
  PENDIENTE: 'pendiente',
  RESUELTA_ANALISTA: 'resuelta_analista', 
  APROBADA_SUPERVISOR: 'aprobada_supervisor',
  RECHAZADA_SUPERVISOR: 'rechazada_supervisor',
  RE_RESUELTA: 're_resuelta',
  RESOLUCION_SUPERVISOR_PENDIENTE: 'resolucion_supervisor_pendiente'
};

export const ESTADOS_DISPLAY = {
  [ESTADOS_INCIDENCIA.PENDIENTE]: 'Pendiente de Resolución',
  [ESTADOS_INCIDENCIA.RESUELTA_ANALISTA]: 'Resuelta por Analista',
  [ESTADOS_INCIDENCIA.APROBADA_SUPERVISOR]: 'Aprobada por Supervisor', 
  [ESTADOS_INCIDENCIA.RECHAZADA_SUPERVISOR]: 'Rechazada por Supervisor',
  [ESTADOS_INCIDENCIA.RE_RESUELTA]: 'Re-resuelta por Analista',
  [ESTADOS_INCIDENCIA.RESOLUCION_SUPERVISOR_PENDIENTE]: 'Confirmación de desaparición pendiente'
};

/**
 * Obtiene el estado real de una incidencia basado en sus resoluciones
 * @param {Object} incidencia - La incidencia con sus resoluciones
 * @returns {Object} - { estado, display }
 */
export const obtenerEstadoReal = (incidencia) => {
  const resoluciones = incidencia.resoluciones || [];
  
  // 1) Priorizar el estado directo del backend si existe y es válido
  const estadosValidos = new Set(Object.values(ESTADOS_INCIDENCIA));
  const estadoDirecto = incidencia?.estado;
  if (estadoDirecto && estadosValidos.has(estadoDirecto)) {
    return {
      estado: estadoDirecto,
      display: ESTADOS_DISPLAY[estadoDirecto] ?? estadoDirecto
    };
  }

  // 2) Si no hay estado directo, inferir desde resoluciones
  if (resoluciones.length === 0) {
    return {
      estado: ESTADOS_INCIDENCIA.PENDIENTE,
      display: ESTADOS_DISPLAY[ESTADOS_INCIDENCIA.PENDIENTE]
    };
  }

  // Ordenar por fecha y obtener la última resolución (copia defensiva)
  const ultimaResolucion = [...resoluciones].sort((a, b) => 
    new Date(b.fecha_resolucion) - new Date(a.fecha_resolucion)
  )[0];

  switch (ultimaResolucion.tipo_resolucion) {
    case 'aprobacion':
      return {
        estado: ESTADOS_INCIDENCIA.APROBADA_SUPERVISOR,
        display: ESTADOS_DISPLAY[ESTADOS_INCIDENCIA.APROBADA_SUPERVISOR]
      };
    case 'rechazo':
      return {
        estado: ESTADOS_INCIDENCIA.RECHAZADA_SUPERVISOR,
        display: ESTADOS_DISPLAY[ESTADOS_INCIDENCIA.RECHAZADA_SUPERVISOR]
      };
    case 'consulta':
    case 'justificacion':
      return {
        estado: ESTADOS_INCIDENCIA.RESUELTA_ANALISTA,
        display: ESTADOS_DISPLAY[ESTADOS_INCIDENCIA.RESUELTA_ANALISTA]
      };
    default:
      return {
        estado: ESTADOS_INCIDENCIA.PENDIENTE,
        display: ESTADOS_DISPLAY[ESTADOS_INCIDENCIA.PENDIENTE]
      };
  }
};

/**
 * Calcula los contadores de incidencias por estado real
 * @param {Array} incidencias - Array de incidencias con resoluciones
 * @returns {Object} - Contadores por estado
 */
export const calcularContadoresEstados = (incidencias) => {
  const contadores = {
    pendiente: 0,
    resuelta_analista: 0,
    aprobada_supervisor: 0,
    rechazada_supervisor: 0,
    re_resuelta: 0,
    resolucion_supervisor_pendiente: 0
  };

  incidencias.forEach(incidencia => {
    const { estado } = obtenerEstadoReal(incidencia);
    if (contadores[estado] == null) {
      // Mapear cualquier estado desconocido a pendiente
      contadores.pendiente++;
    } else {
      contadores[estado]++;
    }
  });

  return contadores;
};

/**
 * Calcula el progreso de resolución de incidencias
 * @param {Array} incidencias - Array de incidencias con resoluciones
 * @returns {Object} - Progreso calculado
 */
export const calcularProgresoIncidencias = (incidencias) => {
  const contadores = calcularContadoresEstados(incidencias);
  
  return {
    aprobadas: contadores.aprobada_supervisor,
    pendientes: contadores.pendiente + contadores.resuelta_analista + (contadores.resolucion_supervisor_pendiente || 0),
    rechazadas: contadores.rechazada_supervisor,
    total: incidencias.length
  };
};
