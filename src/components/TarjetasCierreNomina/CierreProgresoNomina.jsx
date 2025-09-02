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
  obtenerEstadoArchivoAnalista,
  obtenerEstadoArchivoNovedades,
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

  // 🎯 Estados para el botón "Continuar"
  const [actualizandoEstado, setActualizandoEstado] = useState(false);

  // 🎯 Estado para manejar acordeón (solo una sección expandida a la vez)
  const [seccionExpandida, setSeccionExpandida] = useState('archivosTalana'); // Por defecto la primera sección

  // 🎯 Estados para archivos del analista (elevados desde ArchivosAnalistaContainer)
  const [archivosAnalista, setArchivosAnalista] = useState({
    finiquitos: { estado: "loading", archivo: null, error: "" },
    incidencias: { estado: "loading", archivo: null, error: "" },
    ingresos: { estado: "loading", archivo: null, error: "" },
    novedades: { estado: "loading", archivo: null, error: "" }
  });

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
    return estadosSeccion.archivosTalana === 'procesado' && 
           estadosSeccion.archivosAnalista === 'procesado' && 
           cierre?.estado === 'pendiente'; // Solo mostrar cuando esté pendiente, no cuando ya sea archivos_completos
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

  // 🎯 Función para cargar estados de archivos del analista
  const cargarEstadosArchivosAnalista = useCallback(async () => {
    if (!cierre?.id) return;
    
    console.log('📁 [CierreProgresoNomina] Cargando estados de archivos del analista...');
    
    for (const tipo of ['finiquitos', 'incidencias', 'ingresos', 'novedades']) {
      try {
        let data;
        if (tipo === 'novedades') {
          data = await obtenerEstadoArchivoNovedades(cierre.id);
          if (data && data.id) {
            data = [data];
          } else {
            data = [];
          }
        } else {
          data = await obtenerEstadoArchivoAnalista(cierre.id, tipo);
        }
        
        if (data && data.length > 0) {
          const archivo = data[0];
          setArchivosAnalista(prev => ({
            ...prev,
            [tipo]: {
              ...prev[tipo],
              estado: archivo.estado,
              archivo: {
                id: archivo.id,
                nombre: archivo.archivo ? archivo.archivo.split('/').pop() : (archivo.archivo_nombre || ''),
                fecha_subida: archivo.fecha_subida
              }
            }
          }));
        } else {
          // Si no hay archivos, cambiar de "loading" a "no_subido"
          setArchivosAnalista(prev => ({
            ...prev,
            [tipo]: {
              ...prev[tipo],
              estado: "no_subido",
              archivo: null
            }
          }));
        }
      } catch (error) {
        console.error(`❌ [CierreProgresoNomina] Error cargando estado de ${tipo}:`, error);
        // En caso de error, cambiar a "no_subido" para permitir que el usuario intente subir
        setArchivosAnalista(prev => ({
          ...prev,
          [tipo]: {
            ...prev[tipo],
            estado: "no_subido",
            archivo: null,
            error: error.message || "Error cargando estado"
          }
        }));
      }
    }
    
    console.log('✅ [CierreProgresoNomina] Estados de archivos del analista cargados');
  }, [cierre?.id]);

  // 🎯 Función para actualizar estado de un archivo específico del analista
  const actualizarEstadoArchivoAnalista = useCallback(async (tipo) => {
    if (!cierre?.id) return;
    
    try {
      let data;
      if (tipo === 'novedades') {
        data = await obtenerEstadoArchivoNovedades(cierre.id);
        if (data && data.id) {
          data = [data];
        } else {
          data = [];
        }
      } else {
        data = await obtenerEstadoArchivoAnalista(cierre.id, tipo);
      }
      
      if (data && data.length > 0) {
        const archivo = data[0];
        setArchivosAnalista(prev => ({
          ...prev,
          [tipo]: {
            ...prev[tipo],
            estado: archivo.estado,
            archivo: {
              id: archivo.id,
              nombre: archivo.archivo ? archivo.archivo.split('/').pop() : (archivo.archivo_nombre || ''),
              fecha_subida: archivo.fecha_subida
            }
          }
        }));
      }
    } catch (error) {
      console.error(`❌ Error actualizando estado de ${tipo}:`, error);
    }
  }, [cierre?.id]);

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
      
      // 🎯 Cargar estados de archivos del analista
      cargarEstadosArchivosAnalista();
    }
  }, [cierre, cargarEstadosArchivosAnalista]);

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

  // 🎯 Efecto para detectar cambios en el estado de Archivos del Analista
  useEffect(() => {
    const estadosArchivos = Object.values(archivosAnalista);
    
    // Si algún archivo está en "loading", la sección aún está cargando
    if (estadosArchivos.some(archivo => archivo.estado === "loading")) {
      actualizarEstadoSeccion('archivosAnalista', 'pendiente');
      return;
    }
    
    // Si todos están procesados, la sección está procesada
    const todosProcessados = estadosArchivos.every(archivo => archivo.estado === "procesado");
    const estadoGeneral = todosProcessados ? "procesado" : "pendiente";
    
    actualizarEstadoSeccion('archivosAnalista', estadoGeneral);
  }, [archivosAnalista]);

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
            // 🎯 Props para acordeón
            expandido={estaSeccionExpandida('archivosTalana')}
            onToggleExpansion={() => manejarExpansionSeccion('archivosTalana')}
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
            // 🎯 Props para acordeón
            expandido={estaSeccionExpandida('archivosAnalista')}
            onToggleExpansion={() => manejarExpansionSeccion('archivosAnalista')}
            // 🎯 Estados elevados (igual que ArchivosTalanaSection)
            archivosAnalista={archivosAnalista}
            onActualizarEstadoArchivo={actualizarEstadoArchivoAnalista}
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
            onCierreActualizado={(nuevoCierre) => {
              // Callback para actualizar el cierre en el componente padre
              console.log('🔄 Cierre actualizado desde verificador:', nuevoCierre);
              // Aquí podrías refrescar el estado completo del cierre si fuera necesario
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
        headersSinClasificar={headersSinClasificar}
        onGuardarClasificaciones={handleGuardarClasificaciones}
        soloLectura={modoSoloLectura}
      />
    </div>
  );
};

export default CierreProgresoNomina;
