// src/api/payroll/migration-guide.js

/**
 * Guía de Migración de Nómina API → Payroll API
 * Este archivo mapea las funciones de la API antigua a la nueva estructura modular
 */

/**
 * MAPEO DE FUNCIONES
 * 
 * API Antigua (nomina.js) → API Nueva (payroll)
 */

export const MIGRATION_MAP = {
  // ========== CIERRES ==========
  'obtenerResumenNomina': 'payroll.closures.getClientClosuresSummary',
  'obtenerCierreMensual': 'payroll.closures.getMonthlyClosure',
  'crearCierreMensual': 'payroll.closures.createMonthlyClosure',
  'obtenerCierreNominaPorId': 'payroll.closures.getClosureById',
  'actualizarCierreNomina': 'payroll.closures.updateClosure',
  'eliminarCierreNomina': 'payroll.closures.deleteClosure',
  'actualizarEstadoCierreNomina': 'payroll.closures.updateClosureState',
  'consolidarDatosTalana': 'payroll.closures.consolidateTalanaData',
  'consultarEstadoTarea': 'payroll.closures.getTaskStatus',
  'finalizarCierre': 'payroll.closures.finalizeClosure',
  'obtenerCierresCliente': 'payroll.closures.getClientClosures',
  'obtenerCierresNomina': 'payroll.closures.getAllClosures',

  // ========== INCIDENCIAS ==========
  'obtenerIncidenciasCierre': 'payroll.incidents.getClosureIncidents',
  'generarIncidenciasCierre': 'payroll.incidents.generateClosureIncidents',
  'limpiarIncidenciasCierre': 'payroll.incidents.clearClosureIncidents',
  'obtenerResumenIncidencias': 'payroll.incidents.getIncidentsSummary',
  'cambiarEstadoIncidencia': 'payroll.incidents.changeIncidentState',
  'asignarUsuarioIncidencia': 'payroll.incidents.assignUserToIncident',
  'obtenerIncidencia': 'payroll.incidents.getIncident',
  'previewIncidenciasCierre': 'payroll.incidents.previewClosureIncidents',
  'devLimpiarIncidencias': 'payroll.incidents.devClearIncidents',
  'obtenerEstadoIncidenciasCierre': 'payroll.incidents.getClosureIncidentsState',
  'lanzarGeneracionIncidencias': 'payroll.incidents.launchIncidentsGeneration',
  'obtenerIncidenciasMiTurno': 'payroll.incidents.getMyTurnIncidents',
  'obtenerEstadisticasIncidencias': 'payroll.incidents.getIncidentsStatistics',
  'exportarIncidenciasExcel': 'payroll.incidents.exportIncidentsToExcel',
  'obtenerCategoriasIncidencias': 'payroll.incidents.getIncidentCategories',
  'obtenerProgresoIncidencias': 'payroll.incidents.getIncidentsProgress',
  'aprobarIncidencia': 'payroll.incidents.approveIncident',
  'rechazarIncidencia': 'payroll.incidents.rejectIncident',
  'consultarIncidencia': 'payroll.incidents.consultIncident',

  // ========== ANÁLISIS DE DATOS ==========
  'iniciarAnalisisDatos': 'payroll.analysis.startDataAnalysis',
  'obtenerAnalisisDatos': 'payroll.analysis.getDataAnalysis',
  'obtenerAnalisisCompletoTemporal': 'payroll.analysis.getCompleteTemporalAnalysis',
  'obtenerIncidenciasVariacion': 'payroll.analysis.getSalaryVariationIncidents',
  'justificarIncidenciaVariacion': 'payroll.analysis.justifySalaryVariationIncident',
  'aprobarIncidenciaVariacion': 'payroll.analysis.approveSalaryVariationIncident',
  'rechazarIncidenciaVariacion': 'payroll.analysis.rejectSalaryVariationIncident',
  'obtenerResumenIncidenciasVariacion': 'payroll.analysis.getSalaryVariationsSummary',
  'obtenerResumenVariaciones': 'payroll.analysis.getVariationsSummary',

  // ========== RESOLUCIONES ==========
  'crearResolucionIncidencia': 'payroll.resolutions.createIncidentResolution',
  'obtenerHistorialIncidencia': 'payroll.resolutions.getIncidentResolutionHistory',
  'obtenerResolucionesUsuario': 'payroll.resolutions.getUserResolutions',

  // ========== ARCHIVOS ==========
  'subirLibroRemuneraciones': 'payroll.files.uploadPayrollBook',
  'obtenerEstadoLibroRemuneraciones': 'payroll.files.getPayrollBookStatus',
  'procesarLibroRemuneraciones': 'payroll.files.processPayrollBook',
  'obtenerConceptosLibroRemuneraciones': 'payroll.files.getPayrollBookConcepts',
  'guardarClasificacionesLibroRemuneraciones': 'payroll.concepts.savePayrollBookClassifications',
  'obtenerProgresoClasificacionRemu': 'payroll.concepts.getRemunerationClassificationProgress',
  'obtenerEstadoMovimientosMes': 'payroll.files.getMonthlyMovementsStatus',
  'subirMovimientosMes': 'payroll.files.uploadMonthlyMovements',
  'subirArchivoAnalista': 'payroll.files.uploadAnalystFile',
  'obtenerEstadoArchivoAnalista': 'payroll.files.getAnalystFileStatus',
  'reprocesarArchivoAnalista': 'payroll.files.reprocessAnalystFile',
  'subirArchivoNovedades': 'payroll.files.uploadNoveltiesFile',
  'obtenerEstadoArchivoNovedades': 'payroll.files.getNoveltiesFileStatus',
  'reprocesarArchivoNovedades': 'payroll.files.reprocessNoveltiesFile',
  'obtenerHeadersNovedades': 'payroll.files.getNoveltiesFileHeaders',
  'mapearHeadersNovedades': 'payroll.files.mapNoveltiesHeaders',
  'procesarFinalNovedades': 'payroll.files.processFinalNovelties',
  'obtenerConceptosRemuneracionNovedades': 'payroll.files.getRemunerationConceptsForNovelties',
  'obtenerEstadoUploadLogNomina': 'payroll.files.getUploadLogStatus',
  'eliminarLibroRemuneraciones': 'payroll.files.deletePayrollBook',
  'eliminarMovimientosMes': 'payroll.files.deleteMonthlyMovements',
  'eliminarArchivoAnalista': 'payroll.files.deleteAnalystFile',
  'eliminarArchivoNovedades': 'payroll.files.deleteNoveltiesFile',
  'obtenerProgresoClasificacionTodosLosSets': 'payroll.files.getAllSetsClassificationProgress',

  // ========== PLANTILLAS ==========
  'descargarPlantillaLibroRemuneraciones': 'payroll.files.downloadPayrollBookTemplate',
  'descargarPlantillaMovimientosMes': 'payroll.files.downloadMonthlyMovementsTemplate',
  'descargarPlantillaFiniquitos': 'payroll.files.downloadSettlementsTemplate',
  'descargarPlantillaIncidencias': 'payroll.files.downloadIncidentsTemplate',
  'descargarPlantillaIngresos': 'payroll.files.downloadEntriesTemplate',
  'descargarPlantillaNovedades': 'payroll.files.downloadNoveltiesTemplate',

  // ========== CONCEPTOS ==========
  'obtenerClasificacionesCliente': 'payroll.concepts.getClientClassifications',
  'guardarConceptosRemuneracion': 'payroll.concepts.saveRemunerationConcepts',
  'eliminarConceptoRemuneracion': 'payroll.concepts.deleteRemunerationConcept',
  'obtenerConceptosRemuneracionPorCierre': 'payroll.concepts.getRemunerationConceptsByClosure',

  // ========== DISCREPANCIAS ==========
  'obtenerDiscrepanciasCierre': 'payroll.discrepancies.getClosureDiscrepancies',
  'generarDiscrepanciasCierre': 'payroll.discrepancies.generateClosureDiscrepancies',
  'obtenerResumenDiscrepancias': 'payroll.discrepancies.getDiscrepanciesSummary',
  'obtenerEstadoDiscrepanciasCierre': 'payroll.discrepancies.getClosureDiscrepanciesState',
  'limpiarDiscrepanciasCierre': 'payroll.discrepancies.clearClosureDiscrepancies',

  // ========== VISUALIZACIÓN ==========
  'obtenerLibroRemuneraciones': 'payroll.reports.getClosureDashboardData', // Adaptado
  'obtenerMovimientosMes': 'payroll.reports.getClosureDashboardData', // Adaptado
};

/**
 * FUNCIONES DE MIGRACIÓN ASISTIDA
 */

/**
 * Wrapper para mantener compatibilidad temporal con la API antigua
 * @deprecated Usar la nueva API directamente
 */
export const createLegacyWrapper = (payrollApi) => {
  return {
    // Cierres
    obtenerResumenNomina: (clienteId) => payrollApi.closures.getClientClosuresSummary(clienteId),
    obtenerCierreMensual: (clienteId, periodo) => payrollApi.closures.getMonthlyClosure(clienteId, periodo),
    crearCierreMensual: (clienteId, periodo, checklist) => payrollApi.closures.createMonthlyClosure(clienteId, periodo, checklist),
    
    // Incidencias
    obtenerIncidenciasCierre: (cierreId, filtros) => payrollApi.incidents.getClosureIncidents(cierreId, filtros),
    generarIncidenciasCierre: (cierreId, clasificaciones) => payrollApi.incidents.generateClosureIncidents(cierreId, clasificaciones),
    
    // Archivos
    subirLibroRemuneraciones: (cierreId, archivo) => payrollApi.files.uploadPayrollBook(cierreId, archivo),
    obtenerEstadoLibroRemuneraciones: (cierreId) => payrollApi.files.getPayrollBookStatus(cierreId),
    
    // ... agregar más según necesidad
  };
};

/**
 * Guía de migración paso a paso
 */
export const MIGRATION_STEPS = {
  step1: {
    title: "Instalación de la nueva API",
    description: "Importar los módulos de payroll",
    code: `
// Antes
import { obtenerResumenNomina, obtenerCierreMensual } from '@/api/nomina';

// Después
import { closures } from '@/api/payroll';
// o
import payroll from '@/api/payroll';
    `
  },
  
  step2: {
    title: "Actualización de llamadas a funciones",
    description: "Cambiar nombres de funciones y estructura",
    code: `
// Antes
const resumen = await obtenerResumenNomina(clienteId);
const cierre = await obtenerCierreMensual(clienteId, periodo);

// Después
const resumen = await payroll.closures.getClientClosuresSummary(clienteId);
const cierre = await payroll.closures.getMonthlyClosure(clienteId, periodo);
    `
  },
  
  step3: {
    title: "Manejo de respuestas",
    description: "Adaptar el manejo de respuestas si es necesario",
    code: `
// La estructura de respuestas debería ser similar
// pero verificar campos específicos que puedan haber cambiado
    `
  },
  
  step4: {
    title: "Testing",
    description: "Probar todas las funcionalidades migradas",
    code: `
// Ejecutar tests para verificar que todo funciona correctamente
// Comparar respuestas entre API antigua y nueva
    `
  }
};

/**
 * Funciones no migradas (requieren atención especial)
 */
export const FUNCTIONS_PENDING_MIGRATION = [
  'obtenerLibroRemuneraciones', // Necesita adaptación específica
  'obtenerMovimientosMes', // Necesita adaptación específica
  'obtenerIncidenciasConsolidadas', // Backend específico
  'obtenerIncidenciasConsolidadasOptimizado', // Backend específico
  'obtenerHistorialIncidencias', // Posible conflicto de nombres
  // ... otros que requieren análisis específico
];

/**
 * Nuevas funcionalidades disponibles solo en Payroll API
 */
export const NEW_FEATURES = [
  'payroll.analysis.compareClosures',
  'payroll.analysis.getSalaryTrends',
  'payroll.analysis.detectAnomalousPatterns',
  'payroll.discrepancies.analyzeDiscrepancyPatterns',
  'payroll.discrepancies.validateDataConsistency',
  'payroll.reports.generateComparativeReport',
  'payroll.reports.generateComplianceReport',
  'payroll.reports.generateAuditReport',
  'payroll.concepts.suggestConceptClassifications',
  'payroll.concepts.validateConceptConsistency',
  'payroll.resolutions.getResolutionTimeline',
  'payroll.resolutions.transferTurn',
  // ... muchas más funcionalidades nuevas
];

/**
 * Utilidad para verificar migración
 */
export const checkMigrationStatus = (oldFunctionName) => {
  const newFunction = MIGRATION_MAP[oldFunctionName];
  if (newFunction) {
    return {
      status: 'migrated',
      newFunction,
      message: `Usar: ${newFunction}`
    };
  }
  
  if (FUNCTIONS_PENDING_MIGRATION.includes(oldFunctionName)) {
    return {
      status: 'pending',
      message: 'Esta función requiere migración manual'
    };
  }
  
  return {
    status: 'unknown',
    message: 'Función no encontrada en el mapeo'
  };
};
