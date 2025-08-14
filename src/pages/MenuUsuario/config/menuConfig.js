import {
  FolderKanban,
  Wrench,
  ShieldCheck,
  UserCog,
  FileText,
  BarChart3,
  Activity,
  Users,
  Settings,
  Database,
  Monitor,
  DollarSign,
  CalendarCheck,
  FileSpreadsheet,
  TrendingUp,
  Calculator,
  PieChart
} from "lucide-react";

// Configuración de opciones de menú por tipo de usuario y área
export const MENU_CONFIG = {
  analista: {
    base: [
      { 
        label: "Clientes", 
        descripcion: "Ver y trabajar con tus clientes asignados", 
        icon: FolderKanban, 
        color: "#4F46E5", 
        path: "/menu/clientes" 
      },
      { 
        label: "Herramientas", 
        descripcion: "Acceso a recursos y utilidades", 
        icon: Wrench, 
        color: "#10B981", 
        path: "/menu/tools" 
      }
    ],
    areas: {
      Contabilidad: [
        // Opciones específicas de contabilidad para analistas (si las hay)
      ],
      Payroll: [
        // Opciones específicas de payroll para analistas (si las hay)
      ]
    }
  },

  supervisor: {
    base: [
      { 
        label: "Mis Analistas", 
        descripcion: "Gestión y supervisión de analistas asignados", 
        icon: Users, 
        color: "#EC4899", 
        path: "/menu/mis-analistas" 
      },
      { 
        label: "Clientes", 
        descripcion: "Ver y validar clientes asignados", 
        icon: FolderKanban, 
        color: "#4F46E5", 
        path: "/menu/clientes" 
      },
      { 
        label: "Validaciones", 
        descripcion: "Revisar y aprobar cierres", 
        icon: ShieldCheck, 
        color: "#F59E0B", 
        path: "/menu/validaciones" 
      }
    ],
    areas: {
      Contabilidad: [
        // Opciones específicas de contabilidad para supervisores
      ],
      Payroll: [
        { 
          label: "Supervisión Nóminas", 
          descripcion: "Revisar y aprobar cierres de nómina", 
          icon: CalendarCheck, 
          color: "#8B5CF6", 
          path: "/menu/payroll/supervision" 
        },
        { 
          label: "Reportes de Nómina", 
          descripcion: "Informes y análisis de nóminas procesadas", 
          icon: FileSpreadsheet, 
          color: "#059669", 
          path: "/menu/payroll/reportes" 
        }
      ]
    }
  },

  gerente: {
    base: [
      { 
        label: "Clientes", 
        descripcion: "Visión general de todos los clientes", 
        icon: FolderKanban, 
        color: "#4F46E5", 
        path: "/menu/clientes" 
      },
      { 
        label: "Dashboard Gerencial", 
        descripcion: "Dashboard avanzado con métricas, alertas y reportes", 
        icon: Activity, 
        color: "#EF4444", 
        path: "/menu/dashboard-gerente" 
      },
      { 
        label: "Gestión de Analistas", 
        descripcion: "Gestión de analistas y asignaciones", 
        icon: UserCog, 
        color: "#EC4899", 
        path: "/menu/analistas" 
      },
      { 
        label: "Herramientas", 
        descripcion: "Utilidades del sistema", 
        icon: Wrench, 
        color: "#10B981", 
        path: "/menu/tools" 
      }
    ],
    areas: {
      Contabilidad: [
        { 
          label: "Analytics de Performance", 
          descripcion: "KPIs y métricas de contabilidad y cierres", 
          icon: BarChart3, 
          color: "#8B5CF6", 
          path: "/menu/analytics" 
        },
        { 
          label: "Logs y Actividad", 
          descripcion: "Auditoría y logs de actividades de usuarios", 
          icon: FileText, 
          color: "#F97316", 
          path: "/menu/gerente/logs-actividad" 
        },
        { 
          label: "Estados de Cierres", 
          descripcion: "Monitoreo en tiempo real de estados de cierres", 
          icon: Monitor, 
          color: "#06B6D4", 
          path: "/menu/gerente/estados-cierres" 
        },
        { 
          label: "Cache Redis", 
          descripcion: "Estado y gestión del cache Redis de cierres", 
          icon: Database, 
          color: "#10B981", 
          path: "/menu/gerente/cache-redis" 
        },
        { 
          label: "Admin Sistema", 
          descripcion: "Creación de usuarios, clientes y herramientas avanzadas", 
          icon: Settings, 
          color: "#DC2626", 
          path: "/menu/gerente/admin-sistema" 
        }
      ],
      // Áreas para gerentes
      Payroll: [
        { 
          label: "Dashboard Payroll", 
          descripcion: "Métricas y KPIs de nóminas y recursos humanos", 
          icon: PieChart, 
          color: "#7C3AED", 
          path: "/menu/payroll/dashboard" 
        },
        { 
          label: "Gestión de Empleados", 
          descripcion: "Administración completa de empleados y contratos", 
          icon: Users, 
          color: "#059669", 
          path: "/menu/payroll/empleados/gestion" 
        },
        { 
          label: "Cierres de Nómina", 
          descripcion: "Historial y gestión de cierres de nómina", 
          icon: CalendarCheck, 
          color: "#DC2626", 
          path: "/menu/payroll/cierres" 
        },
        { 
          label: "Configuración Payroll", 
          descripcion: "Configurar conceptos, deducciones y parámetros", 
          icon: Settings, 
          color: "#EA580C", 
          path: "/menu/payroll/configuracion" 
        },
        { 
          label: "Analytics Payroll", 
          descripcion: "Análisis avanzado de costos y tendencias salariales", 
          icon: TrendingUp, 
          color: "#0D9488", 
          path: "/menu/payroll/analytics" 
        },
        { 
          label: "Logs Payroll", 
          descripcion: "Auditoría y logs de actividades de payroll", 
          icon: FileText, 
          color: "#B45309", 
          path: "/menu/payroll/logs" 
        }
      ]
    }
  }
};

// Configuración de UI
export const UI_CONFIG = {
  cardOpacity: 0.9,
  animationDelay: 100, // ms between each card animation
};
