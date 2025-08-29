import { useCallback } from 'react';

/**
 * Hook personalizado para manejar el estado del cierre de nómina
 * Basado en el estado del cierre en BD como single source of truth
 * @param {Object} cierre - Datos del cierre recibidos del componente padre
 */
const useCierreNomina = (cierre) => {

  // 🎯 MAPEO DE ESTADOS DEL CIERRE A SECCIONES HABILITADAS
  // 🎯 NUEVA ARQUITECTURA DE FASES - MAPEO: estado_cierre -> fases
const ARQUITECTURA_FASES = {
  // 📌 MAPEO DE ESTADOS ACTUALES A NUEVAS FASES (Case-insensitive)
  'Pendiente': 'pendiente',
  'pendiente': 'pendiente', // ← AGREGADO: variación minúscula
  'Cargando Archivos': 'fase_1_archivos',
  'cargando archivos': 'fase_1_archivos', // ← AGREGADO
  'Archivos Completos': 'fase_1_archivos', 
  'archivos completos': 'fase_1_archivos', // ← AGREGADO
  'Verificacion de Datos': 'fase_2_consolidacion',
  'verificacion de datos': 'fase_2_consolidacion', // ← AGREGADO
  'Verificado Sin Discrepancias': 'fase_2_consolidacion',
  'verificado sin discrepancias': 'fase_2_consolidacion', // ← AGREGADO
  'Datos Consolidados': 'fase_3_verificacion',
  'datos consolidados': 'fase_3_verificacion', // ← AGREGADO
  'Con Discrepancias': 'fase_3_verificacion',
  'con discrepancias': 'fase_3_verificacion', // ← AGREGADO
  'Con Incidencias': 'fase_4_incidencias',
  'con incidencias': 'fase_4_incidencias', // ← AGREGADO
  'Incidencias Resueltas': 'fase_4_incidencias',
  'incidencias resueltas': 'fase_4_incidencias', // ← AGREGADO
  'Requiere Recarga de Archivos': 'requiere_recarga',
  'requiere recarga de archivos': 'requiere_recarga', // ← AGREGADO
  'Validación Final': 'finalizado',
  'validacion final': 'finalizado', // ← AGREGADO
  'Finalizado': 'finalizado',
  'finalizado': 'finalizado' // ← AGREGADO
};

// 🎯 DEFINICIÓN DE FASES Y SECCIONES HABILITADAS
const obtenerSeccionesHabilitadas = (estado_cierre) => {
  // Manejar casos null/undefined
  if (!estado_cierre) {
    console.log(`🔄 [useCierreNomina] Estado nulo/undefined, usando 'pendiente' por defecto`);
    estado_cierre = 'pendiente';
  }
  
  // Convertir estado actual a nueva fase
  const fase = ARQUITECTURA_FASES[estado_cierre] || ARQUITECTURA_FASES[estado_cierre?.toLowerCase()] || 'pendiente';
  
  console.log(`🔄 [useCierreNomina] Estado recibido: "${estado_cierre}" → Fase mapeada: "${fase}"`);
  
  // Debugging adicional si no encuentra el mapeo
  if (!ARQUITECTURA_FASES[estado_cierre] && !ARQUITECTURA_FASES[estado_cierre?.toLowerCase()]) {
    console.warn(`⚠️ [useCierreNomina] Estado desconocido: "${estado_cierre}", usando 'pendiente' como fallback`);
  }
  
  switch(fase) {
    case 'pendiente':
    case 'fase_1_archivos':
      return {
        archivosTalana: true,
        archivosAnalista: false,
        verificadorDatos: false,
        incidencias: false
      };
    
    case 'fase_2_consolidacion':
      return {
        archivosTalana: true,
        archivosAnalista: true,
        verificadorDatos: false,
        incidencias: false
      };
    
    case 'fase_3_verificacion':
      return {
        archivosTalana: true,
        archivosAnalista: true,
        verificadorDatos: true,
        incidencias: false
      };
    
    case 'fase_4_incidencias':
      return {
        archivosTalana: true,
        archivosAnalista: true,
        verificadorDatos: true,
        incidencias: true
      };
    
    case 'finalizado':
      return {
        archivosTalana: true,
        archivosAnalista: true,
        verificadorDatos: true,
        incidencias: true
      };
    
    case 'requiere_recarga':
      // TODO: Implementar lógica para determinar qué fase necesita recarga
      return {
        archivosTalana: true,
        archivosAnalista: false,
        verificadorDatos: false,
        incidencias: false
      };
    
    default:
      console.warn(`⚠️ [useCierreNomina] Fase desconocida: "${fase}", usando pendiente`);
      return {
        archivosTalana: true,
        archivosAnalista: false,
        verificadorDatos: false,
        incidencias: false
      };
  }
};

  // 🎯 CALCULAR SECCIONES HABILITADAS BASADO EN ESTADO ACTUAL
  const seccionesHabilitadas = cierre?.estado 
    ? obtenerSeccionesHabilitadas(cierre.estado)
    : obtenerSeccionesHabilitadas('pendiente'); // ← DEFAULT: pendiente si no hay datos

  // 🎯 FUNCIÓN HELPER PARA VERIFICAR SI UNA SECCIÓN ESTÁ HABILITADA
  const estaSeccionHabilitada = useCallback((nombreSeccion) => {
    return seccionesHabilitadas[nombreSeccion] || false;
  }, [seccionesHabilitadas]);

  return {
    seccionesHabilitadas,
    estaSeccionHabilitada
  };
};

export default useCierreNomina;
