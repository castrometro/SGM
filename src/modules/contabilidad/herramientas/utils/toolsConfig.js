import {
  Receipt,
  Download,
  Upload,
  FileText,
  BarChart3,
  Users,
  TrendingUp,
  FileSpreadsheet,
  Globe,
  Calculator,
  BookOpen,
  Layers,
  PieChart,
  FileCheck,
  ClipboardList,
  Coins
} from "lucide-react";
import { TOOL_CATEGORIES, TOOL_STATUS, TOOL_COLORS } from "../constants/herramientas.constants";

/**
 * Configuración de herramientas de Contabilidad
 * Organiza las herramientas por categorías
 */

/**
 * Herramientas Generales
 */
export const GENERAL_TOOLS = [
  {
    title: "Captura Masiva de Gastos",
    description: "Procesar y clasificar gastos desde archivos Excel",
    icon: Receipt,
    color: TOOL_COLORS.emerald,
    path: "/menu/tools/captura-masiva-gastos",
    status: TOOL_STATUS.AVAILABLE
  },
  {
    title: "Exportar Datos Contables",
    description: "Exportar información de cierres y movimientos",
    icon: Download,
    color: TOOL_COLORS.blue,
    path: null,
    status: TOOL_STATUS.COMING_SOON
  },
  {
    title: "Importar Plan de Cuentas",
    description: "Carga masiva de plan de cuentas desde Excel",
    icon: Upload,
    color: TOOL_COLORS.green,
    path: null,
    status: TOOL_STATUS.COMING_SOON
  }
];

/**
 * Herramientas específicas de Contabilidad
 */
export const CONTABILIDAD_TOOLS = [
  {
    title: "Clasificación de Cuentas",
    description: "Clasificar y categorizar cuentas contables",
    icon: Layers,
    color: TOOL_COLORS.purple,
    path: null,
    status: TOOL_STATUS.COMING_SOON
  },
  {
    title: "Análisis de Libro Mayor",
    description: "Análisis detallado del libro mayor",
    icon: BookOpen,
    color: TOOL_COLORS.indigo,
    path: null,
    status: TOOL_STATUS.COMING_SOON
  },
  {
    title: "Conciliación Bancaria",
    description: "Conciliar movimientos bancarios automáticamente",
    icon: FileCheck,
    color: TOOL_COLORS.cyan,
    path: null,
    status: TOOL_STATUS.COMING_SOON
  },
  {
    title: "Balance de Comprobación",
    description: "Generar balance de comprobación y sumas y saldos",
    icon: Calculator,
    color: TOOL_COLORS.orange,
    path: null,
    status: TOOL_STATUS.COMING_SOON
  },
  {
    title: "Gestión de Asientos",
    description: "Crear y gestionar asientos contables",
    icon: ClipboardList,
    color: TOOL_COLORS.yellow,
    path: null,
    status: TOOL_STATUS.COMING_SOON
  }
];

/**
 * Herramientas de Reportes y Análisis
 */
export const REPORTES_TOOLS = [
  {
    title: "Dashboard Contable",
    description: "Visualización de métricas y KPIs contables",
    icon: BarChart3,
    color: TOOL_COLORS.teal,
    path: null,
    status: TOOL_STATUS.BETA
  },
  {
    title: "Estados Financieros",
    description: "Generar balance general y estado de resultados",
    icon: FileSpreadsheet,
    color: TOOL_COLORS.blue,
    path: null,
    status: TOOL_STATUS.COMING_SOON
  },
  {
    title: "Análisis de Variaciones",
    description: "Comparar periodos y analizar variaciones",
    icon: TrendingUp,
    color: TOOL_COLORS.red,
    path: null,
    status: TOOL_STATUS.COMING_SOON
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
    title: "Análisis por Centro de Costo",
    description: "Distribución de costos por centros",
    icon: PieChart,
    color: TOOL_COLORS.purple,
    path: null,
    status: TOOL_STATUS.COMING_SOON
  },
  {
    title: "Gestión de Analistas",
    description: "Métricas de productividad de analistas",
    icon: Users,
    color: TOOL_COLORS.indigo,
    path: null,
    status: TOOL_STATUS.COMING_SOON
  }
];

/**
 * Herramientas de Integraciones
 */
export const INTEGRACIONES_TOOLS = [
  {
    title: "Integración SII",
    description: "Envío de información al Servicio de Impuestos Internos",
    icon: Globe,
    color: TOOL_COLORS.red,
    path: null,
    status: TOOL_STATUS.COMING_SOON
  },
  {
    title: "Integración ERP",
    description: "Sincronizar datos con sistemas ERP externos",
    icon: FileText,
    color: TOOL_COLORS.blue,
    path: null,
    status: TOOL_STATUS.COMING_SOON
  },
  {
    title: "API Bancaria",
    description: "Importar movimientos bancarios automáticamente",
    icon: Coins,
    color: TOOL_COLORS.green,
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
    id: TOOL_CATEGORIES.CONTABILIDAD,
    name: "Gestión Contable",
    tools: CONTABILIDAD_TOOLS
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
    ...CONTABILIDAD_TOOLS,
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
