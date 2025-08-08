// src/api/payroll/examples.js

/**
 * Ejemplos de uso de la API de Payroll
 * Este archivo demuestra cómo usar los diferentes módulos
 */

import payroll from './index';

// También se puede importar individualmente:
// import { closures, incidents, analysis, files } from './index';

/**
 * Ejemplo 1: Flujo completo de un cierre mensual
 */
export const ejemploFlujoCompleto = async (clientId, period) => {
  try {
    // 1. Crear o obtener cierre mensual
    let closure = await payroll.closures.getMonthlyClosure(clientId, period);
    
    if (!closure) {
      closure = await payroll.closures.createMonthlyClosure(clientId, period, {
        created_by: 'system',
        initial_status: 'pending'
      });
      console.log('✅ Cierre creado:', closure.id);
    }

    // 2. Subir archivos necesarios
    const payrollBookFile = document.getElementById('payroll-file').files[0];
    if (payrollBookFile) {
      const uploadResult = await payroll.files.uploadPayrollBook(closure.id, payrollBookFile);
      console.log('✅ Libro de remuneraciones subido:', uploadResult);
    }

    // 3. Procesar y clasificar datos
    const classificationProgress = await payroll.concepts.getAllSetsClassificationProgress(closure.id);
    console.log('📊 Progreso de clasificación:', classificationProgress);

    // 4. Generar incidencias
    const incidentsResult = await payroll.incidents.generateClosureIncidents(closure.id);
    console.log('🔍 Incidencias generadas:', incidentsResult);

    // 5. Realizar análisis automático
    const analysisResult = await payroll.analysis.startDataAnalysis(closure.id, 30);
    console.log('📈 Análisis iniciado:', analysisResult);

    // 6. Obtener resumen final
    const summary = await payroll.closures.getClientClosuresSummary(clientId);
    console.log('📋 Resumen final:', summary);

    return { closure, summary };
  } catch (error) {
    console.error('❌ Error en flujo completo:', error);
    throw error;
  }
};

/**
 * Ejemplo 2: Gestión de incidencias
 */
export const ejemploGestionIncidencias = async (closureId) => {
  try {
    // 1. Obtener incidencias del cierre
    const incidents = await payroll.incidents.getClosureIncidents(closureId);
    console.log('📋 Incidencias encontradas:', incidents.length);

    // 2. Procesar cada incidencia
    for (const incident of incidents) {
      if (incident.state === 'pending') {
        // Cambiar estado a en progreso
        await payroll.incidents.changeIncidentState(incident.id, 'in_progress');
        
        // Crear resolución
        await payroll.resolutions.createIncidentResolution(incident.id, {
          type: 'manual_review',
          description: 'Revisión manual requerida',
          assigned_to: 'current_user'
        });
      }
    }

    // 3. Obtener resumen actualizado
    const summary = await payroll.incidents.getIncidentsSummary(closureId);
    console.log('📊 Resumen de incidencias:', summary);

    return summary;
  } catch (error) {
    console.error('❌ Error en gestión de incidencias:', error);
    throw error;
  }
};

/**
 * Ejemplo 3: Análisis de variaciones salariales
 */
export const ejemploAnalisisVariaciones = async (closureId) => {
  try {
    // 1. Obtener variaciones salariales
    const variations = await payroll.analysis.getSalaryVariationIncidents(closureId, {
      threshold: 10, // Solo variaciones > 10%
      status: 'pending'
    });

    console.log('📈 Variaciones detectadas:', variations.length);

    // 2. Procesar variaciones significativas
    for (const variation of variations) {
      if (variation.percentage_change > 50) {
        // Variación muy alta, requiere justificación
        await payroll.analysis.justifySalaryVariationIncident(
          variation.id,
          'Variación significativa detectada, requiere revisión manual'
        );
      }
    }

    // 3. Generar reporte de variaciones
    const report = await payroll.reports.generateSalaryVariationsReport(closureId, {
      include_approved: false,
      threshold: 10
    });

    console.log('📋 Reporte generado:', report);
    return report;
  } catch (error) {
    console.error('❌ Error en análisis de variaciones:', error);
    throw error;
  }
};

/**
 * Ejemplo 4: Gestión de archivos y plantillas
 */
export const ejemploGestionArchivos = async (closureId) => {
  try {
    // 1. Descargar plantillas necesarias
    const templates = {
      payrollBook: payroll.files.downloadPayrollBookTemplate(),
      novelties: payroll.files.downloadNoveltiesTemplate(),
      settlements: payroll.files.downloadSettlementsTemplate()
    };

    console.log('📄 URLs de plantillas:', templates);

    // 2. Verificar estado de archivos subidos
    const payrollBookStatus = await payroll.files.getPayrollBookStatus(closureId);
    const noveltiesStatus = await payroll.files.getNoveltiesFileStatus(closureId);

    console.log('📊 Estado de archivos:', {
      payrollBook: payrollBookStatus,
      novelties: noveltiesStatus
    });

    // 3. Obtener progreso de clasificación
    const progress = await payroll.files.getAllSetsClassificationProgress(closureId);
    console.log('📈 Progreso de clasificación:', progress);

    return { templates, status: { payrollBookStatus, noveltiesStatus }, progress };
  } catch (error) {
    console.error('❌ Error en gestión de archivos:', error);
    throw error;
  }
};

/**
 * Ejemplo 5: Generación de reportes
 */
export const ejemploGeneracionReportes = async (closureId, clientId) => {
  try {
    // 1. Generar reporte de resumen de cierre
    const summaryReport = await payroll.reports.generateClosureSummaryReport(closureId, {
      include_details: true,
      format: 'detailed'
    });

    // 2. Generar reporte de incidencias
    const incidentsReport = await payroll.reports.generateIncidentsReport(closureId, {
      status: ['resolved', 'pending'],
      include_resolutions: true
    });

    // 3. Generar reporte comparativo (si hay cierre anterior)
    const previousClosure = await payroll.closures.getMonthlyClosure(clientId, getPreviousPeriod());
    let comparativeReport = null;
    
    if (previousClosure) {
      comparativeReport = await payroll.reports.generateComparativeReport(
        closureId, 
        previousClosure.id,
        { include_variations: true }
      );
    }

    // 4. Obtener datos para dashboard
    const dashboardData = await payroll.reports.getClosureDashboardData(closureId);

    console.log('📊 Reportes generados:', {
      summary: summaryReport,
      incidents: incidentsReport,
      comparative: comparativeReport,
      dashboard: dashboardData
    });

    return {
      summaryReport,
      incidentsReport,
      comparativeReport,
      dashboardData
    };
  } catch (error) {
    console.error('❌ Error en generación de reportes:', error);
    throw error;
  }
};

/**
 * Ejemplo 6: Configuración de conceptos
 */
export const ejemploConfiguracionConceptos = async (clientId) => {
  try {
    // 1. Obtener clasificaciones actuales del cliente
    const classifications = await payroll.concepts.getClientClassifications(clientId);
    console.log('📋 Clasificaciones actuales:', classifications.length);

    // 2. Obtener conceptos no clasificados
    const unclassified = await payroll.concepts.getUnclassifiedConcepts(clientId);
    console.log('❓ Conceptos sin clasificar:', unclassified.length);

    // 3. Sugerir clasificaciones automáticas
    if (unclassified.length > 0) {
      const suggestions = await payroll.concepts.suggestConceptClassifications(
        clientId, 
        unclassified.map(c => c.name)
      );
      console.log('💡 Sugerencias automáticas:', suggestions);
    }

    // 4. Validar consistencia
    const validation = await payroll.concepts.validateConceptConsistency(
      clientId, 
      getCurrentPeriod()
    );
    console.log('✅ Validación de consistencia:', validation);

    return {
      classifications,
      unclassified,
      validation
    };
  } catch (error) {
    console.error('❌ Error en configuración de conceptos:', error);
    throw error;
  }
};

// Funciones auxiliares
const getPreviousPeriod = () => {
  const date = new Date();
  date.setMonth(date.getMonth() - 1);
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
};

const getCurrentPeriod = () => {
  const date = new Date();
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
};

/**
 * Ejemplo completo de uso en un componente React
 */
export const ejemploComponenteReact = `
import React, { useState, useEffect } from 'react';
import payroll from '@/api/payroll';

const PayrollDashboard = ({ clientId }) => {
  const [closures, setClosures] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      try {
        // Cargar cierres del cliente
        const clientClosures = await payroll.closures.getClientClosures(clientId);
        setClosures(clientClosures);
        
        // Si hay cierres, cargar datos adicionales
        if (clientClosures.length > 0) {
          const latestClosure = clientClosures[0];
          
          // Cargar incidencias
          const incidents = await payroll.incidents.getClosureIncidents(latestClosure.id);
          
          // Cargar progreso
          const progress = await payroll.incidents.getIncidentsProgress(latestClosure.id);
          
          console.log('Datos cargados:', { clientClosures, incidents, progress });
        }
      } catch (error) {
        console.error('Error cargando datos:', error);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [clientId]);

  if (loading) return <div>Cargando...</div>;

  return (
    <div>
      <h1>Dashboard de Nómina</h1>
      <p>Cierres encontrados: {closures.length}</p>
      {/* Render de componentes */}
    </div>
  );
};
`;
