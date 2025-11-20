// src/pages/HistorialCierresNominaModuleDemo.jsx
import { useState } from 'react';
import { Link, Routes, Route, useNavigate, useParams } from 'react-router-dom';
import { HistorialCierresNominaPage } from '../modules/nomina/historial-cierres';
import { DevModulesButton } from '../modules/shared/auth';
import { Header, Footer } from '../modules/shared/common';
import { FiArrowLeft, FiCheckCircle, FiSearch } from 'react-icons/fi';

/**
 * Componente interno que muestra el banner y maneja la navegación
 */
const DemoLayout = () => {
  const navigate = useNavigate();
  const { clienteId } = useParams();
  const [inputValue, setInputValue] = useState(clienteId || '11');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (inputValue.trim()) {
      navigate(`/dev/modules/historial-cierres-nomina/demo/${inputValue.trim()}`);
    }
  };

  return (
    <div className="flex flex-col min-h-screen bg-gray-900 text-gray-100">
      {/* Banner de Demo con Input */}
      <div className="fixed top-4 left-1/2 transform -translate-x-1/2 z-50 w-full max-w-5xl px-4">
        <div className="bg-yellow-100 border-2 border-yellow-400 rounded-lg shadow-lg p-4">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <FiCheckCircle className="text-green-600" size={20} />
              <div>
                <span className="text-sm font-semibold text-gray-900 block">
                  DEMO: Módulo Historial de Cierres de Nómina
                </span>
                <span className="text-xs text-gray-700">
                  Filtros, estadísticas y auto-refresh para cierres en proceso
                </span>
              </div>
            </div>

            {/* Input para cambiar cliente */}
            <form onSubmit={handleSubmit} className="flex items-center gap-2">
              <label htmlFor="clienteId" className="text-sm font-medium text-gray-900 whitespace-nowrap">
                Cliente ID:
              </label>
              <input
                type="number"
                id="clienteId"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                className="w-24 px-3 py-1.5 bg-white border border-gray-300 rounded-md text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-teal-600"
                min="1"
              />
              <button
                type="submit"
                className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-teal-600 text-white rounded-md text-sm font-medium hover:bg-teal-700 transition-colors"
              >
                <FiSearch size={14} />
                Cargar
              </button>
            </form>

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
        
        {/* Contenido - HistorialCierresNominaPage */}
        <main className="flex-grow container mx-auto p-6 pt-32">
          <HistorialCierresNominaPage />
        </main>

        <Footer />
      </div>

      {/* Botón flotante de desarrollo */}
      <DevModulesButton />
    </div>
  );
};

/**
 * Demo del módulo Historial de Cierres de Nómina refactorizado
 */
const HistorialCierresNominaModuleDemo = () => {
  return (
    <Routes>
      <Route path="/:clienteId" element={<DemoLayout />} />
      <Route index element={<DemoLayout />} />
    </Routes>
  );
};

export default HistorialCierresNominaModuleDemo;
