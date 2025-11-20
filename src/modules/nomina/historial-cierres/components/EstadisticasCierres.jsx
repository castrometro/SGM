// src/modules/nomina/historial-cierres/components/EstadisticasCierres.jsx
import {
  FileCheck,
  CheckCircle2,
  Clock,
  AlertCircle
} from "lucide-react";

/**
 * Componente de estadísticas de cierres de nómina
 */
const EstadisticasCierres = ({ stats }) => {
  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <div className="bg-gradient-to-br from-gray-800/80 to-gray-900/80 backdrop-blur-sm rounded-xl p-4 border border-gray-700/50">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs text-gray-400">Total</span>
          <FileCheck size={16} className="text-gray-500" />
        </div>
        <p className="text-2xl font-bold text-white">{stats.total}</p>
      </div>

      <div className="bg-gradient-to-br from-emerald-900/20 to-emerald-800/20 backdrop-blur-sm rounded-xl p-4 border border-emerald-500/30">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs text-emerald-300">Finalizados</span>
          <CheckCircle2 size={16} className="text-emerald-400" />
        </div>
        <p className="text-2xl font-bold text-emerald-300">{stats.finalizados}</p>
      </div>

      <div className="bg-gradient-to-br from-yellow-900/20 to-yellow-800/20 backdrop-blur-sm rounded-xl p-4 border border-yellow-500/30">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs text-yellow-300">En Proceso</span>
          <Clock size={16} className="text-yellow-400" />
        </div>
        <p className="text-2xl font-bold text-yellow-300">{stats.enProceso}</p>
      </div>

      <div className="bg-gradient-to-br from-red-900/20 to-red-800/20 backdrop-blur-sm rounded-xl p-4 border border-red-500/30">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs text-red-300">Con Incidencias</span>
          <AlertCircle size={16} className="text-red-400" />
        </div>
        <p className="text-2xl font-bold text-red-300">{stats.conIncidencias}</p>
      </div>
    </div>
  );
};

export default EstadisticasCierres;
