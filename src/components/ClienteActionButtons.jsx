import { useNavigate } from "react-router-dom";
import {
  History,
  FilePlus,
  BookOpenCheck,
  FolderOpen,
  FileText,
  Users,
  ListChecks
} from "lucide-react";

const ClienteActionButtons = ({ clienteId, areaActiva }) => {
  const navigate = useNavigate();
  // Botones para cada área (puedes adaptar/expandir)
  const botonesPorArea = {
    "Contabilidad": [
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
        label: "Libro de Remuneraciones",
        icon: FileText,
        color: "#FBBF24",
        action: () => navigate(`/menu/nomina/clientes/${clienteId}/libro-remuneraciones`),
      },
      {
        label: "Movimientos del Mes",
        icon: Users,
        color: "#C084FC",
        action: () => navigate(`/menu/nomina/clientes/${clienteId}/movimientos-mes`),
      },
      {
        label: "Checklists",
        icon: ListChecks,
        color: "#F472B6",
        action: () => navigate(`/menu/nomina/clientes/${clienteId}/checklists`),
      }
      // Puedes agregar más según lo que se use en Nómina
    ],
  };

  // Si hay más de un área en el futuro, lo tienes cubierto
  const botones = botonesPorArea[areaActiva] || [];

  return (
    <div className={`grid ${botones.length <= 2 ? "grid-cols-2" : "grid-cols-3"} gap-4`}>
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
