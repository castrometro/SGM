import { useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { obtenerCierresCliente as obtenerCierresContabilidad } from "../api/contabilidad";
import { obtenerCierresCliente as obtenerCierresNomina } from "../api/nomina";
import EstadoBadge from "./EstadoBadge";
import {
  Calendar,
  FileCheck,
  Eye,
  BookOpen,
  Filter,
  RefreshCw,
  TrendingUp,
  CheckCircle2,
  Clock,
  AlertCircle,
  ArrowRight
} from "lucide-react";

const HistorialCierres = ({ clienteId, areaActiva }) => {
  const [cierres, setCierres] = useState([]);
  const [filtroEstado, setFiltroEstado] = useState("todos");
  const [isRefreshing, setIsRefreshing] = useState(false);
  const navigate = useNavigate();

  // Helper para determinar si un cierre puede ser finalizado
  const puedeFinalizarse = (cierre) => {
    return cierre.estado === 'sin_incidencias';
  };

  // Helper para obtener icono según estado
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

  // Helper para determinar acciones adicionales según el estado
  const getAccionesAdicionales = (cierre) => {
    if (areaActiva !== "Contabilidad") return null;
    
    if (puedeFinalizarse(cierre)) {
      return (
        <span className="text-xs bg-emerald-500/20 text-emerald-300 px-2 py-1 rounded-full border border-emerald-500/30 flex items-center gap-1">
          <CheckCircle2 size={12} />
          Listo para finalizar
        </span>
      );
    }
    
    if (cierre.estado === 'generando_reportes') {
      return (
        <span className="text-xs bg-yellow-500/20 text-yellow-300 px-2 py-1 rounded-full border border-yellow-500/30 flex items-center gap-1">
          <Clock size={12} className="animate-pulse" />
          Generando reportes...
        </span>
      );
    }
    
    if (cierre.estado === 'completado') {
      return (
        <span className="text-xs bg-blue-500/20 text-blue-300 px-2 py-1 rounded-full border border-blue-500/30 flex items-center gap-1">
          <TrendingUp size={12} />
          Reportes disponibles
        </span>
      );
    }
    
    return null;
  };

  const fetchCierres = useCallback(async (showRefresh = false) => {
    if (showRefresh) setIsRefreshing(true);
    
    let res = [];
    if (areaActiva === "Contabilidad") {
      res = await obtenerCierresContabilidad(clienteId);
    } else if (areaActiva === "Nomina") {
      res = await obtenerCierresNomina(clienteId);
    }
    setCierres(res);
    
    if (showRefresh) {
      setTimeout(() => setIsRefreshing(false), 500);
    }
  }, [clienteId, areaActiva]);

  useEffect(() => {
    if (clienteId) fetchCierres();
  }, [clienteId, fetchCierres]);

  // Auto-refresh para cierres en proceso
  useEffect(() => {
    const cierresEnProceso = cierres.filter(cierre => 
      cierre.estado === 'generando_reportes' || cierre.estado === 'procesando'
    );
    
    if (cierresEnProceso.length > 0) {
      const interval = setInterval(() => fetchCierres(), 30000);
      return () => clearInterval(interval);
    }
  }, [cierres, fetchCierres]);

  // Filtrar cierres
  const cierresFiltrados = cierres.filter(cierre => {
    if (filtroEstado === "todos") return true;
    
    // Para "procesando" incluir tanto "procesando" como "generando_reportes"
    if (filtroEstado === "procesando") {
      return cierre.estado === 'procesando' || cierre.estado === 'generando_reportes';
    }
    
    // Para "finalizado" incluir "finalizado", "completado" y "sin_incidencias"
    if (filtroEstado === "finalizado") {
      return cierre.estado === 'finalizado' || cierre.estado === 'completado' || cierre.estado === 'sin_incidencias';
    }
    
    return cierre.estado === filtroEstado;
  });

  // Estadísticas
  const stats = {
    total: cierres.length,
    finalizados: cierres.filter(c => c.estado === 'finalizado' || c.estado === 'completado').length,
    enProceso: cierres.filter(c => c.estado === 'procesando' || c.estado === 'generando_reportes').length,
    conIncidencias: cierres.filter(c => c.estado === 'con_incidencias').length,
  };

  if (!cierres.length) {
    return (
      <div className="flex flex-col items-center justify-center py-16 px-4">
        <div className="bg-gradient-to-br from-gray-800/50 to-gray-900/50 backdrop-blur-sm rounded-2xl p-8 border border-gray-700/50 max-w-md text-center">
          <FileCheck size={48} className="text-gray-500 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-white mb-2">Sin cierres registrados</h3>
          <p className="text-sm text-gray-400">No hay cierres para este cliente aún.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header con título y controles */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center gap-3">
            <div className="p-2 bg-gradient-to-br from-indigo-500/20 to-purple-500/20 rounded-lg border border-indigo-500/30">
              <FileCheck size={24} className="text-indigo-400" />
            </div>
            Historial de Cierres
            <span className="text-sm font-normal text-gray-400">({areaActiva})</span>
          </h2>
          <p className="text-sm text-gray-400 mt-1">
            {cierresFiltrados.length} de {cierres.length} cierres mostrados
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Botón refresh */}
          <button
            onClick={() => fetchCierres(true)}
            disabled={isRefreshing}
            className="flex items-center gap-2 px-4 py-2 bg-gray-800/80 hover:bg-gray-700/80 border border-gray-600/50 rounded-lg text-sm text-gray-300 transition-all duration-200 disabled:opacity-50"
          >
            <RefreshCw size={16} className={isRefreshing ? "animate-spin" : ""} />
            Actualizar
          </button>
        </div>
      </div>

      {/* Estadísticas rápidas */}
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

      {/* Filtros por estado */}
      <div className="flex flex-wrap gap-2">
        <button
          onClick={() => setFiltroEstado("todos")}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
            filtroEstado === "todos"
              ? "bg-indigo-500 text-white shadow-lg shadow-indigo-500/30"
              : "bg-gray-800/80 text-gray-300 hover:bg-gray-700/80 border border-gray-600/50"
          }`}
        >
          Todos ({cierres.length})
        </button>
        <button
          onClick={() => setFiltroEstado("finalizado")}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
            filtroEstado === "finalizado"
              ? "bg-emerald-500 text-white shadow-lg shadow-emerald-500/30"
              : "bg-gray-800/80 text-gray-300 hover:bg-gray-700/80 border border-gray-600/50"
          }`}
        >
          Finalizados ({stats.finalizados})
        </button>
        <button
          onClick={() => setFiltroEstado("procesando")}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
            filtroEstado === "procesando"
              ? "bg-yellow-500 text-white shadow-lg shadow-yellow-500/30"
              : "bg-gray-800/80 text-gray-300 hover:bg-gray-700/80 border border-gray-600/50"
          }`}
        >
          En Proceso ({stats.enProceso})
        </button>
        <button
          onClick={() => setFiltroEstado("con_incidencias")}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
            filtroEstado === "con_incidencias"
              ? "bg-red-500 text-white shadow-lg shadow-red-500/30"
              : "bg-gray-800/80 text-gray-300 hover:bg-gray-700/80 border border-gray-600/50"
          }`}
        >
          Con Incidencias ({stats.conIncidencias})
        </button>
      </div>

      {/* Tabla de cierres */}
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
                {areaActiva === "Contabilidad" && (
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-300 uppercase tracking-wider">
                    Cuentas Nuevas
                  </th>
                )}
                <th className="px-6 py-4 text-left text-xs font-semibold text-gray-300 uppercase tracking-wider">
                  Fecha Creación
                </th>
                {areaActiva === "Contabilidad" && (
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-300 uppercase tracking-wider">
                    Estado Proceso
                  </th>
                )}
                <th className="px-6 py-4 text-right text-xs font-semibold text-gray-300 uppercase tracking-wider">
                  Acciones
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-700/30">
              {cierresFiltrados.map((cierre) => (
                <tr 
                  key={cierre.id}
                  className="hover:bg-gray-800/50 transition-colors duration-150"
                >
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-gradient-to-br from-indigo-500/20 to-purple-500/20 rounded-lg border border-indigo-500/30">
                        <Calendar size={16} className="text-indigo-400" />
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
                  
                  {areaActiva === "Contabilidad" && (
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="text-sm font-medium text-gray-300">
                        {cierre.cuentas_nuevas || 0}
                      </span>
                    </td>
                  )}
                  
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
                  
                  {areaActiva === "Contabilidad" && (
                    <td className="px-6 py-4">
                      {getAccionesAdicionales(cierre)}
                    </td>
                  )}
                  
                  <td className="px-6 py-4 whitespace-nowrap text-right">
                    <div className="flex items-center justify-end gap-2">
                      <button
                        onClick={() => {
                          if (areaActiva === "Contabilidad") {
                            navigate(`/menu/cierres/${cierre.id}`);
                          } else {
                            navigate(`/menu/nomina/cierres/${cierre.id}`);
                          }
                        }}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-blue-500/20 hover:bg-blue-500/30 border border-blue-500/30 hover:border-blue-400/50 rounded-lg text-xs font-medium text-blue-300 hover:text-blue-200 transition-all duration-200 group"
                      >
                        <Eye size={14} />
                        Ver detalles
                        <ArrowRight size={12} className="group-hover:translate-x-0.5 transition-transform duration-200" />
                      </button>

                      {(cierre.estado === "completo" || 
                        cierre.estado === "sin_incidencias" || 
                        cierre.estado === "finalizado") && 
                       areaActiva === "Contabilidad" && (
                        <button
                          onClick={() => navigate(`/menu/cierres/${cierre.id}/libro`)}
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
        
        {/* Mensaje si no hay resultados */}
        {cierresFiltrados.length === 0 && (
          <div className="flex flex-col items-center justify-center py-12 px-4">
            <AlertCircle size={48} className="text-gray-500 mb-4" />
            <p className="text-gray-400 text-sm">No se encontraron cierres con el filtro seleccionado</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default HistorialCierres;
