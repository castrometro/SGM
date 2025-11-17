import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import ToolCard from "../components/ToolCard";
import CategoryTabs from "../components/CategoryTabs";
import InfoBanner from "../components/InfoBanner";
import { getToolCategories, getToolsStats } from "../utils/toolsConfig";
import { TOOL_CATEGORIES } from "../constants/herramientas.constants";

/**
 * Normaliza una cadena removiendo acentos y convirtiendo a minúsculas
 */
const normalizar = (str) => {
  if (!str) return '';
  return str.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
};

/**
 * HerramientasNominaPage - Página principal de herramientas de Nómina
 * 
 * Muestra herramientas organizadas por categorías con navegación por tabs.
 * Permite acceder a utilidades específicas de nómina.
 * Valida que el usuario tenga acceso al área de Nómina.
 * 
 * @component
 * 
 * @example
 * // En App.jsx
 * <Route path="/menu/nomina/tools/*" element={<HerramientasNominaRouter />} />
 */
const HerramientasNominaPage = () => {
  const [activeCategory, setActiveCategory] = useState(TOOL_CATEGORIES.GENERAL);
  const [hasAccess, setHasAccess] = useState(null);
  const navigate = useNavigate();
  
  // Validar acceso al área de Nómina
  useEffect(() => {
    try {
      const usuarioStr = localStorage.getItem('usuario');
      if (!usuarioStr) {
        setHasAccess(false);
        return;
      }
      
      const usuario = JSON.parse(usuarioStr);
      
      // Verificar si el usuario tiene acceso a Nómina
      const tieneAccesoNomina = usuario.areas?.some(area => {
        const areaNombre = typeof area === 'string' ? area : area.nombre;
        return normalizar(areaNombre) === 'nomina';
      });
      
      setHasAccess(tieneAccesoNomina);
      
      if (!tieneAccesoNomina) {
        console.warn('Usuario no tiene acceso al área de Nómina');
      }
    } catch (error) {
      console.error('Error al validar acceso:', error);
      setHasAccess(false);
    }
  }, []);
  
  // Mostrar mensaje de carga mientras valida
  if (hasAccess === null) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-gray-400">Validando acceso...</div>
      </div>
    );
  }
  
  // Si no tiene acceso, mostrar mensaje
  if (!hasAccess) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="max-w-md mx-auto text-center p-8">
          <div className="text-red-400 text-5xl mb-4">⚠️</div>
          <h2 className="text-2xl font-bold text-gray-100 mb-2">Acceso Denegado</h2>
          <p className="text-gray-400 mb-6">
            No tienes permisos para acceder a las herramientas de Nómina.
          </p>
          <button
            onClick={() => navigate('/menu')}
            className="px-6 py-2 bg-teal-600 hover:bg-teal-700 text-white rounded-lg transition-colors"
          >
            Volver al Menú
          </button>
        </div>
      </div>
    );
  }
  
  const categories = getToolCategories();
  const stats = getToolsStats();
  
  const activeTools = categories.find(c => c.id === activeCategory)?.tools || [];

  const handleToolClick = (tool) => {
    if (tool.path) {
      navigate(tool.path);
    } else {
      console.log('Herramienta en desarrollo:', tool.title);
    }
  };

  return (
    <div className="text-white space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between"
      >
        <div className="flex-1">
          <h1 className="text-3xl font-bold mb-2">Herramientas de Nómina</h1>
          <p className="text-gray-400">
            Utilidades y recursos para la gestión integral de nómina
          </p>
        </div>
      </motion.div>

      {/* Stats Cards */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="grid grid-cols-2 md:grid-cols-4 gap-4"
      >
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
          <div className="text-2xl font-bold text-white mb-1">{stats.total}</div>
          <div className="text-sm text-gray-400">Total Herramientas</div>
        </div>
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
          <div className="text-2xl font-bold text-green-400 mb-1">{stats.available}</div>
          <div className="text-sm text-gray-400">Disponibles</div>
        </div>
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
          <div className="text-2xl font-bold text-blue-400 mb-1">{stats.beta}</div>
          <div className="text-sm text-gray-400">En Beta</div>
        </div>
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
          <div className="text-2xl font-bold text-yellow-400 mb-1">{stats.comingSoon}</div>
          <div className="text-sm text-gray-400">Próximamente</div>
        </div>
      </motion.div>

      {/* Category Tabs */}
      <CategoryTabs
        categories={categories}
        activeCategory={activeCategory}
        onCategoryChange={setActiveCategory}
      />

      {/* Tools Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {activeTools.map((tool, index) => (
          <ToolCard
            key={index}
            title={tool.title}
            description={tool.description}
            icon={tool.icon}
            color={tool.color}
            onClick={() => handleToolClick(tool)}
            status={tool.status}
            index={index}
          />
        ))}
      </div>

      {/* Info Banner */}
      <InfoBanner />
    </div>
  );
};

export default HerramientasNominaPage;
