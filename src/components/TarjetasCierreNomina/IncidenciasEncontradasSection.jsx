import { useState, useEffect } from "react";
import { AlertOctagon, ChevronDown, ChevronRight, Play, Loader2, CheckCircle, AlertTriangle, Users, Eye, Lock, TrendingUp, RefreshCw } from "lucide-react";
import { formatearMonedaChilena } from "../../utils/formatters";
import IncidenciasTable from "./IncidenciasEncontradas/IncidenciasTable";
// Vista unificada (solo incidencias)
import IncidenciasUnifiedTable from "./IncidenciasEncontradas/IncidenciasUnifiedTable";
import IncidenciasKPIs from "./IncidenciasEncontradas/IncidenciasKPIs";
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
// import { actualizarEstadoCierreNomina } from "../../api/nomina";
import { solicitarRecargaArchivosAnalista } from "../../api/nomina";
import { useAuth } from "../../hooks/useAuth";
import { obtenerEstadoReal, ESTADOS_INCIDENCIA } from "../../utils/incidenciaUtils";

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
  const [solicitandoRecarga, setSolicitandoRecarga] = useState(false);
  const { usuario } = useAuth();
  const esSupervisor = (usuario?.tipo_usuario === 'supervisor' || usuario?.tipo_usuario === 'gerente');

  // Fallback local para contadores (cuando el backend reporta 0 pero sí hay incidencias)
  const contadoresLocales = (() => {
    const inc = Array.isArray(incidencias) ? incidencias.filter(i => {
      const noInformativa = !(i?.datos_adicionales?.informativo === true);
      const tipoOk = i?.tipo_comparacion === 'individual' || i?.tipo_comparacion === 'suma_total';
      return noInformativa && tipoOk;
    }) : [];
    const total = inc.length;
    let aprobadas = 0;
    let rechazadas = 0;
    let pendientes = 0;
    for (const i of inc) {
      const { estado } = obtenerEstadoReal(i);
      if (estado === ESTADOS_INCIDENCIA.APROBADA_SUPERVISOR) aprobadas += 1;
      else if (estado === ESTADOS_INCIDENCIA.RECHAZADA_SUPERVISOR) rechazadas += 1;
      else pendientes += 1; // incluye pendiente, resuelta_analista y resolucion_supervisor_pendiente
    }
    return { total, aprobadas, rechazadas, pendientes };
  })();

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

  // Cargar datos de incidencias siempre que tengamos estado (aunque el total sea 0)
  useEffect(() => {
    console.log("🔍 [useEffect] Estado de incidencias cambió:", estadoIncidencias);
    console.log("🔍 [useEffect] Total incidencias del estado:", estadoIncidencias?.total_incidencias);
    if (estadoIncidencias) {
      console.log("🔍 [useEffect] Cargando datos de incidencias (incluye informativas si existen)");
      cargarDatos();
    }
  }, [estadoIncidencias]);

  // 🎯 Efecto para reportar el estado de la sección al componente padre
  useEffect(() => {
    if (estadoIncidencias && onEstadoChange) {
      // Determinar el estado: procesado si todas las incidencias están aprobadas por supervisor
      const total = estadoIncidencias.total_incidencias || 0;
      const aprobadas = estadoIncidencias?.progreso?.aprobadas || 0;
      const estadoFinal = (total > 0 && aprobadas === total) ? "procesado" : "pendiente";

      console.log('📊 [IncidenciasEncontradasSection] Reportando estado:', estadoFinal, {
        totalIncidencias: total,
        incidenciasAprobadas: aprobadas
      });

      onEstadoChange(estadoFinal);
    }
  }, [
    estadoIncidencias?.total_incidencias,
    estadoIncidencias?.progreso?.aprobadas,
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
      const resultado = await generarIncidenciasCierre(cierre.id);

      // Si el backend ejecuta en background, hacer polling hasta SUCCESS antes de refrescar
      const taskId = resultado?.task_id || resultado?.taskId || resultado?.task || resultado?.id;
      if (taskId) {
        console.log(`🚀 Generación de incidencias en background. Task: ${taskId}. Iniciando polling...`);
        const inicio = Date.now();
        const timeoutMs = 10 * 60 * 1000; // 10 minutos
        const intervaloMs = 2000;
        let exito = false;
        while (Date.now() - inicio < timeoutMs) {
          try {
            // eslint-disable-next-line no-await-in-loop
            const estado = await consultarEstadoTarea(cierre.id, taskId);
            const state = estado?.state || estado?.status;
            if (state === 'SUCCESS') {
              exito = true;
              break;
            }
            if (state === 'FAILURE') {
              console.error('❌ Error en generación de incidencias:', estado?.result);
              break;
            }
          } catch (pollErr) {
            // eslint-disable-next-line no-console
            console.warn('Polling estado tarea falló, reintentando...', pollErr?.message || pollErr);
          }
          // eslint-disable-next-line no-await-in-loop
          await new Promise((r) => setTimeout(r, intervaloMs));
        }
        if (!exito) {
          console.warn('⚠️ Polling de generación de incidencias terminó por timeout o error. Se continuará con refresco best-effort.');
        }
      }

      // Dar un pequeño margen y refrescar el cierre (el backend suele actualizar estado por su cuenta)
      if (onCierreActualizado) {
        await new Promise((r) => setTimeout(r, 700));
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
        // Intento adicional de refrescar el cierre tras los datos
        if (onCierreActualizado) {
          await onCierreActualizado();
        }
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

  const manejarSolicitarRecarga = async (e) => {
    // Evitar que el click colapse/expanda la sección
    if (e && typeof e.stopPropagation === 'function') e.stopPropagation();

    if (!cierre?.id) return;

    const motivo = prompt('Indique el motivo para recargar archivos (requerido):');
    if (!motivo || motivo.trim() === '') {
      alert('Debe proporcionar un motivo para la recarga');
      return;
    }

    if (!window.confirm('¿Confirma que desea solicitar la recarga de archivos? Esto permitirá resubir archivos corregidos desde Talana.')) {
      return;
    }

    setSolicitandoRecarga(true);
    try {
      const res = await solicitarRecargaArchivosAnalista(cierre.id, motivo.trim());
      // Refrescar estado del cierre en el padre
      if (onCierreActualizado) {
        await onCierreActualizado();
      }
      // Refrescar estado local de incidencias
      await cargarEstadoIncidencias();
      alert('✅ Solicitud registrada. Pendiente de aprobación del supervisor.');
    } catch (err) {
      const msg = err?.response?.data?.error || err?.message || 'Error solicitando recarga';
      setError(msg);
      alert(`❌ ${msg}`);
    } finally {
      setSolicitandoRecarga(false);
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
              {(estadoIncidencias?.total_incidencias != null || contadoresLocales.total > 0) && (
                <span className="text-gray-300">
                  • {(estadoIncidencias?.total_incidencias && estadoIncidencias.total_incidencias > 0) ? estadoIncidencias.total_incidencias : contadoresLocales.total} incidencias
                </span>
              )}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {(estadoIncidencias?.total_incidencias > 0 || contadoresLocales.total > 0) && (
            <div className="flex items-center gap-2 text-sm">
              <span className="text-gray-400">
                {(estadoIncidencias?.progreso?.pendientes && estadoIncidencias.progreso.pendientes > 0) ? estadoIncidencias.progreso.pendientes : contadoresLocales.pendientes} por aprobar
              </span>
              <span className="text-gray-400">•</span>
              <span className="text-green-400">
                {(estadoIncidencias?.progreso?.aprobadas && estadoIncidencias.progreso.aprobadas > 0) ? estadoIncidencias.progreso.aprobadas : contadoresLocales.aprobadas} aprobadas
              </span>
            </div>
          )}
          {/* Botón Solicitar Recarga (solo analista, y si no hay solicitud/recarga en curso) */}
          {!disabled && !esSupervisor && cierre?.estado !== 'recarga_solicitud_pendiente' && cierre?.estado !== 'requiere_recarga_archivos' && cierre?.estado !== 'finalizado' && (
            <div onClick={(e) => e.stopPropagation()}>
              <button
                onClick={manejarSolicitarRecarga}
                disabled={solicitandoRecarga}
                className="inline-flex items-center gap-2 px-3 py-2 bg-orange-600 hover:bg-orange-700 text-white text-sm rounded-md disabled:opacity-60 disabled:cursor-not-allowed"
                title="Solicitar recarga de archivos Talana"
              >
                {solicitandoRecarga ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    Solicitando...
                  </>
                ) : (
                  <>
                    <RefreshCw className="w-4 h-4" />
                    Solicitar Recarga
                  </>
                )}
              </button>
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
                {(estadoIncidencias?.total_incidencias > 0 || contadoresLocales.total > 0) && (
                  <>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-red-400">
                        {(estadoIncidencias?.progreso?.pendientes && estadoIncidencias.progreso.pendientes > 0) ? estadoIncidencias.progreso.pendientes : contadoresLocales.pendientes}
                      </div>
                      <p className="text-sm text-gray-400">Por aprobar</p>
                    </div>
                    
                    <div className="text-center">
                      <div className="text-2xl font-bold text-green-400">
                        {(estadoIncidencias?.progreso?.aprobadas && estadoIncidencias.progreso.aprobadas > 0) ? estadoIncidencias.progreso.aprobadas : contadoresLocales.aprobadas}
                      </div>
                      <p className="text-sm text-gray-400">Aprobadas</p>
                    </div>
                    
                    <div className="text-center">
                      <div className="text-2xl font-bold text-white">
                        {(estadoIncidencias?.total_incidencias && estadoIncidencias.total_incidencias > 0) ? estadoIncidencias.total_incidencias : contadoresLocales.total}
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

                {/* Botón Finalizar Cierre - Basado en puede_finalizar (backend) o estado local */}
                {(
                  estadoIncidencias?.puede_finalizar ||
                  cierre?.estado === 'incidencias_resueltas' ||
                  (cierre?.estado_incidencias === 'resueltas' && (estadoIncidencias?.total_incidencias === 0 || cierre?.total_incidencias === 0))
                ) && (
                  <button
                    onClick={manejarFinalizarCierre}
                    disabled={finalizandoCierre || (
                      !estadoIncidencias?.puede_finalizar && cierre?.estado !== 'incidencias_resueltas' && cierre?.estado_incidencias !== 'resueltas'
                    )}
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

          {/* Bloque informativo “¿Cómo resolver las incidencias?” eliminado por requerimiento */}

          {/* Bloque de filtros eliminado por requerimiento */}

          {/* Error */}
          {error && (
            <div className="bg-red-900/20 border border-red-500 rounded-lg p-4">
              <div className="flex items-center text-red-400">
                <AlertTriangle className="w-5 h-5 mr-2" />
                {error}
              </div>
            </div>
          )}

          {/* Tabla de incidencias: mostrar si hay incidencias cargadas (aunque total backend sea 0) */}
          {Array.isArray(incidencias) && incidencias.length > 0 ? (
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
              <div className="p-4 space-y-6">
                {/* KPIs estilo 'LibroRemuneraciones' */}
                <IncidenciasKPIs incidencias={incidencias} />
                {/* Tabla unificada de incidencias (individual + suma_total por ítem) */}
                <IncidenciasUnifiedTable
                  incidencias={incidencias}
                  onIncidenciaSeleccionada={manejarIncidenciaSeleccionada}
                  onAfterAction={() => {
                    // Refrescar estado y lista tras acciones individuales
                    cargarEstadoIncidencias();
                    cargarDatos();
                  }}
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
