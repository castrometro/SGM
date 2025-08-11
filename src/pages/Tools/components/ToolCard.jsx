import { AlertTriangle } from "lucide-react";

/**
 * Componente para renderizar una tarjeta de herramienta
 * Maneja estados habilitado/deshabilitado y eventos de clic
 */
const ToolCard = ({ title, description, icon: Icon, color, onClick, disabled = false }) => {
  return (
    <div 
      className={`bg-gray-800 p-6 rounded-lg border border-gray-700 hover:border-gray-600 transition-colors cursor-pointer ${
        disabled ? 'opacity-50 cursor-not-allowed' : ''
      }`}
      onClick={disabled ? undefined : onClick}
    >
      <div className="flex items-center mb-4">
        <div className={`p-3 rounded-lg ${color}`}>
          <Icon className="w-6 h-6 text-white" />
        </div>
        <div className="ml-4">
          <h3 className="font-semibold text-white">{title}</h3>
          <p className="text-gray-400 text-sm">{description}</p>
        </div>
      </div>
      {disabled && (
        <div className="flex items-center text-yellow-400 text-sm">
          <AlertTriangle className="w-4 h-4 mr-1" />
          Próximamente disponible
        </div>
      )}
    </div>
  );
};

export default ToolCard;
