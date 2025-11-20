import { useState, useEffect, useCallback, useRef } from "react";
import { Users, ChevronDown, ChevronRight, Lock } from "lucide-react";
import IngresosCard from "../IngresosCard";
import FiniquitosCard from "../FiniquitosCard";
import AusentismosCard from "../AusentismosCard";
import NovedadesCard from "../NovedadesCard";
import ModalClasificacionHeaders from "../../ModalClasificacionHeaders";
import {
  // 🎯 APIs para archivos del analista
  obtenerEstadoIngresos,
  subirIngresos,
  eliminarIngresos,
  obtenerEstadoFiniquitos,
  subirFiniquitos,
  eliminarFiniquitos,
  obtenerEstadoAusentismos,
  subirAusentismos,
  eliminarAusentismos,
  obtenerEstadoArchivoNovedades,
  subirArchivoNovedades,
  eliminarArchivoNovedades,
  procesarFinalNovedades,
  // 🎯 APIs para clasificaciones
  guardarConceptosRemuneracion,
  eliminarConceptoRemuneracion,
} from "../../api/cierreDetalle.api";

const ArchivosAnalistaSection_v2 = ({
  // 🎯 Props mínimas - Diseño autónomo
  cierreId,                    // ID del cierre
  cliente,                     // Datos del cliente (necesario para clasificaciones)
  disabled = false,            // Si está bloqueada la sección
  onEstadoChange,             // Callback para reportar cambios de estado al padre
  expandido = true,           // Control de acordeón
  onToggleExpansion,          // Handler de acordeón
}) => {
  // 🎯 Estados internos - La sección maneja todo su estado
  // Estados para Ingresos
  const [ingresos, setIngresos] = useState(null);
  const [subiendoIngresos, setSubiendoIngresos] = useState(false);
  
  // Estados para Finiquitos
  const [finiquitos, setFiniquitos] = useState(null);
  const [subiendoFiniquitos, setSubiendoFiniquitos] = useState(false);
  
  // Estados para Ausentismos
  const [ausentismos, setAusentismos] = useState(null);
  const [subiendoAusentismos, setSubiendoAusentismos] = useState(false);
  
  // Estados para Novedades
  const [novedades, setNovedades] = useState(null);
  const [novedadesId, setNovedadesId] = useState(null);
  const [subiendoNovedades, setSubiendoNovedades] = useState(false);
  const [novedadesListo, setNovedadesListo] = useState(false);
  const [mensajeNovedades, setMensajeNovedades] = useState("");
  
  // Estados para modal de clasificación de novedades
  const [modalAbierto, setModalAbierto] = useState(false);
  const [modoSoloLectura, setModoSoloLectura] = useState(false);
  
  // Control de polling
  const isMountedRef = useRef(true);

  // 🎯 Efecto de inicialización - Cargar datos al montar
  useEffect(() => {
    if (!cierreId) return;
    
    const cargarDatosIniciales = async () => {
      try {
        console.log('🔄 Cargando datos iniciales para Archivos del Analista...');
        
        // Cargar todos los archivos en paralelo
        const [ingresosData, finiquitosData, ausentismosData, novedadesData] = await Promise.all([
          obtenerEstadoIngresos(cierreId),
          obtenerEstadoFiniquitos(cierreId),
          obtenerEstadoAusentismos(cierreId),
          obtenerEstadoArchivoNovedades(cierreId)
        ]);
        
        if (isMountedRef.current) {
          setIngresos(ingresosData);
          setFiniquitos(finiquitosData);
          setAusentismos(ausentismosData);
          setNovedades(novedadesData);
          if (novedadesData?.id) {
            setNovedadesId(novedadesData.id);
          }
        }
      } catch (error) {
        console.error('❌ Error cargando datos de Archivos del Analista:', error);
      }
    };

    cargarDatosIniciales();
  }, [cierreId]);

  // 🎯 Detectar cuando novedades está listo para procesar
  useEffect(() => {
    const sinClasificar = Array.isArray(novedades?.header_json?.headers_sin_clasificar)
      ? novedades.header_json.headers_sin_clasificar.length === 0
      : false;
    const enProceso = novedades?.estado === "procesando" || novedades?.estado === "procesado";

    if (sinClasificar && !enProceso && !novedadesListo) {
      setNovedadesListo(true);
    } else if ((!sinClasificar || enProceso) && novedadesListo) {
      setNovedadesListo(false);
    }
  }, [novedades, novedadesListo]);

  // 🎯 Reportar cambios de estado al componente padre
  useEffect(() => {
    if (!onEstadoChange) return;

    const estadoIngresos = ingresos?.estado || "pendiente";
    const estadoFiniquitos = finiquitos?.estado || "pendiente";
    const estadoAusentismos = ausentismos?.estado || "pendiente";
    const estadoNovedades = novedades?.estado === "procesando" || novedades?.estado === "procesado"
      ? novedades?.estado
      : novedadesListo
      ? "clasificado"
      : novedades?.estado || "pendiente";
    
    // Determinar estado general de la sección
    const todosProcessed = [estadoIngresos, estadoFiniquitos, estadoAusentismos, estadoNovedades]
      .every(estado => estado === "procesado");
    
    const estadoGeneral = todosProcessed ? "procesado" : "pendiente";
    
    onEstadoChange(estadoGeneral);
  }, [ingresos, finiquitos, ausentismos, novedades, novedadesListo, onEstadoChange]);
  
  // Cleanup al desmontar
  useEffect(() => {
    return () => {
      isMountedRef.current = false;
    };
  }, []);
  
  // 🎯 Estados calculados para renderizado
  const estadoIngresos = ingresos?.estado || "no_subido";
  const estadoFiniquitos = finiquitos?.estado || "no_subido";
  const estadoAusentismos = ausentismos?.estado || "no_subido";
  
  const estadoNovedades = novedades?.estado === "procesando" || novedades?.estado === "procesado"
    ? novedades?.estado
    : novedadesListo
    ? "clasificado"
    : novedades?.estado || "no_subido";
  
  // Determinar el estado general: Procesado si TODOS están procesados, Pendiente en cualquier otro caso
  const todosArchivosProcessed = [estadoIngresos, estadoFiniquitos, estadoAusentismos, estadoNovedades]
    .every(estado => estado === "procesado");
  
  const estadoGeneral = todosArchivosProcessed ? "Procesado" : "Pendiente";
  const colorEstado = estadoGeneral === "Procesado" ? "text-green-400" : "text-yellow-400";

  // Headers sin clasificar para novedades
  const headersSinClasificarNovedades = Array.isArray(novedades?.header_json?.headers_sin_clasificar)
    ? novedades.header_json.headers_sin_clasificar
    : [];

  // 🎯 Handlers para Ingresos
  const handleSubirIngresos = useCallback(async (archivo) => {
    if (!cierreId) return;
    
    setSubiendoIngresos(true);
    try {
      const formData = new FormData();
      formData.append("archivo", archivo);
      await subirIngresos(cierreId, formData);
      
      setTimeout(async () => {
        if (isMountedRef.current) {
          const nuevoEstado = await obtenerEstadoIngresos(cierreId);
          setIngresos(nuevoEstado);
        }
      }, 1000);
    } catch (error) {
      console.error('❌ Error subiendo ingresos:', error);
    } finally {
      setSubiendoIngresos(false);
    }
  }, [cierreId]);

  const handleActualizarEstadoIngresos = useCallback(async () => {
    if (!cierreId || !isMountedRef.current) return;
    
    try {
      const estado = await obtenerEstadoIngresos(cierreId);
      if (isMountedRef.current) {
        setIngresos(estado);
      }
    } catch (error) {
      console.error("❌ Error actualizando ingresos:", error);
    }
  }, [cierreId]);

  const handleEliminarIngresos = useCallback(async () => {
    if (!ingresos?.id) return;
    
    try {
      await eliminarIngresos(ingresos.id);
      setIngresos(null);
    } catch (error) {
      console.error("❌ Error eliminando ingresos:", error);
    }
  }, [ingresos?.id]);

  // 🎯 Handlers para Finiquitos
  const handleSubirFiniquitos = useCallback(async (archivo) => {
    if (!cierreId) return;
    
    setSubiendoFiniquitos(true);
    try {
      const formData = new FormData();
      formData.append("archivo", archivo);
      await subirFiniquitos(cierreId, formData);
      
      setTimeout(async () => {
        if (isMountedRef.current) {
          const nuevoEstado = await obtenerEstadoFiniquitos(cierreId);
          setFiniquitos(nuevoEstado);
        }
      }, 1000);
    } catch (error) {
      console.error('❌ Error subiendo finiquitos:', error);
    } finally {
      setSubiendoFiniquitos(false);
    }
  }, [cierreId]);

  const handleActualizarEstadoFiniquitos = useCallback(async () => {
    if (!cierreId || !isMountedRef.current) return;
    
    try {
      const estado = await obtenerEstadoFiniquitos(cierreId);
      if (isMountedRef.current) {
        setFiniquitos(estado);
      }
    } catch (error) {
      console.error("❌ Error actualizando finiquitos:", error);
    }
  }, [cierreId]);

  const handleEliminarFiniquitos = useCallback(async () => {
    if (!finiquitos?.id) return;
    
    try {
      await eliminarFiniquitos(finiquitos.id);
      setFiniquitos(null);
    } catch (error) {
      console.error("❌ Error eliminando finiquitos:", error);
    }
  }, [finiquitos?.id]);

  // 🎯 Handlers para Ausentismos
  const handleSubirAusentismos = useCallback(async (archivo) => {
    if (!cierreId) return;
    
    setSubiendoAusentismos(true);
    try {
      const formData = new FormData();
      formData.append("archivo", archivo);
      await subirAusentismos(cierreId, formData);
      
      setTimeout(async () => {
        if (isMountedRef.current) {
          const nuevoEstado = await obtenerEstadoAusentismos(cierreId);
          setAusentismos(nuevoEstado);
        }
      }, 1000);
    } catch (error) {
      console.error('❌ Error subiendo ausentismos:', error);
    } finally {
      setSubiendoAusentismos(false);
    }
  }, [cierreId]);

  const handleActualizarEstadoAusentismos = useCallback(async () => {
    if (!cierreId || !isMountedRef.current) return;
    
    try {
      const estado = await obtenerEstadoAusentismos(cierreId);
      if (isMountedRef.current) {
        setAusentismos(estado);
      }
    } catch (error) {
      console.error("❌ Error actualizando ausentismos:", error);
    }
  }, [cierreId]);

  const handleEliminarAusentismos = useCallback(async () => {
    if (!ausentismos?.id) return;
    
    try {
      await eliminarAusentismos(ausentismos.id);
      setAusentismos(null);
    } catch (error) {
      console.error("❌ Error eliminando ausentismos:", error);
    }
  }, [ausentismos?.id]);

  // 🎯 Handlers para Novedades
  const handleSubirNovedades = useCallback(async (archivo) => {
    if (!cierreId) return;
    
    setSubiendoNovedades(true);
    try {
      const res = await subirArchivoNovedades(cierreId, archivo);
      if (res?.id) {
        setNovedadesId(res.id);
      }
      
      setTimeout(async () => {
        if (isMountedRef.current) {
          const nuevoEstado = await obtenerEstadoArchivoNovedades(cierreId);
          setNovedades(nuevoEstado);
          if (nuevoEstado?.id) {
            setNovedadesId(nuevoEstado.id);
          }
        }
      }, 1000);
    } catch (error) {
      console.error('❌ Error subiendo novedades:', error);
    } finally {
      setSubiendoNovedades(false);
    }
  }, [cierreId]);

  const handleProcesarNovedades = useCallback(async () => {
    const id = novedades?.id || novedadesId;
    if (!id) return;
    
    try {
      setNovedades(prev => ({ ...prev, estado: "procesando" }));
      setNovedadesListo(false);
      
      await procesarFinalNovedades(id);
    } catch (error) {
      console.error("❌ Error al procesar novedades:", error);
      setMensajeNovedades("Error al procesar novedades");
      setNovedades(prev => ({ ...prev, estado: "con_error" }));
    }
  }, [novedades?.id, novedadesId]);

  const handleActualizarEstadoNovedades = useCallback(async () => {
    if (!cierreId || !isMountedRef.current) return;
    
    try {
      const estadoActual = await obtenerEstadoArchivoNovedades(cierreId);
      if (isMountedRef.current) {
        setNovedades(estadoActual);
        if (estadoActual?.id) {
          setNovedadesId(estadoActual.id);
        }
      }
    } catch (error) {
      console.error('❌ Error actualizando estado novedades:', error);
    }
  }, [cierreId]);

  const handleEliminarNovedades = useCallback(async () => {
    if (!novedades?.id) return;
    
    try {
      await eliminarArchivoNovedades(novedades.id);
      setNovedades(null);
      setNovedadesId(null);
      setNovedadesListo(false);
    } catch (error) {
      console.error("❌ Error eliminando novedades:", error);
    }
  }, [novedades?.id]);

  const handleVerClasificacionNovedades = useCallback((soloLectura = false) => {
    console.log('🎯 Abriendo modal de clasificación para novedades, modo solo lectura:', !!soloLectura);
    setModalAbierto(true);
    setModoSoloLectura(!!soloLectura);
  }, []);

  // 🎯 Handler para guardar clasificaciones de novedades
  const handleGuardarClasificaciones = useCallback(async ({ guardar, eliminar }) => {
    if (!cliente?.id || !cierreId) return;
    
    try {
      console.log('💾 Guardando clasificaciones de novedades:', { guardar, eliminar });
      
      // Primero eliminamos las clasificaciones que correspondan
      if (Array.isArray(eliminar) && eliminar.length > 0) {
        await Promise.all(
          eliminar.map((h) => eliminarConceptoRemuneracion(cliente.id, h))
        );
      }

      const tieneGuardar = guardar && Object.keys(guardar).length > 0;

      // Luego guardamos las nuevas clasificaciones
      if (tieneGuardar) {
        await guardarConceptosRemuneracion(cliente.id, guardar, cierreId);
      } else if (Array.isArray(eliminar) && eliminar.length > 0) {
        // Si sólo se eliminaron conceptos, indicamos al backend que recalcule
        await guardarConceptosRemuneracion(cliente.id, {}, cierreId);
      }

      // Refrescamos el estado de novedades
      const nuevoEstado = await obtenerEstadoArchivoNovedades(cierreId);
      if (isMountedRef.current) {
        setNovedades(nuevoEstado);
        if (nuevoEstado?.id) {
          setNovedadesId(nuevoEstado.id);
        }
      }
      
      console.log('✅ Clasificaciones de novedades guardadas exitosamente');
    } catch (error) {
      console.error("❌ Error al guardar clasificaciones de novedades:", error);
      setMensajeNovedades("Error al guardar clasificaciones");
    }
  }, [cliente?.id, cierreId]);

  return (
    <section className="w-full space-y-6">
      {/* Header de la sección - clicable (solo si no está disabled) */}
      <div 
        className={`flex items-center justify-between p-3 -m-3 rounded-lg transition-colors ${
          disabled 
            ? 'opacity-60 cursor-not-allowed' 
            : 'cursor-pointer hover:bg-gray-800/50'
        }`}
        onClick={() => !disabled && onToggleExpansion && onToggleExpansion()}
      >
        <div className="flex items-center gap-3">
          <div className={`flex items-center justify-center w-10 h-10 rounded-lg ${
            disabled ? 'bg-gray-600' : 'bg-purple-600'
          }`}>
            {disabled ? (
              <Lock size={20} className="text-white" />
            ) : (
              <Users size={20} className="text-white" />
            )}
          </div>
          <div>
            <h2 className={`text-xl font-semibold ${disabled ? 'text-gray-400' : 'text-white'}`}>
              Archivos del Analista V2
              {disabled && (
                <span className="ml-2 text-sm font-normal text-gray-500">
                  (Bloqueado)
                </span>
              )}
            </h2>
            <p className="text-gray-400 text-sm">
              {disabled 
                ? 'Sección bloqueada'
                : 'Archivos complementarios procesados por el analista (Autónomo)'
              }
            </p>
          </div>
        </div>
        
        <div className="flex items-center gap-3">
          {!expandido && !disabled && (
            <span className={`text-sm font-medium ${colorEstado}`}>
              {estadoGeneral}
            </span>
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
      
      {/* Grid de tarjetas - solo se muestra cuando está expandido y no disabled */}
      {expandido && !disabled && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Primera fila: Ingresos y Finiquitos */}
          <IngresosCard
            estado={estadoIngresos}
            archivoNombre={ingresos?.archivo ? ingresos.archivo.split('/').pop() : null}
            subiendo={subiendoIngresos}
            onSubirArchivo={handleSubirIngresos}
            onActualizarEstado={handleActualizarEstadoIngresos}
            onEliminarArchivo={handleEliminarIngresos}
            disabled={disabled}
            deberiaDetenerPolling={disabled}
            cierreId={cierreId}
            archivoId={ingresos?.id}
          />
          
          <FiniquitosCard
            estado={estadoFiniquitos}
            archivoNombre={finiquitos?.archivo ? finiquitos.archivo.split('/').pop() : null}
            subiendo={subiendoFiniquitos}
            onSubirArchivo={handleSubirFiniquitos}
            onActualizarEstado={handleActualizarEstadoFiniquitos}
            onEliminarArchivo={handleEliminarFiniquitos}
            disabled={disabled}
            deberiaDetenerPolling={disabled}
            cierreId={cierreId}
            archivoId={finiquitos?.id}
          />
          
          {/* Segunda fila: Ausentismos y Novedades */}
          <AusentismosCard
            estado={estadoAusentismos}
            archivoNombre={ausentismos?.archivo ? ausentismos.archivo.split('/').pop() : null}
            subiendo={subiendoAusentismos}
            onSubirArchivo={handleSubirAusentismos}
            onActualizarEstado={handleActualizarEstadoAusentismos}
            onEliminarArchivo={handleEliminarAusentismos}
            disabled={disabled}
            deberiaDetenerPolling={disabled}
            cierreId={cierreId}
            archivoId={ausentismos?.id}
          />
          
          <NovedadesCard
            estado={estadoNovedades}
            archivoNombre={novedades?.archivo_nombre}
            subiendo={subiendoNovedades}
            onSubirArchivo={handleSubirNovedades}
            onVerClasificacion={handleVerClasificacionNovedades}
            onProcesar={handleProcesarNovedades}
            onActualizarEstado={handleActualizarEstadoNovedades}
            onEliminarArchivo={handleEliminarNovedades}
            novedadesId={novedades?.id}
            cierreId={cierreId}
            headersSinClasificar={headersSinClasificarNovedades}
            headerClasificados={novedades?.header_json?.headers_clasificados || []}
            mensaje={mensajeNovedades}
            disabled={disabled || novedades?.estado === "procesando"}
            deberiaDetenerPolling={disabled}
          />
        </div>
      )}
      
      {/* 🎯 Modal de clasificación para novedades */}
      {modalAbierto && (
        <ModalClasificacionHeaders
          isOpen={modalAbierto}
          onClose={() => setModalAbierto(false)}
          clienteId={cliente?.id}
          headersSinClasificar={headersSinClasificarNovedades}
          onGuardarClasificaciones={handleGuardarClasificaciones}
          soloLectura={modoSoloLectura}
        />
      )}
    </section>
  );
};

export default ArchivosAnalistaSection_v2;
