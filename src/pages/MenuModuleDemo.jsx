// src/pages/MenuModuleDemo.jsx
import { Link } from 'react-router-dom';
import { MenuUsuarioPage } from '../modules/menu';
import { DevModulesButton } from '../modules/auth';
import Header from '../components/Header';
import Footer from '../components/Footer';
import { FiArrowLeft, FiCheckCircle } from 'react-icons/fi';

/**
 * Demo del módulo Menu refactorizado
 * Muestra el MenuUsuarioPage del nuevo módulo con Layout completo
 */
const MenuModuleDemo = () => {
  return (
    <div className="flex flex-col min-h-screen bg-gray-900 text-gray-100">
      {/* Banner de Demo */}
      <div className="fixed top-4 left-1/2 transform -translate-x-1/2 z-50">
        <div className="bg-yellow-100 border-2 border-yellow-400 rounded-lg shadow-lg px-6 py-3 flex items-center gap-4">
          <div className="flex items-center gap-2">
            <FiCheckCircle className="text-green-600" size={20} />
            <span className="text-sm font-semibold text-gray-900">
              DEMO: Módulo Menu Refactorizado
            </span>
          </div>
          <Link
            to="/dev/modules"
            className="inline-flex items-center gap-2 px-3 py-1.5 bg-white border border-gray-300 text-gray-700 rounded-md text-sm font-medium hover:bg-gray-50 transition-colors"
          >
            <FiArrowLeft size={14} />
            Volver al Showcase
          </Link>
        </div>
      </div>

      {/* Fondo con gradiente */}
      <div className="fixed inset-0 z-0">
        <div className="absolute inset-0 bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 opacity-80"></div>
        <div className="absolute inset-0 backdrop-blur-sm"></div>
      </div>

      {/* Contenedor principal con Header, Content y Footer */}
      <div className="relative z-10 flex flex-col min-h-screen">
        <Header />
        
        {/* Contenido - MenuUsuarioPage */}
        <main className="flex-grow container mx-auto p-6 pt-24">
          <MenuUsuarioPage />
        </main>

        <Footer />
      </div>

      {/* Botón flotante de desarrollo */}
      <DevModulesButton />
    </div>
  );
};

export default MenuModuleDemo;
