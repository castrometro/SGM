import OpcionMenu from "../../../components/OpcionMenu";
import { UI_CONFIG } from '../config/menuConfig';

/**
 * Componente que renderiza el grid de opciones del menú
 * con animaciones y efectos de hover
 */
const MenuGrid = ({ opciones }) => {
  const { cardOpacity, animationDelay } = UI_CONFIG;

  if (!opciones || opciones.length === 0) {
    return (
      <div className="text-center text-gray-400 py-8">
        <p>No hay opciones disponibles para tu usuario.</p>
      </div>
    );
  }

  return (
    <>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {opciones.map((opcion, index) => (
          <div
            key={opcion.label}
            className="animate-slide-up"
            style={{
              animationDelay: `${index * animationDelay}ms`,
              opacity: cardOpacity,
              transition: 'opacity 0.2s ease'
            }}
            onMouseEnter={(e) => e.currentTarget.style.opacity = '1'}
            onMouseLeave={(e) => e.currentTarget.style.opacity = cardOpacity}
          >
            <OpcionMenu {...opcion} />
          </div>
        ))}
      </div>
      
      {/* Estilos de animación */}
      <style>
        {`
          @keyframes fade-in {
            from {
              opacity: 0;
              transform: translateY(-10px);
            }
            to {
              opacity: 1;
              transform: translateY(0);
            }
          }
          
          @keyframes slide-up {
            from {
              opacity: 0;
              transform: translateY(20px);
            }
            to {
              opacity: 1;
              transform: translateY(0);
            }
          }
          
          .animate-fade-in {
            animation: fade-in 0.8s ease-out;
          }
          
          .animate-slide-up {
            animation: slide-up 0.6s ease-out both;
          }
        `}
      </style>
    </>
  );
};

export default MenuGrid;
