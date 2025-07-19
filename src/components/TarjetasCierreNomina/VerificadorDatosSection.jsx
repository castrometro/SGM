import { useState, useEffect } from "react";
import { ShieldCheck, ChevronDown, ChevronRight, Loader2, CheckCircle, AlertTriangle, Filter, Eye, RefreshCw } from "lucide-react";
import DiscrepanciasTable from "./VerificadorDatos/DiscrepanciasTable";
import { 
  obtenerDiscrepanciasCierre, 
  obtenerResumenDiscrepancias, 
  generarDiscrepanciasCierre,
  obtenerEstadoDiscrepanciasCierre,
  previewDiscrepanciasCierre,
  limpiarDiscrepanciasCierre
} from "../../api/nomina";

const VerificadorDatosSection = ({ cierre }) => {
  const [expandido, setExpandido] = useState(true);
  const [discrepancias, setDiscrepancias] = useState([]);
  const [resumen, setResumen] = useState(null);
  const [cargando, setCargando] = useState(false);
  const [generando, setGenerando] = useState(false);
  const [error, setError] = useState("");
  const [filtros, setFiltros] = useState({});
  const [estadoDiscrepancias, setEstadoDiscrepancias] = useState(null);
  const [vistaPrevia, setVistaPrevia] = useState(null);
  const [mostrandoPreview, setMostrandoPreview] = useState(false);

  useEffect(() => {
    if (cierre?.id) {
      cargarEstadoDiscrepancias();
    }
  }, [cierre?.id]);

  useEffect(() => {
    if (cierre?.id && estadoDiscrepancias?.total_discrepancias > 0) {
      cargarDatos();
    }
  }, [cierre?.id, estadoDiscrepancias]);

  const cargarEstadoDiscrepancias = async () => {
    if (!cierre?.id) return;
    
    try {
      const estado = await obtenerEstadoDiscrepanciasCierre(cierre.id);
      setEstadoDiscrepancias(estado);
    } catch (err) {
      console.error("Error cargando estado de discrepancias:", err);
    }
  };

  const cargarDatos = async () => {
    if (!cierre?.id) return;
    
    setCargando(true);
    setError("");
    
    try {
      const [discrepanciasData, resumenData] = await Promise.all([
        obtenerDiscrepanciasCierre(cierre.id, filtros),
        obtenerResumenDiscrepancias(cierre.id)
      ]);
      
      setDiscrepancias(Array.isArray(discrepanciasData.results) ? discrepanciasData.results : discrepanciasData);
      setResumen(resumenData);
    } catch (err) {
      console.error("Error cargando datos de discrepancias:", err);
      setError("Error al cargar datos de verificación");
    } finally {
      setCargando(false);
    }
  };

  const manejarGenerarDiscrepancias = async () => {
    if (!cierre?.id) return;
    
    setGenerando(true);
    setError("");
    
    try {
      await generarDiscrepanciasCierre(cierre.id);
      // Esperar un momento para que se procese la tarea
      setTimeout(() => {
        cargarEstadoDiscrepancias();
        cargarDatos();
      }, 2000);
    } catch (err) {
      console.error("Error generando discrepancias:", err);
      setError("Error al generar verificación de datos");
    } finally {
      setGenerando(false);
    }
  };

  const manejarVistaPrevia = async () => {
    if (!cierre?.id) return;
    
    setCargando(true);
    setError("");
    
    try {
      const preview = await previewDiscrepanciasCierre(cierre.id);
      setVistaPrevia(preview);
      setMostrandoPreview(true);
    } catch (err) {
      console.error("Error generando vista previa:", err);
      setError("Error al generar vista previa de verificación");
    } finally {
      setCargando(false);
    }
  };

  const manejarLimpiarDiscrepancias = async () => {
    if (!cierre?.id || !window.confirm("¿Estás seguro de que quieres limpiar todas las discrepancias? Esta acción no se puede deshacer.")) {
      return;
    }
    
    setCargando(true);
    setError("");
    
    try {
      await limpiarDiscrepanciasCierre(cierre.id);
      setDiscrepancias([]);
      setResumen(null);
      setEstadoDiscrepancias(null);
      await cargarEstadoDiscrepancias();
    } catch (err) {
      console.error("Error limpiando discrepancias:", err);
      setError("Error al limpiar discrepancias");
    } finally {
      setCargando(false);
    }
  };

  const manejarFiltroChange = (nuevosFiltros) => {
    setFiltros({ ...filtros, ...nuevosFiltros });
  };

  const puedeGenerarDiscrepancias = () => {
    return cierre?.estado === 'archivos_completos' || cierre?.estado === 'verificacion_datos';
  };

  const mostrarMensajeRestriccion = () => {
    // Solo mostrar el mensaje si el estado no permite generar discrepancias Y aún no se han generado
    const estadosQueNoPermiten = !puedeGenerarDiscrepancias();
    const estadosQueYaTienenDatos = cierre?.estado === 'con_discrepancias' || 
                                    cierre?.estado === 'verificado_sin_discrepancias' || 
                                    cierre?.estado === 'completado';
    
    return estadosQueNoPermiten && !estadosQueYaTienenDatos;
  };

  const obtenerColorEstado = () => {
    if (!estadoDiscrepancias) return 'text-gray-400';
    return estadoDiscrepancias.requiere_correccion ? 'text-red-400' : 'text-green-400';
  };

  const obtenerTextoEstado = () => {
    if (!estadoDiscrepancias) return 'Pendiente';
    return estadoDiscrepancias.requiere_correccion ? 'Con Discrepancias' : 'Verificado';
  };

  return (
    <section className="space-y-6">
      <div
        className="flex items-center justify-between cursor-pointer hover:bg-gray-800/50 p-3 -m-3 rounded-lg transition-colors"
        onClick={() => setExpandido(!expandido)}
      >
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-10 h-10 bg-orange-600 rounded-lg">
            <ShieldCheck size={20} className="text-white" />
          </div>
          <div>
            <h2 className="text-xl font-semibold text-white">
              Verificación de Datos
            </h2>
            <div className="flex items-center gap-2 text-sm">
              <p className="text-gray-400">
                Verificación de consistencia entre Libro de Remuneraciones y Novedades
              </p>
              {estadoDiscrepancias && (
                <span className={`${obtenerColorEstado()} font-medium`}>
                  • {estadoDiscrepancias.total_discrepancias || 0} discrepancias
                </span>
              )}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {estadoDiscrepancias && estadoDiscrepancias.total_discrepancias > 0 && (
            <div className="flex items-center gap-2 text-sm">
              <span className="text-white">
                {estadoDiscrepancias.total_discrepancias} discrepancias detectadas
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
          {/* Panel principal de verificación */}
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <div className="flex items-center justify-between">
              {/* Lado izquierdo - Estado y contadores */}
              <div className="flex items-center gap-6">
                {/* Estado de verificación */}
                <div className="text-center">
                  <div className={`w-16 h-16 rounded-full flex items-center justify-center mb-2 ${
                    estadoDiscrepancias 
                      ? (estadoDiscrepancias.requiere_correccion ? 'bg-red-500/20 border-2 border-red-500' : 'bg-green-500/20 border-2 border-green-500')
                      : 'bg-gray-500/20 border-2 border-gray-500'
                  }`}>
                    <ShieldCheck size={24} className={obtenerColorEstado()} />
                  </div>
                  <p className="text-sm text-gray-400">Estado</p>
                  <p className={`text-sm font-medium ${obtenerColorEstado()}`}>
                    {obtenerTextoEstado()}
                  </p>
                </div>

                {/* Contadores */}
                {estadoDiscrepancias && estadoDiscrepancias.total_discrepancias > 0 && (
                  <>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-white">
                        {estadoDiscrepancias.total_discrepancias || 0}
                      </div>
                      <p className="text-sm text-gray-400">Total</p>
                    </div>
                    
                    <div className="text-center">
                      <div className="text-2xl font-bold text-blue-400">
                        {resumen?.libro_vs_novedades || 0}
                      </div>
                      <p className="text-sm text-gray-400">Libro vs Novedades</p>
                    </div>
                    
                    <div className="text-center">
                      <div className="text-2xl font-bold text-green-400">
                        {resumen?.movimientos_vs_analista || 0}
                      </div>
                      <p className="text-sm text-gray-400">Movimientos vs Analista</p>
                    </div>
                  </>
                )}
              </div>

              {/* Lado derecho - Botones de acción */}
              <div className="flex gap-3">
                <button
                  onClick={manejarVistaPrevia}
                  disabled={cargando || !puedeGenerarDiscrepancias()}
                  className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <Eye className="w-4 h-4 mr-2" />
                  Vista Previa
                </button>

                <button
                  onClick={manejarGenerarDiscrepancias}
                  disabled={generando || !puedeGenerarDiscrepancias()}
                  className="flex items-center px-6 py-3 bg-orange-600 text-white rounded-lg hover:bg-orange-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
                >
                  {generando ? (
                    <>
                      <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                      Verificando...
                    </>
                  ) : (
                    <>
                      <ShieldCheck className="w-5 h-5 mr-2" />
                      Verificar Datos
                    </>
                  )}
                </button>

                {estadoDiscrepancias && estadoDiscrepancias.total_discrepancias > 0 && (
                  <button
                    onClick={manejarLimpiarDiscrepancias}
                    disabled={cargando}
                    className="flex items-center px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    <RefreshCw className="w-4 h-4 mr-2" />
                    Limpiar
                  </button>
                )}
              </div>
            </div>

            {/* Mensaje de restricción si aplica */}
            {mostrarMensajeRestriccion() && (
              <div className="mt-4 p-3 bg-yellow-900/20 border border-yellow-500/30 rounded-lg">
                <div className="flex items-center gap-2 text-yellow-400 text-sm">
                  <AlertTriangle className="w-4 h-4" />
                  <span>
                    El cierre debe estar en estado "Archivos Completos" para verificar datos
                  </span>
                </div>
              </div>
            )}
          </div>

          {/* Vista previa */}
          {mostrandoPreview && vistaPrevia && (
            <div className="bg-blue-900/20 border border-blue-500/30 rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-lg font-medium text-blue-400">Vista Previa de Discrepancias</h3>
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
                  <p className="text-xl font-bold text-white">{vistaPrevia.total_discrepancias}</p>
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
              <p className="text-sm text-blue-300">
                {vistaPrevia.mensaje}
              </p>
            </div>
          )}

          {/* Resumen de discrepancias */}
          {resumen && (
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-400">Total Discrepancias</p>
                    <p className="text-2xl font-bold text-white">{resumen.total}</p>
                  </div>
                  <AlertTriangle className="w-8 h-8 text-orange-500" />
                </div>
              </div>
              
              <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-400">Libro vs Novedades</p>
                    <p className="text-2xl font-bold text-blue-400">
                      {resumen.libro_vs_novedades || 0}
                    </p>
                  </div>
                  <ShieldCheck className="w-8 h-8 text-blue-500" />
                </div>
              </div>
              
              <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-400">Movimientos vs Analista</p>
                    <p className="text-2xl font-bold text-green-400">
                      {resumen.movimientos_vs_analista || 0}
                    </p>
                  </div>
                  <CheckCircle className="w-8 h-8 text-green-500" />
                </div>
              </div>
              
              <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-400">Empleados Afectados</p>
                    <p className="text-lg font-bold text-white">
                      {resumen.empleados_afectados || 0}
                    </p>
                  </div>
                  <span className="text-yellow-400 text-xl">👥</span>
                </div>
              </div>
            </div>
          )}

          {/* Filtros */}
          {estadoDiscrepancias && estadoDiscrepancias.total_discrepancias > 0 && (
            <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
              <div className="flex items-center gap-4 flex-wrap">
                <div className="flex items-center gap-2">
                  <Filter className="w-4 h-4 text-gray-400" />
                  <span className="text-sm text-gray-400">Filtros:</span>
                </div>
                
                <select
                  value={filtros.tipo_discrepancia || ''}
                  onChange={(e) => manejarFiltroChange({ tipo_discrepancia: e.target.value })}
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

          {/* Tabla de discrepancias */}
          {estadoDiscrepancias && estadoDiscrepancias.total_discrepancias > 0 ? (
            <div className="bg-gray-800 rounded-lg border border-gray-700">
              <div className="p-4 border-b border-gray-700">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-medium text-white">
                    Lista de Discrepancias
                  </h3>
                  <div className="flex items-center gap-2 text-sm text-gray-400">
                    <span>Solo informativas - No requieren resolución</span>
                  </div>
                </div>
              </div>
              <div className="p-4">
                <DiscrepanciasTable
                  cierreId={cierre?.id}
                  filtros={filtros}
                />
              </div>
            </div>
          ) : !cargando && estadoDiscrepancias && (
            <div className="text-center py-8 text-gray-400">
              <CheckCircle className="w-12 h-12 mx-auto mb-3 text-green-500" />
              <p className="text-lg">No se encontraron discrepancias</p>
              <p className="text-sm">
                Los datos están en concordancia o aún no se ha ejecutado la verificación
              </p>
            </div>
          )}
        </div>
      )}
    </section>
  );
};

export default VerificadorDatosSection;
