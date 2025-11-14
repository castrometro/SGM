// src/modules/menu/components/MenuOptionCard.jsx
import PropTypes from 'prop-types';
import { useNavigate } from 'react-router-dom';

const MenuOptionCard = ({ label, descripcion, icon: Icon, color, path }) => {
  const navigate = useNavigate();

  return (
    <button
      onClick={() => navigate(path)}
      className="w-full h-full flex flex-col items-start bg-gray-800 hover:bg-gray-700 hover:shadow-xl hover:scale-[1.01] transition-all duration-200 rounded-lg p-6 shadow cursor-pointer text-left"
      type="button"
    >
      {Icon ? <Icon size={28} style={{ color }} /> : null}
      <span className="mt-4 text-lg font-semibold">{label}</span>
      <p className="text-sm text-gray-400 mt-1">{descripcion}</p>
    </button>
  );
};

MenuOptionCard.propTypes = {
  label: PropTypes.string.isRequired,
  descripcion: PropTypes.string.isRequired,
  icon: PropTypes.oneOfType([PropTypes.func, PropTypes.elementType]),
  color: PropTypes.string,
  path: PropTypes.string.isRequired,
};

MenuOptionCard.defaultProps = {
  icon: null,
  color: '#ffffff',
};

export default MenuOptionCard;
