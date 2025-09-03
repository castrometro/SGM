import { useEffect, useState, useCallback, useRef } from "react";
import { CheckCircle, ChevronRight, Loader2 } from "lucide-react";
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
  // Funciones para archivos del analista
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
} from "../../api/nomina";

const CierreProgresoNomina = ({ cierre, cliente, onCierreActualizado }) => {
  const [libro, setLibro] = useState(null);
  const [libroId, setLibroId] = useState(null);
  const [subiendo, setSubiendo] = useState(false);
  const [movimientos, setMovimientos] = useState(null);
  const [subiendoMov, setSubiendoMov] = useState(false);
  const [modalAbierto, setModalAbierto] = useState(false);
  const [tipoModalClasificacion, setTipoModalClasificacion] = useState('libro'); // 'libro' o 'novedades'
  const [libroListo, setLibroListo] = useState(false);
  const [mensajeLibro, setMensajeLibro] = useState("");
  const [modoSoloLectura, setModoSoloLectura] = useState(false);
  
  // Estados para archivos del analista
  const [ingresos, setIngresos] = useState(null);
  const [subiendoIngresos, setSubiendoIngresos] = useState(false);
  const [finiquitos, setFiniquitos] = useState(null);
  const [subiendoFiniquitos, setSubiendoFiniquitos] = useState(false);
  const [ausentismos, setAusentismos] = useState(null);
  const [subiendoAusentismos, setSubiendoAusentismos] = useState(false);
  const [novedades, setNovedades] = useState(null);
  const [novedadesId, setNovedadesId] = useState(null);
  const [subiendoNovedades, setSubiendoNovedades] = useState(false);
  const [novedadesListo, setNovedadesListo] = useState(false);
  const [mensajeNovedades, setMensajeNovedades] = useState("");
  
  // 🔄 REF: Para trackear si el componente está montado y controlar polling
  const isMountedRef = useRef(true);
  
  // Estados para tracking de secciones
  const [estadosSeccion, setEstadosSeccion] = useState({
    archivosTalana: 'archivos_pendientes',        // Estado de libros + movimientos
    archivosAnalista: 'archivos_pendientes',      // Estado de archivos del analista
    verificadorDatos: 'verificacion_pendiente',   // Estado de verificación de datos
    incidencias: 'incidencias_pendientes'         // Estado de incidencias
  });

  // 🎯 Estados para el botón "Continuar"
  const [actualizandoEstado, setActualizandoEstado] = useState(false);

  // 🎯 Estado para manejar acordeón (solo una sección expandida a la vez)
  const [seccionExpandida, setSeccionExpandida] = useState('archivosTalana'); // Por defecto la primera sección

  // 🎯 Función para manejar la expansión de secciones (acordeón)
  const manejarExpansionSeccion = (nombreSeccion) => {
    // Si se hace clic en la sección ya expandida, la colapsamos
    // Si se hace clic en otra sección, la expandimos y colapsamos las demás
    setSeccionExpandida(prev => prev === nombreSeccion ? null : nombreSeccion);
  };

  // 🎯 Función para determinar si una sección está expandida
  const estaSeccionExpandida = (nombreSeccion) => {
    return seccionExpandida === nombreSeccion;
  };

  // 🎯 Función para determinar si mostrar el botón "Continuar"
  const mostrarBotonContinuar = () => {
    const talanaOk = estadosSeccion.archivosTalana === 'archivos_completos';
    const analistaOk = estadosSeccion.archivosAnalista === 'archivos_completos';
    const cierreOk = cierre?.estado === 'pendiente' || cierre?.estado === 'archivos_completos'; // ✅ Incluye archivos_completos
    
    console.log(`🎯 [mostrarBotonContinuar] Talana: ${estadosSeccion.archivosTalana} (${talanaOk}), Analista: ${estadosSeccion.archivosAnalista} (${analistaOk}), Cierre: ${cierre?.estado} (${cierreOk})`);
    
    return talanaOk && analistaOk && cierreOk;
  };

  // 🎯 Función para manejar el botón "Continuar"
  const handleContinuar = async () => {
    if (actualizandoEstado) return; // Evitar doble clic
    
    try {
      setActualizandoEstado(true);
      console.log('🔄 [CierreProgresoNomina] Usuario presionó Continuar - Actualizando estado del cierre...');
      
      // Llamar a la API para actualizar el estado del cierre
      await actualizarEstadoCierreNomina(cierre.id);
      console.log('✅ [CierreProgresoNomina] Estado del cierre actualizado exitosamente');
      
      // Refrescar datos del cierre desde el componente padre
      if (onCierreActualizado) {
        await onCierreActualizado();
        console.log('🔄 [CierreProgresoNomina] Datos del cierre refrescados');
      }
      
    } catch (error) {
      console.error('❌ [CierreProgresoNomina] Error actualizando estado del cierre:', error);
      // Aquí podrías mostrar una notificación de error al usuario
    } finally {
      setActualizandoEstado(false);
    }
  };

  // 🎯 SIMPLIFICADO: Las tarjetas v2 manejan su propio estado
  // Ya no necesitamos cargar estados centralizadamente

  // 🎯 SIMPLIFICADO: Las tarjetas v2 manejan su propio estado

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

  // 🎯 ELIMINADO: Callback de Analista - ahora se calcula directamente como Talana
  // const onEstadoChangeAnalista = useCallback((nuevoEstado) => {
  //   console.log('🔄 [onEstadoChangeAnalista] CALLBACK EJECUTADO para:', nuevoEstado);
  //   actualizarEstadoSeccion('archivosAnalista', nuevoEstado);
  // }, [actualizarEstadoSeccion]);

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
        // Archivos Talana y Analista están desbloqueados desde el inicio
        return !['archivosTalana', 'archivosAnalista'].includes(seccion);
        
      case 'archivos_completos':
      case 'verificacion_datos':
      case 'verificado_sin_discrepancias': 
        // Archivos Talana + Analista + Verificador están desbloqueados
        return !['archivosTalana', 'archivosAnalista', 'verificadorDatos'].includes(seccion);
        
      case 'datos_consolidados':
        // Todos excepto incidencias están desbloqueados
        return !['archivosTalana', 'archivosAnalista', 'verificadorDatos', 'incidencias'].includes(seccion);
        
      case 'con_incidencias':
        // Todos están desbloqueados
        return !['archivosTalana', 'archivosAnalista', 'verificadorDatos', 'incidencias'].includes(seccion);
        
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

      // Refrescamos los conteos consultando nuevamente el backend según el tipo
      if (tipoModalClasificacion === 'libro') {
        const nuevoEstado = await obtenerEstadoLibroRemuneraciones(cierre.id);
        setLibro(nuevoEstado);
        if (nuevoEstado?.id) {
          setLibroId(nuevoEstado.id);
        }
      } else if (tipoModalClasificacion === 'novedades') {
        const nuevoEstado = await obtenerEstadoArchivoNovedades(cierre.id);
        setNovedades(nuevoEstado);
        if (nuevoEstado?.id) {
          setNovedadesId(nuevoEstado.id);
        }
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
      
      // Cargar estados de archivos del analista
      obtenerEstadoIngresos(cierre.id).then(setIngresos);
      obtenerEstadoFiniquitos(cierre.id).then(setFiniquitos);
      obtenerEstadoAusentismos(cierre.id).then(setAusentismos);
      obtenerEstadoArchivoNovedades(cierre.id).then((data) => {
        setNovedades(data);
        if (data?.id) {
          setNovedadesId(data.id);
        }
      });
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

  // Detecta cuando no quedan headers por clasificar en novedades
  useEffect(() => {
    const sinClasificarNovedades = Array.isArray(novedades?.header_json?.headers_sin_clasificar)
      ? novedades.header_json.headers_sin_clasificar.length === 0
      : false;
    const enProcesoNovedades = novedades?.estado === "procesando" || novedades?.estado === "procesado";

    if (sinClasificarNovedades && !enProcesoNovedades && !novedadesListo) {
      setNovedadesListo(true);
    } else if ((!sinClasificarNovedades || enProcesoNovedades) && novedadesListo) {
      setNovedadesListo(false);
    }
  }, [novedades, novedadesListo]);

  // 🎯 Efecto para detectar cambios en el estado de Archivos Talana
  useEffect(() => {
    const estadoLibro = libro?.estado === "procesando" || libro?.estado === "procesado"
      ? libro?.estado
      : libroListo
      ? "clasificado"
      : libro?.estado || "no_subido";
      
    const estadoMovimientos = movimientos?.estado || "archivos_pendientes";
    
    // Determinar el estado general: Archivos completos si ambos están procesados
    const estadoGeneral = (estadoLibro === "procesado" && estadoMovimientos === "procesado") 
      ? "archivos_completos" 
      : "archivos_pendientes";
    
    actualizarEstadoSeccion('archivosTalana', estadoGeneral);
  }, [libro, movimientos, libroListo]);

  // 🎯 Efecto para detectar cambios en el estado de Archivos del Analista
  useEffect(() => {
    const estadoIngresos = ingresos?.estado || "no_subido";
    const estadoFiniquitos = finiquitos?.estado || "no_subido";
    const estadoAusentismos = ausentismos?.estado || "no_subido";
    
    const estadoNovedades = novedades?.estado === "procesando" || novedades?.estado === "procesado"
      ? novedades?.estado
      : novedadesListo
      ? "clasificado"
      : novedades?.estado || "no_subido";
    
    // Determinar el estado general: Archivos completos si TODOS están procesados
    const todosArchivosProcessed = [estadoIngresos, estadoFiniquitos, estadoAusentismos, estadoNovedades]
      .every(estado => estado === "procesado");
    
    const estadoGeneral = todosArchivosProcessed ? "archivos_completos" : "archivos_pendientes";
    
    actualizarEstadoSeccion('archivosAnalista', estadoGeneral);
  }, [ingresos, finiquitos, ausentismos, novedades, novedadesListo]);

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
      console.log('✅ Archivo subido exitosamente, actualizando estado...');
      // Actualizar estado inmediatamente después de subir
      setTimeout(() => {
        obtenerEstadoLibroRemuneraciones(cierre.id).then((data) => {
          console.log('📡 Estado actualizado post-subida:', data);
          setLibro(data);
          if (data?.id) {
            setLibroId(data.id);
          }
        });
      }, 1000); // 1 segundo para dar tiempo al backend
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
      console.log('✅ Movimientos subidos exitosamente, actualizando estado...');
      // Actualizar estado inmediatamente después de subir
      setTimeout(() => {
        obtenerEstadoMovimientosMes(cierre.id).then((data) => {
          console.log('📡 Movimientos actualizados post-subida:', data);
          setMovimientos(data);
        });
      }, 1000); // 1 segundo para dar tiempo al backend
    } finally {
      setSubiendoMov(false);
    }
  };

  // Handlers de subida para archivos del analista
  const handleSubirIngresos = async (archivo) => {
    setSubiendoIngresos(true);
    try {
      const formData = new FormData();
      formData.append("archivo", archivo);
      await subirIngresos(cierre.id, formData);
      console.log('✅ Ingresos subidos exitosamente, actualizando estado...');
      setTimeout(() => {
        obtenerEstadoIngresos(cierre.id).then((data) => {
          console.log('📡 Ingresos actualizados post-subida:', data);
          setIngresos(data);
        });
      }, 1000);
    } finally {
      setSubiendoIngresos(false);
    }
  };

  const handleSubirFiniquitos = async (archivo) => {
    setSubiendoFiniquitos(true);
    try {
      const formData = new FormData();
      formData.append("archivo", archivo);
      await subirFiniquitos(cierre.id, formData);
      console.log('✅ Finiquitos subidos exitosamente, actualizando estado...');
      setTimeout(() => {
        obtenerEstadoFiniquitos(cierre.id).then((data) => {
          console.log('📡 Finiquitos actualizados post-subida:', data);
          setFiniquitos(data);
        });
      }, 1000);
    } finally {
      setSubiendoFiniquitos(false);
    }
  };

  const handleSubirAusentismos = async (archivo) => {
    setSubiendoAusentismos(true);
    try {
      const formData = new FormData();
      formData.append("archivo", archivo);
      await subirAusentismos(cierre.id, formData);
      console.log('✅ Ausentismos subidos exitosamente, actualizando estado...');
      setTimeout(() => {
        obtenerEstadoAusentismos(cierre.id).then((data) => {
          console.log('📡 Ausentismos actualizados post-subida:', data);
          setAusentismos(data);
        });
      }, 1000);
    } finally {
      setSubiendoAusentismos(false);
    }
  };

  const handleSubirNovedades = async (archivo) => {
    setSubiendoNovedades(true);
    try {
      const formData = new FormData();
      formData.append("archivo", archivo);
      const res = await subirArchivoNovedades(cierre.id, formData);
      if (res?.id) {
        setNovedadesId(res.id);
      }
      console.log('✅ Novedades subidas exitosamente, actualizando estado...');
      setTimeout(() => {
        obtenerEstadoArchivoNovedades(cierre.id).then((data) => {
          console.log('📡 Novedades actualizadas post-subida:', data);
          setNovedades(data);
          if (data?.id) {
            setNovedadesId(data.id);
          }
        });
      }, 1000);
    } finally {
      setSubiendoNovedades(false);
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

  const handleProcesarNovedades = async () => {
    console.log('=== PROCESAR NOVEDADES ===');
    
    const id = novedades?.id || novedadesId;
    console.log('ID final para procesar novedades:', id);
    
    if (!id) {
      console.log('❌ No hay ID para procesar novedades');  
      return;
    }
    
    try {
      console.log('🔄 Llamando a procesarFinalNovedades...');
      
      // FORZAR el estado a "procesando" ANTES de la llamada
      setNovedades(prev => ({
        ...prev,
        estado: "procesando"
      }));
      setNovedadesListo(false);
      
      await procesarFinalNovedades(id);
      console.log('✅ Procesamiento final novedades iniciado - el polling monitoreará el progreso');
      
    } catch (error) {
      console.error("❌ Error al procesar novedades:", error);
      setMensajeNovedades("Error al procesar novedades");
      setNovedades(prev => ({ 
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

  // Handlers de actualización para archivos del analista
  const handleActualizarEstadoIngresos = useCallback(async () => {
    if (!isMountedRef.current) {
      console.log('🚫 [handleActualizarEstadoIngresos] Componente desmontado, cancelando operación');
      return;
    }
    
    try {
      const estado = await obtenerEstadoIngresos(cierre.id);
      if (isMountedRef.current) {
        setIngresos(estado);
      }
    } catch (error) {
      console.error("Error al actualizar estado de ingresos:", error);
    }
  }, [cierre?.id]);

  const handleActualizarEstadoFiniquitos = useCallback(async () => {
    if (!isMountedRef.current) {
      console.log('🚫 [handleActualizarEstadoFiniquitos] Componente desmontado, cancelando operación');
      return;
    }
    
    try {
      const estado = await obtenerEstadoFiniquitos(cierre.id);
      if (isMountedRef.current) {
        setFiniquitos(estado);
      }
    } catch (error) {
      console.error("Error al actualizar estado de finiquitos:", error);
    }
  }, [cierre?.id]);

  const handleActualizarEstadoAusentismos = useCallback(async () => {
    if (!isMountedRef.current) {
      console.log('🚫 [handleActualizarEstadoAusentismos] Componente desmontado, cancelando operación');
      return;
    }
    
    try {
      const estado = await obtenerEstadoAusentismos(cierre.id);
      if (isMountedRef.current) {
        setAusentismos(estado);
      }
    } catch (error) {
      console.error("Error al actualizar estado de ausentismos:", error);
    }
  }, [cierre?.id]);

  const handleActualizarEstadoNovedades = useCallback(async () => {
    if (!isMountedRef.current) {
      console.log('🚫 [handleActualizarEstadoNovedades] Componente desmontado, cancelando operación');
      return;
    }
    
    try {
      console.log('📡 Consultando estado actual de novedades...');
      const estadoActual = await obtenerEstadoArchivoNovedades(cierre.id);
      console.log('📊 Estado novedades recibido del servidor:', estadoActual);
      
      if (isMountedRef.current) {
        setNovedades(estadoActual);
        
        if (estadoActual?.estado !== novedades?.estado) {
          console.log(`🔄 Estado novedades cambió de "${novedades?.estado}" a "${estadoActual?.estado}"`);
          
          // ✅ MEJORA: Actualizar novedadesListo cuando se procesa completamente
          if (estadoActual?.estado === "procesado") {
            console.log('✅ Novedades procesadas completamente - marcando como listo');
            setNovedadesListo(true);
          }
        }
      }
      
    } catch (error) {
      console.error('❌ Error actualizando estado novedades:', error);
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
    
    setTipoModalClasificacion('libro');
    setModalAbierto(true);
    setModoSoloLectura(esSoloLectura);
  };

  const handleVerClasificacionNovedades = (soloLectura = false) => {
    // Si las novedades ya están procesadas, forzar modo solo lectura
    const esSoloLectura = soloLectura || novedades?.estado === "procesado";
    
    setTipoModalClasificacion('novedades');
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

  // Handlers de eliminación para archivos del analista
  const handleEliminarIngresos = async () => {
    if (!ingresos?.id) return;
    
    try {
      await eliminarIngresos(ingresos.id);
      setIngresos(null);
    } catch (error) {
      console.error("Error al eliminar ingresos:", error);
    }
  };

  const handleEliminarFiniquitos = async () => {
    if (!finiquitos?.id) return;
    
    try {
      await eliminarFiniquitos(finiquitos.id);
      setFiniquitos(null);
    } catch (error) {
      console.error("Error al eliminar finiquitos:", error);
    }
  };

  const handleEliminarAusentismos = async () => {
    if (!ausentismos?.id) return;
    
    try {
      await eliminarAusentismos(ausentismos.id);
      setAusentismos(null);
    } catch (error) {
      console.error("Error al eliminar ausentismos:", error);
    }
  };

  const handleEliminarNovedades = async () => {
    if (!novedades?.id) return;
    
    try {
      await eliminarArchivoNovedades(novedades.id);
      setNovedades(null);
      setNovedadesId(null);
      setNovedadesListo(false);
    } catch (error) {
      console.error("Error al eliminar novedades:", error);
    }
  };

  const headersSinClasificar = Array.isArray(libro?.header_json?.headers_sin_clasificar)
    ? libro.header_json.headers_sin_clasificar
    : [];

  const headersSinClasificarNovedades = Array.isArray(novedades?.header_json?.headers_sin_clasificar)
    ? novedades.header_json.headers_sin_clasificar
    : [];

  const estadoMovimientos = movimientos?.estado || "archivos_pendientes";

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
            // 🎯 Props para acordeón
            expandido={estaSeccionExpandida('archivosTalana')}
            onToggleExpansion={() => manejarExpansionSeccion('archivosTalana')}
          />
          
          {/* Sección 2: Archivos del Analista */}
          <ArchivosAnalistaSection
            // Props para Ingresos
            ingresos={ingresos}
            subiendoIngresos={subiendoIngresos}
            onSubirIngresos={handleSubirIngresos}
            onActualizarEstadoIngresos={handleActualizarEstadoIngresos}
            onEliminarIngresos={handleEliminarIngresos}
            
            // Props para Finiquitos
            finiquitos={finiquitos}
            subiendoFiniquitos={subiendoFiniquitos}
            onSubirFiniquitos={handleSubirFiniquitos}
            onActualizarEstadoFiniquitos={handleActualizarEstadoFiniquitos}
            onEliminarFiniquitos={handleEliminarFiniquitos}
            
            // Props para Ausentismos
            ausentismos={ausentismos}
            subiendoAusentismos={subiendoAusentismos}
            onSubirAusentismos={handleSubirAusentismos}
            onActualizarEstadoAusentismos={handleActualizarEstadoAusentismos}
            onEliminarAusentismos={handleEliminarAusentismos}
            
            // Props para Novedades
            novedades={novedades}
            subiendoNovedades={subiendoNovedades}
            onSubirNovedades={handleSubirNovedades}
            onVerClasificacionNovedades={handleVerClasificacionNovedades}
            onProcesarNovedades={handleProcesarNovedades}
            onActualizarEstadoNovedades={handleActualizarEstadoNovedades}
            onEliminarNovedades={handleEliminarNovedades}
            headersSinClasificarNovedades={novedades?.header_json?.headers_sin_clasificar || []}
            mensajeNovedades={mensajeNovedades}
            novedadesListo={novedadesListo}
            
            // Props de control
            disabled={estaSeccionBloqueada('archivosAnalista')}
            deberiaDetenerPolling={deberiaDetenerPolling}
            cierreId={cierre?.id}
            
            // Props para acordeón
            expandido={estaSeccionExpandida('archivosAnalista')}
            onToggleExpansion={() => manejarExpansionSeccion('archivosAnalista')}
          />

          {/* 🎯 BOTÓN "CONTINUAR" - Solo cuando secciones 1 y 2 están procesadas */}
          {mostrarBotonContinuar() && (
            <div className="bg-gray-800 border border-gray-700 rounded-lg p-6 text-center mb-6">
              <div className="flex items-center justify-center mb-4">
                <div className="flex items-center justify-center w-12 h-12 bg-green-600 rounded-full mr-4">
                  <CheckCircle className="h-6 w-6 text-white" />
                </div>
                <div className="text-left">
                  <h3 className="text-white text-lg font-semibold">
                    Archivos Base Completados
                  </h3>
                  <p className="text-gray-400 text-sm">
                    Todas las secciones requeridas están procesadas
                  </p>
                </div>
              </div>
              <p className="text-gray-300 mb-6 text-sm leading-relaxed">
                Las secciones de <strong>Archivos Talana</strong> y <strong>Archivos del Analista</strong> están procesadas completamente.
                <br />
                Puedes continuar para habilitar la verificación de datos y avanzar en el proceso de cierre.
              </p>
              <button
                onClick={handleContinuar}
                disabled={actualizandoEstado}
                className="bg-blue-700 hover:bg-blue-600 disabled:opacity-60 disabled:cursor-not-allowed text-white px-6 py-3 rounded-lg font-medium transition-all duration-200 flex items-center justify-center mx-auto shadow-lg"
              >
                {actualizandoEstado ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin mr-2" />
                    Actualizando Estado...
                  </>
                ) : (
                  <>
                    Continuar al Siguiente Paso
                    <ChevronRight className="h-4 w-4 ml-2" />
                  </>
                )}
              </button>
            </div>
          )}

          {/* Sección 3: Verificación de Datos (Discrepancias) */}
          <VerificadorDatosSection 
            cierre={cierre} 
            disabled={estaSeccionBloqueada('verificadorDatos')}
            onCierreActualizado={async () => {
              // 🔄 Callback para actualizar el cierre en el componente padre
              console.log('🔄 [CierreProgresoNomina] Actualizando cierre desde verificador...');
              if (onCierreActualizado) {
                await onCierreActualizado();
                console.log('✅ [CierreProgresoNomina] Cierre actualizado exitosamente desde verificador');
              } else {
                console.log('⚠️ [CierreProgresoNomina] No hay callback onCierreActualizado disponible');
              }
            }}
            onEstadoChange={onEstadoChangeVerificador}
            deberiaDetenerPolling={deberiaDetenerPolling}
            // 🎯 Props para acordeón
            expandido={estaSeccionExpandida('verificadorDatos')}
            onToggleExpansion={() => manejarExpansionSeccion('verificadorDatos')}
          />

          {/* Sección 4: Sistema de Incidencias */}
          <IncidenciasEncontradasSection 
            cierre={cierre} 
            disabled={estaSeccionBloqueada('incidencias')}
            onCierreActualizado={onCierreActualizado}
            onEstadoChange={onEstadoChangeIncidencias}
            // 🎯 Props para acordeón
            expandido={estaSeccionExpandida('incidencias')}
            onToggleExpansion={() => manejarExpansionSeccion('incidencias')}
          />
        </>
      )}

      <ModalClasificacionHeaders
        isOpen={modalAbierto}
        onClose={() => setModalAbierto(false)}
        clienteId={cliente.id}
        headersSinClasificar={tipoModalClasificacion === 'libro' ? headersSinClasificar : headersSinClasificarNovedades}
        onGuardarClasificaciones={handleGuardarClasificaciones}
        soloLectura={modoSoloLectura}
      />
    </div>
  );
};

export default CierreProgresoNomina;
