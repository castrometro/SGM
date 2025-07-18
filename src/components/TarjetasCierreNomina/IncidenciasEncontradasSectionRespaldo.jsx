import { useState, useEffect } from "react";
import { AlertOctagon, ChevronDown, ChevronRight, Play, Loader2, CheckCircle, AlertTriangle, Filter, Users, Eye } from "lucide-react";
import IncidenciasTable from "./IncidenciasEncontradas/IncidenciasTable";
import ModalResolucionIncidencia from "./IncidenciasEncontradas/ModalResolucionIncidencia";
import { 
  obtenerIncidenciasCierre, 
  obtenerResumenIncidencias, 
  generarIncidenciasCierre,
  obtenerEstadoIncidenciasCierre,
  previewIncidenciasCierre
} from "../../api/nomina";

const IncidenciasEncontradasSectionRespaldo = ({ cierre }) => {
  const [expandido, setExpandido] = useState(true);
  const [incidencias, setIncidencias] = useState([]);
  const [resumen, setResumen] = useState(null);
  const [cargando, setCargando] = useState(false);
  const [generando, setGenerando] = useState(false);
  const [error, setError] = useState("");
  const [filtros, setFiltros] = useState({});
  const [incidenciaSeleccionada, setIncidenciaSeleccionada] = useState(null);
  const [modalAbierto, setModalAbierto] = useState(false);
  const [estadoIncidencias, setEstadoIncidencias] = useState(null);
  const [vistaPrevia, setVistaPrevia] = useState(null);
  const [mostrandoPreview, setMostrandoPreview] = useState(false);

  useEffect(() => {
    if (cierre?.id) {
      cargarEstadoIncidencias();
      if (estadoIncidencias?.tiene_incidencias) {
        cargarDatos();
      }
    }
  }, [cierre?.id]);

  const cargarEstadoIncidencias = async () => {
    if (!cierre?.id) return;
    
    try {
      const estado = await obtenerEstadoIncidenciasCierre(cierre.id);
      setEstadoIncidencias(estado);
    } catch (err) {
      console.error("Error cargando estado de incidencias:", err);
    }
  };

  const cargarDatos = async () => {
    if (!cierre?.id) return;
    
    setCargando(true);
    setError("");
    
    try {
      const [incidenciasData, resumenData] = await Promise.all([
        obtenerIncidenciasCierre(cierre.id, filtros),
        obtenerResumenIncidencias(cierre.id)
      ]);
      
      setIncidencias(Array.isArray(incidenciasData.results) ? incidenciasData.results : incidenciasData);
      setResumen(resumenData);
    } catch (err) {
      console.error("Error cargando datos de incidencias:", err);
      setError("Error al cargar las incidencias");
    } finally {
      setCargando(false);
    }
  };

  const manejarGenerarIncidencias = async () => {
    if (!cierre?.id) return;
    
    setGenerando(true);
    setError("");
    
    try {
      await generarIncidenciasCierre(cierre.id);
      // Esperar un momento para que se procese la tarea
      setTimeout(() => {
        cargarEstadoIncidencias();
        cargarDatos();
      }, 2000);
    } catch (err) {
      console.error("Error generando incidencias:", err);
      setError("Error al generar incidencias");
    } finally {
      setGenerando(false);
    }
  };

  const manejarVistaPrevia = async () => {
    if (!cierre?.id) return;
    
    setCargando(true);
    setError("");
    
    try {
      const preview = await previewIncidenciasCierre(cierre.id);
      setVistaPrevia(preview);
      setMostrandoPreview(true);
    } catch (err) {
      console.error("Error generando vista previa:", err);
      setError("Error al generar vista previa de incidencias");
    } finally {
      setCargando(false);
    }
  };

  const manejarFiltroChange = (nuevosFiltros) => {
    setFiltros({ ...filtros, ...nuevosFiltros });
  };

  const manejarIncidenciaSeleccionada = (incidencia) => {
    setIncidenciaSeleccionada(incidencia);
    setModalAbierto(true);
  };

  const manejarResolucionCreada = () => {
    cargarDatos(); // Recargar datos después de crear una resolución
    cargarEstadoIncidencias();
  };

  const obtenerColorEstado = (estado) => {
    switch (estado) {
      case 'sin_incidencias': return 'text-green-400';
      case 'con_incidencias_pendientes': return 'text-yellow-400';
      case 'incidencias_resueltas': return 'text-blue-400';
      case 'todas_aprobadas': return 'text-green-400';
      default: return 'text-gray-400';
    }
  };

  const puedeGenerarIncidencias = () => {
    return cierre?.estado === 'datos_consolidados' || cierre?.estado === 'completado';
  };

  return (
    <section className="space-y-6">
      <div
        className="flex items-center justify-between cursor-pointer hover:bg-gray-800/50 p-3 -m-3 rounded-lg transition-colors"
        onClick={() => setExpandido(!expandido)}
      >
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-10 h-10 bg-red-600 rounded-lg">
            <AlertOctagon size={20} className="text-white" />
          </div>
          <div>
            <h2 className="text-xl font-semibold text-white">
              Sistema de Incidencias (RESPALDO FUNCIONAL)
            </h2>
            <div className="flex items-center gap-2 text-sm">
              <p className="text-gray-400">
                Detección y resolución analista de incidencias entre archivos
              </p>
              {estadoIncidencias && (
                <span className={`${obtenerColorEstado(estadoIncidencias.estado_incidencias)} font-medium`}>
                  • {estadoIncidencias.total_incidencias || 0} incidencias
                </span>
              )}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {estadoIncidencias?.tiene_incidencias && (
            <div className="flex items-center gap-2 text-sm">
              <span className="text-gray-400">
                {estadoIncidencias.incidencias_pendientes} pendientes
              </span>
              <span className="text-gray-400">•</span>
              <span className="text-green-400">
                {estadoIncidencias.incidencias_resueltas} resueltas
              </span>
            </div>
          )}
          {expandido ? (
            <ChevronDown size={20} className="text-gray-400" />
          ) : (
            <ChevronRight size={20} className="text-gray-400" />
          )}
        </div>
      </div>

      {expandido && (
        <div className="space-y-6">
          {/* Botón para generar incidencias */}
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-medium text-white mb-2">
                  Generación de Incidencias
                </h3>
                <p className="text-gray-400 text-sm mb-4">
                  Compara los archivos procesados y detecta automáticamente las incidencias entre:
                </p>
                <div className="space-y-1 text-sm text-gray-300 mb-4">
                  <div className="flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-green-500" />
                    <span>Libro de Remuneraciones vs Archivo de Novedades</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-green-500" />
                    <span>MovimientosMes vs Archivos del Analista</span>
                  </div>
                </div>
                <div className="bg-blue-900/20 border border-blue-500/30 rounded-lg p-3 mb-4">
                  <div className="flex items-start gap-2">
                    <AlertTriangle className="w-4 h-4 text-blue-400 mt-0.5" />
                    <div className="text-sm text-blue-300">
                      <strong>Flujo de Resolución de Incidencias:</strong>
                      <ul className="mt-1 space-y-1 list-disc list-inside">
                        <li>🔍 <strong>Detectar:</strong> Generar incidencias para identificar diferencias entre archivos</li>
                        <li>📝 <strong>Resolver:</strong> Marcar incidencias como resueltas una vez corregidas</li>
                        <li>🔄 <strong>Resubir:</strong> Si es necesario, resubir archivos y regenerar incidencias</li>
                        <li>✅ <strong>Meta:</strong> Llegar a 0 incidencias para completar el cierre</li>
                      </ul>
                    </div>
                  </div>
                </div>
                {!puedeGenerarIncidencias() && (
                  <div className="flex items-center gap-2 text-yellow-400 text-sm">
                    <AlertTriangle className="w-4 h-4" />
                    <span>
                      El cierre debe estar en estado "Datos Consolidados" para generar incidencias
                    </span>
                  </div>
                )}
              </div>
              <div className="flex gap-3">
                <button
                  onClick={manejarVistaPrevia}
                  disabled={cargando || !puedeGenerarIncidencias()}
                  className="flex items-center px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {cargando ? (
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  ) : (
                    <Eye className="w-4 h-4 mr-2" />
                  )}
                  Vista Previa
                </button>
                <button
                  onClick={manejarGenerarIncidencias}
                  disabled={generando || !puedeGenerarIncidencias()}
                  className="flex items-center px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  {generando ? (
                    <>
                      <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                      Generando...
                    </>
                  ) : (
                    <>
                      <Play className="w-5 h-5 mr-2" />
                      Generar Incidencias
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>

          {/* Vista previa */}
          {mostrandoPreview && vistaPrevia && (
            <div className="bg-yellow-900/20 border border-yellow-500/30 rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-lg font-medium text-yellow-400">Vista Previa de Incidencias</h3>
                <button
                  onClick={() => setMostrandoPreview(false)}
                  className="text-gray-400 hover:text-white"
                >
                  ×
                </button>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                <div className="bg-gray-800 rounded p-3">
                  <p className="text-sm text-gray-400">Total a generar</p>
                  <p className="text-xl font-bold text-white">{vistaPrevia.total_incidencias}</p>
                </div>
                <div className="bg-gray-800 rounded p-3">
                  <p className="text-sm text-gray-400">Libro vs Novedades</p>
                  <p className="text-xl font-bold text-blue-400">{vistaPrevia.libro_vs_novedades}</p>
                </div>
                <div className="bg-gray-800 rounded p-3">
                  <p className="text-sm text-gray-400">Movimientos vs Analista</p>
                  <p className="text-xl font-bold text-green-400">{vistaPrevia.movimientos_vs_analista}</p>
                </div>
              </div>
              <p className="text-sm text-yellow-300">
                {vistaPrevia.mensaje}
              </p>
            </div>
          )}

          {/* Resumen de incidencias */}
          {resumen && (
            <>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-400">Total Incidencias</p>
                      <p className="text-2xl font-bold text-white">{resumen.total}</p>
                    </div>
                    <AlertOctagon className="w-8 h-8 text-red-500" />
                  </div>
                </div>
                
                <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-400">Críticas</p>
                      <p className="text-2xl font-bold text-red-400">
                        {resumen.por_prioridad?.critica || 0}
                      </p>
                    </div>
                    <AlertTriangle className="w-8 h-8 text-red-500" />
                  </div>
                </div>
                
                <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-400">Pendientes</p>
                      <p className="text-2xl font-bold text-yellow-400">
                        {resumen.por_estado?.pendiente || 0}
                      </p>
                    </div>
                    <Loader2 className="w-8 h-8 text-yellow-500" />
                  </div>
                </div>
                
                <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-400">Impacto Total</p>
                      <p className="text-lg font-bold text-white">
                        ${Number(resumen.impacto_monetario_total || 0).toLocaleString('es-CL')}
                      </p>
                    </div>
                    <span className="text-green-400 text-xl">$</span>
                  </div>
                </div>
              </div>

              {/* Mensaje sobre cómo resolver incidencias */}
              {resumen.total > 0 && (
                <div className="bg-yellow-900/20 border border-yellow-500/30 rounded-lg p-4">
                  <div className="flex items-start gap-2">
                    <AlertTriangle className="w-5 h-5 text-yellow-400 mt-0.5" />
                    <div className="text-sm text-yellow-300">
                      <strong>¿Cómo resolver las incidencias?</strong>
                      <p className="mt-1">
                        Para resolver las incidencias detectadas, puedes seguir este flujo:
                      </p>
                      <ol className="mt-2 space-y-1 list-decimal list-inside">
                        <li><strong>Revisar incidencias:</strong> Examina las diferencias detectadas en la tabla inferior.</li>
                        <li><strong>Opción A - Marcar como resueltas:</strong> Si las diferencias son correctas o aceptables, marca las incidencias individuales como resueltas.</li>
                        <li><strong>Opción B - Corregir y resubir:</strong> Si hay errores en los datos:</li>
                        <ul className="ml-6 mt-1 space-y-1 list-disc list-inside text-xs">
                          <li>Usa el botón "Resubir archivo" en las tarjetas de archivos correspondientes</li>
                          <li>Sube los archivos corregidos</li>
                          <li>Regresa aquí y presiona "Generar Incidencias" nuevamente</li>
                          <li>Repite hasta llegar a 0 incidencias</li>
                        </ul>
                      </ol>
                    </div>
                  </div>
                </div>
              )}
            </>
          )}

          {/* Filtros */}
          {estadoIncidencias?.tiene_incidencias && (
            <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
              <div className="flex items-center gap-4 flex-wrap">
                <div className="flex items-center gap-2">
                  <Filter className="w-4 h-4 text-gray-400" />
                  <span className="text-sm text-gray-400">Filtros:</span>
                </div>
                
                <select
                  value={filtros.estado || ''}
                  onChange={(e) => manejarFiltroChange({ estado: e.target.value })}
                  className="bg-gray-700 border border-gray-600 rounded px-3 py-1 text-sm text-white"
                >
                  <option value="">Todos los estados</option>
                  <option value="pendiente">Pendientes</option>
                  <option value="resuelta_analista">Resueltas</option>
                </select>
                
                <select
                  value={filtros.prioridad || ''}
                  onChange={(e) => manejarFiltroChange({ prioridad: e.target.value })}
                  className="bg-gray-700 border border-gray-600 rounded px-3 py-1 text-sm text-white"
                >
                  <option value="">Todas las prioridades</option>
                  <option value="critica">Crítica</option>
                  <option value="alta">Alta</option>
                  <option value="media">Media</option>
                  <option value="baja">Baja</option>
                </select>
                
                <select
                  value={filtros.tipo_incidencia || ''}
                  onChange={(e) => manejarFiltroChange({ tipo_incidencia: e.target.value })}
                  className="bg-gray-700 border border-gray-600 rounded px-3 py-1 text-sm text-white"
                >
                  <option value="">Todos los tipos</option>
                  {/* Grupo 1: Libro vs Novedades */}
                  <optgroup label="Libro vs Novedades">
                    <option value="empleado_solo_libro">Empleado solo en Libro</option>
                    <option value="empleado_solo_novedades">Empleado solo en Novedades</option>
                    <option value="diff_datos_personales">Diferencia en Datos Personales</option>
                    <option value="diff_sueldo_base">Diferencia en Sueldo Base</option>
                    <option value="diff_concepto_monto">Diferencia en Monto por Concepto</option>
                    <option value="concepto_solo_libro">Concepto solo en Libro</option>
                    <option value="concepto_solo_novedades">Concepto solo en Novedades</option>
                  </optgroup>
                  {/* Grupo 2: MovimientosMes vs Analista */}
                  <optgroup label="Movimientos vs Analista">
                    <option value="ingreso_no_reportado">Ingreso no reportado</option>
                    <option value="finiquito_no_reportado">Finiquito no reportado</option>
                    <option value="ausencia_no_reportada">Ausencia no reportada</option>
                    <option value="diff_fechas_ausencia">Diferencia en Fechas de Ausencia</option>
                    <option value="diff_dias_ausencia">Diferencia en Días de Ausencia</option>
                    <option value="diff_tipo_ausencia">Diferencia en Tipo de Ausencia</option>
                  </optgroup>
                </select>
                
                <input
                  type="text"
                  placeholder="Buscar por RUT, descripción, concepto..."
                  value={filtros.busqueda || ''}
                  onChange={(e) => manejarFiltroChange({ busqueda: e.target.value })}
                  className="bg-gray-700 border border-gray-600 rounded px-3 py-1 text-sm text-white placeholder-gray-400"
                />
              </div>
            </div>
          )}

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
          {estadoIncidencias?.tiene_incidencias ? (
            <div className="bg-gray-800 rounded-lg border border-gray-700">
              <div className="p-4 border-b border-gray-700">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-medium text-white">
                    Lista de Incidencias
                  </h3>
                  <div className="flex items-center gap-2 text-sm text-gray-400">
                    <Users className="w-4 h-4" />
                    <span>Resolución por Analista</span>
                  </div>
                </div>
              </div>
              <div className="p-4">
                <IncidenciasTable
                  cierreId={cierre?.id}
                  filtros={filtros}
                  onIncidenciaSeleccionada={manejarIncidenciaSeleccionada}
                />
              </div>
            </div>
          ) : !cargando && estadoIncidencias && (
            <div className="text-center py-8 text-gray-400">
              <CheckCircle className="w-12 h-12 mx-auto mb-3 text-green-500" />
              <p className="text-lg">No se encontraron incidencias</p>
              <p className="text-sm">
                Los archivos están en concordancia o aún no se han generado las incidencias
              </p>
            </div>
          )}
        </div>
      )}

      {/* Modal de resolución */}
      <ModalResolucionIncidencia
        abierto={modalAbierto}
        incidencia={incidenciaSeleccionada}
        onCerrar={() => {
          setModalAbierto(false);
          setIncidenciaSeleccionada(null);
        }}
        onResolucionCreada={manejarResolucionCreada}
      />
    </section>
  );
};

export default IncidenciasEncontradasSectionRespaldo;
