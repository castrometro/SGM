import { UI_CONFIG } from "../config/toolsConfig";

/**
 * Componente para mostrar información del centro de herramientas
 */
const InfoSection = () => {
  const { infoSection } = UI_CONFIG;
  const { icon: Icon, title, description, note } = infoSection;

  return (
    <div className="bg-blue-900/20 border border-blue-500/30 rounded-lg p-6">
      <div className="flex items-start">
        <div className="p-2 bg-blue-600 rounded-lg mr-4">
          <Icon className="w-5 h-5 text-white" />
        </div>
        <div>
          <h3 className="font-semibold text-blue-400 mb-2">{title}</h3>
          <p className="text-gray-300 text-sm">
            {description}
          </p>
          <p className="text-gray-400 text-xs mt-2">
            {note}
          </p>
        </div>
      </div>
    </div>
  );
};

export default InfoSection;
