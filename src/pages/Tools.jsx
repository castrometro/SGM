import { useState } from "react";
import { useNavigate } from "react-router-dom";
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
  AlertTriangle,
  Receipt
} from "lucide-react";
import AreaIndicator from "../components/AreaIndicator";

const ToolCard = ({ title, description, icon: Icon, color, onClick, disabled = false }) => (
  <div 
    className={`bg-gray-800 p-6 rounded-lg border border-gray-700 hover:border-gray-600 transition-colors cursor-pointer ${
      disabled ? 'opacity-50 cursor-not-allowed' : ''
    }`}
    onClick={disabled ? undefined : onClick}
  >
    <div className="flex items-center mb-4">
      <div className={`p-3 rounded-lg ${color}`}>
        <Icon className="w-6 h-6 text-white" />
      </div>
      <div className="ml-4">
        <h3 className="font-semibold text-white">{title}</h3>
        <p className="text-gray-400 text-sm">{description}</p>
      </div>
    </div>
    {disabled && (
      <div className="flex items-center text-yellow-400 text-sm">
        <AlertTriangle className="w-4 h-4 mr-1" />
        Próximamente disponible
      </div>
    )}
  </div>
);

const Tools = () => {
  const [activeSection, setActiveSection] = useState("general");
  const navigate = useNavigate();
  
  // Obtener usuario para mostrar sus áreas
  const usuario = JSON.parse(localStorage.getItem("usuario"));

  const generalTools = [
    {
      title: "Captura Masiva de Gastos",
      description: "Procesar y clasificar gastos desde Excel",
      icon: Receipt,
      color: "bg-emerald-600",
      onClick: () => navigate("/menu/tools/captura-masiva-gastos"),
      disabled: false
    },
    {
      title: "Exportar Datos",
      description: "Exportar información de clientes y cierres",
      icon: Download,
      color: "bg-blue-600",
      onClick: () => console.log("Exportar datos"),
      disabled: true
    },
    {
      title: "Importar Configuraciones",
      description: "Cargar configuraciones desde archivo",
      icon: Upload,
      color: "bg-green-600",
      onClick: () => console.log("Importar config"),
      disabled: true
    },
    {
      title: "Generar Reportes",
      description: "Crear reportes personalizados",
      icon: FileText,
      color: "bg-purple-600",
      onClick: () => console.log("Generar reportes"),
      disabled: true
    },
    {
      title: "Backup de Base de Datos",
      description: "Respaldar información crítica",
      icon: Database,
      color: "bg-red-600",
      onClick: () => console.log("Backup DB"),
      disabled: true
    }
  ];

  const analyticsTools = [
    {
      title: "Análisis de Performance",
      description: "Métricas avanzadas de rendimiento",
      icon: BarChart3,
      color: "bg-indigo-600",
      onClick: () => console.log("Análisis performance"),
      disabled: true
    },
    {
      title: "Gestión de Usuarios",
      description: "Administración avanzada de usuarios",
      icon: Users,
      color: "bg-pink-600",
      onClick: () => console.log("Gestión usuarios"),
      disabled: true
    }
  ];

  const systemTools = [
    {
      title: "Configuración del Sistema",
      description: "Ajustes y parámetros generales",
      icon: Settings,
      color: "bg-gray-600",
      onClick: () => console.log("Config sistema"),
      disabled: true
    },
    {
      title: "Sincronizar Datos",
      description: "Actualizar información desde fuentes externas",
      icon: RefreshCw,
      color: "bg-yellow-600",
      onClick: () => console.log("Sync datos"),
      disabled: true
    }
  ];

  const sections = [
    { id: "general", name: "Herramientas Generales", tools: generalTools },
    { id: "analytics", name: "Análisis y Reportes", tools: analyticsTools },
    { id: "system", name: "Sistema", tools: systemTools }
  ];

  return (
    <div className="text-white space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <h1 className="text-3xl font-bold mb-2">Herramientas</h1>
          <p className="text-gray-400">Utilidades y recursos para la gestión del sistema</p>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex space-x-4 border-b border-gray-700">
        {sections.map((section) => (
          <button
            key={section.id}
            onClick={() => setActiveSection(section.id)}
            className={`pb-4 px-2 font-medium transition-colors ${
              activeSection === section.id
                ? 'text-blue-400 border-b-2 border-blue-400'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            {section.name}
          </button>
        ))}
      </div>

      {/* Tools Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {sections
          .find(s => s.id === activeSection)
          ?.tools.map((tool, index) => (
            <ToolCard
              key={index}
              title={tool.title}
              description={tool.description}
              icon={tool.icon}
              color={tool.color}
              onClick={tool.onClick}
              disabled={tool.disabled}
            />
          ))
        }
      </div>

      {/* Info Section */}
      <div className="bg-blue-900/20 border border-blue-500/30 rounded-lg p-6">
        <div className="flex items-start">
          <div className="p-2 bg-blue-600 rounded-lg mr-4">
            <Wrench className="w-5 h-5 text-white" />
          </div>
          <div>
            <h3 className="font-semibold text-blue-400 mb-2">Centro de Herramientas</h3>
            <p className="text-gray-300 text-sm">
              Esta sección está en desarrollo activo. Las herramientas se habilitarán progresivamente 
              conforme se completen las pruebas de funcionalidad y seguridad.
            </p>
            <p className="text-gray-400 text-xs mt-2">
              ¿Necesitas alguna herramienta específica? Contacta al equipo de desarrollo.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Tools;
