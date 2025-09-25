import { useNavigate } from "react-router-dom";
import {
  History,
  FilePlus,
  BookOpenCheck,
  FolderOpen,
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
    "Nomina": [
      {
        label: "Dashboard Nómina",
        icon: BarChart3,
        color: "#10B981",
        action: () => navigate(`/menu/nomina/clientes/${clienteId}/dashboard`),
      },
      {
        label: "Crear Cierre",
        icon: FilePlus,
        color: "#34D399",
        action: () => navigate(`/menu/clientes/${clienteId}/crear-cierre`),
      },
      {
        label: "Historial de Cierres",
        icon: History,
        color: "#60A5FA",
        action: () => navigate(`/menu/clientes/${clienteId}/cierres`),
      },
      // Puedes agregar más según lo que se use en Nómina
    ],
  };

  // Si hay más de un área en el futuro, lo tienes cubierto
  const botones = botonesPorArea[areaActiva] || [];

  return (
    <div
      className="grid gap-4"
      style={{
        gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))'
      }}
    >
      {botones.map(({ label, icon: Icon, color, action }) => (
        <button
          key={label}
          type="button"
          onClick={action}
          className="group relative flex flex-col items-center justify-center rounded-lg border border-gray-600/40 bg-gray-800/80 backdrop-blur-sm p-4 min-h-[110px] shadow-sm hover:shadow-md hover:border-gray-500/70 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 focus:ring-offset-gray-900 transition"
        >
          <div className="absolute inset-0 rounded-lg opacity-0 group-hover:opacity-100 bg-gradient-to-br from-white/5 to-white/0 pointer-events-none transition" />
          <div className="flex items-center justify-center w-12 h-12 rounded-full mb-1" style={{ background: color + '20' }}>
            <Icon size={26} style={{ color }} />
          </div>
          <span className="mt-1 text-[13px] font-medium text-gray-200 text-center leading-tight tracking-wide">
            {label}
          </span>
        </button>
      ))}
    </div>
  );
};

export default ClienteActionButtons;
