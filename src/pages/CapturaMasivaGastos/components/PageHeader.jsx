import { useNavigate } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { CAPTURA_CONFIG, STYLES_CONFIG } from "../config/capturaConfig";

/**
 * Componente header de la página de captura masiva
 */
const PageHeader = () => {
  const navigate = useNavigate();
  const { page } = CAPTURA_CONFIG;
  const { containers, buttons } = STYLES_CONFIG;

  return (
    <div className={containers.header}>
      <div className="max-w-4xl mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate(-1)}
              className={buttons.back}
            >
              <ArrowLeft size={20} />
            </button>
            <div className="flex items-center gap-3">
              <div className="p-2 bg-emerald-600 rounded-lg">
                <page.icon size={24} />
              </div>
              <div>
                <h1 className="text-2xl font-bold">{page.title}</h1>
                <p className="text-gray-400">{page.description}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PageHeader;
