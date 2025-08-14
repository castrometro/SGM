import { 
  Wrench, 
  Download, 
  Upload, 
  FileText, 
  Database, 
  Settings,
  BarChart3,
  Users,
  RefreshCw,
  Receipt,
  Calculator,
  TrendingUp,
  FileSpreadsheet,
  PieChart,
  Building,
  CreditCard,
  UserCheck,
  ClipboardList,
  Archive,
  Wallet,
  Calendar,
  Target
} from "lucide-react";

/**
 * Configuración de herramientas organizadas por áreas y tipos de usuario
 * Similar al patrón usado en MenuUsuario
 */
export const TOOLS_CONFIG = {
  // Herramientas base disponibles para todos
  base: [
    {
      title: "Exportar Datos Básicos",
      description: "Exportar información general del sistema",
      icon: Download,
      color: "bg-blue-600",
      action: "exportar-basicos",
      section: "general",
      disabled: true
    }
  ],

  // Herramientas por tipo de usuario
  byUserType: {
    analista: {
      base: [
        // Herramientas generales para analistas (sin área específica)
      ],
      
      // Herramientas específicas por área para analistas
      byArea: {
        "Contabilidad": [
          {
            title: "Captura Masiva RindeGastos",
            description: "Cargar múltiples gastos desde archivo Excel",
            icon: Receipt,
            color: "bg-emerald-600",
            action: "captura-gastos",
            section: "contabilidad",
            disabled: false
          },
          {
            title: "Validar Comprobantes",
            description: "Verificar integridad de documentos contables",
            icon: FileSpreadsheet,
            color: "bg-blue-600",
            action: "validar-comprobantes",
            section: "contabilidad",
            disabled: true
          }
        ],
        
        "Payroll": [
          {
            title: "Procesar Nómina Asignada",
            description: "Procesar nóminas de clientes asignados",
            icon: UserCheck,
            color: "bg-green-600",
            action: "procesar-nomina-asignada",
            section: "nomina",
            disabled: true
          },
          {
            title: "Validar Datos Empleados",
            description: "Verificar información de empleados",
            icon: ClipboardList,
            color: "bg-blue-600",
            action: "validar-empleados",
            section: "nomina",
            disabled: true
          }
        ]
      }
    },

    gerente: {
      base: [
        {
          title: "Dashboard Ejecutivo",
          description: "Métricas y KPIs consolidados",
          icon: BarChart3,
          color: "bg-indigo-600",
          action: "dashboard-ejecutivo",
          section: "analytics",
          disabled: true
        },
        {
          title: "Gestión de Usuarios Avanzada",
          description: "Administración completa de usuarios",
          icon: Users,
          color: "bg-pink-600",
          action: "gestion-usuarios-avanzada",
          section: "system",
          disabled: true
        }
      ],

      // Herramientas específicas por área para gerentes
      byArea: {
        "Contabilidad": [
          {
            title: "Consolidación Contable",
            description: "Consolidar estados financieros",
            icon: Calculator,
            color: "bg-green-600",
            action: "consolidacion-contable",
            section: "contabilidad",
            disabled: true
          },
          {
            title: "Análisis de Costos",
            description: "Herramientas avanzadas de análisis de costos",
            icon: TrendingUp,
            color: "bg-purple-600",
            action: "analisis-costos",
            section: "contabilidad",
            disabled: true
          },
          {
            title: "Reportes Contables",
            description: "Generar reportes contables personalizados",
            icon: FileText,
            color: "bg-blue-600",
            action: "reportes-contables",
            section: "contabilidad",
            disabled: true
          },
          {
            title: "Backup Contable",
            description: "Respaldar información contable crítica",
            icon: Database,
            color: "bg-red-600",
            action: "backup-contable",
            section: "contabilidad",
            disabled: true
          }
        ],

        "Nómina": [
          {
            title: "Procesamiento Masivo Nómina",
            description: "Procesar múltiples nóminas simultáneamente",
            icon: UserCheck,
            color: "bg-orange-600",
            action: "procesamiento-nomina",
            section: "nomina",
            disabled: true
          },
          {
            title: "Cálculo de Liquidaciones",
            description: "Automatizar cálculos de liquidación",
            icon: Calculator,
            color: "bg-yellow-600",
            action: "calculo-liquidaciones",
            section: "nomina",
            disabled: true
          },
          {
            title: "Reportes de Nómina",
            description: "Generar reportes de nómina detallados",
            icon: ClipboardList,
            color: "bg-indigo-600",
            action: "reportes-nomina",
            section: "nomina",
            disabled: true
          },
          {
            title: "Archivo Plano PILA",
            description: "Generar archivos para PILA",
            icon: Archive,
            color: "bg-gray-600",
            action: "archivo-pila",
            section: "nomina",
            disabled: true
          }
        ],

        "Recursos Humanos": [
          {
            title: "Gestión de Vacaciones",
            description: "Administrar solicitudes de vacaciones",
            icon: Calendar,
            color: "bg-green-600",
            action: "gestion-vacaciones",
            section: "rrhh",
            disabled: true
          },
          {
            title: "Evaluaciones de Desempeño",
            description: "Crear y gestionar evaluaciones",
            icon: Target,
            color: "bg-purple-600",
            action: "evaluaciones",
            section: "rrhh",
            disabled: true
          }
        ]
      }
    },

    admin: {
      base: [
        {
          title: "Configuración del Sistema",
          description: "Ajustes y parámetros generales",
          icon: Settings,
          color: "bg-gray-600",
          action: "config-sistema",
          section: "system",
          disabled: true
        },
        {
          title: "Sincronizar Datos",
          description: "Actualizar información desde fuentes externas",
          icon: RefreshCw,
          color: "bg-yellow-600",
          action: "sync-datos",
          section: "system",
          disabled: true
        },
        {
          title: "Backup Completo",
          description: "Respaldar toda la información del sistema",
          icon: Database,
          color: "bg-red-600",
          action: "backup-completo",
          section: "system",
          disabled: true
        }
      ]
    }
  }
};

/**
 * Configuración de secciones dinámicas
 */
export const SECTIONS_CONFIG = {
  general: {
    id: "general",
    name: "Herramientas Generales",
    description: "Utilidades básicas disponibles para todos",
    icon: Wrench
  },
  contabilidad: {
    id: "contabilidad", 
    name: "Contabilidad",
    description: "Herramientas específicas del área contable",
    icon: Calculator
  },
  nomina: {
    id: "nomina",
    name: "Nómina", 
    description: "Herramientas para gestión de nómina",
    icon: Wallet
  },
  rrhh: {
    id: "rrhh",
    name: "Recursos Humanos",
    description: "Herramientas de gestión humana",
    icon: Users
  },
  analytics: {
    id: "analytics",
    name: "Análisis y Reportes",
    description: "Métricas avanzadas y reportes ejecutivos",
    icon: BarChart3
  },
  system: {
    id: "system",
    name: "Sistema",
    description: "Configuración y administración del sistema",
    icon: Settings
  }
};

/**
 * Configuración de UI para la página de herramientas
 */
export const UI_CONFIG = {
  infoSection: {
    icon: Wrench,
    title: "Centro de Herramientas",
    description: "Esta sección está en desarrollo activo. Las herramientas se habilitarán progresivamente conforme se completen las pruebas de funcionalidad y seguridad.",
    note: "¿Necesitas alguna herramienta específica? Contacta al equipo de desarrollo."
  }
};
