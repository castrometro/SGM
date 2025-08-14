import { useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { TOOLS_CONFIG, SECTIONS_CONFIG } from "../config/toolsConfig";

/**
 * Hook personalizado para generar herramientas dinámicamente
 * basado en el tipo de usuario y sus áreas asignadas
 * Similar al patrón usado en MenuUsuario
 */
export const useToolsOptions = (usuario) => {
  const navigate = useNavigate();

  // Mapear acciones a funciones
  const actionHandlers = useMemo(() => ({
    "captura-gastos": () => navigate('/menu/tools/captura-masiva-gastos'),
    "exportar-basicos": () => console.log("Exportar datos básicos"),
    "validar-comprobantes": () => console.log("Validar comprobantes"),
    "procesar-nomina-asignada": () => console.log("Procesar nómina asignada"),
    "validar-empleados": () => console.log("Validar datos empleados"),
    "dashboard-ejecutivo": () => console.log("Dashboard ejecutivo"),
    "gestion-usuarios-avanzada": () => console.log("Gestión usuarios avanzada"),
    "consolidacion-contable": () => console.log("Consolidación contable"),
    "analisis-costos": () => console.log("Análisis de costos"),
    "reportes-contables": () => console.log("Reportes contables"),
    "backup-contable": () => console.log("Backup contable"),
    "procesamiento-nomina": () => console.log("Procesamiento nómina"),
    "calculo-liquidaciones": () => console.log("Cálculo liquidaciones"),
    "reportes-nomina": () => console.log("Reportes nómina"),
    "archivo-pila": () => console.log("Archivo PILA"),
    "gestion-vacaciones": () => console.log("Gestión vacaciones"),
    "evaluaciones": () => console.log("Evaluaciones"),
    "config-sistema": () => console.log("Config sistema"),
    "sync-datos": () => console.log("Sync datos"),
    "backup-completo": () => console.log("Backup completo")
  }), [navigate]);

  // Generar herramientas disponibles para el usuario
  const availableTools = useMemo(() => {
    if (!usuario || !usuario.tipo_usuario) {
      return [];
    }

    let herramientas = [];

    // Agregar herramientas base globales
    herramientas = [...TOOLS_CONFIG.base];

    // Obtener configuración del tipo de usuario
    const userConfig = TOOLS_CONFIG.byUserType[usuario.tipo_usuario];
    if (!userConfig) {
      console.warn(`Configuración de herramientas no encontrada para tipo de usuario: ${usuario.tipo_usuario}`);
      return herramientas;
    }

    // Agregar herramientas base del tipo de usuario
    if (userConfig.base) {
      herramientas = [...herramientas, ...userConfig.base];
    }

    // Agregar herramientas específicas por área
    if (userConfig.byArea && usuario.areas?.length > 0) {
      const areas = usuario.areas || [];
      
      areas.forEach(area => {
        const areaHerramientas = userConfig.byArea[area.nombre] || [];
        herramientas = [...herramientas, ...areaHerramientas];
      });
    }

    // Filtrar herramientas según las áreas del usuario (para todos los tipos de usuario)
    const userAreas = usuario.areas?.map(area => area.nombre) || [];
    
    // Mapeo de secciones a áreas
    const sectionToArea = {
      'contabilidad': 'Contabilidad',
      'nomina': 'Payroll', // Puede ser Payroll, Nómina o RRHH
      'rrhh': 'RRHH'
    };

    herramientas = herramientas.filter(herramienta => {
      const section = herramienta.section;
      
      // Siempre permitir herramientas generales, analytics y system
      if (['general', 'analytics', 'system'].includes(section)) {
        return true;
      }
      
      // Verificar si el usuario tiene acceso al área de la herramienta
      const requiredArea = sectionToArea[section];
      if (requiredArea) {
        return userAreas.includes(requiredArea) || 
               userAreas.some(area => area.toLowerCase().includes('payroll')) ||
               userAreas.some(area => area.toLowerCase().includes('nomina')) ||
               userAreas.some(area => area.toLowerCase().includes('rrhh'));
      }
      
      return true; // Por defecto permitir si no hay restricción específica
    });

    // Agregar handlers de acción a cada herramienta
    return herramientas.map(herramienta => ({
      ...herramienta,
      onClick: actionHandlers[herramienta.action] || (() => console.log(`Acción no implementada: ${herramienta.action}`))
    }));

  }, [usuario, actionHandlers]);

  // Organizar herramientas por secciones
  const organizedSections = useMemo(() => {
    const sectionMap = {};

    // Agrupar herramientas por sección
    availableTools.forEach(tool => {
      const sectionId = tool.section || 'general';
      
      if (!sectionMap[sectionId]) {
        sectionMap[sectionId] = {
          ...SECTIONS_CONFIG[sectionId],
          tools: []
        };
      }
      
      sectionMap[sectionId].tools.push(tool);
    });

    // Convertir a array y ordenar
    return Object.values(sectionMap).sort((a, b) => {
      const order = ['general', 'contabilidad', 'nomina', 'rrhh', 'analytics', 'system'];
      return order.indexOf(a.id) - order.indexOf(b.id);
    });

  }, [availableTools]);

  return {
    tools: availableTools,
    sections: organizedSections,
    executeAction: (actionName) => {
      const handler = actionHandlers[actionName];
      if (handler) {
        handler();
      } else {
        console.warn(`Acción no encontrada: ${actionName}`);
      }
    }
  };
};
