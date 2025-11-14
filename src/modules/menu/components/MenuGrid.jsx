// src/modules/menu/components/MenuGrid.jsx
import PropTypes from 'prop-types';
import MenuOptionCard from './MenuOptionCard';
import { EMPTY_STATE_COPY } from '../data/menu-options.map';
import './MenuAnimations.css';

const MenuGrid = ({ options }) => {
  if (!options.length) {
    return (
      <div className="bg-gray-900 border border-gray-800 rounded-lg p-6 text-center text-gray-400">
        <p className="font-semibold text-white mb-2">{EMPTY_STATE_COPY.title}</p>
        <p className="text-sm">{EMPTY_STATE_COPY.description}</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
      {options.map((option, index) => {
        const { key, animationDelay, initialOpacity, ...cardProps } = option;
        const baseOpacity = initialOpacity ?? 1;

        return (
          <div
            key={key ?? cardProps.label}
            className="animate-menu-slide-up"
            style={{
              animationDelay: animationDelay ?? `${index * 100}ms`,
              opacity: baseOpacity,
              transition: 'opacity 0.2s ease',
            }}
            onMouseEnter={(event) => {
              event.currentTarget.style.opacity = '1';
            }}
            onMouseLeave={(event) => {
              event.currentTarget.style.opacity = `${baseOpacity}`;
            }}
          >
            <MenuOptionCard {...cardProps} />
          </div>
        );
      })}
    </div>
  );
};

MenuGrid.propTypes = {
  options: PropTypes.arrayOf(
    PropTypes.shape({
      key: PropTypes.string,
      label: PropTypes.string.isRequired,
      descripcion: PropTypes.string.isRequired,
      icon: PropTypes.oneOfType([PropTypes.func, PropTypes.elementType]),
      color: PropTypes.string,
      path: PropTypes.string.isRequired,
      animationDelay: PropTypes.string,
      initialOpacity: PropTypes.number,
    }),
  ),
};

MenuGrid.defaultProps = {
  options: [],
};

export default MenuGrid;
