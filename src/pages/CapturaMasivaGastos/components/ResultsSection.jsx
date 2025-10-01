import { CheckCircle, Info } from "lucide-react";
import { CAPTURA_CONFIG, STYLES_CONFIG } from "../config/capturaConfig";

/**
 * Componente para mostrar los resultados del procesamiento
 * TEMPORALMENTE SIMPLIFICADO - Solo muestra el botón de descarga
 */
const ResultsSection = ({ resultados, onDescargar }) => {
  const { containers, buttons } = STYLES_CONFIG;

  if (!resultados) return null;

  // Solo mostrar el botón de descarga por ahora
  return (
    <div className={containers.section}>
      <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
        <CheckCircle className="w-5 h-5" />
        Resultados del Procesamiento
      </h2>
      
      <p className="text-gray-300 mb-4">
        Archivo procesado exitosamente. Puedes descargar los resultados:
      </p>

      {/* Botón de descarga - LO IMPORTANTE 😄 */}
      {resultados.archivo_disponible && (
        <button
          onClick={onDescargar}
          className={buttons.primary}
        >
          <CheckCircle className="w-4 h-4" />
          Descargar Resultados
        </button>
      )}
    </div>
  );

  // TODO: Reactivar las métricas detalladas cuando se corrijan los errores
  // - Total de registros
  // - Procesados exitosamente  
  // - Grupos por tipo de documento
  // - Lista de grupos creados
};

export default ResultsSection;
