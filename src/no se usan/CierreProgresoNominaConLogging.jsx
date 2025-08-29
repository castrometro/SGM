import { useEffect, useState, useRef, useCallback } from "react";
import LibroRemuneracionesCardConLogging from "./LibroRemuneracionesCardConLogging";
import MovimientosMesCard from "./MovimientosMesCard";
import ModalClasificacionHeaders from "../ModalClasificacionHeaders";
import {
  obtenerEstadoLibroRemuneraciones,
  subirLibroRemuneraciones,
  procesarLibroRemuneraciones,
  obtenerEstadoMovimientosMes,
  subirMovimientosMes,
  guardarConceptosRemuneracion,
  eliminarConceptoRemuneracion,
  obtenerEstadoArchivoAnalista,
  obtenerEstadoArchivoNovedades,
} from "../../api/nomina";

const CierreProgresoNominaConLogging = ({ 
  cierre, 
  cliente,
  libroRemuneracionesReady,
  setLibroRemuneracionesReady,
  movimientosMesReady,
  setMovimientosMesReady,
  archivoAnalistaReady,
  setArchivoAnalistaReady,
  archivoNovedadesReady,
  setArchivoNovedadesReady,
}) => {
  const [libro, setLibro] = useState(null);
  const [libroId, setLibroId] = useState(null);
  const [subiendo, setSubiendo] = useState(false);
  
  // Logging de renders del componente padre
  console.log('🔄 CierreProgresoNominaConLogging RENDER:', {
    timestamp: new Date().toISOString(),
    cierreId: cierre?.id,
    clienteId: cliente?.id,
    libroEstado: libro?.estado,
    subiendo
  });
  const [movimientos, setMovimientos] = useState(null);
  const [subiendoMov, setSubiendoMov] = useState(false);
  const [modalAbierto, setModalAbierto] = useState(false);
  const [libroListo, setLibroListo] = useState(false);
  const [mensajeLibro, setMensajeLibro] = useState("");
  const [modoSoloLectura, setModoSoloLectura] = useState(false);

  // Estados para los otros archivos
  const [archivoAnalista, setArchivoAnalista] = useState(null);
  const [archivoNovedades, setArchivoNovedades] = useState(null);

  const handleGuardarClasificaciones = useCallback(async ({ guardar, eliminar }) => {
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
  }, [cliente.id, cierre.id]);

  if (!cierre || !cliente) {
    return (
      <div className="text-white text-center py-6">
        Cargando datos de cierre de nómina...
      </div>
    );
  }

  // Fetch por etapas, basado en el estado de cada paso
  useEffect(() => {
    const fetchEstados = async () => {
      if (!cierre?.id) return;

      try {
        // 1. Libro de Remuneraciones
        const estadoLibro = await obtenerEstadoLibroRemuneraciones(cierre.id);
        setLibro(estadoLibro);
        if (estadoLibro?.id) {
          setLibroId(estadoLibro.id);
        }
        const libroOk = estadoLibro?.estado === "procesado";
        setLibroRemuneracionesReady(libroOk);

        // 2. Movimientos del Mes (solo si libro está listo)
        if (libroOk) {
          const estadoMov = await obtenerEstadoMovimientosMes(cierre.id);
          setMovimientos(estadoMov);
          const movOk = estadoMov?.estado === "procesado";
          setMovimientosMesReady(movOk);

          // 3. Archivo Analista (solo si movimientos están listos)
          if (movOk) {
            const estadoAnalista = await obtenerEstadoArchivoAnalista(cierre.id);
            setArchivoAnalista(estadoAnalista);
            const analistaOk = estadoAnalista?.estado === "procesado";
            setArchivoAnalistaReady(analistaOk);

            // 4. Archivo Novedades (solo si analista está listo)
            if (analistaOk) {
              const estadoNovedades = await obtenerEstadoArchivoNovedades(cierre.id);
              setArchivoNovedades(estadoNovedades);
              const novedadesOk = estadoNovedades?.estado === "procesado";
              setArchivoNovedadesReady(novedadesOk);
            } else {
              setArchivoNovedadesReady(false);
            }
          } else {
            setArchivoAnalistaReady(false);
            setArchivoNovedadesReady(false);
          }
        } else {
          setMovimientosMesReady(false);
          setArchivoAnalistaReady(false);
          setArchivoNovedadesReady(false);
        }

      } catch (error) {
        console.error("Error fetching estados:", error);
      }
    };

    fetchEstados();
  }, [cierre, cliente, setLibroRemuneracionesReady, setMovimientosMesReady, setArchivoAnalistaReady, setArchivoNovedadesReady]);

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

  const handleSubirArchivo = useCallback(async (archivo) => {
    // Agregar logging detallado para diagnosticar múltiples llamadas
    console.log('🔍 handleSubirArchivo LLAMADO:', {
      timestamp: new Date().toISOString(),
      fileName: archivo.name,
      fileSize: archivo.size,
      subiendo: subiendo,
      stackTrace: new Error().stack.split('\n').slice(0, 10).join('\n')
    });
    
    // Prevenir múltiples envíos si ya está subiendo
    if (subiendo) {
      console.warn('⚠️ Upload ya en progreso, ignorando nuevo intento');
      return;
    }

    setSubiendo(true);
    console.log('📤 Iniciando subida de archivo:', archivo.name);
    
    try {
      const res = await subirLibroRemuneraciones(cierre.id, archivo);
      console.log('✅ Respuesta del servidor:', res);
      
      if (res?.id) {
        setLibroId(res.id);
      }
      
      // Si hay upload_log_id en la respuesta, devolverlo para el monitoreo
      if (res?.upload_log_id) {
        console.log('🔍 Upload log ID recibido:', res.upload_log_id);
        return { upload_log_id: res.upload_log_id };
      }
      
      // Refrescar estado después de un breve delay
      setTimeout(() => {
        obtenerEstadoLibroRemuneraciones(cierre.id).then((data) => {
          setLibro(data);
          if (data?.id) {
            setLibroId(data.id);
          }
        });
      }, 1200);
      
      return res;
    } catch (error) {
      console.error('❌ Error en subida:', error);
      throw error;
    } finally {
      console.log('🏁 Finalizando handleSubirArchivo, setSubiendo(false)');
      setSubiendo(false);
    }
  }, [cierre.id, subiendo]); // Estabilizar dependencias

  const handleSubirMovimientos = useCallback(async (archivo) => {
    setSubiendoMov(true);
    try {
      const formData = new FormData();
      formData.append("archivo", archivo);
      await subirMovimientosMes(cierre.id, formData);
      setTimeout(() => {
        obtenerEstadoMovimientosMes(cierre.id).then(setMovimientos);
      }, 1200);
    } finally {
      setSubiendoMov(false);
    }
  }, [cierre.id]);

  const handleProcesarLibro = useCallback(async () => {
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
      setLibroListo(false);
      
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
  }, [libro?.id, libroId]);

  const handleActualizarEstadoMovimientos = useCallback(async () => {
    try {
      console.log('📡 Consultando estado actual de movimientos...');
      const estadoActual = await obtenerEstadoMovimientosMes(cierre.id);
      console.log('📊 Estado movimientos recibido del servidor:', estadoActual);
      
      setMovimientos(estadoActual);
      
      if (estadoActual?.estado !== movimientos?.estado) {
        console.log(`🔄 Estado movimientos cambió de "${movimientos?.estado}" a "${estadoActual?.estado}"`);
      }
      
    } catch (error) {
      console.error('❌ Error actualizando estado movimientos:', error);
    }
  }, [cierre.id]);

  const handleActualizarEstado = useCallback(async () => {
    try {
      console.log('📡 Consultando estado actual del libro...');
      const estadoActual = await obtenerEstadoLibroRemuneraciones(cierre.id);
      console.log('📊 Estado recibido del servidor:', estadoActual);
      
      setLibro(estadoActual);
      
      if (estadoActual?.estado !== libro?.estado) {
        console.log(`🔄 Estado cambió de "${libro?.estado}" a "${estadoActual?.estado}"`);
      }
      
    } catch (error) {
      console.error('❌ Error actualizando estado:', error);
    }
  }, [cierre.id]); // Solo depende de cierre.id, no de libro

  const handleVerClasificacion = useCallback((soloLectura = false) => {
    setModoSoloLectura(soloLectura);
    setModalAbierto(true);
  }, []);

  const handleLibroCompletado = useCallback((ready) => {
    setLibroRemuneracionesReady(ready);
  }, [setLibroRemuneracionesReady]);

  const handleMovimientosCompletado = useCallback((ready) => {
    setMovimientosMesReady(ready);
  }, [setMovimientosMesReady]);

  const handleAnalistaCompletado = useCallback((ready) => {
    setArchivoAnalistaReady(ready);
  }, [setArchivoAnalistaReady]);

  const handleNovedadesCompletado = useCallback((ready) => {
    setArchivoNovedadesReady(ready);
  }, [setArchivoNovedadesReady]);

  let paso = 1;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* Paso 1: Libro de Remuneraciones */}
      <LibroRemuneracionesCardConLogging
        estado={libro?.estado || "no_subido"}
        archivoNombre={libro?.archivo ? libro.archivo.split("/").pop() : ""}
        onSubirArchivo={handleSubirArchivo}
        onVerClasificacion={() => handleVerClasificacion()}
        onProcesar={handleProcesarLibro}
        onActualizarEstado={handleActualizarEstado}
        headersSinClasificar={libro?.header_json?.headers_sin_clasificar || []}
        headerClasificados={libro?.header_json?.headers_clasificados || []}
        subiendo={subiendo}
        disabled={false}
        mensaje={mensajeLibro}
        onEliminarArchivo={() => {
          // Implementar eliminación si es necesario
          console.log("Eliminar archivo libro");
        }}
        libroId={libroId}
        onCompletado={handleLibroCompletado}
        numeroPaso={paso++}
      />

      {/* Paso 2: Movimientos del Mes */}
      <MovimientosMesCard
        estado={movimientos?.estado || "no_subido"}
        archivoNombre={movimientos?.archivo ? movimientos.archivo.split("/").pop() : ""}
        onSubirArchivo={handleSubirMovimientos}
        onActualizarEstado={handleActualizarEstadoMovimientos}
        subiendo={subiendoMov}
        disabled={!libroRemuneracionesReady}
        onCompletado={handleMovimientosCompletado}
        numeroPaso={paso++}
      />

      {/* Paso 3: Archivo Analista - Implementar cuando esté listo */}
      {/* <ArchivoAnalistaCard
        estado={archivoAnalista?.estado || "no_subido"}
        disabled={!movimientosMesReady}
        onCompletado={handleAnalistaCompletado}
        numeroPaso={paso++}
      /> */}

      {/* Paso 4: Archivo Novedades - Implementar cuando esté listo */}
      {/* <ArchivoNovedadesCard
        estado={archivoNovedades?.estado || "no_subido"}
        disabled={!archivoAnalistaReady}
        onCompletado={handleNovedadesCompletado}
        numeroPaso={paso++}
      /> */}

      {/* Modal de Clasificación */}
      <ModalClasificacionHeaders
        isOpen={modalAbierto}
        onClose={() => setModalAbierto(false)}
        clienteId={cliente.id}
        headersSinClasificar={libro?.header_json?.headers_sin_clasificar || []}
        onGuardarClasificaciones={handleGuardarClasificaciones}
        soloLectura={modoSoloLectura}
      />
    </div>
  );
};

export default CierreProgresoNominaConLogging;
