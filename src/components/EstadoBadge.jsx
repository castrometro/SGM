// src/components/EstadoBadge.jsx
import { renderEstadoCierre } from "../constants/estadoCierreColors";

/**
 * Componente global para mostrar estados con colores consistentes
 * @param {string} estado - El estado a mostrar
 * @param {string} size - Tamaño del badge: xs, sm, md, lg
 * @param {string} className - Clases CSS adicionales
 * @param {boolean} showSpinner - Mostrar spinner para estados de procesamiento
 */
const EstadoBadge = ({ estado, size = "sm", className = "", showSpinner = true }) => {
  if (!estado) {
    return (
      <span className={`text-gray-400 italic ${className}`}>
        No iniciado
      </span>
    );
  }

  const estadoInfo = renderEstadoCierre(estado, size);
  
  // Estados que muestran spinner
  const estadosConSpinner = ["procesando", "en_proceso", "analizando_hdrs", "clasif_en_proceso"];
  const deberiaSpinner = showSpinner && estadosConSpinner.includes(estado);
  
  return (
    <span className={`${estadoInfo.className} ${className} ${deberiaSpinner ? 'flex items-center gap-1' : ''}`}>
      {deberiaSpinner && (
        <svg className="animate-spin h-4 w-4 inline" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"></path>
        </svg>
      )}
      {estadoInfo.texto}
    </span>
  );
};

export default EstadoBadge;
