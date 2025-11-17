// src/modules/contabilidad/clientes/components/EmptyState.jsx
import { MENSAJES } from '../constants/clientes.constants';
import { getMensajeSinClientes } from '../utils/clientesHelpers';

/**
 * 📭 Componente EmptyState
 * Mensaje cuando no hay clientes o no se encontraron resultados
 */
const EmptyState = ({ 
  totalClientes, 
  filtro, 
  areaActiva, 
  tipoUsuario 
}) => {
  if (totalClientes === 0) {
    return (
      <div className="text-center py-8">
        <p className="text-gray-300 mb-2">
          {MENSAJES.SIN_CLIENTES_AREA} "{areaActiva}".
        </p>
        <p className="text-gray-500 text-sm">
          {getMensajeSinClientes(tipoUsuario, areaActiva)}
        </p>
      </div>
    );
  }

  return (
    <div className="text-center py-8">
      <p className="text-gray-300">
        {MENSAJES.SIN_RESULTADOS_FILTRO} "{filtro}".
      </p>
    </div>
  );
};

export default EmptyState;
