import { useState, useEffect } from "react";
import { TrendingUp, TrendingDown, ChevronDown, ChevronRight, AlertTriangle, CheckCircle, Clock, Eye, User } from "lucide-react";
import { 
  obtenerIncidenciasVariacion, 
  obtenerResumenIncidenciasVariacion,
  justificarIncidenciaVariacion,
  aprobarIncidenciaVariacion,
  rechazarIncidenciaVariacion
} from "../../api/nomina";

const IncidenciasVariacionSection = ({ cierre, onCierreActualizado }) => {
  const [expandido, setExpandido] = useState(true);
  const [incidencias, setIncidencias] = useState([]);
  const [resumen, setResumen] = useState(null);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState("");
  const [filtros, setFiltros] = useState({});
  const [incidenciaEnEdicion, setIncidenciaEnEdicion] = useState(null);
  const [justificacion, setJustificacion] = useState("");
  const [comentarioSupervisor, setComentarioSupervisor] = useState("");

  useEffect(() => {
    if (cierre?.id) {
      cargarDatos();
    }
  }, [cierre?.id]);

  const cargarDatos = async () => {
    if (!cierre?.id) return;
    
    setCargando(true);
    setError("");
    
    try {
      const [incidenciasData, resumenData] = await Promise.all([
        obtenerIncidenciasVariacion(cierre.id, filtros),
        obtenerResumenIncidenciasVariacion(cierre.id)
      ]);
      
      setIncidencias(incidenciasData);
      setResumen(resumenData);
    } catch (err) {
      console.error("Error cargando incidencias de variación:", err);
      setError("Error al cargar incidencias de variación");
    } finally {
      setCargando(false);
    }
  };

  const manejarJustificar = async (incidenciaId) => {
    if (!justificacion.trim()) {
      alert("La justificación es requerida");
      return;
    }

    try {
      await justificarIncidenciaVariacion(incidenciaId, justificacion);
      setIncidenciaEnEdicion(null);
      setJustificacion("");
      await cargarDatos();
      alert("✅ Incidencia justificada correctamente");
    } catch (err) {
      console.error("Error justificando incidencia:", err);
      alert("❌ Error al justificar incidencia");
    }
  };

  const manejarAprobar = async (incidenciaId) => {
    try {
      await aprobarIncidenciaVariacion(incidenciaId, comentarioSupervisor);
      setIncidenciaEnEdicion(null);
      setComentarioSupervisor("");
      await cargarDatos();
      alert("✅ Incidencia aprobada correctamente");
    } catch (err) {
      console.error("Error aprobando incidencia:", err);
      alert("❌ Error al aprobar incidencia");
    }
  };

  const manejarRechazar = async (incidenciaId) => {
    if (!comentarioSupervisor.trim()) {
      alert("El comentario es requerido para rechazar");
      return;
    }

    try {
      await rechazarIncidenciaVariacion(incidenciaId, comentarioSupervisor);
      setIncidenciaEnEdicion(null);
      setComentarioSupervisor("");
      await cargarDatos();
      alert("✅ Incidencia rechazada correctamente");
    } catch (err) {
      console.error("Error rechazando incidencia:", err);
      alert("❌ Error al rechazar incidencia");
    }
  };

  const obtenerColorEstado = (estado) => {
    switch (estado) {
      case 'pendiente': return 'text-yellow-400';
      case 'en_analisis': return 'text-blue-400';
      case 'justificado': return 'text-purple-400';
      case 'aprobado': return 'text-green-400';
      case 'rechazado': return 'text-red-400';
      default: return 'text-gray-400';
    }
  };

  const obtenerIconoVariacion = (tipo) => {
    return tipo === 'aumento' ? 
      <TrendingUp className="w-4 h-4 text-green-500" /> : 
      <TrendingDown className="w-4 h-4 text-red-500" />;
  };

  const formatearMonto = (monto) => {
    return new Intl.NumberFormat('es-CL', {
      style: 'currency',
      currency: 'CLP',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(monto);
  };

  if (!resumen || resumen.total === 0) {
    return null; // No mostrar si no hay incidencias de variación
  }

  return (
    <section className="space-y-6">
      <div
        className="flex items-center justify-between cursor-pointer hover:bg-gray-800/50 p-3 -m-3 rounded-lg transition-colors"
        onClick={() => setExpandido(!expandido)}
      >
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-10 h-10 bg-orange-600 rounded-lg">
            <TrendingUp size={20} className="text-white" />
          </div>
          <div>
            <h2 className="text-xl font-semibold text-white">
              Incidencias de Variación Salarial
            </h2>
            <div className="flex items-center gap-2 text-sm">
              <p className="text-gray-400">
                Variaciones significativas en sueldos base
              </p>
              {resumen && (
                <span className="text-orange-400 font-medium">
                  • {resumen.total} incidencias detectadas
                </span>
              )}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {expandido ? (
            <ChevronDown size={20} className="text-gray-400" />
          ) : (
            <ChevronRight size={20} className="text-gray-400" />
          )}
        </div>
      </div>

      {expandido && (
        <div className="space-y-6">
          {/* Resumen estadístico */}
          {resumen && (
            <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
              <h3 className="text-lg font-medium text-white mb-3">Resumen</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-orange-400">{resumen.total}</div>
                  <div className="text-sm text-gray-400">Total</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-yellow-400">{resumen.por_estado.pendiente}</div>
                  <div className="text-sm text-gray-400">Pendientes</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-400">{resumen.por_estado.en_analisis}</div>
                  <div className="text-sm text-gray-400">En Análisis</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-400">{resumen.por_estado.aprobado}</div>
                  <div className="text-sm text-gray-400">Aprobadas</div>
                </div>
              </div>
            </div>
          )}

          {/* Filtros */}
          <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
            <div className="flex flex-wrap gap-3">
              <select
                value={filtros.estado || ''}
                onChange={(e) => setFiltros({ ...filtros, estado: e.target.value })}
                className="bg-gray-700 border border-gray-600 rounded px-3 py-1 text-sm text-white"
              >
                <option value="">Todos los estados</option>
                <option value="pendiente">Pendiente</option>
                <option value="en_analisis">En Análisis</option>
                <option value="justificado">Justificado</option>
                <option value="aprobado">Aprobado</option>
                <option value="rechazado">Rechazado</option>
              </select>
              
              <select
                value={filtros.tipo_variacion || ''}
                onChange={(e) => setFiltros({ ...filtros, tipo_variacion: e.target.value })}
                className="bg-gray-700 border border-gray-600 rounded px-3 py-1 text-sm text-white"
              >
                <option value="">Todos los tipos</option>
                <option value="aumento">Aumento</option>
                <option value="disminucion">Disminución</option>
              </select>
              
              <input
                type="text"
                placeholder="Buscar por RUT o nombre..."
                value={filtros.busqueda || ''}
                onChange={(e) => setFiltros({ ...filtros, busqueda: e.target.value })}
                className="bg-gray-700 border border-gray-600 rounded px-3 py-1 text-sm text-white placeholder-gray-400"
              />
            </div>
          </div>

          {/* Error */}
          {error && (
            <div className="bg-red-900/20 border border-red-500 rounded-lg p-4">
              <div className="flex items-center text-red-400">
                <AlertTriangle className="w-5 h-5 mr-2" />
                {error}
              </div>
            </div>
          )}

          {/* Tabla de incidencias */}
          <div className="bg-gray-800 rounded-lg border border-gray-700">
            <div className="p-4 border-b border-gray-700">
              <h3 className="text-lg font-medium text-white">
                Incidencias de Variación Salarial
              </h3>
            </div>
            
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-gray-700">
                  <tr>
                    <th className="text-left p-3 text-gray-300">Empleado</th>
                    <th className="text-left p-3 text-gray-300">Variación</th>
                    <th className="text-left p-3 text-gray-300">Sueldo Anterior</th>
                    <th className="text-left p-3 text-gray-300">Sueldo Actual</th>
                    <th className="text-left p-3 text-gray-300">Estado</th>
                    <th className="text-left p-3 text-gray-300">Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  {incidencias.map((incidencia) => (
                    <tr key={incidencia.id} className="border-b border-gray-700">
                      <td className="p-3">
                        <div>
                          <div className="font-medium text-white">{incidencia.nombre_empleado}</div>
                          <div className="text-gray-400">{incidencia.rut_empleado}</div>
                        </div>
                      </td>
                      <td className="p-3">
                        <div className="flex items-center gap-2">
                          {obtenerIconoVariacion(incidencia.tipo_variacion)}
                          <span className={`font-medium ${
                            incidencia.tipo_variacion === 'aumento' ? 'text-green-400' : 'text-red-400'
                          }`}>
                            {incidencia.porcentaje_variacion > 0 ? '+' : ''}{incidencia.porcentaje_variacion}%
                          </span>
                        </div>
                      </td>
                      <td className="p-3 text-gray-300">
                        {formatearMonto(incidencia.sueldo_base_anterior)}
                      </td>
                      <td className="p-3 text-gray-300">
                        {formatearMonto(incidencia.sueldo_base_actual)}
                      </td>
                      <td className="p-3">
                        <span className={`px-2 py-1 rounded text-xs ${obtenerColorEstado(incidencia.estado)}`}>
                          {incidencia.estado}
                        </span>
                      </td>
                      <td className="p-3">
                        <div className="flex gap-2">
                          {incidencia.estado === 'pendiente' && (
                            <button
                              onClick={() => setIncidenciaEnEdicion(incidencia.id)}
                              className="px-3 py-1 bg-blue-600 text-white rounded text-xs hover:bg-blue-700"
                            >
                              Justificar
                            </button>
                          )}
                          {incidencia.estado === 'en_analisis' && (
                            <>
                              <button
                                onClick={() => setIncidenciaEnEdicion(incidencia.id)}
                                className="px-3 py-1 bg-green-600 text-white rounded text-xs hover:bg-green-700"
                              >
                                Aprobar
                              </button>
                              <button
                                onClick={() => setIncidenciaEnEdicion(incidencia.id)}
                                className="px-3 py-1 bg-red-600 text-white rounded text-xs hover:bg-red-700"
                              >
                                Rechazar
                              </button>
                            </>
                          )}
                          <button
                            onClick={() => setIncidenciaEnEdicion(incidencia.id)}
                            className="px-3 py-1 bg-gray-600 text-white rounded text-xs hover:bg-gray-700"
                          >
                            <Eye className="w-3 h-3" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Modal de edición */}
          {incidenciaEnEdicion && (
            <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
              <div className="bg-gray-800 rounded-lg p-6 max-w-md w-full m-4">
                <h3 className="text-lg font-medium text-white mb-4">
                  Gestionar Incidencia
                </h3>
                
                {/* Contenido según el estado */}
                <div className="space-y-4">
                  <textarea
                    value={justificacion}
                    onChange={(e) => setJustificacion(e.target.value)}
                    placeholder="Escriba su justificación o comentario..."
                    className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2 text-white placeholder-gray-400"
                    rows="4"
                  />
                  
                  <div className="flex gap-3">
                    <button
                      onClick={() => manejarJustificar(incidenciaEnEdicion)}
                      className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                    >
                      Justificar
                    </button>
                    <button
                      onClick={() => setIncidenciaEnEdicion(null)}
                      className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-700"
                    >
                      Cancelar
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </section>
  );
};

export default IncidenciasVariacionSection;
