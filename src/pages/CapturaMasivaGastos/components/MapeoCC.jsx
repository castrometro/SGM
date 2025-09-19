import { Settings, Info } from "lucide-react";
import { CAPTURA_CONFIG, STYLES_CONFIG, UI_MESSAGES } from "../config/capturaConfig";

/**
 * Componente para configurar el mapeo de centros de costos
 */
const MapeoCC = ({ 
  mostrarMapeoCC, 
  headersExcel, 
  centrosCostoDetectados = {}, // Valor por defecto
  mapeoCC, 
  setMapeoCC 
}) => {
  const { mapeoCC: config } = CAPTURA_CONFIG;
  const { alerts } = STYLES_CONFIG;
  const { ccInfo } = UI_MESSAGES;

  console.log('🗺️ MapeoCC renderizado:', { mostrarMapeoCC, headersExcel, centrosCostoDetectados, mapeoCC });

  if (!mostrarMapeoCC || !headersExcel) return null;

  const handleInputChange = (key, value) => {
    setMapeoCC(prev => ({ ...prev, [key]: value }));
  };

  // Generar configuración de columnas dinámicamente basada en centros de costo detectados
  const generarColumnasDetectadas = () => {
    console.log('🔍 Generando columnas detectadas (dinámico RG):', centrosCostoDetectados);
    const columnas = [];

    // Si tenemos detección RG, iterar todas las claves detectadas (nombres tal cual en header)
    const keysDetectadas = Object.keys(centrosCostoDetectados || {});
    if (keysDetectadas.length > 0) {
      keysDetectadas.forEach((key) => {
        const info = centrosCostoDetectados[key];
        columnas.push({
          key, // usaremos el nombre del header como key
          label: `${info.nombre}`,
          subtitle: `Columna ${info.posicion + 1}`,
          placeholder: 'Código CC (ej: 01-003 o 001-003)'
        });
      });
      console.log('✅ Columnas RG generadas:', columnas);
      return columnas;
    }

    // Fallback: configuración por defecto (PyC, PS/EB, ...)
    console.log('⚠️ No se detectaron centros de costo (RG), usando configuración por defecto');
    return config.columns.map(col => ({
      ...col,
      subtitle: 'Sin nombre'
    }));
  };

  const columnasAMostrar = generarColumnasDetectadas();

  return (
    <div className={`mt-6 ${alerts.warning}`}>
      <div className="flex items-center gap-2 mb-4">
        <Settings className="w-5 h-5 text-yellow-400" />
        <h3 className="font-semibold text-yellow-400">{config.title}</h3>
      </div>
      <p className="text-gray-300 text-sm mb-4">
        {config.description}
      </p>
      
      <div className="space-y-4">
        {columnasAMostrar.map((column) => (
          <div key={column.key} className="flex items-center gap-4">
            <div className="w-40">
              <label className="block text-sm font-medium text-gray-300 mb-1">
                {column.label}:
              </label>
              <p className="text-xs text-gray-400 truncate">
                {column.subtitle}
              </p>
            </div>
            <div className="flex-1">
              <input
                type="text"
                placeholder={column.placeholder}
                value={mapeoCC[column.key] || ''}
                onChange={(e) => handleInputChange(column.key, e.target.value)}
                className="w-full bg-gray-700 border border-gray-600 text-white px-3 py-2 rounded-lg focus:outline-none focus:border-yellow-500"
              />
            </div>
          </div>
        ))}
      </div>

      <div className={`mt-4 ${alerts.info}`}>
        <div className="flex items-start gap-2">
          <Info className="w-4 h-4 text-blue-400 mt-0.5" />
          <div className="text-xs text-blue-300">
            <p className="font-medium mb-1">{ccInfo.title}</p>
            <ul className="space-y-1">
              {ccInfo.items.map((item, index) => (
                <li key={index}>• {item}</li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MapeoCC;
