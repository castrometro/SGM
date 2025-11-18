// src/modules/contabilidad/cliente-detalle/components/ClienteActionButtons.jsx
import { useNavigate } from "react-router-dom";
import {
  History,
  FilePlus,
  BarChart3,
  BookOpen,
  Wrench,
  ArrowRight
} from "lucide-react";

/**
 * Botones de acción para cliente de Contabilidad
 * Permite navegar a dashboard, cierres, libros y herramientas
 */
const ClienteActionButtons = ({ clienteId }) => {
  const navigate = useNavigate();
  
  const botones = [
    {
      label: "Dashboard Contabilidad",
      description: "Ver análisis completo",
      icon: BarChart3,
      gradient: "from-purple-500 to-indigo-600",
      iconBg: "from-purple-500/20 to-indigo-500/20",
      borderColor: "border-purple-500/30",
      hoverBorder: "hover:border-purple-400",
      action: () => navigate(`/menu/contabilidad/clientes/${clienteId}/dashboard`),
    },
    {
      label: "Crear Cierre",
      description: "Nuevo cierre contable",
      icon: FilePlus,
      gradient: "from-blue-500 to-cyan-600",
      iconBg: "from-blue-500/20 to-cyan-500/20",
      borderColor: "border-blue-500/30",
      hoverBorder: "hover:border-blue-400",
      action: () => navigate(`/menu/clientes/${clienteId}/crear-cierre`),
    },
    {
      label: "Historial de Cierres",
      description: "Ver todos los cierres",
      icon: History,
      gradient: "from-indigo-500 to-purple-600",
      iconBg: "from-indigo-500/20 to-purple-500/20",
      borderColor: "border-indigo-500/30",
      hoverBorder: "hover:border-indigo-400",
      action: () => navigate(`/menu/clientes/${clienteId}/cierres`),
    },
    {
      label: "Libros Contables",
      description: "Consultar libros",
      icon: BookOpen,
      gradient: "from-teal-500 to-emerald-600",
      iconBg: "from-teal-500/20 to-emerald-500/20",
      borderColor: "border-teal-500/30",
      hoverBorder: "hover:border-teal-400",
      action: () => navigate(`/menu/contabilidad/clientes/${clienteId}/libros`),
    },
    {
      label: "Herramientas",
      description: "Utilidades contables",
      icon: Wrench,
      gradient: "from-amber-500 to-orange-600",
      iconBg: "from-amber-500/20 to-orange-500/20",
      borderColor: "border-amber-500/30",
      hoverBorder: "hover:border-amber-400",
      action: () => navigate(`/menu/contabilidad/tools`),
    },
  ];

  return (
    <div className="bg-gray-800 rounded-lg p-6 shadow-lg border border-gray-700">
      <h3 className="text-lg font-semibold text-white mb-1">Acciones Rápidas</h3>
      <p className="text-sm text-gray-400 mb-6">Gestiona las operaciones del cliente</p>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {botones.map((btn, idx) => {
          const Icon = btn.icon;
          return (
            <button
              key={idx}
              onClick={btn.action}
              className={`group relative overflow-hidden bg-gradient-to-br from-gray-700/40 to-gray-800/40 
                rounded-xl p-5 border ${btn.borderColor} ${btn.hoverBorder} 
                hover:shadow-xl transition-all duration-300 hover:-translate-y-1 text-left`}
            >
              {/* Fondo con gradiente en hover */}
              <div className={`absolute inset-0 bg-gradient-to-br ${btn.gradient} opacity-0 
                group-hover:opacity-10 transition-opacity duration-300`} />
              
              <div className="relative z-10">
                {/* Icono */}
                <div className={`inline-flex items-center justify-center w-12 h-12 rounded-lg 
                  bg-gradient-to-br ${btn.iconBg} border ${btn.borderColor} mb-3
                  group-hover:scale-110 transition-transform duration-300`}>
                  <Icon className="w-6 h-6 text-white" />
                </div>
                
                {/* Texto */}
                <div className="mb-2">
                  <h4 className="text-base font-semibold text-white mb-1 
                    group-hover:text-white transition-colors">
                    {btn.label}
                  </h4>
                  <p className="text-xs text-gray-400 group-hover:text-gray-300 transition-colors">
                    {btn.description}
                  </p>
                </div>
                
                {/* Flecha */}
                <div className="flex items-center justify-end">
                  <ArrowRight className="w-4 h-4 text-gray-500 group-hover:text-white 
                    group-hover:translate-x-1 transition-all duration-300" />
                </div>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
};

export default ClienteActionButtons;
