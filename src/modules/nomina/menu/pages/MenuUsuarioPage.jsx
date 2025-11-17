import MenuCard from "../components/MenuCard";
import { getUserMenuOptions } from "../utils/menuConfig";
import { ANIMATION_DELAY_STEP, GRID_BREAKPOINTS } from "../constants/menu.constants";

/**
 * MenuUsuarioPage - Página principal del menú del sistema
 * 
 * Muestra opciones dinámicas según el tipo de usuario y áreas asignadas.
 * Obtiene la información del usuario desde localStorage y construye
 * el menú de navegación correspondiente.
 * 
 * @component
 * 
 * @example
 * // En App.jsx
 * <Route path="/menu" element={<MenuUsuarioPage />} />
 */
const MenuUsuarioPage = () => {
  // Obtener usuario del localStorage
  const usuario = JSON.parse(localStorage.getItem("usuario"));

  // DEBUG: Log del usuario y opciones
  console.log('🔍 MenuUsuarioPage - Usuario:', usuario);
  
  // Obtener opciones de menú según el usuario
  const opciones = getUserMenuOptions(usuario);
  
  console.log('📋 MenuUsuarioPage - Opciones obtenidas:', opciones);

  return (
    <div className="text-white">
      <h1 className="text-3xl font-bold mb-6 animate-fade-in">Menú Principal</h1>
      
      <div className={`grid grid-cols-1 ${GRID_BREAKPOINTS.sm} ${GRID_BREAKPOINTS.lg} gap-6`}>
        {opciones.map((opcion, index) => (
          <div
            key={opcion.label}
            className="animate-slide-up"
            style={{
              animationDelay: `${index * ANIMATION_DELAY_STEP}ms`
            }}
          >
            <MenuCard {...opcion} />
          </div>
        ))}
      </div>
      
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
    </div>
  );
};

export default MenuUsuarioPage;
