import { useNavigate } from "react-router-dom";
import { CARD_OPACITY } from "../constants/menu.constants";

/**
 * MenuCard - Tarjeta individual de opción de menú
 * 
 * @component
 * @param {Object} props
 * @param {string} props.label - Título de la opción
 * @param {string} props.descripcion - Descripción breve de la funcionalidad
 * @param {React.Component} props.icon - Componente de icono de Lucide React
 * @param {string} props.color - Color hex para el icono
 * @param {string} props.path - Ruta de navegación con React Router
 * 
 * @example
 * <MenuCard 
 *   label="Clientes"
 *   descripcion="Ver tus clientes asignados"
 *   icon={FolderKanban}
 *   color="#4F46E5"
 *   path="/menu/clientes"
 * />
 */
const MenuCard = ({ label, descripcion, icon: Icon, color, path }) => {
  const navigate = useNavigate();

  return (
    <button
      onClick={() => navigate(path)}
      className="w-full h-full flex flex-col items-start bg-gray-800 hover:bg-gray-700 hover:shadow-xl hover:scale-[1.01] transition-all duration-200 rounded-lg p-6 shadow cursor-pointer"
      style={{
        opacity: CARD_OPACITY,
        transition: 'opacity 0.2s ease, transform 0.2s ease, box-shadow 0.2s ease'
      }}
      onMouseEnter={(e) => e.currentTarget.style.opacity = '1'}
      onMouseLeave={(e) => e.currentTarget.style.opacity = CARD_OPACITY}
    >
      <Icon size={28} style={{ color }} />
      <span className="mt-4 text-lg font-semibold">{label}</span>
      <p className="text-sm text-gray-400 mt-1 text-left">{descripcion}</p>
    </button>
  );
};

export default MenuCard;
