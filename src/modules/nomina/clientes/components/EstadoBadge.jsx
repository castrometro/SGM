// src/modules/nomina/clientes/components/EstadoBadge.jsx
import { ESTADO_COLORS, ESTADO_LABELS } from '../constants/clientes.constants';

/**
 * 🏷️ Componente EstadoBadge
 * Badge que muestra el estado de un cierre con color apropiado
 */
const EstadoBadge = ({ estado }) => {
  if (!estado) {
    return (
      <span className="px-2.5 py-1 rounded-full text-xs font-medium bg-gray-600 text-gray-300">
        Sin estado
      </span>
    );
  }

  const colorClass = ESTADO_COLORS[estado] || 'bg-gray-500';
  const label = ESTADO_LABELS[estado] || estado;

  return (
    <span className={`px-2.5 py-1 rounded-full text-xs font-medium text-white ${colorClass}`}>
      {label}
    </span>
  );
};

export default EstadoBadge;
