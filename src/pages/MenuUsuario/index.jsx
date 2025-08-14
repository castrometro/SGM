import { useMenuOptions } from './hooks/useMenuOptions';
import MenuGrid from './components/MenuGrid';
import AreaIndicators from './components/AreaIndicators';

/**
 * Página principal del menú de usuario
 * Muestra opciones personalizadas según el tipo de usuario y sus áreas asignadas
 */
const MenuUsuario = () => {
  // Obtener datos del usuario desde localStorage
  const usuario = JSON.parse(localStorage.getItem("usuario"));
  
  // Generar opciones de menú usando el hook personalizado
  const opciones = useMenuOptions(usuario);

  return (
    <div className="text-white">
      <h1 className="text-3xl font-bold mb-6 animate-fade-in">
        Menú Principal
      </h1>
      
      {/* Indicadores de áreas activas */}
      <AreaIndicators usuario={usuario} />
      
      <MenuGrid opciones={opciones} />
    </div>
  );
};

export default MenuUsuario;
