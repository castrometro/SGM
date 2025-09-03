import { useState, useEffect, useRef } from "react";
import { ShieldCheck, Loader2, CheckCircle, AlertTriangle, RefreshCw, X } from "lucide-react";
import EstadoBadge from "../../../components/EstadoBadge";
import { 
  generarDiscrepanciasCierre,
  obtenerEstadoDiscrepanciasCierre,
  limpiarDiscrepanciasCierre,
  actualizarEstadoCierreNomina,
  consolidarDatosTalana,
  consultarEstadoTarea
} from "../../../api/nomina";

const VerificacionControl = ({ 
  cierre, 
  disabled = false, 
  onEstadoChange, 
  onCierreActualizado, 
  deberiaDetenerPolling = false,
  onEstadoDiscrepanciasChange, // Nuevo callback para pasar estadoDiscrepancias al padre
}) => {
  const [estadoDiscrepancias, setEstadoDiscrepancias] = useState(null);
  const [generando, setGenerando] = useState(false);
  const [actualizandoEstado, setActualizandoEstado] = useState(false);
  const [consolidando, setConsolidando] = useState(false);
  const [taskIdConsolidacion, setTaskIdConsolidacion] = useState(null);
  const [mostrarModalConsolidacion, setMostrarModalConsolidacion] = useState(false);
  const [error, setError] = useState("");
  const pollingRef = useRef(null);

  useEffect(() => {
    console.log('🎯 [VerificacionControl] useEffect inicial - cierre:', cierre?.id, 'estado:', cierre?.estado);
    
    if (cierre?.id) {
      // Solo cargar si el cierre está en un estado que indica que puede tener discrepancias
      if (cierre?.estado === 'con_discrepancias' || 
          cierre?.estado === 'verificado_sin_discrepancias' || 
          cierre?.estado === 'sin_discrepancias' ||
          cierre?.estado === 'datos_consolidados' ||
          cierre?.estado === 'verificacion_datos') {
        console.log('🔄 [VerificacionControl] Estado válido para cargar discrepancias, cargando...');
        cargarEstadoDiscrepancias();
      } else {
        console.log('⏭️ [VerificacionControl] Estado no requiere carga de discrepancias:', cierre?.estado);
      }
    } else {
      console.log('⚠️ [VerificacionControl] No hay ID de cierre disponible en useEffect inicial');
    }
  }, [cierre?.id, cierre?.estado]);

  // 🎯 Efecto para reportar el estado de la sección al componente padre
  useEffect(() => {
    if (onEstadoChange) {
      let estadoFinal;
      
      if (!estadoDiscrepancias) {
        // Sin verificación realizada aún
        estadoFinal = "pendiente";
      } else if (estadoDiscrepancias.total_discrepancias === 0 && estadoDiscrepancias.verificacion_completada) {
        // Verificación completada sin discrepancias
        estadoFinal = "procesado";
      } else {
        // Verificación con discrepancias o incompleta
        estadoFinal = "pendiente";
      }
      
      console.log('📊 [VerificacionControl] Reportando estado:', estadoFinal, {
        tieneEstadoDiscrepancias: !!estadoDiscrepancias,
        totalDiscrepancias: estadoDiscrepancias?.total_discrepancias,
        verificacionCompletada: estadoDiscrepancias?.verificacion_completada
      });
      
      onEstadoChange(estadoFinal);
    }
  }, [
    estadoDiscrepancias,
    onEstadoChange
  ]);

  // 🎯 Efecto para pasar estadoDiscrepancias al componente padre
  useEffect(() => {
    if (onEstadoDiscrepanciasChange) {
      onEstadoDiscrepanciasChange(estadoDiscrepancias);
    }
  }, [estadoDiscrepancias, onEstadoDiscrepanciasChange]);

  const cargarEstadoDiscrepancias = async () => {
    if (!cierre?.id) {
      console.log('❌ [cargarEstadoDiscrepancias] No hay ID de cierre disponible');
      return;
    }
    
    console.log('🔄 [cargarEstadoDiscrepancias] Iniciando carga para cierre:', cierre.id);
    
    try {
      const estado = await obtenerEstadoDiscrepanciasCierre(cierre.id);
      console.log('📊 [cargarEstadoDiscrepancias] Respuesta de API:', estado);
      
      // 🎯 VALIDAR que realmente haya datos de verificación
      if (estado && (estado.total_discrepancias > 0 || estado.verificacion_completada)) {
        console.log('✅ [cargarEstadoDiscrepancias] Estado de discrepancias válido:', estado);
        setEstadoDiscrepancias(estado);
        
        // 🎯 NUEVA LÓGICA: Auto-actualizar estado del cierre si 0 discrepancias
        if (estado.total_discrepancias === 0 && estado.verificacion_completada) {
          console.log('🎯 [cargarEstadoDiscrepancias] 0 discrepancias detectadas, actualizando estado...');
          await actualizarEstadoSinDiscrepancias();
        }
      } else {
        console.log('⚠️ [cargarEstadoDiscrepancias] No hay datos de verificación válidos, manteniendo estado null');
        setEstadoDiscrepancias(null);
      }
    } catch (err) {
      console.error("❌ [cargarEstadoDiscrepancias] Error:", err);
      // Si hay error, mantener estado null para indicar que no hay verificación
      setEstadoDiscrepancias(null);
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

  const manejarGenerarDiscrepancias = async () => {
    if (!cierre?.id) return;
    
    setGenerando(true);
    setError("");
    
    try {
      const resultado = await generarDiscrepanciasCierre(cierre.id);
      console.log('✅ [VerificacionControl] Respuesta completa del backend:', resultado);
      console.log('✅ [VerificacionControl] Task ID recibido:', resultado.task_id);
      
      // Iniciar polling automático para seguir el progreso
      if (resultado.task_id) {
        console.log('🚀 [VerificacionControl] Iniciando polling con task_id:', resultado.task_id);
        iniciarPollingEstado(resultado.task_id, 'verificacion');
      } else {
        console.error('❌ [VerificacionControl] No se recibió task_id en la respuesta');
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
    
    setError("");
    
    try {
      console.log('🧹 Limpiando discrepancias y revirtiendo estado del cierre...');
      
      // Limpiar discrepancias
      await limpiarDiscrepanciasCierre(cierre.id);
      
      // Actualizar estado local
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
    }
  };

  // Función para actualizar estado del cierre automáticamente
  const actualizarEstadoCierre = async () => {
    console.log('🔄 [actualizarEstadoCierre] Iniciando actualización...');
    
    try {
      console.log('🔄 [actualizarEstadoCierre] Actualizando estado del cierre...');
      
      // Refrescar el cierre completo desde la API
      if (onCierreActualizado) {
        console.log('🔄 [actualizarEstadoCierre] Llamando onCierreActualizado para refrescar desde API...');
        await onCierreActualizado();
        console.log('✅ [actualizarEstadoCierre] Estado del cierre actualizado exitosamente');
      } else {
        console.log('⚠️ [actualizarEstadoCierre] No hay callback onCierreActualizado disponible');
      }
    } catch (error) {
      console.error("❌ [actualizarEstadoCierre] Error actualizando estado del cierre:", error);
    }
  };

  // Función para hacer polling del estado durante operaciones
  const iniciarPollingEstado = (taskId, tipoOperacion = 'verificacion') => {
    console.log('🔄 [PollingEstado] Iniciando polling para:', { taskId, tipoOperacion, cierreId: cierre?.id, deberiaDetenerPolling });
    
    // No iniciar polling si se debe detener
    if (deberiaDetenerPolling) {
      console.log('🛑 [PollingEstado] No se inicia polling - señal global de parada');
      return;
    }
    
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
    }

    // 🔄 POLLING REACTIVADO - Similar a LibroRemuneracionesCard
    let contadorPolling = 0;
    let contadorErrores = 0;
    
    pollingRef.current = setInterval(async () => {
      contadorPolling++;
      
      // Verificar en cada iteración si se debe detener
      if (deberiaDetenerPolling) {
        console.log('🛑 [PollingEstado] Deteniendo polling - señal global de parada');
        clearInterval(pollingRef.current);
        pollingRef.current = null;
        return;
      }
      
      try {
        // Consultar estado de la tarea
        console.log(`🔍 [PollingEstado] Polling #${contadorPolling} - Consultando estado de tarea:`, taskId);
        const estadoTarea = await consultarEstadoTarea(cierre?.id, taskId);
        console.log('📊 [PollingEstado] Estado recibido:', estadoTarea);
        
        // Reset error counter on success
        contadorErrores = 0;
        
        if (estadoTarea.status === 'SUCCESS') {
          console.log(`✅ [PollingEstado] ${tipoOperacion} completada exitosamente`);
          
          // Actualizar estados locales y cierre
          console.log('🔄 [PollingEstado] Actualizando estados locales...');
          await Promise.all([
            cargarEstadoDiscrepancias(),
            actualizarEstadoCierre()
          ]);
          
          console.log('🔄 [PollingEstado] Estados actualizados, limpiando polling...');
          
          // Detener polling
          clearInterval(pollingRef.current);
          pollingRef.current = null;
          
          // Resetear estados de carga
          if (tipoOperacion === 'verificacion') {
            setGenerando(false);
            console.log('✅ [PollingEstado] Estado "generando" reseteado');
          } else if (tipoOperacion === 'consolidacion') {
            setConsolidando(false);
            setTaskIdConsolidacion(null);
            setMostrarModalConsolidacion(false);
            console.log('✅ [PollingEstado] Estados de consolidación reseteados');
          }
          
          console.log('🎉 [PollingEstado] Procesamiento completado exitosamente');
          
        } else if (estadoTarea.status === 'FAILURE') {
          console.error(`❌ Error en ${tipoOperacion}:`, estadoTarea.result);
          setError(`Error en ${tipoOperacion}: ${estadoTarea.result?.error || 'Error desconocido'}`);
          
          // Detener polling y resetear estados
          clearInterval(pollingRef.current);
          pollingRef.current = null;
          setGenerando(false);
          setConsolidando(false);
          setTaskIdConsolidacion(null);
          setMostrarModalConsolidacion(false);
        } else if (estadoTarea.status === 'PENDING') {
          console.log(`⏳ [PollingEstado] ${tipoOperacion} aún en progreso...`);
        }
      } catch (error) {
        contadorErrores++;
        console.error(`❌ [PollingEstado] Error en polling #${contadorPolling} (${contadorErrores}/3):`, error);
        console.error('❌ [PollingEstado] Detalles del error:', { taskId, cierreId: cierre?.id, tipoOperacion });
        
        // Si hay 3 errores consecutivos, parar el polling por seguridad
        if (contadorErrores >= 3) {
          console.log('🛑 [PollingEstado] Demasiados errores consecutivos, deteniendo polling por seguridad');
          clearInterval(pollingRef.current);
          pollingRef.current = null;
          setGenerando(false);
          setConsolidando(false);
          setTaskIdConsolidacion(null);
          setError('Error de comunicación - La verificación puede haber terminado. Refresca la página.');
        }
      }
    }, 3000); // 🎯 Cada 3 segundos (igual que LibroRemuneraciones)
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
        pollingRef.current = null;
      }
    };
  }, []);

  // 🔄 POLLING AUTOMÁTICO: Similar a LibroRemuneracionesCard
  useEffect(() => {
    console.log('🎯 [VerificacionControl] useEffect polling - estado cierre:', cierre?.estado, 'deberiaDetener:', deberiaDetenerPolling);
    console.log('🎯 [VerificacionControl] Cierre completo:', cierre);
    console.log('🎯 [VerificacionControl] Polling actual:', !!pollingRef.current);
    
    // Detener polling si se debe detener globalmente
    if (deberiaDetenerPolling && pollingRef.current) {
      console.log('🛑 [VerificacionControl] Deteniendo polling - señal global de parada');
      clearInterval(pollingRef.current);
      pollingRef.current = null;
      setGenerando(false);
      setConsolidando(false);
      return;
    }
    
    // 🚀 ESTADOS DEL CIERRE QUE REQUIEREN POLLING
    const estadosQueRequierenPolling = [
      "verificacion_datos",       // Cuando está verificando
      "con_discrepancias",       // Podría estar procesando correcciones
      "verificado_sin_discrepancias" // Podría estar finalizando verificación
    ];
    
    const deberiaHacerPolling = estadosQueRequierenPolling.includes(cierre?.estado);
    
    if (deberiaHacerPolling && !pollingRef.current && !deberiaDetenerPolling) {
      console.log(`🔄 [VerificacionControl] Iniciando polling automático para estado: "${cierre?.estado}"`);
      
      // Marcar como generando si está en verificación
      if (cierre?.estado === 'verificacion_datos') {
        setGenerando(true);
      }
      
      let contadorPolling = 0;
      let contadorErrores = 0;
      
      pollingRef.current = setInterval(async () => {
        contadorPolling++;
        
        // Verificar en cada iteración si se debe detener
        if (deberiaDetenerPolling) {
          console.log('🛑 [VerificacionControl] Deteniendo polling automático - señal global de parada');
          clearInterval(pollingRef.current);
          pollingRef.current = null;
          return;
        }
        
        try {
          console.log(`📡 [VerificacionControl] Polling automático #${contadorPolling} - Verificando estado...`);
          console.log(`📡 [VerificacionControl] Estado actual del cierre:`, cierre?.estado);
          console.log(`📡 [VerificacionControl] ID del cierre:`, cierre?.id);
          
          // Actualizar estado de discrepancias
          console.log(`📡 [VerificacionControl] Llamando cargarEstadoDiscrepancias...`);
          await cargarEstadoDiscrepancias();
          
          // Actualizar estado del cierre
          if (onCierreActualizado) {
            console.log(`📡 [VerificacionControl] Llamando onCierreActualizado...`);
            await onCierreActualizado();
            console.log(`📡 [VerificacionControl] onCierreActualizado completado`);
          } else {
            console.log(`⚠️ [VerificacionControl] No hay callback onCierreActualizado`);
          }
          
          // Reset error counter on success
          contadorErrores = 0;
          console.log(`✅ [VerificacionControl] Polling automático #${contadorPolling} completado exitosamente`);
          
        } catch (pollError) {
          contadorErrores++;
          console.error(`❌ [VerificacionControl] Error en polling automático #${contadorPolling} (${contadorErrores}/3):`, pollError);
          
          // Si hay 3 errores consecutivos, parar el polling por seguridad
          if (contadorErrores >= 3) {
            console.log('🛑 [VerificacionControl] Demasiados errores consecutivos, deteniendo polling automático');
            clearInterval(pollingRef.current);
            pollingRef.current = null;
            setGenerando(false);
            setError('Error de comunicación. Refresca la página.');
          }
        }
      }, 3000); // Cada 3 segundos para mejor UX
      
    } else if ((!deberiaHacerPolling || deberiaDetenerPolling) && pollingRef.current) {
      console.log(`✅ [VerificacionControl] Estado cambió a "${cierre?.estado}" o detención solicitada - deteniendo polling automático`);
      clearInterval(pollingRef.current);
      pollingRef.current = null;
      setGenerando(false);
      setConsolidando(false);
    }
  }, [cierre?.estado, deberiaDetenerPolling, onCierreActualizado]);

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

  const obtenerEstadoBadge = () => {
    // 🎯 LÓGICA SIMPLIFICADA: Solo se enfoca en el estado de la VERIFICACIÓN
    
    // Si el cierre está en estado "verificado_sin_discrepancias" -> Verificado exitosamente
    if (cierre?.estado === 'verificado_sin_discrepancias') {
      return 'verificado_sin_discrepancias';
    }
    
    // Si el cierre está en estado "con_discrepancias" -> Discrepancias detectadas
    if (cierre?.estado === 'con_discrepancias') {
      return 'con_discrepancias';
    }
    
    // En todos los demás casos -> Pendiente (no se ha verificado aún)
    return 'verificacion_pendiente';
  };

  return (
    <>
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
                <ShieldCheck size={24} className={`${
                  estadoDiscrepancias 
                    ? (estadoDiscrepancias.requiere_correccion ? 'text-red-400' : 'text-green-400')
                    : 'text-gray-400'
                }`} />
              </div>
              <p className="text-xs text-gray-400 mb-1">Estado</p>
              <EstadoBadge estado={obtenerEstadoBadge()} size="sm" />
            </div>

            {/* Separador visual */}
            {estadoDiscrepancias && estadoDiscrepancias.total_discrepancias > 0 && (
              <div className="w-px h-16 bg-gray-600"></div>
            )}

            {/* Contadores de discrepancias - Solo mostramos el total aquí */}
            {estadoDiscrepancias && estadoDiscrepancias.total_discrepancias > 0 && (
              <div className="flex items-center gap-6">
                <div className="text-center">
                  <div className="text-3xl font-bold text-white mb-1">
                    {estadoDiscrepancias.total_discrepancias || 0}
                  </div>
                  <p className="text-xs text-gray-400">Total Discrepancias</p>
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
                disabled={generando}
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

        {/* Error */}
        {error && (
          <div className="mt-4 bg-red-900/20 border border-red-500 rounded-lg p-4">
            <div className="flex items-center text-red-400">
              <AlertTriangle className="w-5 h-5 mr-2" />
              {error}
            </div>
          </div>
        )}
      </div>

      {/* 🆕 MODAL DE CONFIRMACIÓN PARA CONSOLIDACIÓN */}
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
    </>
  );
};

export default VerificacionControl;
