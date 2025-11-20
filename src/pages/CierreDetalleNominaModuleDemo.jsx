// src/pages/CierreDetalleNominaModuleDemo.jsx
import { useState } from 'react';
import { Link, useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { FiArrowLeft, FiFileText } from 'react-icons/fi';
import { CierreDetalleNominaPage } from '../modules/nomina/cierre-detalle';
import { DevModulesButton } from '../modules/shared/auth';

/**
 * Página de demostración del módulo de cierre detalle de nómina
 * Permite ingresar un cierreId y ver el detalle completo del cierre
 */
const CierreDetalleNominaModuleDemo = () => {
  const { cierreId: cierreIdParam } = useParams();
  const navigate = useNavigate();
  const [cierreId, setCierreId] = useState(cierreIdParam || '');
  const [mostrarDetalle, setMostrarDetalle] = useState(!!cierreIdParam);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (cierreId.trim()) {
      setMostrarDetalle(true);
      navigate(`/dev/modules/cierre-detalle-nomina/demo/${cierreId}`);
    }
  };

  if (mostrarDetalle) {
    return <CierreDetalleNominaPage />;
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
                <h1 className="text-xl font-bold">Cierre Detalle de Nómina</h1>
                <p className="text-sm text-gray-400">Demo del Módulo</p>
              </div>
            </div>
            <Link to="/dev/modules/cierre-detalle-nomina/docs" className="inline-flex items-center gap-2 px-4 py-2 bg-teal-600 hover:bg-teal-700 rounded-lg text-sm font-medium transition-colors">
              <FiFileText size={16} />
              Ver Documentación
            </Link>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-12">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="max-w-2xl mx-auto">
          <div className="bg-gradient-to-br from-teal-600 to-emerald-600 rounded-lg p-8 mb-8 text-center">
            <div className="text-6xl mb-4">📊</div>
            <h2 className="text-3xl font-bold mb-2">Detalle de Cierre de Nómina</h2>
            <p className="text-teal-100">Vista completa del progreso y estado del cierre</p>
          </div>

          <div className="bg-gray-800 rounded-lg border border-gray-700 p-8">
            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <label htmlFor="cierreId" className="block text-sm font-medium text-gray-300 mb-2">
                  ID del Cierre de Nómina
                </label>
                <input
                  type="number"
                  id="cierreId"
                  value={cierreId}
                  onChange={(e) => setCierreId(e.target.value)}
                  placeholder="Ej: 123"
                  className="w-full px-4 py-3 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent"
                  required
                />
                <p className="mt-2 text-sm text-gray-400">
                  Ingresa el ID de un cierre de nómina válido para ver su detalle completo
                </p>
              </div>

              <button
                type="submit"
                className="w-full px-6 py-3 bg-teal-600 hover:bg-teal-700 text-white font-medium rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-teal-500 focus:ring-offset-2 focus:ring-offset-gray-800"
              >
                Ver Detalle del Cierre
              </button>
            </form>

            <div className="mt-8 pt-6 border-t border-gray-700">
              <h3 className="text-sm font-medium text-gray-300 mb-3">💡 Características del módulo:</h3>
              <ul className="space-y-2 text-sm text-gray-400">
                <li className="flex items-start gap-2">
                  <span className="text-green-400 mt-0.5">✓</span>
                  <span>Validación de acceso al área de Nómina</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-green-400 mt-0.5">✓</span>
                  <span>Progreso completo con 8+ tarjetas y secciones</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-green-400 mt-0.5">✓</span>
                  <span>Archivos Talana: Libro de Remuneraciones + Movimientos del Mes</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-green-400 mt-0.5">✓</span>
                  <span>Archivos Analista: Ingresos, Finiquitos, Ausentismos, Novedades</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-green-400 mt-0.5">✓</span>
                  <span>Verificador de datos con análisis automático</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-green-400 mt-0.5">✓</span>
                  <span>Incidencias encontradas con resolución</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-green-400 mt-0.5">✓</span>
                  <span>Resumen del cierre con KPIs y métricas</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-green-400 mt-0.5">✓</span>
                  <span>Auto-actualización del estado del cierre</span>
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

export default CierreDetalleNominaModuleDemo;
