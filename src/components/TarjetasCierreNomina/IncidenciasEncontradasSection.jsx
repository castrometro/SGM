import { useState, useEffect } from "react";
import { AlertOctagon, ChevronDown, ChevronRight, Play, Loader2, CheckCircle, AlertTriangle, Filter, Users, Eye, Lock, TrendingUp } from "lucide-react";
import { formatearMonedaChilena } from "../../utils/formatters";
import IncidenciasTable from "./IncidenciasEncontradas/IncidenciasTable";
import ModalResolucionIncidencia from "./IncidenciasEncontradas/ModalResolucionIncidencia";
import { 
  obtenerIncidenciasCierre, 
  obtenerResumenIncidencias, 
  generarIncidenciasCierre,
  obtenerEstadoIncidenciasCierre,
  previewIncidenciasCierre,
  finalizarCierre,
  consultarEstadoTarea,
  obtenerAnalisisCompletoTemporal,
  limpiarIncidenciasCierre
} from "../../api/nomina";

// Clasificaciones disponibles para selección
const clasificacionesDisponibles = [
  "haberes_imponibles",
  "haberes_no_imponibles", 
  "horas_extras",
  "descuentos_legales",
  "otros_descuentos",
  "aportes_patronales",
  "informacion_adicional",
  "impuestos"
];

const nombresClasificaciones = {
  haberes_imponibles: "💰 Haberes Imponibles",
  haberes_no_imponibles: "🎁 Haberes No Imponibles",
  horas_extras: "⏰ Horas Extras",
  descuentos_legales: "⚖️ Descuentos Legales",
  otros_descuentos: "📋 Otros Descuentos",
  aportes_patronales: "🏢 Aportes Patronales",
  informacion_adicional: "📝 Información Adicional",
  impuestos: "🏛️ Impuestos",
};

const IncidenciasEncontradasSection = ({ 
  cierre, 
  disabled = false, 
  onCierreActualizado, 
  onEstadoChange,
  
  // 🎯 Props para acordeón
  expandido = true,
  onToggleExpansion,
}) => {
  // Remover estado interno de expandido ya que ahora viene como prop
  // const [expandido, setExpandido] = useState(true); // ← ELIMINADO
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
  
  // 🎯 CONFIGURACIÓN PABLO - SIN CHECKBOXES
  // Los conceptos están configurados automáticamente en el backend:
  // - Análisis detallado: haberes_imponibles, haberes_no_imponibles, otros_descuentos
  // - Solo resumen: descuentos_legales, aportes_patronales, informacion_adicional, impuestos, horas_extras
  
  const [mostrandoPreview, setMostrandoPreview] = useState(false);
  const [finalizandoCierre, setFinalizandoCierre] = useState(false);
  const [analisisCompleto, setAnalisisCompleto] = useState(null);
  const [mostrandoAnalisisCompleto, setMostrandoAnalisisCompleto] = useState(false);
  const [cargandoAnalisis, setCargandoAnalisis] = useState(false);

  // Cargar estado de incidencias automáticamente al montar el componente
  useEffect(() => {
    console.log("🔍 [useEffect Init] Componente montado, cierre:", cierre);
    console.log("🔍 [useEffect Init] cierre.id:", cierre?.id);
    
    if (cierre?.id) {
      console.log("✅ [useEffect Init] Llamando cargarEstadoIncidencias para cierre:", cierre.id);
      cargarEstadoIncidencias();
    } else {
      console.warn("⚠️ [useEffect Init] No se puede cargar estado - cierre.id no disponible");
    }
  }, [cierre?.id]);

  // Cargar datos de incidencias cuando se detecta que existen
  useEffect(() => {
    console.log("🔍 [useEffect] Estado de incidencias cambió:", estadoIncidencias);
    console.log("🔍 [useEffect] Total incidencias del estado:", estadoIncidencias?.total_incidencias);
    
    if (estadoIncidencias?.total_incidencias > 0) {
      console.log("🔍 [useEffect] Detectadas incidencias, llamando cargarDatos()");
      cargarDatos();
    } else {
      console.log("🔍 [useEffect] No hay incidencias para cargar");
    }
  }, [estadoIncidencias?.total_incidencias]);

  // 🎯 Efecto para reportar el estado de la sección al componente padre
  useEffect(() => {
    if (estadoIncidencias && onEstadoChange) {
      // Determinar el estado: procesado si todas las incidencias están resueltas
      const estadoFinal = (estadoIncidencias.total_incidencias_resueltas === estadoIncidencias.total_incidencias && 
                          estadoIncidencias.total_incidencias >= 0) 
        ? "procesado" 
        : "pendiente";
      
      console.log('📊 [IncidenciasEncontradasSection] Reportando estado:', estadoFinal, {
        totalIncidencias: estadoIncidencias.total_incidencias,
        incidenciasResueltas: estadoIncidencias.total_incidencias_resueltas
      });
      
      onEstadoChange(estadoFinal);
    }
  }, [
    estadoIncidencias?.total_incidencias, 
    estadoIncidencias?.total_incidencias_resueltas, 
    onEstadoChange
  ]);

  const cargarEstadoIncidencias = async () => {
    if (!cierre?.id) {
      console.warn("⚠️ [cargarEstadoIncidencias] No hay cierre.id disponible:", cierre);
      return;
    }
    
    console.log("🔍 [cargarEstadoIncidencias] Iniciando carga para cierre:", cierre.id);
    console.log("🔍 [cargarEstadoIncidencias] Cierre completo:", cierre);
    
    try {
      const estado = await obtenerEstadoIncidenciasCierre(cierre.id);
      console.log("✅ [cargarEstadoIncidencias] Estado de incidencias recibido:", estado);
      console.log("✅ [cargarEstadoIncidencias] Tipo de dato recibido:", typeof estado);
      console.log("✅ [cargarEstadoIncidencias] Keys del estado:", Object.keys(estado || {}));
      
      if (estado) {
        setEstadoIncidencias(estado);
        console.log("✅ [cargarEstadoIncidencias] Estado guardado exitosamente");
        
        // También actualizar el prop cierre con el estado administrativo
        if (estado.estado_cierre && cierre) {
          cierre.estado_incidencias = estado.estado_cierre;
          console.log("✅ [cargarEstadoIncidencias] Estado del cierre actualizado:", estado.estado_cierre);
        }
      } else {
        console.warn("⚠️ [cargarEstadoIncidencias] Estado recibido es null o undefined");
        setEstadoIncidencias(null);
      }
    } catch (err) {
      console.error("❌ [cargarEstadoIncidencias] Error cargando estado de incidencias:", err);
      console.error("❌ [cargarEstadoIncidencias] Error detallado:", {
        message: err.message,
        status: err.response?.status,
        statusText: err.response?.statusText,
        data: err.response?.data,
        url: err.config?.url
      });
      setEstadoIncidencias(null);
      setError(`Error cargando estado de incidencias: ${err.message}`);
    }
  };

  const cargarDatos = async () => {
    if (!cierre?.id) return;
    
    console.log("🔍 [cargarDatos] Iniciando carga de datos para cierre:", cierre.id);
    
    setCargando(true);
    setError("");
    
    try {
      console.log("🔍 [cargarDatos] Llamando APIs con filtros:", filtros);
      
      const [incidenciasData, resumenData] = await Promise.all([
        obtenerIncidenciasCierre(cierre.id, filtros),
        obtenerResumenIncidencias(cierre.id)
      ]);
      
      console.log("🔍 [cargarDatos] Datos de incidencias recibidos:", incidenciasData);
      console.log("🔍 [cargarDatos] Resumen recibido:", resumenData);
      
      const incidenciasArray = Array.isArray(incidenciasData.results) ? incidenciasData.results : incidenciasData;
      console.log("🔍 [cargarDatos] Incidencias procesadas:", incidenciasArray);
      console.log("🔍 [cargarDatos] Total de incidencias:", incidenciasArray?.length || 0);
      
      setIncidencias(incidenciasArray);
      setResumen(resumenData);
    } catch (err) {
      console.error("❌ [cargarDatos] Error cargando datos de incidencias:", err);
      setError("Error al cargar incidencias");
    } finally {
      setCargando(false);
    }
  };

  const manejarLimpiarIncidencias = async () => {
    if (!cierre?.id) return;
    
    if (!window.confirm('⚠️ ¿Estás seguro de limpiar TODAS las incidencias? Esta acción no se puede deshacer.')) {
      return;
    }
    
    setCargando(true);
    setError("");
    
    try {
      console.log("🗑️ Limpiando incidencias...");
      const resultado = await limpiarIncidenciasCierre(cierre.id);
      console.log("✅ Resultado limpieza:", resultado);
      
      // Limpiar estados y recargar
      setIncidencias([]);
      setResumen(null);
      setEstadoIncidencias(null);
      
      setTimeout(async () => {
        await cargarEstadoIncidencias();
        console.log("🔄 Estados recargados después de limpiar");
      }, 1000);
      
      alert(`✅ ${resultado.incidencias_borradas} incidencias limpiadas exitosamente`);
      
    } catch (err) {
      console.error("Error limpiando incidencias:", err);
      setError("Error al limpiar incidencias");
      alert("❌ Error al limpiar incidencias");
    } finally {
      setCargando(false);
    }
  };

  const manejarGenerarIncidencias = async () => {
    if (!cierre?.id) return;
    
    setGenerando(true);
    setError("");
    
    try {
      console.log("🔄 Iniciando generación de incidencias con configuración automática de Pablo...");
      console.log("📋 Análisis detallado: haberes imponibles, haberes no imponibles y descuentos");
      console.log("📋 Solo resumen: descuentos legales, aportes patronales, información adicional, impuestos, horas extras");
      
      // Usar configuración automática del backend (sin clasificaciones manuales)
      await generarIncidenciasCierre(cierre.id);
      
      console.log("✅ Incidencias generadas, refrescando estado del cierre...");
      
      // Refrescar el estado del cierre para mostrar el cambio automáticamente
      if (onCierreActualizado) {
        await onCierreActualizado();
      }
      
      console.log("✅ Incidencias generadas, limpiando cache y recargando datos...");
      
      // Limpiar estados para forzar recarga completa
      setIncidencias([]);
      setResumen(null);
      setEstadoIncidencias(null);
      
      // Recargar estados inmediatamente y después con delay
      setTimeout(async () => {
        await cargarEstadoIncidencias();
        await cargarDatos();
        console.log("🔄 Primera recarga completada");
      }, 1000);
      
      // Segunda recarga para asegurar sincronización
      setTimeout(async () => {
        await cargarEstadoIncidencias();
        await cargarDatos();
        console.log("🔄 Segunda recarga completada");
      }, 3000);
      
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

  const manejarAnalisisCompleto = async () => {
    if (!cierre?.id) return;
    
    setCargandoAnalisis(true);
    setError("");
    
    try {
      const response = await obtenerAnalisisCompletoTemporal(cierre.id);
      setAnalisisCompleto(response.analisis);
      setMostrandoAnalisisCompleto(true);
    } catch (err) {
      console.error("Error generando análisis completo:", err);
      setError("Error al generar análisis completo temporal");
    } finally {
      setCargandoAnalisis(false);
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

  const manejarFinalizarCierre = async () => {
    if (!cierre?.id) return;
    
    // Confirmación del usuario
    if (!window.confirm('¿Está seguro de que desea finalizar este cierre? Este proceso generará los reportes finales y no se podrá revertir.')) {
      return;
    }
    
    setFinalizandoCierre(true);
    setError("");
    
    try {
      const resultado = await finalizarCierre(cierre.id);

      // Feedback inmediato
      if (resultado?.message) {
        alert(`▶️ ${resultado.message}`);
      }

      const taskId = resultado?.task_id || resultado?.taskId || resultado?.task || resultado?.id;

      // Si hay task_id, hacer polling hasta que termine la finalización
      if (taskId) {
        const inicio = Date.now();
        const timeoutMs = 10 * 60 * 1000; // 10 minutos
        const intervaloMs = 2000;

        while (Date.now() - inicio < timeoutMs) {
          try {
            const estado = await consultarEstadoTarea(cierre.id, taskId);
            const state = estado?.state || estado?.status;

            if (state === 'SUCCESS') {
              // Actualizar datos del cierre al completar
              if (onCierreActualizado) {
                await onCierreActualizado();
              }
              alert('🎉 Cierre finalizado correctamente.');
              break;
            }
            if (state === 'FAILURE') {
              const detalle = (estado?.result && (estado.result.detail || estado.result.message)) || '';
              const msg = `Error al finalizar cierre${detalle ? `: ${detalle}` : ''}`;
              setError(msg);
              alert(`❌ ${msg}`);
              break;
            }
          } catch (pollErr) {
            // Continuar reintentando a menos que sea un 4xx persistente
            // eslint-disable-next-line no-console
            console.warn('Polling estado tarea falló, reintentando...', pollErr?.message || pollErr);
          }
          // Esperar siguiente intento
          // eslint-disable-next-line no-await-in-loop
          await new Promise((r) => setTimeout(r, intervaloMs));
        }
      } else if (resultado?.success) {
        // Sin task_id, pero éxito inmediato (fallback)
        if (onCierreActualizado) {
          await onCierreActualizado();
        }
        alert('🎉 Cierre finalizado.');
      } else {
        const msg = resultado?.message || 'Error al finalizar cierre';
        setError(msg);
        alert(`❌ ${msg}`);
      }
    } catch (err) {
      console.error("Error finalizando cierre:", err);
      const errorMsg = err.response?.data?.message || err.message || 'Error al finalizar cierre';
      setError(errorMsg);
      alert(`Error: ${errorMsg}`);
    } finally {
      setFinalizandoCierre(false);
    }
  };

  const obtenerColorEstado = (estado) => {
    switch (estado) {
      case 'pendiente': return 'text-gray-400';
      case 'detectadas': return 'text-yellow-400';
      case 'en_revision': return 'text-blue-400';
      case 'resueltas': return 'text-green-400';
      // Estados legacy para compatibilidad
      case 'sin_incidencias': return 'text-green-400';
      case 'con_incidencias_pendientes': return 'text-yellow-400';
      case 'incidencias_resueltas': return 'text-green-400';
      case 'todas_aprobadas': return 'text-green-400';
      default: return 'text-gray-400';
    }
  };

  const obtenerTextoEstadoIncidencias = (estado) => {
    switch (estado) {
      case 'pendiente': return 'Pendiente';
      case 'detectadas': return 'Detectadas';
      case 'en_revision': return 'En Revisión';
      case 'resueltas': return 'Resueltas';
      default: return 'Pendiente';
    }
  };

  const puedeGenerarIncidencias = () => {
    return cierre?.estado === 'datos_consolidados' || 
           cierre?.estado === 'con_incidencias' || 
           cierre?.estado === 'sin_incidencias' ||
           cierre?.estado === 'incidencias_resueltas' ||
           cierre?.estado === 'finalizado';
  };

  // Funciones de selección de clasificaciones eliminadas - ahora usa configuración automática de Pablo

  return (
    <section className="space-y-6">
      <div
        className={`flex items-center justify-between cursor-pointer hover:bg-gray-800/50 p-3 -m-3 rounded-lg transition-colors ${
          disabled ? 'opacity-60' : ''
        }`}
        onClick={() => onToggleExpansion && onToggleExpansion()}
      >
        <div className="flex items-center gap-3">
          <div className={`flex items-center justify-center w-10 h-10 rounded-lg ${
            disabled ? 'bg-gray-600' : 'bg-red-600'
          }`}>
            {disabled ? (
              <Lock size={20} className="text-white" />
            ) : (
              <AlertOctagon size={20} className="text-white" />
            )}
          </div>
          <div>
            <h2 className="text-xl font-semibold text-white">
              Sistema de Incidencias
              {disabled && <span className="text-gray-400 text-sm ml-2">(Bloqueado - Cierre Finalizado)</span>}
            </h2>
            <div className="flex items-center gap-2 text-sm">
              <p className="text-gray-400">
                Detección automática de inconsistencias respecto al cierre anterior
              </p>
              {cierre?.estado_incidencias && (
                <span className={`${obtenerColorEstado(cierre.estado_incidencias)} font-medium`}>
                  • Estado: {obtenerTextoEstadoIncidencias(cierre.estado_incidencias)}
                </span>
              )}
              {estadoIncidencias?.total_incidencias && (
                <span className="text-gray-300">
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
                {estadoIncidencias.incidencias_pendientes} incidencias pendientes
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

      {expandido && !disabled && (
        <div className="space-y-6">
          {/* Verificación de datos - Diseño simplificado */}
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <div className="flex items-center justify-between">
              {/* Lado izquierdo - Estado y contadores */}
              <div className="flex items-center gap-6">
                {/* Estado de verificación */}
                <div className="text-center">
                  <div className={`w-16 h-16 rounded-full flex items-center justify-center mb-2 ${
                    cierre?.estado_incidencias === 'resueltas' ? 'bg-green-500/20 border-2 border-green-500' :
                    cierre?.estado_incidencias === 'detectadas' || cierre?.estado_incidencias === 'en_revision' ? 'bg-yellow-500/20 border-2 border-yellow-500' :
                    'bg-gray-500/20 border-2 border-gray-500'
                  }`}>
                    <AlertOctagon size={24} className={
                      cierre?.estado_incidencias === 'resueltas' ? 'text-green-400' :
                      cierre?.estado_incidencias === 'detectadas' || cierre?.estado_incidencias === 'en_revision' ? 'text-yellow-400' :
                      'text-gray-400'
                    } />
                  </div>
                  <p className="text-sm text-gray-400">Estado</p>
                  <p className={`text-sm font-medium ${obtenerColorEstado(cierre?.estado_incidencias || 'pendiente')}`}>
                    {obtenerTextoEstadoIncidencias(cierre?.estado_incidencias || 'pendiente')}
                  </p>
                </div>

                {/* Contadores */}
                {estadoIncidencias?.total_incidencias && estadoIncidencias.total_incidencias > 0 && (
                  <>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-red-400">
                        {(estadoIncidencias.estados?.pendiente || 0) + (estadoIncidencias.estados?.resuelta_analista || 0)}
                      </div>
                      <p className="text-sm text-gray-400">Pendientes</p>
                    </div>
                    
                    <div className="text-center">
                      <div className="text-2xl font-bold text-green-400">
                        {estadoIncidencias.estados?.aprobada_supervisor || 0}
                      </div>
                      <p className="text-sm text-gray-400">Resueltas</p>
                    </div>
                    
                    <div className="text-center">
                      <div className="text-2xl font-bold text-white">
                        {estadoIncidencias.total_incidencias || 0}
                      </div>
                      <p className="text-sm text-gray-400">Total</p>
                    </div>
                  </>
                )}
              </div>

              {/* Lado derecho - Botones de acción */}
              <div className="flex gap-3">
                {/* Botón de Debug - Limpiar Incidencias */}
                <button
                  onClick={manejarLimpiarIncidencias}
                  disabled={cargando}
                  className="flex items-center px-3 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium text-sm"
                  title="Debug: Limpiar todas las incidencias"
                >
                  🗑️ Limpiar
                </button>


                <button
                  onClick={manejarGenerarIncidencias}
                  disabled={generando || !puedeGenerarIncidencias()}
                  className="flex items-center px-6 py-3 bg-orange-600 text-white rounded-lg hover:bg-orange-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
                >
                  {generando ? (
                    <>
                      <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                      Generando incidencias...
                    </>
                  ) : (
                    <>
                      <AlertOctagon className="w-5 h-5 mr-2" />
                      Detectar Incidencias
                    </>
                  )}
                </button>

                {/* Botón Finalizar Cierre - Solo cuando estado es incidencias_resueltas */}
                {cierre?.estado === 'incidencias_resueltas' && (
                  <button
                    onClick={manejarFinalizarCierre}
                    disabled={finalizandoCierre}
                    className="flex items-center px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
                  >
                    {finalizandoCierre ? (
                      <>
                        <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                        Finalizando cierre...
                      </>
                    ) : (
                      <>
                        <CheckCircle className="w-5 h-5 mr-2" />
                        Finalizar Cierre
                      </>
                    )}
                  </button>
                )}
              </div>
            </div>

            {/* Mensaje de restricción si aplica */}
            {!puedeGenerarIncidencias() && (
              <div className="mt-4 p-3 bg-yellow-900/20 border border-yellow-500/30 rounded-lg">
                <div className="flex items-center gap-2 text-yellow-400 text-sm">
                  <AlertTriangle className="w-4 h-4" />
                  <span>
                    El cierre debe estar en estado "Datos Consolidados" o posteriores para generar incidencias
                  </span>
                </div>
              </div>
            )}
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

          {/* Análisis Completo Temporal */}
          {mostrandoAnalisisCompleto && analisisCompleto && (
            <div className="bg-blue-900/20 border border-blue-500/30 rounded-lg p-6">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl font-medium text-blue-400">
                  📊 Análisis Completo: Comparación Temporal
                </h3>
                <button
                  onClick={() => setMostrandoAnalisisCompleto(false)}
                  className="text-gray-400 hover:text-white text-xl"
                >
                  ×
                </button>
              </div>

              <div className="space-y-6">
                {/* Información del período */}
                <div className="bg-gray-800 rounded-lg p-4">
                  <h4 className="text-lg font-medium text-white mb-2">Períodos Comparados</h4>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                      <p className="text-sm text-gray-400">Cliente</p>
                      <p className="text-white font-medium">{analisisCompleto.cliente}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-400">Período Actual</p>
                      <p className="text-blue-400 font-medium">{analisisCompleto.periodo_actual}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-400">Período Anterior</p>
                      <p className="text-gray-300 font-medium">{analisisCompleto.periodo_anterior}</p>
                    </div>
                  </div>
                </div>

                {/* Resumen estadístico */}
                {analisisCompleto.resumen && (
                  <div className="bg-gray-800 rounded-lg p-4">
                    <h4 className="text-lg font-medium text-white mb-3">Resumen General</h4>
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                      <div className="text-center">
                        <div className="text-2xl font-bold text-white">
                          {analisisCompleto.resumen.total_comparaciones}
                        </div>
                        <p className="text-sm text-gray-400">Total Comparaciones</p>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-red-400">
                          {analisisCompleto.resumen.total_incidencias}
                        </div>
                        <p className="text-sm text-gray-400">Incidencias Detectadas</p>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-green-400">
                          {analisisCompleto.resumen.total_validaciones_ok}
                        </div>
                        <p className="text-sm text-gray-400">Validaciones OK</p>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-blue-400">
                          {analisisCompleto.resumen.porcentaje_cumplimiento}%
                        </div>
                        <p className="text-sm text-gray-400">% Cumplimiento</p>
                      </div>
                    </div>
                  </div>
                )}

                {/* REGLA 1: Variaciones de Conceptos */}
                {analisisCompleto.variaciones_conceptos && (
                  <div className="bg-gray-800 rounded-lg p-4">
                    <h4 className="text-lg font-medium text-white mb-3">
                      📈 Regla 1: Variaciones de Conceptos (Todas)
                    </h4>
                    <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-4">
                      <div className="text-center">
                        <div className="text-xl font-bold text-white">
                          {analisisCompleto.variaciones_conceptos.total_comparaciones}
                        </div>
                        <p className="text-xs text-gray-400">Total</p>
                      </div>
                      <div className="text-center">
                        <div className="text-xl font-bold text-red-400">
                          {analisisCompleto.variaciones_conceptos.incidencias_detectadas}
                        </div>
                        <p className="text-xs text-gray-400">Incidencias (≥30%)</p>
                      </div>
                      <div className="text-center">
                        <div className="text-xl font-bold text-yellow-400">
                          {analisisCompleto.variaciones_conceptos.variaciones_menores}
                        </div>
                        <p className="text-xs text-gray-400">Var. Menores (&lt;30%)</p>
                      </div>
                      <div className="text-center">
                        <div className="text-xl font-bold text-green-400">
                          {analisisCompleto.variaciones_conceptos.sin_cambios}
                        </div>
                        <p className="text-xs text-gray-400">Sin Cambios</p>
                      </div>
                      <div className="text-center">
                        <div className="text-xl font-bold text-blue-400">
                          {analisisCompleto.variaciones_conceptos.con_variacion}
                        </div>
                        <p className="text-xs text-gray-400">Con Variación</p>
                      </div>
                    </div>

                    {/* Tabla de variaciones más importantes */}
                    {analisisCompleto.variaciones_conceptos.detalle && 
                     analisisCompleto.variaciones_conceptos.detalle.length > 0 && (
                      <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                          <thead>
                            <tr className="border-b border-gray-700">
                              <th className="text-left p-2 text-gray-400">Empleado</th>
                              <th className="text-left p-2 text-gray-400">Concepto</th>
                              <th className="text-right p-2 text-gray-400">Actual</th>
                              <th className="text-right p-2 text-gray-400">Anterior</th>
                              <th className="text-right p-2 text-gray-400">Variación %</th>
                              <th className="text-center p-2 text-gray-400">Estado</th>
                            </tr>
                          </thead>
                          <tbody>
                            {analisisCompleto.variaciones_conceptos.detalle.slice(0, 10).map((item, index) => (
                              <tr key={index} className="border-b border-gray-700/50">
                                <td className="p-2 text-white">
                                  <div>
                                    <p className="font-medium">{item.nombre_empleado}</p>
                                    <p className="text-xs text-gray-400">{item.rut_empleado}</p>
                                  </div>
                                </td>
                                <td className="p-2 text-gray-300">{item.concepto}</td>
                                <td className="p-2 text-right text-white">
                                  ${item.monto_actual.toLocaleString('es-CL')}
                                </td>
                                <td className="p-2 text-right text-gray-300">
                                  ${item.monto_anterior.toLocaleString('es-CL')}
                                </td>
                                <td className={`p-2 text-right font-medium ${
                                  item.es_incidencia ? 'text-red-400' : 
                                  Math.abs(item.variacion_pct) > 0.01 ? 'text-yellow-400' : 'text-green-400'
                                }`}>
                                  {item.variacion_pct.toFixed(1)}%
                                </td>
                                <td className="p-2 text-center">
                                  <span className={`px-2 py-1 rounded text-xs ${
                                    item.es_incidencia ? 'bg-red-900 text-red-200' :
                                    Math.abs(item.variacion_pct) > 0.01 ? 'bg-yellow-900 text-yellow-200' :
                                    'bg-green-900 text-green-200'
                                  }`}>
                                    {item.estado}
                                  </span>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                        {analisisCompleto.variaciones_conceptos.detalle.length > 10 && (
                          <p className="text-center text-gray-400 text-sm mt-2">
                            ... y {analisisCompleto.variaciones_conceptos.detalle.length - 10} más
                          </p>
                        )}
                      </div>
                    )}
                  </div>
                )}

                {/* REGLA 3: Ingresos del Mes Anterior */}
                {analisisCompleto.ingresos_mes_anterior && (
                  <div className="bg-gray-800 rounded-lg p-4">
                    <h4 className="text-lg font-medium text-white mb-3">
                      👤 Regla 3: Ingresos del Mes Anterior
                    </h4>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                      <div className="text-center">
                        <div className="text-xl font-bold text-white">
                          {analisisCompleto.ingresos_mes_anterior.total_ingresos_anteriores}
                        </div>
                        <p className="text-xs text-gray-400">Total Ingresos</p>
                      </div>
                      <div className="text-center">
                        <div className="text-xl font-bold text-green-400">
                          {analisisCompleto.ingresos_mes_anterior.estan_presentes}
                        </div>
                        <p className="text-xs text-gray-400">Presentes</p>
                      </div>
                      <div className="text-center">
                        <div className="text-xl font-bold text-red-400">
                          {analisisCompleto.ingresos_mes_anterior.no_estan_presentes}
                        </div>
                        <p className="text-xs text-gray-400">Ausentes</p>
                      </div>
                      <div className="text-center">
                        <div className="text-xl font-bold text-red-400">
                          {analisisCompleto.ingresos_mes_anterior.incidencias_detectadas}
                        </div>
                        <p className="text-xs text-gray-400">Incidencias</p>
                      </div>
                    </div>

                    {/* Lista de ingresos */}
                    {analisisCompleto.ingresos_mes_anterior.detalle && 
                     analisisCompleto.ingresos_mes_anterior.detalle.length > 0 && (
                      <div className="space-y-2">
                        {analisisCompleto.ingresos_mes_anterior.detalle.map((item, index) => (
                          <div key={index} className={`p-3 rounded-lg ${
                            item.es_incidencia ? 'bg-red-900/20 border border-red-500/30' : 
                            'bg-green-900/20 border border-green-500/30'
                          }`}>
                            <div className="flex items-center justify-between">
                              <div>
                                <p className="font-medium text-white">{item.nombre_empleado}</p>
                                <p className="text-sm text-gray-400">{item.rut_empleado}</p>
                                <p className="text-xs text-gray-500">
                                  Ingreso detectado: {item.ingreso_detectado_en}
                                </p>
                              </div>
                              <span className={`px-3 py-1 rounded text-sm ${
                                item.es_incidencia ? 'bg-red-700 text-red-200' : 'bg-green-700 text-green-200'
                              }`}>
                                {item.estado}
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* REGLA 4: Finiquitos del Mes Anterior */}
                {analisisCompleto.finiquitos_mes_anterior && (
                  <div className="bg-gray-800 rounded-lg p-4">
                    <h4 className="text-lg font-medium text-white mb-3">
                      🚪 Regla 4: Finiquitos del Mes Anterior
                    </h4>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                      <div className="text-center">
                        <div className="text-xl font-bold text-white">
                          {analisisCompleto.finiquitos_mes_anterior.total_finiquitos_anteriores}
                        </div>
                        <p className="text-xs text-gray-400">Total Finiquitos</p>
                      </div>
                      <div className="text-center">
                        <div className="text-xl font-bold text-green-400">
                          {analisisCompleto.finiquitos_mes_anterior.correctamente_ausentes}
                        </div>
                        <p className="text-xs text-gray-400">Correctamente Ausentes</p>
                      </div>
                      <div className="text-center">
                        <div className="text-xl font-bold text-red-400">
                          {analisisCompleto.finiquitos_mes_anterior.aun_presentes}
                        </div>
                        <p className="text-xs text-gray-400">Aún Presentes</p>
                      </div>
                      <div className="text-center">
                        <div className="text-xl font-bold text-red-400">
                          {analisisCompleto.finiquitos_mes_anterior.incidencias_detectadas}
                        </div>
                        <p className="text-xs text-gray-400">Incidencias</p>
                      </div>
                    </div>

                    {/* Lista de finiquitos */}
                    {analisisCompleto.finiquitos_mes_anterior.detalle && 
                     analisisCompleto.finiquitos_mes_anterior.detalle.length > 0 && (
                      <div className="space-y-2">
                        {analisisCompleto.finiquitos_mes_anterior.detalle.map((item, index) => (
                          <div key={index} className={`p-3 rounded-lg ${
                            item.es_incidencia ? 'bg-red-900/20 border border-red-500/30' : 
                            'bg-green-900/20 border border-green-500/30'
                          }`}>
                            <div className="flex items-center justify-between">
                              <div>
                                <p className="font-medium text-white">{item.nombre_empleado}</p>
                                <p className="text-sm text-gray-400">{item.rut_empleado}</p>
                                <p className="text-xs text-gray-500">
                                  Finiquito detectado: {item.finiquito_detectado_en}
                                </p>
                              </div>
                              <span className={`px-3 py-1 rounded text-sm ${
                                item.es_incidencia ? 'bg-red-700 text-red-200' : 'bg-green-700 text-green-200'
                              }`}>
                                {item.estado}
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* Mensaje si no hay período anterior */}
                {!analisisCompleto.tiene_periodo_anterior && (
                  <div className="bg-yellow-900/20 border border-yellow-500/30 rounded-lg p-4">
                    <div className="flex items-start gap-3">
                      <AlertTriangle className="w-5 h-5 text-yellow-400 mt-0.5" />
                      <div>
                        <p className="text-yellow-300 font-medium mb-2">Sin Período Anterior para Comparación</p>
                        <p className="text-yellow-200 text-sm mb-3">{analisisCompleto.mensaje}</p>
                        
                        {/* Información adicional si se encontró un período pero no es válido */}
                        {analisisCompleto.periodo_anterior_encontrado && (
                          <div className="bg-yellow-800/30 rounded p-3 text-sm">
                            <p className="text-yellow-100">
                              <strong>Período encontrado:</strong> {analisisCompleto.periodo_anterior_encontrado}
                            </p>
                            <p className="text-yellow-100">
                              <strong>Estado actual:</strong> {analisisCompleto.estado_periodo_anterior}
                            </p>
                            <p className="text-yellow-200 mt-2">
                              💡 <strong>Solución:</strong> Para realizar el análisis temporal, el período anterior debe estar
                              <code className="bg-yellow-700/50 px-1 rounded ml-1">finalizado</code>.
                              Este es un comparativo directo solo con cierres anteriores finalizados.
                            </p>
                          </div>
                        )}

                        {/* Botón para mostrar información del período actual */}
                        <div className="mt-4">
                          <p className="text-yellow-200 text-sm">
                            📊 <strong>Alternativa:</strong> Puedes generar incidencias normalmente para revisar la consistencia interna de los datos del período actual.
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
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
                        {(estadoIncidencias?.estados?.pendiente || 0) + (estadoIncidencias?.estados?.resuelta_analista || 0)}
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
                        {formatearMonedaChilena(resumen.impacto_monetario_total || 0)}
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
                        Las incidencias comparan datos actuales vs históricos. Para resolverlas:
                      </p>
                      <ol className="mt-2 space-y-1 list-decimal list-inside">
                        <li><strong>Revisar incidencias:</strong> Examina las diferencias temporales detectadas en la tabla inferior.</li>
                        <li><strong>Opción A - Marcar como resueltas:</strong> Si las diferencias son esperadas o correctas, marca las incidencias como resueltas.</li>
                        <li><strong>Opción B - Corregir datos actuales:</strong> Si hay errores en los datos del mes actual:</li>
                        <ul className="ml-6 mt-1 space-y-1 list-disc list-inside text-xs">
                          <li>Usa "Resubir archivo" en las tarjetas de <strong>Talana</strong> (Libro de Remuneraciones, MovimientosMes)</li>
                          <li>Sube los archivos de Talana corregidos</li>
                          <li>Regresa aquí y presiona "Generar Incidencias" nuevamente</li>
                          <li>Repite hasta resolver todas las inconsistencias temporales</li>
                        </ul>
                      </ol>
                    </div>
                  </div>
                </div>
              )}
            </>
          )}

          {/* Filtros */}
          {estadoIncidencias?.total_incidencias > 0 && (
            <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
              <div className="flex items-center gap-4 flex-wrap">
                <div className="flex items-center gap-2">
                  <Filter className="w-4 h-4 text-gray-400" />
                  <span className="text-sm text-gray-400">Filtros:</span>
                </div>

                <select
                  value={filtros.tipo_comparacion || ''}
                  onChange={(e) => manejarFiltroChange({ tipo_comparacion: e.target.value })}
                  className="bg-gray-700 border border-gray-600 rounded px-3 py-1 text-sm text-white"
                >
                  <option value="">Todos los análisis</option>
                  <option value="individual">Individual</option>
                  <option value="suma_total">Suma Total</option>
                  <option value="legacy">Legacy</option>
                </select>
                
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
          {estadoIncidencias?.total_incidencias > 0 ? (
            <div className="bg-gray-800 rounded-lg border border-gray-700">
              <div className="p-4 border-b border-gray-700">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-medium text-white">
                    Lista de Incidencias
                  </h3>
                  <div className="flex items-center gap-2 text-sm text-gray-400">
                    <span>Análisis temporal - Corrección vía resubida de archivos Talana si necesario</span>
                  </div>
                </div>
              </div>
              <div className="p-4">
                <IncidenciasTable
                  cierreId={cierre?.id}
                  cierre={cierre}
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
                Los archivos están perfectamente sincronizados o aún no se han generado las incidencias
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

export default IncidenciasEncontradasSection;
