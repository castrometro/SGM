import { CheckCircle, Info } from "lucide-react";
import { CAPTURA_CONFIG, STYLES_CONFIG } from "../config/capturaConfig";

/**
 * Componente para mostrar los resultados del procesamiento
 */
const ResultsSection = ({ resultados, onDescargar }) => {
  const { steps } = CAPTURA_CONFIG;
  const { containers, buttons, alerts } = STYLES_CONFIG;

  if (!resultados) return null;

  return (
    <div className={containers.section}>
      <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
        <steps.results.icon className="w-5 h-5" />
        {steps.results.title}
      </h2>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-blue-900/20 border border-blue-500/30 rounded-lg p-4">
          <p className="text-blue-400 text-sm">Total de Registros</p>
          <p className="text-2xl font-bold">{resultados.total}</p>
        </div>
        <div className="bg-green-900/20 border border-green-500/30 rounded-lg p-4">
          <p className="text-green-400 text-sm">Procesados Exitosamente</p>
          <p className="text-2xl font-bold text-green-400">{resultados.exitosos}</p>
        </div>
        <div className="bg-purple-900/20 border border-purple-500/30 rounded-lg p-4">
          <p className="text-purple-400 text-sm">Grupos por Tipo Doc</p>
          <p className="text-2xl font-bold text-purple-400">{resultados.grupos?.length || 0}</p>
        </div>
      </div>

      {/* Grupos creados */}
      {resultados.grupos && resultados.grupos.length > 0 && (
        <div className={`${alerts.info} mb-4`}>
          <div className="flex items-center gap-2 mb-3">
            <Info className="w-5 h-5 text-blue-400" />
            <h3 className="font-semibold text-blue-400">Grupos Creados por Tipo de Documento</h3>
          </div>
          <div className="flex flex-wrap gap-2">
            {resultados.grupos.map((grupo, index) => (
              <span key={index} className="bg-blue-600 text-white px-3 py-1 rounded-full text-sm">
                {grupo}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Botón de descarga */}
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
};

export default ResultsSection;
