import { useState, useEffect, useRef } from "react";
import { ShieldCheck, ChevronDown, ChevronRight, Loader2, CheckCircle, AlertTriangle, Filter, RefreshCw, X, Lock } from "lucide-react";
import DiscrepanciasTable from "./VerificadorDatos/DiscrepanciasTable";
import { 
  obtenerDiscrepanciasCierre, 
  obtenerResumenDiscrepancias, 
  generarDiscrepanciasCierre,
  obtenerEstadoDiscrepanciasCierre,
  limpiarDiscrepanciasCierre,
  actualizarEstadoCierreNomina,
  consolidarDatosTalana,
  consultarEstadoTarea,
  obtenerCierreNominaPorId
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
      const resultado = await generarDiscrepanciasCierre(cierre.id);
      console.log('✅ [VerificadorDatos] Respuesta completa del backend:', resultado);
      console.log('✅ [VerificadorDatos] Task ID recibido:', resultado.task_id);
      
      // Iniciar polling automático para seguir el progreso
      if (resultado.task_id) {
        console.log('🚀 [VerificadorDatos] Iniciando polling con task_id:', resultado.task_id);
        iniciarPollingEstado(resultado.task_id, 'verificacion');
      } else {
        console.error('❌ [VerificadorDatos] No se recibió task_id en la respuesta');
        // Fallback si no hay task_id
        setTimeout(async () => {
          await Promise.all([
            cargarEstadoDiscrepancias(),
            actualizarEstadoCierre()
          ]);
          setGenerando(false);
        }, 3000);
      }
      
    } catch (err) {
      console.error("Error generando discrepancias:", err);
      setError("Error al generar verificación de datos");
      setGenerando(false);
    }
  };

  const manejarLimpiarDiscrepancias = async () => {
    if (!cierre?.id || !window.confirm("¿Estás seguro de que quieres limpiar todas las discrepancias?\n\nEsta acción:\n• Eliminará todas las discrepancias detectadas\n• Revertirá el cierre al estado 'Archivos Completos'\n• Permitirá ejecutar una nueva verificación\n\nEsta acción no se puede deshacer.")) {
      return;
    }
    
    setCargando(true);
    setError("");
    
    try {
      console.log('🧹 Limpiando discrepancias y revirtiendo estado del cierre...');
      
      // Limpiar discrepancias
      await limpiarDiscrepanciasCierre(cierre.id);
      
      // Actualizar estado local
      setDiscrepancias([]);
      setResumen(null);
      setEstadoDiscrepancias(null);
      
      // 🆕 NUEVO: Actualizar estado del cierre automáticamente 
      console.log('🔄 Actualizando estado del cierre después de limpiar...');
      await Promise.all([
        cargarEstadoDiscrepancias(),
        actualizarEstadoCierre()
      ]);
      
      console.log('✅ Discrepancias limpiadas y estado revertido exitosamente');
      
      // Mostrar mensaje de éxito temporal
      setError(""); // Limpiar errores previos
      
    } catch (err) {
      console.error("Error limpiando discrepancias:", err);
      setError("Error al limpiar discrepancias");
    } finally {
      setCargando(false);
    }
  };

  // Función para actualizar estado del cierre automáticamente
  const actualizarEstadoCierre = async () => {
    try {
      const cierreActualizado = await obtenerCierreNominaPorId(cierre.id);
      if (onCierreActualizado) {
        onCierreActualizado(cierreActualizado);
      }
    } catch (error) {
      console.error("Error actualizando estado del cierre:", error);
    }
  };

  // Función para hacer polling del estado durante operaciones
  const iniciarPollingEstado = (taskId, tipoOperacion = 'verificacion') => {
    console.log('🔄 [PollingEstado] Iniciando polling para:', { taskId, tipoOperacion, cierreId: cierre?.id });
    
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
    }

    pollingRef.current = setInterval(async () => {
      try {
        // Consultar estado de la tarea
        console.log('🔍 [PollingEstado] Consultando estado de tarea:', taskId);
        const estadoTarea = await consultarEstadoTarea(cierre?.id, taskId);
        console.log('📊 [PollingEstado] Estado recibido:', estadoTarea);
        
        if (estadoTarea.status === 'SUCCESS') {
          console.log(`✅ ${tipoOperacion} completada exitosamente`);
          
          // Actualizar estados locales
          await Promise.all([
            cargarEstadoDiscrepancias(),
            actualizarEstadoCierre()
          ]);
          
          // Detener polling
          clearInterval(pollingRef.current);
          pollingRef.current = null;
          
          // Resetear estados de carga
          if (tipoOperacion === 'verificacion') {
            setGenerando(false);
          } else if (tipoOperacion === 'consolidacion') {
            setConsolidando(false);
            setTaskIdConsolidacion(null);
            setMostrarModalConsolidacion(false);
          }
          
        } else if (estadoTarea.status === 'FAILURE') {
          console.error(`❌ Error en ${tipoOperacion}:`, estadoTarea.result);
          setError(`Error en ${tipoOperacion}: ${estadoTarea.result?.error || 'Error desconocido'}`);
          
          // Detener polling y resetear estados
          clearInterval(pollingRef.current);
          pollingRef.current = null;
          setGenerando(false);
          setConsolidando(false);
          setTaskIdConsolidacion(null);
        }
        } catch (error) {
        console.error(`❌ [PollingEstado] Error consultando estado de ${tipoOperacion}:`, error);
        console.error('❌ [PollingEstado] Detalles del error:', { taskId, cierreId: cierre?.id, tipoOperacion });
      }
    }, 2000); // Consultar cada 2 segundos
  };  const manejarFiltroChange = (nuevosFiltros) => {
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
        iniciarPollingEstado(resultado.task_id, 'consolidacion');
        
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

  // 🧹 LIMPIEZA: Cancelar polling al desmontar componente
  useEffect(() => {
    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
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
    // Sin datos de verificación aún
    if (!estadoDiscrepancias) {
      if (cierre?.estado === 'creado' || cierre?.estado === 'archivos_pendientes') {
        return 'text-gray-500'; // Más tenue para estados iniciales
      } else if (cierre?.estado === 'archivos_completos') {
        return 'text-blue-400'; // Azul para "listo para verificar"
      } else if (cierre?.estado === 'verificacion_datos') {
        return 'text-yellow-400'; // Amarillo para "procesando"
      } else {
        return 'text-gray-400';
      }
    }
    
    // Con datos de verificación
    return estadoDiscrepancias.requiere_correccion ? 'text-red-400' : 'text-green-400';
  };

  const obtenerTextoEstado = () => {
    // Sin datos de verificación aún
    if (!estadoDiscrepancias) {
      // Determinar texto según el estado del cierre
      if (cierre?.estado === 'creado' || cierre?.estado === 'archivos_pendientes') {
        return 'No Disponible';
      } else if (cierre?.estado === 'archivos_completos') {
        return 'Listo para Verificar';
      } else if (cierre?.estado === 'verificacion_datos') {
        return 'Verificando...';
      } else {
        return 'Pendiente';
      }
    }
    
    // Con datos de verificación
    if (estadoDiscrepancias.requiere_correccion) {
      return 'Con Discrepancias';
    } else if (estadoDiscrepancias.total_discrepancias === 0 && estadoDiscrepancias.verificacion_completada) {
      return 'Verificado ✓';
    } else {
      return 'Verificado';
    }
  };

  const obtenerMensajeDescriptivo = () => {
    if (!estadoDiscrepancias) {
      // Mensajes según el estado del cierre cuando no hay verificación
      if (cierre?.estado === 'creado' || cierre?.estado === 'archivos_pendientes') {
        return 'Complete la carga de archivos para habilitar la verificación';
      } else if (cierre?.estado === 'archivos_completos') {
        return 'Todos los archivos cargados - Listo para verificar consistencia de datos';
      } else if (cierre?.estado === 'verificacion_datos') {
        return 'Procesando verificación de consistencia...';
      } else {
        return 'Verificación de consistencia entre Libro de Remuneraciones y Novedades';
      }
    } else {
      // Mensaje cuando ya hay datos de verificación
      return 'Verificación de consistencia entre Libro de Remuneraciones y Novedades';
    }
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
                  : obtenerMensajeDescriptivo()
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
                <div className="flex flex-col items-center justify-center min-w-[120px]">
                  <div className={`w-16 h-16 rounded-full flex items-center justify-center mb-3 shadow-lg ${
                    estadoDiscrepancias 
                      ? (estadoDiscrepancias.requiere_correccion ? 'bg-red-500/20 border-2 border-red-500' : 'bg-green-500/20 border-2 border-green-500')
                      : 'bg-gray-500/20 border-2 border-gray-500'
                  }`}>
                    <ShieldCheck size={24} className={obtenerColorEstado()} />
                  </div>
                  <p className="text-xs text-gray-400 mb-1">Estado</p>
                  <p className={`text-sm font-medium text-center ${obtenerColorEstado()}`}>
                    {obtenerTextoEstado()}
                  </p>
                </div>

                {/* Separador visual */}
                {estadoDiscrepancias && estadoDiscrepancias.total_discrepancias > 0 && (
                  <div className="w-px h-16 bg-gray-600"></div>
                )}

                {/* Contadores de discrepancias */}
                {estadoDiscrepancias && estadoDiscrepancias.total_discrepancias > 0 && (
                  <div className="flex items-center gap-6">
                    <div className="text-center">
                      <div className="text-3xl font-bold text-white mb-1">
                        {estadoDiscrepancias.total_discrepancias || 0}
                      </div>
                      <p className="text-xs text-gray-400">Total Discrepancias</p>
                    </div>
                    
                    <div className="text-center">
                      <div className="text-2xl font-bold text-blue-400 mb-1">
                        {resumen?.total_libro_vs_novedades || 0}
                      </div>
                      <p className="text-xs text-gray-400">Libro vs Novedades</p>
                    </div>
                    
                    <div className="text-center">
                      <div className="text-2xl font-bold text-purple-400 mb-1">
                        {resumen?.total_movimientos_vs_analista || 0}
                      </div>
                      <p className="text-xs text-gray-400">Movimientos vs Analista</p>
                    </div>
                  </div>
                )}
              </div>

              {/* Lado derecho - Botones de acción */}
              <div className="flex gap-3">
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
              
              <div className="bg-gray-800 rounded-lg p-4 border border-blue-700/50">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-400">Libro vs Novedades</p>
                    <p className="text-2xl font-bold text-blue-400">
                      {resumen.total_libro_vs_novedades || 0}
                    </p>
                  </div>
                  <div className="bg-blue-500/20 p-2 rounded-full">
                    <ShieldCheck className="w-6 h-6 text-blue-400" />
                  </div>
                </div>
                <p className="text-xs text-blue-300 mt-2">Comparación entre fuentes principales</p>
              </div>
              
              <div className="bg-gray-800 rounded-lg p-4 border border-purple-700/50">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-400">Movimientos vs Analista</p>
                    <p className="text-2xl font-bold text-purple-400">
                      {resumen.total_movimientos_vs_analista || 0}
                    </p>
                  </div>
                  <div className="bg-purple-500/20 p-2 rounded-full">
                    <CheckCircle className="w-6 h-6 text-purple-400" />
                  </div>
                </div>
                <p className="text-xs text-purple-300 mt-2">Validación con datos del analista</p>
              </div>
              
              <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-400">Empleados Afectados</p>
                    <p className="text-lg font-bold text-white">
                      {resumen.empleados_afectados || 0}
                    </p>
                  </div>
                  <span className="text-yellow-400 text-2xl">👥</span>
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
