// src/modules/nomina/historial-cierres/components/TablaCierres.jsx
import { useNavigate } from "react-router-dom";
import {
  Calendar,
  Eye,
  BookOpen,
  CheckCircle2,
  Clock,
  AlertCircle,
  ArrowRight,
  FileCheck
} from "lucide-react";
import EstadoBadge from "../../../../components/EstadoBadge";

/**
 * Componente de tabla de cierres de nómina
 */
const TablaCierres = ({ cierres }) => {
  const navigate = useNavigate();

  const getEstadoIcon = (estado) => {
    switch (estado) {
      case 'finalizado':
      case 'completado':
      case 'sin_incidencias':
        return <CheckCircle2 size={16} className="text-emerald-400" />;
      case 'generando_reportes':
      case 'procesando':
        return <Clock size={16} className="text-yellow-400 animate-pulse" />;
      case 'con_incidencias':
        return <AlertCircle size={16} className="text-red-400" />;
      default:
        return <FileCheck size={16} className="text-blue-400" />;
    }
  };

  if (cierres.length === 0) {
    return (
      <div className="bg-gradient-to-br from-gray-800/80 to-gray-900/80 backdrop-blur-sm rounded-xl border border-gray-700/50 p-12">
        <div className="flex flex-col items-center justify-center">
          <AlertCircle size={48} className="text-gray-500 mb-4" />
          <p className="text-gray-400 text-sm">No se encontraron cierres con el filtro seleccionado</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gradient-to-br from-gray-800/80 to-gray-900/80 backdrop-blur-sm rounded-xl border border-gray-700/50 overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-700/50 bg-gray-900/50">
              <th className="px-6 py-4 text-left text-xs font-semibold text-gray-300 uppercase tracking-wider">
                Periodo
              </th>
              <th className="px-6 py-4 text-left text-xs font-semibold text-gray-300 uppercase tracking-wider">
                Estado
              </th>
              <th className="px-6 py-4 text-left text-xs font-semibold text-gray-300 uppercase tracking-wider">
                Fecha Creación
              </th>
              <th className="px-6 py-4 text-right text-xs font-semibold text-gray-300 uppercase tracking-wider">
                Acciones
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-700/30">
            {cierres.map((cierre) => (
              <tr 
                key={cierre.id}
                className="hover:bg-gray-800/50 transition-colors duration-150"
              >
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-gradient-to-br from-teal-500/20 to-emerald-500/20 rounded-lg border border-teal-500/30">
                      <Calendar size={16} className="text-teal-400" />
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-white">{cierre.periodo}</p>
                      <p className="text-xs text-gray-400">
                        {new Date(cierre.fecha_creacion).toLocaleDateString('es-ES', { 
                          day: 'numeric', 
                          month: 'short',
                          year: 'numeric' 
                        })}
                      </p>
                    </div>
                  </div>
                </td>
                
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center gap-2">
                    {getEstadoIcon(cierre.estado)}
                    <EstadoBadge estado={cierre.estado} size="sm" />
                  </div>
                </td>
                
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="text-sm text-gray-300">
                    {new Date(cierre.fecha_creacion).toLocaleDateString('es-ES', { 
                      day: 'numeric', 
                      month: 'long',
                      year: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit'
                    })}
                  </span>
                </td>
                
                <td className="px-6 py-4 whitespace-nowrap text-right">
                  <div className="flex items-center justify-end gap-2">
                    <button
                      onClick={() => navigate(`/menu/nomina/cierres/${cierre.id}`)}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-blue-500/20 hover:bg-blue-500/30 border border-blue-500/30 hover:border-blue-400/50 rounded-lg text-xs font-medium text-blue-300 hover:text-blue-200 transition-all duration-200 group"
                    >
                      <Eye size={14} />
                      Ver detalles
                      <ArrowRight size={12} className="group-hover:translate-x-0.5 transition-transform duration-200" />
                    </button>

                    {(cierre.estado === "completo" || 
                      cierre.estado === "sin_incidencias" || 
                      cierre.estado === "finalizado") && (
                      <button
                        onClick={() => navigate(`/menu/cierres-nomina/${cierre.id}/libro-remuneraciones`)}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-emerald-500/20 hover:bg-emerald-500/30 border border-emerald-500/30 hover:border-emerald-400/50 rounded-lg text-xs font-medium text-emerald-300 hover:text-emerald-200 transition-all duration-200 group"
                      >
                        <BookOpen size={14} />
                        Ver libro
                        <ArrowRight size={12} className="group-hover:translate-x-0.5 transition-transform duration-200" />
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default TablaCierres;
