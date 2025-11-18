import { AlertCircle } from "lucide-react";
import { STYLES_CONFIG } from "../constants/capturaConfig";

/**
 * Componente para mostrar errores
 */
const ErrorSection = ({ error }) => {
  const { alerts } = STYLES_CONFIG;

  if (!error) return null;

  return (
    <div className={alerts.error}>
      <div className="flex items-center gap-2 mb-2">
        <AlertCircle className="w-5 h-5 text-red-400" />
        <h3 className="font-semibold text-red-400">Error</h3>
      </div>
      <p className="text-gray-300 text-sm whitespace-pre-line">{error}</p>
    </div>
  );
};

export default ErrorSection;
