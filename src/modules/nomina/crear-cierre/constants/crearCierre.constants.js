// src/modules/nomina/crear-cierre/constants/crearCierre.constants.js

/**
 * Mensajes del módulo de Crear Cierre de Nómina
 */
export const MENSAJES = {
  // Títulos
  TITULO: 'Crear Cierre Mensual de Nómina',
  
  // Validaciones
  ERROR_PERIODO: 'Debes seleccionar el periodo',
  ERROR_TAREAS: 'Debes agregar al menos una tarea y que todas tengan descripción',
  ERROR_CIERRE_EXISTENTE: 'Ya existe un cierre para este periodo',
  ERROR_CREANDO: 'Error creando el cierre',
  
  // Confirmaciones
  CONFIRMAR_CREACION: '¿Crear cierre para el periodo {periodo}? Una vez creado, la lista de tareas no podrá ser editada.',
  
  // Estados de carga
  CARGANDO_CLIENTE: 'Cargando datos del cliente...',
  CREANDO: 'Creando...',
  CREAR: 'Crear Cierre',
  
  // Checklist
  TITULO_CHECKLIST: 'Tareas a comprometer para este cierre',
  AGREGAR_TAREA: '+ Agregar Tarea',
  PLACEHOLDER_TAREA: 'Nombre Tarea',
  
  // Acceso
  SIN_ACCESO: 'No tienes permisos para crear cierres de Nómina',
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
  NOMINA: 'Nomina'
};
