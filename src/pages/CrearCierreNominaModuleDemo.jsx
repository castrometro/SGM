// src/pages/CrearCierreNominaModuleDemo.jsx
import { useState } from 'react';
import { Link, Routes, Route, useNavigate, useParams } from 'react-router-dom';
import { CrearCierreNominaPage } from '../modules/nomina/crear-cierre';
import { DevModulesButton } from '../modules/shared/auth';
import { Header, Footer } from '../modules/shared/common';
import { FiArrowLeft, FiCheckCircle, FiSearch } from 'react-icons/fi';

/**
 * Componente interno que muestra el banner y maneja la navegación
 */
const DemoLayout = () => {
  const navigate = useNavigate();
  const { clienteId } = useParams();
  const [inputValue, setInputValue] = useState(clienteId || '1');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (inputValue.trim()) {
      navigate(`/dev/modules/crear-cierre-nomina/demo/${inputValue.trim()}`);
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
                  DEMO: Módulo Crear Cierre de Nómina
                </span>
                <span className="text-xs text-gray-700">
                  Formulario con checklist de tareas y validaciones
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
                className="w-20 px-2 py-1 border border-gray-300 rounded text-gray-900 text-sm"
                min="1"
              />
              <button
                type="submit"
                className="px-3 py-1 bg-purple-600 hover:bg-purple-700 text-white rounded text-sm transition-colors flex items-center gap-1"
              >
                <FiSearch size={14} />
                Ir
              </button>
            </form>

            <Link
              to="/dev/modules"
              className="px-3 py-1 bg-gray-700 hover:bg-gray-600 text-white rounded text-sm transition-colors flex items-center gap-2 whitespace-nowrap"
            >
              <FiArrowLeft size={14} />
              Showcase
            </Link>
          </div>
        </div>
      </div>

      {/* Espaciado para el banner fijo */}
      <div className="h-24"></div>

      {/* Header */}
      <Header />

      {/* Contenido Principal */}
      <main className="flex-1 container mx-auto px-4 py-8">
        {clienteId ? (
          <CrearCierreNominaPage />
        ) : (
          <div className="flex items-center justify-center py-16">
            <div className="text-center">
              <p className="text-gray-400 mb-4">
                Ingresa un ID de cliente arriba para ver la página de crear cierre
              </p>
              <p className="text-gray-500 text-sm">
                Ejemplo: Cliente ID 1, 2, 11, etc.
              </p>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <Footer />

      {/* Botón flotante para volver al showcase */}
      <DevModulesButton />
    </div>
  );
};

/**
 * Demo del módulo Crear Cierre de Nómina
 */
const CrearCierreNominaModuleDemo = () => {
  return (
    <Routes>
      <Route path="/:clienteId?" element={<DemoLayout />} />
    </Routes>
  );
};

export default CrearCierreNominaModuleDemo;
