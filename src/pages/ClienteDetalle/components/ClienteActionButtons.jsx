import { useNavigate } from "react-router-dom";
import {
  History,
  FilePlus,
  BarChart3
} from "lucide-react";

const ClienteActionButtons = ({ clienteId, areaActiva }) => {
  const navigate = useNavigate();
  // Botones para cada área (puedes adaptar/expandir)
  const botonesPorArea = {
    "Contabilidad": [
      {
        label: "Dashboard Contable",
        icon: BarChart3,
        color: "#8B5CF6",
        action: () => {
          const streamlitUrl = `http://172.17.11.18:8502/?cliente_id=${clienteId}`;
          window.open(streamlitUrl, '_blank');
        },
      },
      {
        label: "Historial de Cierres",
        icon: History,
        color: "#60A5FA",
        action: () => navigate(`/menu/clientes/${clienteId}/cierres`),
      },
      {
        label: "Crear Cierre",
        icon: FilePlus,
        color: "#34D399",
        action: () => navigate(`/menu/clientes/${clienteId}/crear-cierre`),
      },
    ],
    "Payroll": [
      {
        label: "Dashboard Payroll",
        icon: BarChart3,
        color: "#10B981",
        action: () => {
          // TODO: Implementar dashboard Streamlit para payroll
          console.log("Dashboard Payroll - En desarrollo");
        },
      },
      {
        label: "Historial de Cierres",
        icon: History,
        color: "#60A5FA",
        action: () => navigate(`/menu/clientes/${clienteId}/cierres-payroll`),
      },
      {
        label: "Crear Cierre",
        icon: FilePlus,
        color: "#34D399",
        action: () => navigate(`/menu/clientes/${clienteId}/crear-cierre-payroll`),
      },
    ],
    "Nomina": [
      {
        label: "Dashboard Payroll",
        icon: BarChart3,
        color: "#10B981",
        action: () => {
          // TODO: Implementar dashboard Streamlit para payroll
          console.log("Dashboard Payroll - En desarrollo");
        },
      },
      {
        label: "Historial de Cierres",
        icon: History,
        color: "#60A5FA",
        action: () => navigate(`/menu/clientes/${clienteId}/cierres-payroll`),
      },
      {
        label: "Crear Cierre",
        icon: FilePlus,
        color: "#34D399",
        action: () => navigate(`/menu/clientes/${clienteId}/crear-cierre-payroll`),
      },
    ],
  };

  // Si hay más de un área en el futuro, lo tienes cubierto
  const botones = botonesPorArea[areaActiva] || [];

  // Debug temporal para verificar qué área está activa
  console.log("ClienteActionButtons - Área activa:", areaActiva);
  console.log("ClienteActionButtons - Botones disponibles:", botones.length);

  return (
    <div className="grid gap-4" style={{ gridTemplateColumns: `repeat(${botones.length}, 1fr)` }}>
      {botones.map(({ label, icon: Icon, color, action }) => (
        <button
          key={label}
          onClick={action}
          className="flex flex-col items-center justify-center bg-gray-800 hover:bg-gray-700 hover:shadow-xl hover:scale-[1.02] transition-all duration-300 rounded-lg p-4 shadow cursor-pointer"
        >
          <Icon size={28} style={{ color }} />
          <span className="mt-2 text-sm text-white text-center">{label}</span>
        </button>
      ))}
    </div>
  );
};

export default ClienteActionButtons;
