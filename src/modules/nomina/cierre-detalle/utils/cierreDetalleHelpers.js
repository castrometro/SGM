// src/modules/nomina/cierre-detalle/utils/cierreDetalleHelpers.js

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
 * Obtiene el color del estado del cierre
 */
export const getEstadoColor = (estado) => {
  const colores = {
    'pendiente': 'yellow',
    'procesando': 'blue',
    'finalizado': 'green',
    'error': 'red',
    'generando_reportes': 'purple'
  };
  return colores[estado] || 'gray';
};

/**
 * Formatea el período del cierre (YYYY-MM) a formato legible
 */
export const formatearPeriodo = (periodo) => {
  if (!periodo) return '';
  const [año, mes] = periodo.split('-');
  const meses = [
    'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
  ];
  return `${meses[parseInt(mes) - 1]} ${año}`;
};

/**
 * Determina si un cierre puede ser finalizado
 */
export const puedeFinalizar = (cierre) => {
  if (!cierre) return false;
  return cierre.estado === 'procesando' && cierre.incidencias_count === 0;
};
