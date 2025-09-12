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
    console.log('🔍 Generando columnas detectadas:', centrosCostoDetectados);
    const columnas = [];
    
    // PyC
    if (centrosCostoDetectados.PyC) {
      columnas.push({
        key: 'col10',
        label: `${centrosCostoDetectados.PyC.nombre}`,
        subtitle: `Columna ${centrosCostoDetectados.PyC.posicion + 1}`,
        placeholder: 'Código CC (ej: 01-003)'
      });
    }
    
    // PS/EB
    if (centrosCostoDetectados.PS) {
      columnas.push({
        key: 'col11',
        label: `${centrosCostoDetectados.PS.nombre}`,
        subtitle: `Columna ${centrosCostoDetectados.PS.posicion + 1}`,
        placeholder: 'Código CC (ej: 02-004)'
      });
    }
    
    // CO
    if (centrosCostoDetectados.CO) {
      columnas.push({
        key: 'col12',
        label: `${centrosCostoDetectados.CO.nombre}`,
        subtitle: `Columna ${centrosCostoDetectados.CO.posicion + 1}`,
        placeholder: 'Código CC (ej: 03-005)'
      });
    }
    
    // Si no se detectaron centros de costo, mostrar los 3 campos con etiquetas fijas y subtítulo 'No detectado'
    if (columnas.length === 0) {
      console.log('⚠️ No se detectaron centros de costo, mostrando 3 entradas por defecto');
      return [
        { key: 'col10', label: 'PyC', subtitle: 'No detectado', placeholder: 'Código CC (ej: 01-003)' },
        { key: 'col11', label: 'PS/EB', subtitle: 'No detectado', placeholder: 'Código CC (ej: 02-004)' },
        { key: 'col12', label: 'CO', subtitle: 'No detectado', placeholder: 'Código CC (ej: 03-005)' },
      ];
    }
    // Si se detectaron menos de 3, completar con la configuración por defecto
    const required = ['col10', 'col11', 'col12'];
    const usados = new Set(columnas.map(c => c.key));
    for (const key of required) {
      if (!usados.has(key)) {
        // Insertar entrada faltante con etiqueta fija y subtítulo claro
        const label = key === 'col10' ? 'PyC' : key === 'col11' ? 'PS/EB' : 'CO';
        const placeholder = key === 'col10'
          ? 'Código CC (ej: 01-003)'
          : key === 'col11'
            ? 'Código CC (ej: 02-004)'
            : 'Código CC (ej: 03-005)';
        columnas.push({ key, label, subtitle: 'No detectado', placeholder });
      }
    }

    console.log('✅ Columnas generadas:', columnas);
    return columnas;
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
                value={mapeoCC[column.key]}
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
