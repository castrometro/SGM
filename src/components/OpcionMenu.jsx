import { useNavigate } from "react-router-dom";

const OpcionMenu = ({ label, descripcion, icon: Icon, color, path }) => {
  const navigate = useNavigate();

  return (
    <button
      onClick={() => navigate(path)}
      className="w-full h-full flex flex-col items-start bg-gray-800 hover:bg-gray-700 hover:shadow-xl hover:scale-[1.01] transition-all duration-200 rounded-lg p-6 shadow cursor-pointer"
    >
      <Icon size={28} style={{ color }} />
      <span className="mt-4 text-lg font-semibold">{label}</span>
      <p className="text-sm text-gray-400 mt-1 text-left">{descripcion}</p>
    </button>
  );
};

export default OpcionMenu;
