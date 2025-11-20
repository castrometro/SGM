// src/modules/nomina/historial-cierres/components/FiltrosCierres.jsx

/**
 * Componente de filtros por estado para cierres de nómina
 */
const FiltrosCierres = ({ filtroActivo, stats, onCambiarFiltro }) => {
  const filtros = [
    { id: 'todos', label: 'Todos', count: stats.total, color: 'indigo' },
    { id: 'finalizado', label: 'Finalizados', count: stats.finalizados, color: 'emerald' },
    { id: 'procesando', label: 'En Proceso', count: stats.enProceso, color: 'yellow' },
    { id: 'con_incidencias', label: 'Con Incidencias', count: stats.conIncidencias, color: 'red' },
  ];

  const getColorClasses = (color, isActive) => {
    if (isActive) {
      const activeColors = {
        indigo: 'bg-indigo-500 text-white shadow-lg shadow-indigo-500/30',
        emerald: 'bg-emerald-500 text-white shadow-lg shadow-emerald-500/30',
        yellow: 'bg-yellow-500 text-white shadow-lg shadow-yellow-500/30',
        red: 'bg-red-500 text-white shadow-lg shadow-red-500/30',
      };
      return activeColors[color];
    }
    return 'bg-gray-800/80 text-gray-300 hover:bg-gray-700/80 border border-gray-600/50';
  };

  return (
    <div className="flex flex-wrap gap-2">
      {filtros.map((filtro) => (
        <button
          key={filtro.id}
          onClick={() => onCambiarFiltro(filtro.id)}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
            getColorClasses(filtro.color, filtroActivo === filtro.id)
          }`}
        >
          {filtro.label} ({filtro.count})
        </button>
      ))}
    </div>
  );
};

export default FiltrosCierres;
