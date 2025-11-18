import { FileSpreadsheet } from "lucide-react";
import { CAPTURA_CONFIG, STYLES_CONFIG } from "../constants/capturaConfig";

/**
 * Componente para descargar la plantilla Excel
 */
const DownloadTemplateSection = ({ onDownload }) => {
  const { steps } = CAPTURA_CONFIG;
  const { containers, buttons } = STYLES_CONFIG;

  return (
    <div className={containers.section}>
      <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
        <steps.download.icon className="w-5 h-5" />
        {steps.download.title}
      </h2>
      <p className="text-gray-400 mb-4">
        {steps.download.description}
      </p>
      <button
        onClick={onDownload}
        className={buttons.primary}
      >
        <FileSpreadsheet className="w-4 h-4" />
        Descargar Plantilla Excel
      </button>
    </div>
  );
};

export default DownloadTemplateSection;
