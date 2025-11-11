// src/pages/AuthModuleDemo.jsx
import { Link } from 'react-router-dom';
import { LoginPage, DevModulesButton } from '../modules/auth';
import { FiArrowLeft, FiCheckCircle } from 'react-icons/fi';

/**
 * Demo del módulo Auth refactorizado
 * Muestra el LoginPage del nuevo módulo
 */
const AuthModuleDemo = () => {
  return (
    <div className="relative">
      {/* Banner de Demo */}
      <div className="absolute top-4 left-1/2 transform -translate-x-1/2 z-50">
        <div className="bg-yellow-100 border-2 border-yellow-400 rounded-lg shadow-lg px-6 py-3 flex items-center gap-4">
          <div className="flex items-center gap-2">
            <FiCheckCircle className="text-green-600" size={20} />
            <span className="text-sm font-semibold text-gray-900">
              DEMO: Módulo Auth Refactorizado
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

      {/* Componente LoginPage del módulo refactorizado */}
      <LoginPage />

      {/* Botón flotante de desarrollo */}
      <DevModulesButton />
    </div>
  );
};

export default AuthModuleDemo;
