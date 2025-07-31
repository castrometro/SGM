import { useEffect, useState, useCallback, useRef } from "react";
import ArchivosTalanaSection from "./ArchivosTalanaSection";
import ArchivosAnalistaSection from "./ArchivosAnalistaSection";
import VerificadorDatosSection from "./VerificadorDatosSection";
import IncidenciasEncontradasSection from "./IncidenciasEncontradasSection";
import ResumenCierreSection from "./ResumenCierreSection";
import ModalClasificacionHeaders from "../ModalClasificacionHeaders";
import {
  obtenerEstadoLibroRemuneraciones,
  subirLibroRemuneraciones,
  procesarLibroRemuneraciones,
  eliminarLibroRemuneraciones,
  obtenerEstadoMovimientosMes,
  subirMovimientosMes,
  eliminarMovimientosMes,
  guardarConceptosRemuneracion,
  eliminarConceptoRemuneracion,
  actualizarEstadoCierreNomina,
} from "../../api/nomina";

const CierreProgresoNomina = ({ cierre, cliente, onCierreActualizado }) => {
  const [libro, setLibro] = useState(null);
  const [libroId, setLibroId] = useState(null);
  const [subiendo, setSubiendo] = useState(false);
  const [movimientos, setMovimientos] = useState(null);
  const [subiendoMov, setSubiendoMov] = useState(false);
  const [modalAbierto, setModalAbierto] = useState(false);
  const [libroListo, setLibroListo] = useState(false);
  const [mensajeLibro, setMensajeLibro] = useState("");
  const [modoSoloLectura, setModoSoloLectura] = useState(false);
  
  // 🔄 REF: Para trackear si el componente está montado y controlar polling
  const isMountedRef = useRef(true);
  
  // Estados para tracking de secciones
  const [estadosSeccion, setEstadosSeccion] = useState({
    archivosTalana: 'pendiente',     // Estado de libros + movimientos
    archivosAnalista: 'pendiente',   // Estado de archivos del analista  
    verificadorDatos: 'pendiente',   // Estado de verificación de datos
    incidencias: 'pendiente'         // Estado de incidencias
  });

  const esEstadoPosteriorAConsolidacion = (estado) => {
    // Estados posteriores a la consolidación donde se aplican restricciones específicas
    // NOTA: 'incidencias_resueltas' tiene manejo específico en el switch, no se bloquea automáticamente
    const estadosPosteriores = [
      'datos_consolidados', 'con_incidencias', 'incidencias_resueltas', 'validacion_final', 'finalizado'
    ];
    return estadosPosteriores.includes(estado);
  };

  const esEstadoFinalizado = (estado) => {
    return estado === 'finalizado';
  };

  // 🎯 Función para verificar si todas las secciones están procesadas
  const verificarTodasLasSeccionesProcesadas = () => {
    const { archivosTalana, archivosAnalista, verificadorDatos, incidencias } = estadosSeccion;
    
    console.log('🔍 [CierreProgresoNomina] Verificando estados de secciones:', {
      archivosTalana,
      archivosAnalista, 
      verificadorDatos,
      incidencias,
      estadoCierre: cierre?.estado
    });
    
    return archivosTalana === 'procesado' && 
           archivosAnalista === 'procesado' && 
           verificadorDatos === 'procesado' && 
           incidencias === 'procesado';
  };

  // 🎯 Efecto para detectar cuando todas las secciones están procesadas
  useEffect(() => {
    const todasProcesadas = verificarTodasLasSeccionesProcesadas();
    const puedeActualizar = cierre?.estado !== 'finalizado' && 
                           cierre?.estado !== 'validacion_final' && 
                           cierre?.estado !== 'datos_consolidados';
    
    if (todasProcesadas && puedeActualizar) {
      console.log('🎯 [CierreProgresoNomina] Todas las secciones procesadas - Actualizando estado del cierre...');
      
      const actualizarEstadoFinal = async () => {
        try {
          await actualizarEstadoCierreNomina(cierre.id);
          console.log('✅ [CierreProgresoNomina] Estado del cierre actualizado automáticamente');
          
          if (onCierreActualizado) {
            await onCierreActualizado();
          }
        } catch (error) {
          console.error('❌ [CierreProgresoNomina] Error actualizando estado del cierre:', error);
        }
      };
      
      actualizarEstadoFinal();
    }
  }, [estadosSeccion, cierre?.id, cierre?.estado, onCierreActualizado]);

  // 🎯 Funciones para actualizar estados de las secciones
  const actualizarEstadoSeccion = useCallback((seccion, nuevoEstado) => {
    console.log(`📊 [CierreProgresoNomina] Actualizando estado ${seccion}: ${nuevoEstado} (${Date.now()})`);
    setEstadosSeccion(prev => {
      // Evitar actualizaciones innecesarias si el estado no cambió
      if (prev[seccion] === nuevoEstado) {
        console.log(`📊 [CierreProgresoNomina] Estado ${seccion} ya es ${nuevoEstado} - evitando actualización`);
        return prev;
      }
      
      return {
        ...prev,
        [seccion]: nuevoEstado
      };
    });
  }, []);

  // 🎯 Funciones memoizadas específicas para cada sección (evitar infinite polling)
  const onEstadoChangeAnalista = useCallback((nuevoEstado) => {
    console.log('🔄 [onEstadoChangeAnalista] CALLBACK EJECUTADO para:', nuevoEstado);
    actualizarEstadoSeccion('archivosAnalista', nuevoEstado);
  }, [actualizarEstadoSeccion]);

  const onEstadoChangeVerificador = useCallback((nuevoEstado) => {
    console.log('🔄 [onEstadoChangeVerificador] CALLBACK EJECUTADO para:', nuevoEstado);
    actualizarEstadoSeccion('verificadorDatos', nuevoEstado);
  }, [actualizarEstadoSeccion]);

  const onEstadoChangeIncidencias = useCallback((nuevoEstado) => {
    console.log('🔄 [onEstadoChangeIncidencias] CALLBACK EJECUTADO para:', nuevoEstado);
    actualizarEstadoSeccion('incidencias', nuevoEstado);
  }, [actualizarEstadoSeccion]);

  // 🎯 Función para determinar si una sección debe estar bloqueada
  const estaSeccionBloqueada = (seccion) => {
    // Si el cierre está finalizado, todo está bloqueado
    if (esEstadoFinalizado(cierre?.estado)) {
      return true;
    }
    
    // Determinar bloqueo según estado del cierre
    switch (cierre?.estado) {
      case 'pendiente':
      case 'cargando_archivos':
        // Solo archivos Talana y Analista están desbloqueados
        return !['archivosTalana', 'archivosAnalista'].includes(seccion);
        
      case 'archivos_completos':
      case 'verificacion_datos':
      case 'verificado_sin_discrepancias': 
        // Archivos + Verificador están desbloqueados
        return !['archivosTalana', 'archivosAnalista', 'verificadorDatos'].includes(seccion);
        
      case 'datos_consolidados':
        // Solo Talana + Verificador + Incidencias están desbloqueados (bloquear archivos analista)
        return !['archivosTalana', 'verificadorDatos', 'incidencias'].includes(seccion);
        
      case 'con_incidencias':
        // Solo Talana + Verificador + Incidencias están desbloqueados (mantener archivos analista bloqueados)
        return !['archivosTalana', 'verificadorDatos', 'incidencias'].includes(seccion);
        
      case 'incidencias_resueltas':
        // 🎯 ESTADO ESPECIAL: Solo la sección de incidencias debe estar desbloqueada para mostrar el botón "Finalizar Cierre"
        // Las demás secciones se bloquean para evitar cambios mientras se prepara la finalización
        return seccion !== 'incidencias';
        
      default:
        // Estados posteriores: bloquear según la lógica existente
        return esEstadoPosteriorAConsolidacion(cierre?.estado);
    }
  };

  const handleGuardarClasificaciones = async ({ guardar, eliminar }) => {
    try {
      // Primero eliminamos las clasificaciones que correspondan
      if (Array.isArray(eliminar) && eliminar.length > 0) {
        await Promise.all(
          eliminar.map((h) => eliminarConceptoRemuneracion(cliente.id, h))
        );
      }

      const tieneGuardar = guardar && Object.keys(guardar).length > 0;

      // Luego guardamos las nuevas clasificaciones
      if (tieneGuardar) {
        await guardarConceptosRemuneracion(cliente.id, guardar, cierre.id);
      } else if (Array.isArray(eliminar) && eliminar.length > 0) {
        // Si sólo se eliminaron conceptos, indicamos al backend que recalcule
        await guardarConceptosRemuneracion(cliente.id, {}, cierre.id);
      }

      // Refrescamos los conteos consultando nuevamente el backend
      const nuevoEstado = await obtenerEstadoLibroRemuneraciones(cierre.id);
      setLibro(nuevoEstado);
      if (nuevoEstado?.id) {
        setLibroId(nuevoEstado.id);
      }
    } catch (error) {
      console.error("Error al guardar clasificaciones:", error);
    }
  };

  if (!cierre || !cliente) {
    return (
      <div className="text-white text-center py-6">
        Cargando datos de cierre de nómina...
      </div>
    );
  }

  useEffect(() => {
    if (cierre?.id) {
      obtenerEstadoLibroRemuneraciones(cierre.id).then((data) => {
        setLibro(data);
        if (data?.id) {
          setLibroId(data.id);
        }
      });
      obtenerEstadoMovimientosMes(cierre.id).then(setMovimientos);
    }
  }, [cierre]);

  // Detecta cuando no quedan headers por clasificar
  useEffect(() => {
    const sinClasificar = Array.isArray(libro?.header_json?.headers_sin_clasificar)
      ? libro.header_json.headers_sin_clasificar.length === 0
      : false;
    const enProceso = libro?.estado === "procesando" || libro?.estado === "procesado";

    if (sinClasificar && !enProceso && !libroListo) {
      setLibroListo(true);
    } else if ((!sinClasificar || enProceso) && libroListo) {
      setLibroListo(false);
    }
  }, [libro, libroListo]);

  // 🎯 Efecto para detectar cambios en el estado de Archivos Talana
  useEffect(() => {
    const estadoLibro = libro?.estado === "procesando" || libro?.estado === "procesado"
      ? libro?.estado
      : libroListo
      ? "clasificado"
      : libro?.estado || "no_subido";
      
    const estadoMovimientos = movimientos?.estado || "pendiente";
    
    // Determinar el estado general: Procesado si ambos están procesados
    const estadoGeneral = (estadoLibro === "procesado" && estadoMovimientos === "procesado") 
      ? "procesado" 
      : "pendiente";
    
    actualizarEstadoSeccion('archivosTalana', estadoGeneral);
  }, [libro, movimientos, libroListo]);

  // Función para ir al Dashboard
  const handleIrDashboard = () => {
    // Redirigir al dashboard principal
    window.location.href = '/dashboard';
  };

  const handleSubirArchivo = async (archivo) => {
    setSubiendo(true);
    try {
      const res = await subirLibroRemuneraciones(cierre.id, archivo);
      if (res?.id) {
        setLibroId(res.id);
      }
      console.log('🔄 [PAUSADO] Polling post-subida de libro pausado temporalmente');
      // setTimeout(() => {
      //   obtenerEstadoLibroRemuneraciones(cierre.id).then((data) => {
      //     setLibro(data);
      //     if (data?.id) {
      //       setLibroId(data.id);
      //     }
      //   });
      // }, 1200);
    } finally {
      setSubiendo(false);
    }
  };

  const handleSubirMovimientos = async (archivo) => {
    setSubiendoMov(true);
    try {
      const formData = new FormData();
      formData.append("archivo", archivo);
      await subirMovimientosMes(cierre.id, formData);
      console.log('🔄 [PAUSADO] Polling post-subida de movimientos pausado temporalmente');
      // setTimeout(() => {
      //   obtenerEstadoMovimientosMes(cierre.id).then(setMovimientos);
      // }, 1200);
    } finally {
      setSubiendoMov(false);
    }
  };

  const handleProcesarLibro = async () => {
    console.log('=== PROCESAR LIBRO ===');
    
    const id = libro?.id || libroId;
    console.log('ID final para procesar:', id);
    
    if (!id) {
      console.log('❌ No hay ID para procesar');  
      return;
    }
    
    try {
      console.log('🔄 Llamando a procesarLibroRemuneraciones...');
      
      // FORZAR el estado a "procesando" ANTES de la llamada
      setLibro(prev => ({
        ...prev,
        estado: "procesando"
      }));
      setLibroListo(false); // asegura que la tarjeta muestre el estado de procesamiento
      
      await procesarLibroRemuneraciones(id);
      console.log('✅ Procesamiento iniciado - el polling monitoreará el progreso');
      
    } catch (error) {
      console.error("❌ Error al procesar libro:", error);
      setMensajeLibro("Error al procesar libro");
      // Revertir el estado en caso de error
      setLibro(prev => ({ 
        ...prev, 
        estado: "con_error" 
      }));
    }
  };

  const handleActualizarEstadoMovimientos = useCallback(async () => {
    // Verificar si el componente aún está montado
    if (!isMountedRef.current) {
      console.log('🚫 [handleActualizarEstadoMovimientos] Componente desmontado, cancelando operación');
      return;
    }
    
    try {
      const estado = await obtenerEstadoMovimientosMes(cierre.id);
      if (isMountedRef.current) {
        setMovimientos(estado);
      }
    } catch (error) {
      console.error("Error al actualizar estado de movimientos:", error);
    }
  }, [cierre?.id]);

  const handleActualizarEstado = useCallback(async () => {
    // Verificar si el componente aún está montado
    if (!isMountedRef.current) {
      console.log('🚫 [handleActualizarEstado] Componente desmontado, cancelando operación');
      return;
    }
    
    try {
      console.log('📡 Consultando estado actual del libro...');
      const estadoActual = await obtenerEstadoLibroRemuneraciones(cierre.id);
      console.log('📊 Estado recibido del servidor:', estadoActual);
      console.log('📊 Estado anterior:', libro?.estado);
      console.log('📊 Estado nuevo:', estadoActual?.estado);
      
      if (isMountedRef.current) {
        setLibro(estadoActual);
        
        // Log adicional para verificar el cambio
        if (estadoActual?.estado !== libro?.estado) {
          console.log(`🔄 Estado cambió de "${libro?.estado}" a "${estadoActual?.estado}"`);
        }
      }
      
    } catch (error) {
      console.error('❌ Error actualizando estado:', error);
    }
  }, [cierre?.id, libro?.estado]);

  const handleVerClasificacion = (soloLectura = false) => {
    // Si el libro ya está procesado, forzar modo solo lectura
    const esSoloLectura = soloLectura || libro?.estado === "procesado";
    
    setModalAbierto(true);
    setModoSoloLectura(esSoloLectura);
  };

  const handleEliminarLibro = async () => {
    if (!libro?.id) return;
    
    try {
      await eliminarLibroRemuneraciones(libro.id);
      // Resetear estado del libro
      setLibro(null);
      setLibroId(null);
      setLibroListo(false);
    } catch (error) {
      console.error("Error al eliminar libro:", error);
    }
  };

  const handleEliminarMovimientos = async () => {
    if (!movimientos?.id) return;
    
    try {
      await eliminarMovimientosMes(movimientos.id);
      // Resetear estado de movimientos
      setMovimientos(null);
    } catch (error) {
      console.error("Error al eliminar movimientos:", error);
    }
  };

  const headersSinClasificar = Array.isArray(libro?.header_json?.headers_sin_clasificar)
    ? libro.header_json.headers_sin_clasificar
    : [];

  const estadoMovimientos = movimientos?.estado || "pendiente";

  // Agregar esta función temporal para debug
  const debugEstado = async () => {
    try {
      console.log('🔍 DEBUG: Consultando estado directamente...');
      const estado = await obtenerEstadoLibroRemuneraciones(cierre.id);
      console.log('🔍 DEBUG: Respuesta completa:', estado);
    } catch (error) {
      console.error('🔍 DEBUG: Error:', error);
    }
  };

  // 🛑 Determinar si se debe detener el polling globalmente
  const deberiaDetenerPolling = esEstadoFinalizado(cierre?.estado) || !isMountedRef.current;

  const esCierreFinalizadoSoloResumen = esEstadoFinalizado(cierre.estado);

  return (
    <div className="space-y-10">
      {/* OPCIÓN 1: Solo mostrar resumen cuando está finalizado (comentar OPCIÓN 2) */}
      {esCierreFinalizadoSoloResumen ? (
        <ResumenCierreSection 
          cierre={cierre} 
          onIrDashboard={handleIrDashboard}
        />
      ) : (
        <>
          {/* Sección 1: Archivos Talana */}
          <ArchivosTalanaSection
            libro={libro}
            subiendo={subiendo}
            onSubirArchivo={handleSubirArchivo}
            onVerClasificacion={handleVerClasificacion}
            onProcesarLibro={handleProcesarLibro}
            onActualizarEstado={handleActualizarEstado}
            headersSinClasificar={headersSinClasificar}
            mensajeLibro={mensajeLibro}
            libroListo={libroListo}
            movimientos={movimientos}
            subiendoMov={subiendoMov}
            onSubirMovimientos={handleSubirMovimientos}
            onActualizarEstadoMovimientos={handleActualizarEstadoMovimientos}
            onEliminarLibro={handleEliminarLibro}
            onEliminarMovimientos={handleEliminarMovimientos}
            disabled={estaSeccionBloqueada('archivosTalana')}
            deberiaDetenerPolling={deberiaDetenerPolling}
            cierreId={cierre?.id}
          />
          
          {/* Sección 2: Archivos del Analista */}
          <ArchivosAnalistaSection
            cierreId={cierre.id}
            cliente={cliente}
            cierre={cierre}
            disabled={estaSeccionBloqueada('archivosAnalista')}
            onCierreActualizado={onCierreActualizado}
            onEstadoChange={onEstadoChangeAnalista}
            deberiaDetenerPolling={deberiaDetenerPolling}
          />

          {/* Sección 3: Verificación de Datos (Discrepancias) */}
          <VerificadorDatosSection 
            cierre={cierre} 
            disabled={estaSeccionBloqueada('verificadorDatos')}
            onCierreActualizado={(nuevoCierre) => {
              // Callback para actualizar el cierre en el componente padre
              console.log('🔄 Cierre actualizado desde verificador:', nuevoCierre);
              // Aquí podrías refrescar el estado completo del cierre si fuera necesario
            }}
            onEstadoChange={onEstadoChangeVerificador}
            deberiaDetenerPolling={deberiaDetenerPolling}
          />

          {/* Sección 4: Sistema de Incidencias */}
          <IncidenciasEncontradasSection 
            cierre={cierre} 
            disabled={estaSeccionBloqueada('incidencias')}
            onCierreActualizado={onCierreActualizado}
            onEstadoChange={onEstadoChangeIncidencias}
          />
        </>
      )}

      <ModalClasificacionHeaders
        isOpen={modalAbierto}
        onClose={() => setModalAbierto(false)}
        clienteId={cliente.id}
        headersSinClasificar={headersSinClasificar}
        onGuardarClasificaciones={handleGuardarClasificaciones}
        soloLectura={modoSoloLectura}
      />
    </div>
  );
};

export default CierreProgresoNomina;
