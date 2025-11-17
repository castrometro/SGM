// src/pages/HerramientasNominaModuleDemo.jsx
import { Link } from 'react-router-dom';
import { HerramientasNominaPage } from '../modules/nomina/herramientas';
import { DevModulesButton } from '../modules/shared/auth';
import { Header, Footer } from '../modules/shared/common';
import { FiArrowLeft, FiCheckCircle } from 'react-icons/fi';

/**
 * Demo del módulo Herramientas de Nómina refactorizado
 * Muestra la página de herramientas con Layout completo
 * Usa el usuario real del localStorage
 */
const HerramientasNominaModuleDemo = () => {
  return (
    <div className="flex flex-col min-h-screen bg-gray-900 text-gray-100">
      {/* Banner de Demo */}
      <div className="fixed top-4 left-1/2 transform -translate-x-1/2 z-50 w-full max-w-4xl px-4">
        <div className="bg-yellow-100 border-2 border-yellow-400 rounded-lg shadow-lg p-4">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <FiCheckCircle className="text-green-600" size={20} />
              <div>
                <span className="text-sm font-semibold text-gray-900 block">
                  DEMO: Módulo Herramientas de Nómina
                </span>
                <span className="text-xs text-gray-700">
                  Utilidades y recursos para gestión de nómina
                </span>
              </div>
            </div>

            <Link
              to="/dev/modules"
              className="inline-flex items-center gap-2 px-3 py-1.5 bg-white border border-gray-300 text-gray-700 rounded-md text-sm font-medium hover:bg-gray-50 transition-colors"
            >
              <FiArrowLeft size={14} />
              Volver
            </Link>
          </div>
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
        
        {/* Contenido - HerramientasNominaPage */}
        <main className="flex-grow container mx-auto p-6 pt-32">
          <HerramientasNominaPage />
        </main>

        <Footer />
      </div>

      {/* Botón flotante de desarrollo */}
      <DevModulesButton />
    </div>
  );
};

export default HerramientasNominaModuleDemo;
