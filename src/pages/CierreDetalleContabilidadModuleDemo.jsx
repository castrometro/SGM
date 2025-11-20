// src/pages/CierreDetalleContabilidadModuleDemo.jsx
import { useState } from 'react';
import { Link, useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { FiArrowLeft, FiFileText } from 'react-icons/fi';
import { CierreDetalleContabilidadPage } from '../modules/contabilidad/cierre-detalle';
import { DevModulesButton } from '../modules/shared/auth';

/**
 * Página de demostración del módulo de cierre detalle de contabilidad
 * Permite ingresar un cierreId y ver el detalle completo del cierre
 */
const CierreDetalleContabilidadModuleDemo = () => {
  const { cierreId: cierreIdParam } = useParams();
  const navigate = useNavigate();
  const [cierreId, setCierreId] = useState(cierreIdParam || '');
  const [mostrarDetalle, setMostrarDetalle] = useState(!!cierreIdParam);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (cierreId.trim()) {
      setMostrarDetalle(true);
      navigate(`/dev/modules/cierre-detalle-contabilidad/demo/${cierreId}`);
    }
  };

  if (mostrarDetalle) {
    return <CierreDetalleContabilidadPage />;
  }

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100">
      <header className="bg-gray-800 border-b border-gray-700 sticky top-0 z-40">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link to="/dev/modules" className="inline-flex items-center gap-2 px-3 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm font-medium transition-colors">
                <FiArrowLeft size={16} />
                Volver
              </Link>
              <div>
                <h1 className="text-xl font-bold">Cierre Detalle de Contabilidad</h1>
                <p className="text-sm text-gray-400">Demo del Módulo</p>
              </div>
            </div>
            <Link to="/dev/modules/cierre-detalle-contabilidad/docs" className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-medium transition-colors">
              <FiFileText size={16} />
              Ver Documentación
            </Link>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-12">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="max-w-2xl mx-auto">
          <div className="bg-gradient-to-br from-blue-600 to-indigo-600 rounded-lg p-8 mb-8 text-center">
            <div className="text-6xl mb-4">📊</div>
            <h2 className="text-3xl font-bold mb-2">Detalle de Cierre de Contabilidad</h2>
            <p className="text-blue-100">Vista completa del progreso y estado del cierre contable</p>
          </div>

          <div className="bg-gray-800 rounded-lg border border-gray-700 p-8">
            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <label htmlFor="cierreId" className="block text-sm font-medium text-gray-300 mb-2">
                  ID del Cierre Contable
                </label>
                <input
                  type="number"
                  id="cierreId"
                  value={cierreId}
                  onChange={(e) => setCierreId(e.target.value)}
                  placeholder="Ej: 123"
                  className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  required
                />
                <p className="mt-2 text-sm text-gray-400">
                  Ingresa el ID de un cierre contable válido para ver su detalle completo
                </p>
              </div>

              <button
                type="submit"
                className="w-full px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition-colors shadow-lg hover:shadow-xl"
              >
                Ver Detalle del Cierre
              </button>
            </form>

            <div className="mt-8 p-4 bg-gray-900 rounded-lg border border-gray-700">
              <h3 className="text-sm font-semibold text-gray-300 mb-3">ℹ️ Información</h3>
              <ul className="space-y-2 text-sm text-gray-400">
                <li className="flex items-start gap-2">
                  <span className="text-blue-400 mt-0.5">•</span>
                  <span>Este módulo muestra el progreso completo de un cierre contable</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-blue-400 mt-0.5">•</span>
                  <span>Incluye: Tipo de Documento, Clasificación de Cuentas, Nombres en Inglés y Libro Mayor</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-blue-400 mt-0.5">•</span>
                  <span>Cada tarjeta permite subir archivos, ver progreso y gestionar el proceso</span>
                </li>
              </ul>
            </div>
          </div>
        </motion.div>
      </div>

      <DevModulesButton />
    </div>
  );
};

export default CierreDetalleContabilidadModuleDemo;
