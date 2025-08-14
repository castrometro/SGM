import { 
  Users, 
  DollarSign, 
  CalendarCheck, 
  TrendingUp, 
  AlertTriangle,
  FileSpreadsheet,
  Clock,
  CheckCircle
} from "lucide-react";

/**
 * Configuración de tipos de usuario y sus permisos en el dashboard de payroll
 */
export const PAYROLL_USER_CONFIG = {
  gerente: {
    title: "Gerente de Payroll",
    description: "Dashboard completo con todas las métricas y controles",
    permissions: {
      viewAllEmployees: true,
      viewFinancialMetrics: true,
      approvePayrolls: true,
      viewReports: true,
      manageConfig: true
    }
  },
  supervisor: {
    title: "Supervisor de Nóminas", 
    description: "Supervisión y aprobación de nóminas de su área",
    permissions: {
      viewAllEmployees: false,
      viewFinancialMetrics: true,
      approvePayrolls: true,
      viewReports: true,
      manageConfig: false
    }
  },
  analista: {
    title: "Analista de Payroll",
    description: "Vista limitada para procesamiento de nóminas",
    permissions: {
      viewAllEmployees: false,
      viewFinancialMetrics: false,
      approvePayrolls: false,
      viewReports: false,
      manageConfig: false
    }
  }
};

/**
 * Configuración de tarjetas de métricas del dashboard
 */
export const DASHBOARD_CARDS = {
  empleados: {
    title: "Empleados Activos",
    icon: Users,
    color: "#10B981",
    bgColor: "bg-green-600/20",
    borderColor: "border-green-500/30"
  },
  nominasEnProceso: {
    title: "Nóminas en Proceso",
    icon: Clock,
    color: "#F59E0B",
    bgColor: "bg-yellow-600/20",
    borderColor: "border-yellow-500/30"
  },
  nominasAprobadas: {
    title: "Nóminas Aprobadas",
    icon: CheckCircle,
    color: "#059669",
    bgColor: "bg-emerald-600/20",
    borderColor: "border-emerald-500/30"
  },
  costoMensual: {
    title: "Costo Mensual",
    icon: DollarSign,
    color: "#3B82F6",
    bgColor: "bg-blue-600/20",
    borderColor: "border-blue-500/30"
  },
  alertas: {
    title: "Alertas Pendientes",
    icon: AlertTriangle,
    color: "#EF4444",
    bgColor: "bg-red-600/20",
    borderColor: "border-red-500/30"
  },
  reportes: {
    title: "Reportes Generados",
    icon: FileSpreadsheet,
    color: "#8B5CF6",
    bgColor: "bg-purple-600/20",
    borderColor: "border-purple-500/30"
  }
};

/**
 * Configuración de widgets según tipo de usuario
 */
export const USER_WIDGETS = {
  gerente: [
    'empleados',
    'nominasEnProceso', 
    'nominasAprobadas',
    'costoMensual',
    'alertas',
    'reportes'
  ],
  supervisor: [
    'nominasEnProceso',
    'nominasAprobadas', 
    'alertas',
    'reportes'
  ],
  analista: [
    'nominasEnProceso'
  ]
};

/**
 * Mensajes de la aplicación
 */
export const MESSAGES = {
  loading: "Cargando dashboard de payroll...",
  error: "Error al cargar los datos del dashboard.",
  noAccess: "No tienes acceso a esta funcionalidad.",
  noData: "No hay datos disponibles para mostrar.",
  welcome: "Bienvenido al Dashboard de Payroll",
  subtitle: "Gestión integral de nóminas y recursos humanos"
};

/**
 * Función para obtener widgets según el tipo de usuario
 */
export const getUserWidgets = (tipoUsuario) => {
  return USER_WIDGETS[tipoUsuario] || USER_WIDGETS.analista;
};

/**
 * Función para verificar permisos
 */
export const hasPermission = (tipoUsuario, permission) => {
  const userConfig = PAYROLL_USER_CONFIG[tipoUsuario];
  return userConfig?.permissions?.[permission] || false;
};
