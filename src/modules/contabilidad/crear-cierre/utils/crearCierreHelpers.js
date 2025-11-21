// src/modules/contabilidad/crear-cierre/utils/crearCierreHelpers.js

/**
 * Normaliza una cadena removiendo acentos y convirtiendo a minúsculas
 */
const normalizar = (str) => {
  if (!str) return '';
  return str.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
};

/**
 * Valida si el usuario tiene acceso al área de Contabilidad
 * @param {Object} usuario - Datos del usuario desde localStorage
 * @returns {boolean} true si tiene acceso, false si no
 */
export const validarAccesoContabilidad = (usuario) => {
  if (!usuario) return false;
  
  // Gerente tiene acceso a todo
  if (usuario.tipo_usuario === 'Gerente') return true;
  
  // Verificar si tiene áreas asignadas
  if (usuario.areas && Array.isArray(usuario.areas)) {
    return usuario.areas.some(area => {
      const areaNombre = typeof area === 'string' ? area : area.nombre;
      return normalizar(areaNombre) === 'contabilidad';
    });
  }
  
  // Fallback: verificar area_asignada (formato antiguo)
  if (usuario.area_asignada) {
    return normalizar(usuario.area_asignada) === 'contabilidad';
  }
  
  return false;
};

/**
 * Formatea el periodo para mostrar en mensajes de confirmación
 * @param {string} periodo - Periodo en formato AAAA-MM
 * @returns {string} Periodo formateado para mostrar
 */
export const formatearPeriodoConfirmacion = (periodo) => {
  if (!periodo) return '';
  
  const [anio, mes] = periodo.split('-');
  const meses = [
    'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
  ];
  
  const nombreMes = meses[parseInt(mes, 10) - 1];
  return `${nombreMes} ${anio}`;
};

/**
 * Valida que el formulario esté completo
 * @param {string} periodo - Periodo seleccionado
 * @returns {Object} {valido: boolean, error: string}
 */
export const validarFormulario = (periodo) => {
  if (!periodo || periodo.trim() === '') {
    return {
      valido: false,
      error: 'Debes seleccionar el periodo'
    };
  }
  
  return {
    valido: true,
    error: null
  };
};
