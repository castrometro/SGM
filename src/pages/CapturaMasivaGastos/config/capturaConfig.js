import { 
  Receipt, 
  Upload, 
  FileSpreadsheet, 
  Download, 
  ArrowLeft, 
  AlertCircle,
  CheckCircle,
  Info,
  X,
  Clock,
  Settings,
  MapPin
} from "lucide-react";

/**
 * Configuración de la página de captura masiva de gastos
 */
export const CAPTURA_CONFIG = {
  page: {
    title: "Captura Masiva RindeGastos",
    description: "Carga múltiples gastos desde archivo Excel",
    icon: Receipt
  },
  
  steps: {
    download: {
      title: "Paso 1: Descargar Plantilla",
      description: "Descarga la plantilla Excel con el formato correcto para la carga masiva de gastos.",
      icon: Download
    },
    upload: {
      title: "Paso 2: Cargar Archivo",
      description: "Sube tu archivo Excel completado",
      icon: Upload
    },
    results: {
      title: "Resultados del Procesamiento",
      icon: CheckCircle
    }
  },

  fileConfig: {
    acceptedFormats: ".xlsx,.xls",
    supportedText: "Formatos soportados: .xlsx, .xls",
    placeholderText: "Seleccionar archivo Excel"
  },

  mapeoCC: {
    title: "Configurar Códigos de Centros de Costos",
    description: "Por favor, asigne los códigos de centro de costos para las columnas detectadas:",
    formatPattern: /^\d{2,3}-\d{3}$/,
    formatExample: "01-003 o 001-003",
    // Fallback cuando no se detectan CC en el Excel: mostrar los 7 tipos posibles
    // Las keys ahora son por tipo lógico para evitar dependencias con posiciones
    columns: [
      { key: 'PyC', label: 'PyC', placeholder: 'Solo números y guiones (ej: 01-003)' },
      { key: 'PS', label: 'PS/EB', placeholder: 'Solo números y guiones (ej: 02-004)' },
      { key: 'CO', label: 'CO', placeholder: 'Solo números y guiones (ej: 03-005)' },
      { key: 'RE', label: 'RE', placeholder: 'Solo números y guiones (ej: 04-006)' },
      { key: 'TR', label: 'TR', placeholder: 'Solo números y guiones (ej: 05-007)' },
      { key: 'CF', label: 'CF', placeholder: 'Solo números y guiones (ej: 06-008)' },
      { key: 'LRC', label: 'LRC', placeholder: 'Solo números y guiones (ej: 07-009)' }
    ]
  }
};

/**
 * Mensajes y textos de la interfaz
 */
export const UI_MESSAGES = {
  instructions: {
    title: "Instrucciones de Uso",
    icon: Info,
    items: [
      "Descarga la plantilla Excel con el formato requerido",
      "Completa los datos de gastos en las columnas correspondientes", 
      "Sube el archivo completado para procesamiento automático",
      "Revisa los resultados y corrige cualquier error reportado"
    ]
  },
  
  processing: {
    idle: "Procesar Archivo",
    active: "Procesando con Celery..."
  },

  errors: {
    noFile: "Por favor, selecciona un archivo antes de procesar",
    noCCConfig: "Por favor, configure al menos un código de centro de costos",
    invalidFormat: "Errores de formato:",
    processing: "Error procesando archivo:",
    download: "Error descargando archivo:"
  },

  ccInfo: {
    title: "Información importante:",
    items: [
      "Solo se permiten números y guiones en los códigos de centro de costos",
      "Use el formato XX-XXX o XXX-XXX para códigos de centro de costos (ej: 01-003 o 001-003)",
      "Deje vacío si la columna no corresponde a un centro de costos",
      'Los valores nulos, "-" o "0" en el Excel se consideran sin centro de costos',
      "Cualquier otro valor se considera como 1 centro de costos"
    ]
  },

  comingSoon: "Próximamente disponible"
};

/**
 * Configuración de estilos y clases CSS
 */
export const STYLES_CONFIG = {
  containers: {
    main: "min-h-screen bg-gray-900 text-white",
    header: "bg-gray-800 border-b border-gray-700",
    content: "max-w-4xl mx-auto px-6 py-8 space-y-8",
    section: "bg-gray-800 rounded-lg p-6"
  },
  
  buttons: {
    primary: "bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg flex items-center gap-2 transition-colors",
    secondary: "bg-emerald-600 hover:bg-emerald-700 text-white px-6 py-3 rounded-lg transition-colors flex items-center justify-center gap-2",
    disabled: "disabled:bg-gray-600 disabled:cursor-not-allowed",
    back: "p-2 hover:bg-gray-700 rounded-lg transition-colors"
  },

  alerts: {
    info: "bg-blue-900/20 border border-blue-500/30 rounded-lg p-6",
    warning: "bg-yellow-900/20 border border-yellow-500/30 rounded-lg p-6", 
    error: "bg-red-900/20 border border-red-500/30 rounded-lg p-4",
    success: "bg-green-900/20 border border-green-500/30 rounded-lg p-4"
  }
};
