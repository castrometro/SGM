// src/modules/contabilidad/crear-cierre/constants/crearCierre.constants.js

/**
 * Mensajes del módulo de Crear Cierre de Contabilidad
 */
export const MENSAJES = {
  // Títulos
  TITULO: 'Crear Cierre Mensual de Contabilidad',
  
  // Validaciones
  ERROR_PERIODO: 'Debes seleccionar el periodo',
  ERROR_CIERRE_EXISTENTE: 'Ya existe un cierre para este periodo',
  ERROR_CREANDO: 'Error creando el cierre',
  
  // Confirmaciones
  CONFIRMAR_CREACION: '¿Crear cierre para el periodo {periodo}?',
  
  // Estados de carga
  CARGANDO_CLIENTE: 'Cargando datos del cliente...',
  CREANDO: 'Creando...',
  CREAR: 'Crear Cierre',
  
  // Acceso
  SIN_ACCESO: 'No tienes permisos para crear cierres de Contabilidad',
  ERROR_VALIDANDO: 'Error al validar permisos'
};

/**
 * Labels de formulario
 */
export const LABELS = {
  PERIODO: 'Periodo (AAAA-MM)',
  PLACEHOLDER_PERIODO: 'Selecciona el mes y año'
};

/**
 * Áreas de trabajo
 */
export const AREAS = {
  CONTABILIDAD: 'Contabilidad'
};
