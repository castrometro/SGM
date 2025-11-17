import { AlertTriangle } from "lucide-react";
import { motion } from "framer-motion";
import { TOOL_STATUS } from "../constants/herramientas.constants";

/**
 * ToolCard - Card individual para cada herramienta
 * 
 * @param {string} title - Título de la herramienta
 * @param {string} description - Descripción breve
 * @param {Component} icon - Ícono de Lucide React
 * @param {string} color - Clase de color de Tailwind
 * @param {Function} onClick - Callback al hacer click
 * @param {string} status - Estado de la herramienta (available, coming_soon, beta, maintenance)
 * @param {number} index - Índice para animación escalonada
 */
const ToolCard = ({ 
  title, 
  description, 
  icon: Icon, 
  color, 
  onClick, 
  status = TOOL_STATUS.AVAILABLE,
  index = 0 
}) => {
  const disabled = status !== TOOL_STATUS.AVAILABLE && status !== TOOL_STATUS.BETA;
  
  const statusLabels = {
    [TOOL_STATUS.COMING_SOON]: 'Próximamente',
    [TOOL_STATUS.BETA]: 'Beta',
    [TOOL_STATUS.MAINTENANCE]: 'Mantenimiento'
  };

  const statusColors = {
    [TOOL_STATUS.COMING_SOON]: 'text-yellow-400',
    [TOOL_STATUS.BETA]: 'text-blue-400',
    [TOOL_STATUS.MAINTENANCE]: 'text-red-400'
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, delay: index * 0.1 }}
      className={`bg-gray-800 p-6 rounded-lg border border-gray-700 hover:border-gray-600 transition-all ${
        disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer hover:shadow-lg hover:scale-105'
      }`}
      onClick={disabled ? undefined : onClick}
    >
      <div className="flex items-start mb-4">
        <div className={`p-3 rounded-lg ${color} flex-shrink-0`}>
          <Icon className="w-6 h-6 text-white" />
        </div>
        <div className="ml-4 flex-1">
          <h3 className="font-semibold text-white text-lg mb-1">{title}</h3>
          <p className="text-gray-400 text-sm leading-relaxed">{description}</p>
        </div>
      </div>
      
      {status !== TOOL_STATUS.AVAILABLE && (
        <div className={`flex items-center ${statusColors[status]} text-sm mt-3 pt-3 border-t border-gray-700`}>
          <AlertTriangle className="w-4 h-4 mr-2 flex-shrink-0" />
          <span className="font-medium">{statusLabels[status]}</span>
        </div>
      )}
    </motion.div>
  );
};

export default ToolCard;
