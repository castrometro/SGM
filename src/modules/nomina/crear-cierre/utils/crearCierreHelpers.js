// src/modules/nomina/crear-cierre/utils/crearCierreHelpers.js

/**
 * Normaliza una cadena removiendo acentos y convirtiendo a minúsculas
 */
const normalizar = (str) => {
  if (!str) return '';
  return str.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
};

/**
 * Valida si el usuario tiene acceso al área de Nómina
 * @param {Object} usuario - Datos del usuario desde localStorage
 * @returns {boolean} true si tiene acceso, false si no
 */
export const validarAccesoNomina = (usuario) => {
  if (!usuario) return false;
  
  // Gerente tiene acceso a todo
  if (usuario.tipo_usuario === 'Gerente') return true;
  
  // Verificar si tiene áreas asignadas
  if (usuario.areas && Array.isArray(usuario.areas)) {
    return usuario.areas.some(area => {
      const areaNombre = typeof area === 'string' ? area : area.nombre;
      return normalizar(areaNombre) === 'nomina';
    });
  }
  
  // Fallback: verificar area_asignada (formato antiguo)
  if (usuario.area_asignada) {
    return normalizar(usuario.area_asignada) === 'nomina';
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
 * @param {Array} tareas - Array de tareas
 * @returns {Object} {valido: boolean, error: string}
 */
export const validarFormulario = (periodo, tareas) => {
  if (!periodo || periodo.trim() === '') {
    return {
      valido: false,
      error: 'Debes seleccionar el periodo'
    };
  }
  
  if (!tareas || tareas.length === 0) {
    return {
      valido: false,
      error: 'Debes agregar al menos una tarea'
    };
  }
  
  const tareasSinDescripcion = tareas.some(t => !t.descripcion || t.descripcion.trim() === '');
  if (tareasSinDescripcion) {
    return {
      valido: false,
      error: 'Todas las tareas deben tener descripción'
    };
  }
  
  return {
    valido: true,
    error: null
  };
};
