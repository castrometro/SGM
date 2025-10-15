import { useNavigate } from "react-router-dom";
import {
  History,
  FilePlus,
  BookOpenCheck,
  FolderOpen,
  BarChart3,
  ArrowRight
} from "lucide-react";

const ClienteActionButtons = ({ clienteId, areaActiva }) => {
  const navigate = useNavigate();
  
  // Botones para cada área (puedes adaptar/expandir)
  const botonesPorArea = {
    "Contabilidad": [
      {
        label: "Dashboard Contable",
        description: "Ver análisis completo",
        icon: BarChart3,
        gradient: "from-purple-500 to-indigo-600",
        iconBg: "from-purple-500/20 to-indigo-500/20",
        borderColor: "border-purple-500/30",
        hoverBorder: "hover:border-purple-400",
        action: () => {
          const streamlitUrl = `http://172.17.11.18:8502/?cliente_id=${clienteId}`;
          window.open(streamlitUrl, '_blank');
        },
      },
      {
        label: "Historial de Cierres",
        description: "Ver todos los cierres",
        icon: History,
        gradient: "from-blue-500 to-cyan-600",
        iconBg: "from-blue-500/20 to-cyan-500/20",
        borderColor: "border-blue-500/30",
        hoverBorder: "hover:border-blue-400",
        action: () => navigate(`/menu/clientes/${clienteId}/cierres`),
      },
      {
        label: "Crear Cierre",
        description: "Nuevo cierre contable",
        icon: FilePlus,
        gradient: "from-emerald-500 to-green-600",
        iconBg: "from-emerald-500/20 to-green-500/20",
        borderColor: "border-emerald-500/30",
        hoverBorder: "hover:border-emerald-400",
        action: () => navigate(`/menu/clientes/${clienteId}/crear-cierre`),
      },
      {
        label: "Ver Cuentas",
        description: "Plan de cuentas",
        icon: BookOpenCheck,
        gradient: "from-amber-500 to-orange-600",
        iconBg: "from-amber-500/20 to-orange-500/20",
        borderColor: "border-amber-500/30",
        hoverBorder: "hover:border-amber-400",
        action: () => navigate(`/menu/clientes/${clienteId}/cuentas`),
      },
      {
        label: "Archivos Subidos",
        description: "Gestión de archivos",
        icon: FolderOpen,
        gradient: "from-pink-500 to-rose-600",
        iconBg: "from-pink-500/20 to-rose-500/20",
        borderColor: "border-pink-500/30",
        hoverBorder: "hover:border-pink-400",
        action: () => navigate(`/menu/clientes/${clienteId}/archivos`),
      },
    ],
    "Nomina": [
      {
        label: "Dashboard Nómina",
        description: "Ver análisis completo",
        icon: BarChart3,
        gradient: "from-emerald-500 to-teal-600",
        iconBg: "from-emerald-500/20 to-teal-500/20",
        borderColor: "border-emerald-500/30",
        hoverBorder: "hover:border-emerald-400",
        action: () => navigate(`/menu/nomina/clientes/${clienteId}/dashboard`),
      },
      {
        label: "Crear Cierre",
        description: "Nuevo cierre de nómina",
        icon: FilePlus,
        gradient: "from-blue-500 to-indigo-600",
        iconBg: "from-blue-500/20 to-indigo-500/20",
        borderColor: "border-blue-500/30",
        hoverBorder: "hover:border-blue-400",
        action: () => navigate(`/menu/clientes/${clienteId}/crear-cierre`),
      },
      {
        label: "Historial de Cierres",
        description: "Ver todos los cierres",
        icon: History,
        gradient: "from-purple-500 to-pink-600",
        iconBg: "from-purple-500/20 to-pink-500/20",
        borderColor: "border-purple-500/30",
        hoverBorder: "hover:border-purple-400",
        action: () => navigate(`/menu/clientes/${clienteId}/cierres`),
      },
    ],
  };

  const botones = botonesPorArea[areaActiva] || [];

  return (
    <div className="space-y-4">
      {/* Título de sección */}
      <div className="flex items-center justify-center gap-3">
        <h3 className="text-lg font-semibold text-white">Acciones Rápidas</h3>
        <span className="text-xs text-gray-400 bg-gray-800/50 px-2 py-1 rounded-full">
          {botones.length} opciones
        </span>
      </div>

      {/* Grid de botones centrado */}
      <div className="flex justify-center w-full">
        <div className="inline-grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {botones.map(({ label, description, icon: Icon, gradient, iconBg, borderColor, hoverBorder, action }) => (
          <button
            key={label}
            type="button"
            onClick={action}
            className={`group relative flex flex-col bg-gradient-to-br from-gray-800/80 to-gray-900/80 backdrop-blur-sm rounded-xl p-5 border ${borderColor} ${hoverBorder} hover:shadow-2xl hover:-translate-y-1 transition-all duration-300 overflow-hidden w-64`}
          >
            {/* Gradiente de fondo animado en hover */}
            <div className={`absolute inset-0 bg-gradient-to-br ${gradient} opacity-0 group-hover:opacity-10 transition-opacity duration-300`} />
            
            {/* Contenido */}
            <div className="relative z-10 flex flex-col h-full">
              {/* Icono con gradiente */}
              <div className={`flex items-center justify-center w-14 h-14 rounded-xl bg-gradient-to-br ${iconBg} border ${borderColor} mb-4 group-hover:scale-110 transition-transform duration-300`}>
                <Icon size={28} className="text-white" />
              </div>
              
              {/* Textos */}
              <div className="flex-1 mb-3">
                <h4 className="text-base font-semibold text-white mb-1 group-hover:text-white transition-colors">
                  {label}
                </h4>
                <p className="text-xs text-gray-400 leading-relaxed">
                  {description}
                </p>
              </div>
              
              {/* Flecha indicadora */}
              <div className="flex items-center justify-end">
                <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-white/5 border border-white/10 group-hover:bg-white/10 group-hover:border-white/20 transition-all duration-300">
                  <ArrowRight size={16} className="text-gray-400 group-hover:text-white group-hover:translate-x-0.5 transition-all duration-300" />
                </div>
              </div>
            </div>

            {/* Efecto de brillo en hover */}
            <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none">
              <div className="absolute inset-0 bg-gradient-to-br from-white/[0.05] via-transparent to-transparent" />
            </div>

            {/* Borde brillante en hover */}
            <div className="absolute inset-0 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300">
              <div className={`absolute inset-0 rounded-xl bg-gradient-to-br ${gradient} opacity-20 blur-xl`} />
            </div>
          </button>
        ))}
        </div>
      </div>
    </div>
  );
};

export default ClienteActionButtons;
