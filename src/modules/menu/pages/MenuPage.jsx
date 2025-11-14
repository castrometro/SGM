// src/modules/menu/pages/MenuPage.jsx
import MenuLayout from '../components/MenuLayout';
import MenuHero from '../components/MenuHero';
import MenuGrid from '../components/MenuGrid';
import useMenuOptions from '../hooks/useMenuOptions';
import useUserContext from '../hooks/useUserContext';

const MenuPage = () => {
  const { usuario, isAuthenticated, hasSession } = useUserContext();
  const options = useMenuOptions(usuario);

  if (!hasSession || !isAuthenticated) {
    return (
      <MenuLayout>
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-6 text-center text-gray-300">
          <p className="font-semibold text-white mb-2">Sesión no válida</p>
          <p className="text-sm">
            Para acceder al menú principal debes iniciar sesión nuevamente.
          </p>
        </div>
      </MenuLayout>
    );
  }

  if (!usuario) {
    return (
      <MenuLayout>
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-6 text-center text-gray-300">
          <p className="font-semibold text-white mb-2">No pudimos cargar tu perfil</p>
          <p className="text-sm">
            Intenta recargar la página o contacta al equipo de soporte si el problema persiste.
          </p>
        </div>
      </MenuLayout>
    );
  }

  return (
    <MenuLayout>
      <MenuHero usuario={usuario} totalOpciones={options.length} />
      <MenuGrid
        options={options.map((option) => ({
          ...option,
          descripcion: option.descripcion,
        }))}
      />
    </MenuLayout>
  );
};

export default MenuPage;
