// src/modules/nomina/clientes/components/ClientesListHeader.jsx

/**
 * 📌 Componente ClientesListHeader
 * Header con título, badge de área y botón de debug
 */
const ClientesListHeader = ({ areaActiva, totalClientes, onDebugClick }) => {
  return (
    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
      <div className="flex items-center gap-3 flex-wrap">
        <h1 className="text-2xl sm:text-3xl font-bold text-white">Lista de Clientes de Nómina</h1>
        <span className="px-3 py-1 rounded-full bg-teal-600 text-white text-xs sm:text-sm font-semibold">
          {areaActiva}
        </span>
      </div>
      <div className="text-gray-400 text-xs sm:text-sm flex items-center gap-2">
        <span className="hidden sm:inline">
          {totalClientes} cliente{totalClientes !== 1 ? 's' : ''} en tu área
        </span>
        <span className="sm:hidden">
          {totalClientes} cliente{totalClientes !== 1 ? 's' : ''}
        </span>
        <button
          onClick={onDebugClick}
          className="text-xs text-blue-400 hover:text-blue-300 underline"
        >
          🔍 Debug
        </button>
      </div>
    </div>
  );
};

export default ClientesListHeader;
