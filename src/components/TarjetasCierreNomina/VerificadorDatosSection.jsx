import { useState, useEffect, useRef } from "react";
import { ShieldCheck, ChevronDown, ChevronRight, Loader2, CheckCircle, AlertTriangle, Filter, Eye, RefreshCw, X, Lock } from "lucide-react";
import DiscrepanciasTable from "./VerificadorDatos/DiscrepanciasTable";
import { 
  obtenerDiscrepanciasCierre, 
  obtenerResumenDiscrepancias, 
  generarDiscrepanciasCierre,
  obtenerEstadoDiscrepanciasCierre,
  previewDiscrepanciasCierre,
  limpiarDiscrepanciasCierre,
  actualizarEstadoCierreNomina,
  consolidarDatosTalana,
  consultarEstadoTarea
} from "../../api/nomina";

const VerificadorDatosSection = ({ cierre, disabled = false, onCierreActualizado }) => {
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
  const [actualizandoEstado, setActualizandoEstado] = useState(false);
  const [consolidando, setConsolidando] = useState(false);
  const [taskIdConsolidacion, setTaskIdConsolidacion] = useState(null);
  const [mostrarModalConsolidacion, setMostrarModalConsolidacion] = useState(false);
  const pollingRef = useRef(null);

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
      
      // 🎯 NUEVA LÓGICA: Auto-actualizar estado del cierre si 0 discrepancias
      if (estado && estado.total_discrepancias === 0 && estado.verificacion_completada) {
        await actualizarEstadoSinDiscrepancias();
      }
    } catch (err) {
      console.error("Error cargando estado de discrepancias:", err);
    }
  };

  // 🆕 NUEVA FUNCIÓN: Actualizar estado cuando no hay discrepancias
  const actualizarEstadoSinDiscrepancias = async () => {
    if (actualizandoEstado) return; // Evitar múltiples llamadas
    
    try {
      setActualizandoEstado(true);
      console.log(`🎯 Detectadas 0 discrepancias - Actualizando estado del cierre ${cierre.id}...`);
      const estadoActualizado = await actualizarEstadoCierreNomina(cierre.id);
      console.log(`✅ Estado actualizado:`, estadoActualizado);
      
      // Notificar al componente padre para que refresque el cierre
      if (onCierreActualizado) {
        await onCierreActualizado();
      }
      
      // Mostrar notificación al usuario
      setError(""); // Limpiar errores previos
      
    } catch (error) {
      console.error("Error actualizando estado del cierre:", error);
      setError("Error al actualizar automáticamente el estado del cierre");
    } finally {
      setActualizandoEstado(false);
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
      console.log('✅ [VerificadorDatos] Discrepancias generadas, refrescando estado del cierre...');
      
      // Refrescar el estado del cierre para mostrar el cambio automáticamente
      if (onCierreActualizado) {
        await onCierreActualizado();
      }
      
      // Esperar un momento para que se procese la tarea y luego cargar datos
      setTimeout(async () => {
        await cargarEstadoDiscrepancias();
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

  // 🆕 NUEVA FUNCIÓN: Consolidar datos de Talana
  const manejarConsolidarDatos = async () => {
    console.log('🚀 manejarConsolidarDatos iniciado para cierre:', cierre?.id);
    
    if (!cierre?.id) {
      console.error('❌ No hay cierre ID disponible');
      return;
    }
    
    setConsolidando(true);
    setError("");
    setTaskIdConsolidacion(null);
    
    try {
      console.log(`🎯 Iniciando consolidación de datos para cierre ${cierre.id}...`);
      const resultado = await consolidarDatosTalana(cierre.id);
      console.log('📋 Respuesta del servidor:', resultado);
      
      if (resultado.success && resultado.task_id) {
        console.log(`📋 Tarea de consolidación iniciada: ${resultado.task_id}`);
        setTaskIdConsolidacion(resultado.task_id);
        
        // Iniciar polling para verificar estado de la tarea
        iniciarPollingTarea(resultado.task_id);
        
      } else {
        throw new Error(resultado.error || "Error desconocido al iniciar consolidación");
      }
      
    } catch (error) {
      console.error("❌ Error consolidando datos:", error);
      setError("Error al consolidar datos de Talana");
      setConsolidando(false);
      setTaskIdConsolidacion(null);
    }
  };

  // 🔄 FUNCIÓN: Polling para verificar estado de tarea
  const iniciarPollingTarea = (taskId) => {
    const verificarEstado = async () => {
      try {
        const estadoTarea = await consultarEstadoTarea(cierre.id, taskId);
        console.log(`📊 Estado tarea ${taskId}:`, estadoTarea);
        
        if (estadoTarea.ready) {
          // Tarea terminó
          setConsolidando(false);
          setTaskIdConsolidacion(null);
          pollingRef.current = null;
          
          if (estadoTarea.success) {
            console.log(`✅ Consolidación completada:`, estadoTarea.result);
            
            // Refrescar el estado del cierre en el componente padre
            if (onCierreActualizado) {
              await onCierreActualizado();
            }
            
            // Mostrar mensaje de éxito
            setError(""); 
            setMostrarModalConsolidacion(false);
            
          } else {
            console.error("❌ Error en consolidación:", estadoTarea.error);
            setError(`Error en consolidación: ${estadoTarea.error}`);
          }
        } else {
          // Tarea aún en proceso, continuar polling
          pollingRef.current = setTimeout(verificarEstado, 2000); // Verificar cada 2 segundos
        }
        
      } catch (error) {
        console.error("Error verificando estado de tarea:", error);
        setError("Error verificando estado de consolidación");
        setConsolidando(false);
        setTaskIdConsolidacion(null);
        pollingRef.current = null;
      }
    };
    
    // Iniciar el polling
    pollingRef.current = setTimeout(verificarEstado, 1000); // Primera verificación en 1 segundo
  };

  // 🧹 LIMPIEZA: Cancelar polling al desmontar componente
  useEffect(() => {
    return () => {
      if (pollingRef.current) {
        clearTimeout(pollingRef.current);
      }
    };
  }, []);

  // 🔧 FUNCIÓN: Verificar si se puede consolidar
  const puedeConsolidarDatos = () => {
    console.log('🔍 Verificando si puede consolidar datos:', {
      estado: cierre?.estado,
      estadoDiscrepancias: estadoDiscrepancias,
      totalDiscrepancias: estadoDiscrepancias?.total_discrepancias,
      verificacionCompletada: estadoDiscrepancias?.verificacion_completada
    });
    
    const puede = cierre?.estado === 'verificado_sin_discrepancias' || 
           cierre?.estado === 'sin_discrepancias' ||
           cierre?.estado === 'datos_consolidados' || // ✅ Permitir re-consolidación
           (estadoDiscrepancias && estadoDiscrepancias.total_discrepancias === 0 && estadoDiscrepancias.verificacion_completada);
    
    console.log('✅ Resultado puedeConsolidarDatos:', puede);
    return puede;
  };

  const puedeGenerarDiscrepancias = () => {
    return cierre?.estado === 'archivos_completos' || 
           cierre?.estado === 'verificacion_datos' ||
           cierre?.estado === 'con_discrepancias';
  };

  const mostrarMensajeRestriccion = () => {
    // Solo mostrar el mensaje si el estado no permite generar discrepancias Y aún no se han generado
    const estadosQueNoPermiten = !puedeGenerarDiscrepancias();
    const estadosQueYaTienenDatos = cierre?.estado === 'con_discrepancias' || 
                                    cierre?.estado === 'verificado_sin_discrepancias' || 
                                    cierre?.estado === 'finalizado';
    
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
      {/* Header unificado - maneja tanto disabled como normal */}
      <div 
        className={`flex items-center justify-between p-3 -m-3 rounded-lg transition-colors ${
          disabled 
            ? 'opacity-60 cursor-not-allowed' 
            : 'cursor-pointer hover:bg-gray-800/50'
        }`}
        onClick={() => !disabled && setExpandido(!expandido)}
      >
        <div className="flex items-center gap-3">
          <div className={`flex items-center justify-center w-10 h-10 rounded-lg ${
            disabled ? 'bg-gray-600' : 'bg-orange-600'
          }`}>
            {disabled ? (
              <Lock size={20} className="text-white" />
            ) : (
              <ShieldCheck size={20} className="text-white" />
            )}
          </div>
          <div>
            <h2 className={`text-xl font-semibold ${disabled ? 'text-gray-400' : 'text-white'}`}>
              Verificación de Datos
              {disabled && (
                <span className="ml-2 text-sm font-normal text-gray-500">
                  (Bloqueado - Datos Consolidados)
                </span>
              )}
            </h2>
            <div className="flex items-center gap-2 text-sm">
              <p className="text-gray-400">
                {disabled 
                  ? 'La verificación está bloqueada porque los datos ya han sido consolidados'
                  : 'Verificación de consistencia entre Libro de Remuneraciones y Novedades'
                }
              </p>
              {!disabled && estadoDiscrepancias && (
                <span className={`${obtenerColorEstado()} font-medium`}>
                  • {estadoDiscrepancias.total_discrepancias || 0} discrepancias
                  {estadoDiscrepancias.total_discrepancias === 0 && estadoDiscrepancias.verificacion_completada && (
                    <span className="ml-2 text-green-300">✅ Verificación exitosa</span>
                  )}
                </span>
              )}
            </div>
          </div>
        </div>
        
        <div className="flex items-center gap-3">
          {!disabled && !expandido && estadoDiscrepancias && estadoDiscrepancias.total_discrepancias > 0 && (
            <div className="flex items-center gap-2 text-sm">
              <span className="text-white">
                {estadoDiscrepancias.total_discrepancias} discrepancias detectadas
              </span>
            </div>
          )}
          {disabled ? (
            <span className="text-sm font-medium text-gray-500">Bloqueado</span>
          ) : (
            expandido ? (
              <ChevronDown size={20} className="text-gray-400" />
            ) : (
              <ChevronRight size={20} className="text-gray-400" />
            )
          )}
        </div>
      </div>

      {/* Contenido condicional - solo se muestra cuando está expandido y no disabled */}
      {expandido && !disabled && (
        /* Contenido normal - Verificación completa */

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

                {/* 🆕 BOTÓN DE CONSOLIDAR DATOS */}
                {puedeConsolidarDatos() && (
                  <button
                    onClick={() => setMostrarModalConsolidacion(true)}
                    disabled={consolidando}
                    className="flex items-center px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
                  >
                    {consolidando ? (
                      <>
                        <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                        {taskIdConsolidacion ? 'Procesando datos...' : 'Iniciando...'}
                      </>
                    ) : (
                      <>
                        <CheckCircle className="w-5 h-5 mr-2" />
                        Consolidar Datos
                      </>
                    )}
                  </button>
                )}

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

            {/* Mensaje de éxito cuando hay 0 discrepancias */}
            {estadoDiscrepancias && estadoDiscrepancias.total_discrepancias === 0 && estadoDiscrepancias.verificacion_completada && (
              <div className="mt-4 p-4 bg-green-900/20 border border-green-500/30 rounded-lg">
                <div className="flex items-center gap-3">
                  <div className="flex-shrink-0">
                    {actualizandoEstado ? (
                      <Loader2 className="w-6 h-6 text-blue-400 animate-spin" />
                    ) : (
                      <CheckCircle className="w-6 h-6 text-green-400" />
                    )}
                  </div>
                  <div className="flex-1">
                    <h4 className="text-green-400 font-medium">
                      {actualizandoEstado ? "Actualizando estado..." : "¡Verificación Exitosa!"}
                    </h4>
                    <p className="text-sm text-gray-300 mt-1">
                      {actualizandoEstado ? (
                        "Actualizando automáticamente el estado del cierre..."
                      ) : (
                        "No se detectaron discrepancias entre el Libro de Remuneraciones y las Novedades. El sistema ha actualizado automáticamente el estado del cierre para activar el sistema de incidencias."
                      )}
                    </p>
                  </div>
                </div>
              </div>
            )}

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

      {/* 🆕 MODAL DE CONFIRMACIÓN PARA CONSOLIDACIÓN - MOVIDO FUERA DEL CONDICIONAL */}
      {mostrarModalConsolidacion && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          {console.log('🎭 Modal de consolidación renderizándose...')}
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4 shadow-lg">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Actualizar Consolidación</h3>
              <button
                onClick={() => setMostrarModalConsolidacion(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <div className="mb-6">
              <div className="flex items-center mb-3">
                <AlertTriangle className="w-6 h-6 text-amber-500 mr-2" />
                <p className="font-medium text-gray-900">¡Importante!</p>
              </div>
              <p className="text-gray-600 mb-3">
                Al actualizar la consolidación:
              </p>
              <ul className="text-sm text-gray-600 space-y-1 ml-4">
                <li>• <strong>Se eliminará</strong> toda la consolidación existente</li>
                <li>• <strong>Se regenerará</strong> desde cero con los datos actuales</li>
                <li>• El sistema procesará los datos únicamente de Talana</li>
                <li>• Incluirá cualquier archivo nuevo subido después de la consolidación anterior</li>
                <li>• El proceso no se puede deshacer una vez iniciado</li>
              </ul>
            </div>

            <div className="flex justify-end space-x-3">
              <button
                onClick={() => setMostrarModalConsolidacion(false)}
                className="px-4 py-2 text-gray-700 bg-gray-200 rounded-lg hover:bg-gray-300 transition-colors"
              >
                Cancelar
              </button>
              <button
                onClick={() => {
                  console.log('🔴 Click en botón Confirmar Actualización');
                  manejarConsolidarDatos();
                }}
                disabled={consolidando}
                className="flex items-center px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {consolidando ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Actualizando...
                  </>
                ) : (
                  <>
                    <CheckCircle className="w-4 h-4 mr-2" />
                    Confirmar Actualización
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
};

export default VerificadorDatosSection;
