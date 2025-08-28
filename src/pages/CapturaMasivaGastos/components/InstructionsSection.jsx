import { UI_MESSAGES, STYLES_CONFIG } from "../config/capturaConfig";

/**
 * Componente que muestra las instrucciones de uso
 */
const InstructionsSection = () => {
  const { instructions } = UI_MESSAGES;
  const { alerts } = STYLES_CONFIG;

  return (
    <div className={alerts.info}>
      <div className="flex items-start gap-3">
        <instructions.icon className="w-5 h-5 text-blue-400 mt-0.5" />
        <div>
          <h3 className="font-semibold text-blue-400 mb-2">{instructions.title}</h3>
          <ul className="text-gray-300 text-sm space-y-1">
            {instructions.items.map((item, index) => (
              <li key={index}>• {item}</li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
};

export default InstructionsSection;
