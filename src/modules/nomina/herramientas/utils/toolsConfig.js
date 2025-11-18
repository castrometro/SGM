import {
  Receipt,
  Download,
  Upload,
  FileText,
  BarChart3,
  Users,
  Calendar,
  TrendingUp,
  FileSpreadsheet,
  Globe,
  DollarSign,
  ClipboardCheck
} from "lucide-react";
import { TOOL_CATEGORIES, TOOL_STATUS, TOOL_COLORS } from "../constants/herramientas.constants";

/**
 * Configuración de herramientas de Nómina
 * Organiza las herramientas por categorías
 */

/**
 * Herramientas Generales
 */
export const GENERAL_TOOLS = [
  {
    title: "Exportar Datos de Nómina",
    description: "Exportar información de empleados y cierres",
    icon: Download,
    color: TOOL_COLORS.blue,
    path: null,
    status: TOOL_STATUS.COMING_SOON
  },
  {
    title: "Importar Empleados",
    description: "Carga masiva de empleados desde Excel",
    icon: Upload,
    color: TOOL_COLORS.green,
    path: null,
    status: TOOL_STATUS.COMING_SOON
  }
];

/**
 * Herramientas específicas de Nómina
 */
export const NOMINA_TOOLS = [
  {
    title: "Libro de Remuneraciones",
    description: "Generar libro de remuneraciones oficial",
    icon: FileSpreadsheet,
    color: TOOL_COLORS.purple,
    path: null,
    status: TOOL_STATUS.COMING_SOON
  },
  {
    title: "Cálculo de Finiquitos",
    description: "Calcular finiquitos y liquidaciones",
    icon: DollarSign,
    color: TOOL_COLORS.orange,
    path: null,
    status: TOOL_STATUS.COMING_SOON
  },
  {
    title: "Gestión de Incidencias",
    description: "Administrar ausencias, licencias y permisos",
    icon: ClipboardCheck,
    color: TOOL_COLORS.yellow,
    path: null,
    status: TOOL_STATUS.COMING_SOON
  },
  {
    title: "Calendario Laboral",
    description: "Gestionar días festivos y periodos de pago",
    icon: Calendar,
    color: TOOL_COLORS.indigo,
    path: null,
    status: TOOL_STATUS.COMING_SOON
  }
];

/**
 * Herramientas de Reportes y Análisis
 */
export const REPORTES_TOOLS = [
  {
    title: "Dashboard de Nómina",
    description: "Visualización de métricas y KPIs de nómina",
    icon: BarChart3,
    color: TOOL_COLORS.teal,
    path: null,
    status: TOOL_STATUS.BETA
  },
  {
    title: "Reportes Personalizados",
    description: "Crear reportes avanzados con filtros",
    icon: FileText,
    color: TOOL_COLORS.pink,
    path: null,
    status: TOOL_STATUS.COMING_SOON
  },
  {
    title: "Análisis de Costos",
    description: "Análisis detallado de costos de personal",
    icon: TrendingUp,
    color: TOOL_COLORS.red,
    path: null,
    status: TOOL_STATUS.COMING_SOON
  },
  {
    title: "Gestión de Analistas",
    description: "Métricas de productividad de analistas",
    icon: Users,
    color: TOOL_COLORS.purple,
    path: null,
    status: TOOL_STATUS.COMING_SOON
  }
];

/**
 * Herramientas de Integraciones
 */
export const INTEGRACIONES_TOOLS = [
  {
    title: "Integración Previred",
    description: "Sincronizar datos con Previred",
    icon: Globe,
    color: TOOL_COLORS.blue,
    path: null,
    status: TOOL_STATUS.COMING_SOON
  },
  {
    title: "Integración SII",
    description: "Envío de información al Servicio de Impuestos Internos",
    icon: FileText,
    color: TOOL_COLORS.red,
    path: null,
    status: TOOL_STATUS.COMING_SOON
  }
];

/**
 * Obtener categorías con sus herramientas
 */
export const getToolCategories = () => [
  {
    id: TOOL_CATEGORIES.GENERAL,
    name: "Herramientas Generales",
    tools: GENERAL_TOOLS
  },
  {
    id: TOOL_CATEGORIES.NOMINA,
    name: "Gestión de Nómina",
    tools: NOMINA_TOOLS
  },
  {
    id: TOOL_CATEGORIES.REPORTES,
    name: "Reportes y Análisis",
    tools: REPORTES_TOOLS
  },
  {
    id: TOOL_CATEGORIES.INTEGRACIONES,
    name: "Integraciones",
    tools: INTEGRACIONES_TOOLS
  }
];

/**
 * Obtener estadísticas de herramientas
 */
export const getToolsStats = () => {
  const allTools = [
    ...GENERAL_TOOLS,
    ...NOMINA_TOOLS,
    ...REPORTES_TOOLS,
    ...INTEGRACIONES_TOOLS
  ];

  return {
    total: allTools.length,
    available: allTools.filter(t => t.status === TOOL_STATUS.AVAILABLE).length,
    beta: allTools.filter(t => t.status === TOOL_STATUS.BETA).length,
    comingSoon: allTools.filter(t => t.status === TOOL_STATUS.COMING_SOON).length
  };
};
