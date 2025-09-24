import { useState, useEffect, useMemo, useRef } from "react";
import { AlertOctagon, ChevronDown, ChevronRight, Loader2, CheckCircle, AlertTriangle, Users, Eye, Lock, TrendingUp, RefreshCw } from "lucide-react";

// Vista unificada (solo incidencias)
import IncidenciasUnifiedTable from "./IncidenciasEncontradas/IncidenciasUnifiedTable";
import IncidenciasKPIs from "./IncidenciasEncontradas/IncidenciasKPIs";
import ModalResolucionIncidencia from "./IncidenciasEncontradas/ModalResolucionIncidencia";
import { 
  obtenerIncidenciasCierre, 
  obtenerResumenIncidencias, 
  obtenerEstadoIncidenciasCierre,
  finalizarCierre,
  consultarEstadoTarea,
  limpiarIncidenciasCierre,
  generarIncidenciasTotalesVariacion,
  obtenerEstadoCacheCierre,
  obtenerCierreMensual
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
  const [filtroCategoria, setFiltroCategoria] = useState(''); // Nuevo filtro por categoría
  const [incidenciaSeleccionada, setIncidenciaSeleccionada] = useState(null);
  const [modalAbierto, setModalAbierto] = useState(false);
  const [estadoIncidencias, setEstadoIncidencias] = useState(null);
  const [vistaPrevia, setVistaPrevia] = useState(null);
  // Guardar si el componente sigue montado para cortar polling en desmontaje
  const montadoRef = useRef(true);
  useEffect(() => {
    montadoRef.current = true;
    return () => {
      montadoRef.current = false;
    };
  }, []);
  
  // 🎯 CONFIGURACIÓN PABLO - SIN CHECKBOXES
  // Los conceptos están configurados automáticamente en el backend:
  // - Análisis detallado: haberes_imponibles, haberes_no_imponibles, otros_descuentos
  // - Solo resumen: descuentos_legales, aportes_patronales, informacion_adicional, impuestos, horas_extras
  
  const [mostrandoPreview, setMostrandoPreview] = useState(false);
  const [finalizandoCierre, setFinalizandoCierre] = useState(false);
  const [analisisCompleto, setAnalisisCompleto] = useState(null);
  const [mostrandoAnalisisCompleto, setMostrandoAnalisisCompleto] = useState(false);
  const [solicitandoRecarga, setSolicitandoRecarga] = useState(false);
  const { usuario } = useAuth();
  const esSupervisor = (usuario?.tipo_usuario === 'supervisor' || usuario?.tipo_usuario === 'gerente');

  // --- Helpers de período ---
  const getPeriodoAnterior = (periodo) => {
    // periodo esperado: 'YYYY-MM'
    if (!periodo || typeof periodo !== 'string' || !/^[0-9]{4}-[0-9]{2}$/.test(periodo)) return null;
    const [yStr, mStr] = periodo.split('-');
    let y = parseInt(yStr, 10);
    let m = parseInt(mStr, 10);
    m -= 1;
    if (m === 0) { m = 12; y -= 1; }
    const mm = String(m).padStart(2, '0');
    return `${y}-${mm}`;
  };

  // Diagnóstico: consulta explícita al estado de caché del cierre actual y el anterior
  const diagnosticarCache = async () => {
    try {
      if (!cierre?.id) return;
      console.log('🧠 [CACHE][DIAG] Consultando estado-cache (cierre actual):', cierre?.id, cierre?.periodo);
      const cacheActual = await obtenerEstadoCacheCierre(cierre.id);
      console.log('🧠 [CACHE][DIAG] Resultado cierre actual:', cacheActual);

      const periodoAnterior = getPeriodoAnterior(cierre?.periodo);
      if (periodoAnterior && cierre?.cliente) {
        console.log('🧠 [CACHE][DIAG] Buscando cierre anterior por período:', periodoAnterior, 'cliente:', cierre.cliente);
        const cierreAnterior = await obtenerCierreMensual(cierre.cliente, periodoAnterior);
        if (cierreAnterior?.id) {
          console.log('🧠 [CACHE][DIAG] Consultando estado-cache (cierre anterior):', cierreAnterior.id, cierreAnterior.periodo);
          const cacheAnterior = await obtenerEstadoCacheCierre(cierreAnterior.id);
          console.log('🧠 [CACHE][DIAG] Resultado cierre anterior:', cacheAnterior);
        } else {
          console.warn('🧠 [CACHE][DIAG] No se encontró cierre anterior en BD para', periodoAnterior);
        }
      } else {
        console.warn('🧠 [CACHE][DIAG] No se pudo determinar período/cliente para cierre anterior');
      }
    } catch (e) {
      console.warn('🧠 [CACHE][DIAG] Error consultando estado de cache:', e?.message || e);
    }
  };

  // Filtrado local por categoría
  const incidenciasFiltradas = useMemo(() => {
    if (!filtroCategoria) return incidencias;
    
    return Array.isArray(incidencias) ? incidencias.filter(incidencia => {
      const tipoConcepto = incidencia?.datos_adicionales?.tipo_concepto || incidencia?.tipo_concepto;
      return tipoConcepto === filtroCategoria;
    }) : [];
  }, [incidencias, filtroCategoria]);

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
      // Ejecutar diagnóstico de caché al iniciar
      diagnosticarCache();
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
      // Diagnóstico previo a generación
      await diagnosticarCache();
      console.log("🚀 Generando incidencias simplificadas (variación totales ±30%)...");
      const resultado = await generarIncidenciasTotalesVariacion(cierre.id);
      console.log("✅ Resultado generación variaciones:", resultado);
      // Actualización optimista inmediata usando respuesta
      if (resultado?.incidencias) {
        const adaptadas = resultado.incidencias.map((i, idx) => ({
          id: `temp-${idx}`,
          tipo_comparacion: 'suma_total',
          concepto_afectado: i.concepto,
          descripcion: `${i.tipo.toUpperCase()} ${i.concepto} Δ ${i.delta_pct?.toFixed ? i.delta_pct.toFixed(1) : i.delta_pct}%`,
          impacto_monetario: Math.abs(i.delta_abs || 0),
          datos_adicionales: {
            monto_actual: i.monto_actual,
            monto_anterior: i.monto_anterior,
            delta_abs: i.delta_abs,
            delta_pct: i.delta_pct,
            tipo_generado: i.tipo,
            umbral_pct: resultado?.parametros?.umbral_pct,
            informativo: false
          },
          estado: 'pendiente'
        }));
        setIncidencias(adaptadas);
      }
      // Refrescar estado de cierre / incidencias desde backend para IDs reales
      if (onCierreActualizado) {
        await onCierreActualizado();
      }
      await cargarEstadoIncidencias();
      await cargarDatos();
    } catch (err) {
      console.error("Error generando incidencias (variaciones):", err);
      setError("Error al generar incidencias de variaciones");
      alert("❌ Error generando incidencias de variaciones");
    } finally {
      setGenerando(false);
    }
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
        // Polling sin límite de tiempo mientras el componente esté montado
        const intervaloMs = 5000;
        // Bucle de espera hasta SUCCESS o FAILURE
        // Se corta automáticamente si el componente se desmonta
        while (montadoRef.current) {
          try {
            const estado = await consultarEstadoTarea(cierre.id, taskId);
            const state = estado?.state || estado?.status;

            if (state === 'SUCCESS') {
              if (onCierreActualizado) {
                await onCierreActualizado();
              }
              alert('🎉 Cierre finalizado correctamente.');
              break;
            }
            if (state === 'FAILURE') {
              const detalle = (estado?.result && (estado.result.detail || estado.result.message)) || estado?.error || '';
              const msg = `Error al finalizar cierre${detalle ? `: ${detalle}` : ''}`;
              setError(msg);
              alert(`❌ ${msg}`);
              break;
            }
          } catch (pollErr) {
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
        className={`flex items-center justify-between cursor-pointer hover:bg-gray-800/50 p-3 -m-3 rounded-lg transition-colores ${
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
                  className="flex items-center px-6 py-3 bg-orange-600 text-white rounded-lg hover:bg-orange-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colores font-medium"
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
                    className="flex items-center px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colores font-medium"
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

          

        

    

          {/* Tabla de incidencias: mostrar si hay incidencias cargadas (aunque total backend sea 0) */}
          {Array.isArray(incidencias) && incidencias.length > 0 ? (
            <div className="bg-gray-800 rounded-lg border border-gray-700">
              <div className="p-4 border-b border-gray-700">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-medium text-white">
                    Lista de Incidencias
                  </h3>
                  
                </div>
              </div>
              <div className="p-4 space-y-6">
                {/* Filtro por Categoría */}
                <div className="flex items-center gap-4 p-3 bg-gray-800/40 rounded-lg border border-gray-700/50">
                  <label className="text-sm font-medium text-gray-300">Filtrar por categoría:</label>
                  <select
                    value={filtroCategoria}
                    onChange={(e) => setFiltroCategoria(e.target.value)}
                    className="bg-gray-900/60 border border-gray-600 rounded-lg px-3 py-2 text-sm text-gray-200 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="">Todas las categorías</option>
                    {clasificacionesDisponibles.map(categoria => (
                      <option key={categoria} value={categoria}>
                        {nombresClasificaciones[categoria]}
                      </option>
                    ))}
                  </select>
                  {filtroCategoria && (
                    <button
                      onClick={() => setFiltroCategoria('')}
                      className="text-xs text-gray-400 hover:text-gray-200 underline"
                    >
                      Limpiar filtro
                    </button>
                  )}
                </div>

                {/* KPIs estilo 'LibroRemuneraciones' */}
                <IncidenciasKPIs incidencias={incidenciasFiltradas} />
                {/* Tabla unificada de incidencias (individual + suma_total por ítem) */}
                <IncidenciasUnifiedTable
                  incidencias={incidenciasFiltradas}
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
