import { useNavigate } from "react-router-dom";
import {
  History,
  FilePlus,
  BookOpenCheck,
  FolderOpen,
  FileText,
  Users,
  ListChecks,
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
      {
        label: "Ver Cuentas",
        icon: BookOpenCheck,
        color: "#FBBF24",
        action: () => navigate(`/menu/clientes/${clienteId}/cuentas`),
      },
      {
        label: "Archivos Subidos",
        icon: FolderOpen,
        color: "#F472B6",
        action: () => navigate(`/menu/clientes/${clienteId}/archivos`),
      },
    ],
  };

  // Si hay más de un área en el futuro, lo tienes cubierto
  const botones = botonesPorArea[areaActiva] || [];

  return (
    <div className={`grid ${botones.length <= 2 ? "grid-cols-2" : botones.length <= 4 ? "grid-cols-2 md:grid-cols-4" : "grid-cols-2 md:grid-cols-3"} gap-4`}>
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
