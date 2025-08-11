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
  Monitor
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
      // Futuras opciones específicas por área para analistas
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
      // Futuras opciones específicas por área para supervisores
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
      // Futuras áreas como Payroll, Tax, etc.
      Payroll: [
        // Se agregarán cuando implementes payroll
      ]
    }
  }
};

// Configuración de UI
export const UI_CONFIG = {
  cardOpacity: 0.9,
  animationDelay: 100, // ms between each card animation
};
