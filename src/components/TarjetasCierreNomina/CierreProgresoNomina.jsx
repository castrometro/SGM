import { useEffect, useState } from "react";
import ArchivosTalanaSection from "./ArchivosTalanaSection";
import ArchivosAnalistaSection from "./ArchivosAnalistaSection";
import VerificadorDatosSection from "./VerificadorDatosSection";
import IncidenciasEncontradasSection from "./IncidenciasEncontradasSection";
import ModalClasificacionHeaders from "../ModalClasificacionHeaders";
import {
  obtenerEstadoLibroRemuneraciones,
  obtenerHeadersClasificacion,
  guardarMapeosManualesRedis,
  eliminarMapeoManualRedis,
  subirLibroRemuneraciones,
  procesarLibroRemuneraciones,
  eliminarLibroRemuneraciones,
  obtenerEstadoMovimientosMes,
  subirMovimientosMes,
  eliminarMovimientosMes,
  guardarConceptosRemuneracion,
  eliminarConceptoRemuneracion,
} from "../../api/nomina";

const CierreProgresoNomina = ({ cierre, cliente }) => {
  const [libro, setLibro] = useState(null);
  const [libroId, setLibroId] = useState(null);
  const [subiendo, setSubiendo] = useState(false);
  const [movimientos, setMovimientos] = useState(null);
  const [subiendoMov, setSubiendoMov] = useState(false);
  const [modalAbierto, setModalAbierto] = useState(false);
  const [libroListo, setLibroListo] = useState(false);
  const [mensajeLibro, setMensajeLibro] = useState("");
  const [modoSoloLectura, setModoSoloLectura] = useState(false);
  const [headersParaModal, setHeadersParaModal] = useState([]);

  const handleGuardarClasificaciones = async ({ guardar, eliminar }) => {
    try {
      console.log('💾 Operación CRUD en mapeos: Redis (PHASE 1) + BD (permanente):', { guardar, eliminar });
      
      // ===== OPERACIÓN CREATE/UPDATE =====
      const mapeosPorGuardar = guardar || {};
      if (Object.keys(mapeosPorGuardar).length > 0) {
        // Usar el nuevo endpoint que guarda en Redis + BD
        const resultado = await guardarMapeosManualesRedis(cierre.id, mapeosPorGuardar);
        console.log('✅ Mapeos guardados exitosamente:', resultado);
        
        // Mostrar confirmación de memoria permanente
        if (resultado.data?.memoria_permanente) {
          console.log(`🧠 MEMORIA PERMANENTE: ${resultado.data.mapeos_guardados_bd} mapeos guardados en BD para futuros cierres`);
        }
      }
      
      // ===== OPERACIÓN DELETE =====
      if (Array.isArray(eliminar) && eliminar.length > 0) {
        console.log(`🗑️ Eliminando ${eliminar.length} mapeos...`);
        
        for (const headerName of eliminar) {
          try {
            const resultadoEliminar = await eliminarMapeoManualRedis(cierre.id, headerName);
            console.log(`✅ Eliminado: ${headerName}`, resultadoEliminar);
          } catch (error) {
            console.error(`❌ Error eliminando ${headerName}:`, error);
          }
        }
      }
      
      // ===== ACTUALIZAR ESTADO =====
      // Actualizar estado del libro después de todas las operaciones
      const nuevoEstado = await obtenerEstadoLibroRemuneraciones(cierre.id);
      setLibro(nuevoEstado);
      
      // Mostrar información del progreso
      if (nuevoEstado?.estado === 'listo_procesar') {
        console.log('🎯 ¡Todos los headers mapeados! Libro listo para procesar');
      } else if (nuevoEstado?.estado === 'mapeo_requerido') {
        console.log(`⚠️ Aún quedan headers por mapear`);
      }
      
    } catch (error) {
      console.error("❌ Error en operaciones CRUD de mapeos:", error);
      throw error; // Re-lanzar para que el modal pueda manejar el error
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

  const handleSubirArchivo = async (archivo) => {
    setSubiendo(true);
    try {
      const res = await subirLibroRemuneraciones(cierre.id, archivo);
      if (res?.id) {
        setLibroId(res.id);
      }
      setTimeout(() => {
        obtenerEstadoLibroRemuneraciones(cierre.id).then((data) => {
          setLibro(data);
          if (data?.id) {
            setLibroId(data.id);
          }
        });
      }, 1200);
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
      setTimeout(() => {
        obtenerEstadoMovimientosMes(cierre.id).then(setMovimientos);
      }, 1200);
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

  const handleActualizarEstadoMovimientos = async () => {
    try {
      const estado = await obtenerEstadoMovimientosMes(cierre.id);
      setMovimientos(estado);
    } catch (error) {
      console.error("Error al actualizar estado de movimientos:", error);
    }
  };

  const handleActualizarEstado = async () => {
    try {
      console.log('📡 Consultando estado actual del libro...');
      const estadoActual = await obtenerEstadoLibroRemuneraciones(cierre.id);
      console.log('📊 Estado recibido del servidor:', estadoActual);
      console.log('📊 Estado anterior:', libro?.estado);
      console.log('📊 Estado nuevo:', estadoActual?.estado);
      
      setLibro(estadoActual);
      
      // Log adicional para verificar el cambio
      if (estadoActual?.estado !== libro?.estado) {
        console.log(`🔄 Estado cambió de "${libro?.estado}" a "${estadoActual?.estado}"`);
      }
      
    } catch (error) {
      console.error('❌ Error actualizando estado:', error);
    }
  };

  const handleVerClasificacion = async (soloLectura = false) => {
    // Si el libro ya está procesado, forzar modo solo lectura
    const esSoloLectura = soloLectura || libro?.estado === "procesado";
    
    // Si el libro fue analizado (tiene análisis en Redis), obtener headers del endpoint
    const tieneAnalisis = libro?.estado && ['mapeo_requerido', 'listo_procesar', 'procesando', 'procesado', 'fase1_completa'].includes(libro.estado);
    
    if (tieneAnalisis) {
      try {
        console.log(`🔄 Obteniendo headers de Redis para estado: ${libro.estado}`);
        const headersData = await obtenerHeadersClasificacion(cierre.id);
        console.log('🔄 Headers obtenidos del endpoint:', headersData);
        
        // Usar headers_sin_clasificar para el modal (tanto en modo edición como solo lectura)
        setHeadersParaModal(headersData.headers_sin_clasificar || []);
      } catch (error) {
        console.error('Error obteniendo headers para modal:', error);
        // Fallback a headers locales si hay error
        setHeadersParaModal(headersSinClasificar);
      }
    } else {
      // Si no hay análisis aún, usar headers locales (no debería suceder normalmente)
      console.log('📝 Usando headers locales - no hay análisis en Redis aún');
      setHeadersParaModal(headersSinClasificar);
    }
    
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

  return (
    <div className="space-y-10">
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
      />
      
      {/* Sección 2: Archivos del Analista */}
      <ArchivosAnalistaSection
        cierreId={cierre.id}
        cliente={cliente}
        disabled={false}
      />

      {/* Sección 3: Verificación de Datos (Discrepancias) */}
      <VerificadorDatosSection cierre={cierre} />

      {/* Sección 4: Sistema de Incidencias */}
      <IncidenciasEncontradasSection cierre={cierre} />

      <ModalClasificacionHeaders
        isOpen={modalAbierto}
        onClose={() => setModalAbierto(false)}
        clienteId={cliente.id}
        cierreId={cierre.id}
        headersSinClasificar={headersParaModal}
        onGuardarClasificaciones={handleGuardarClasificaciones}
        soloLectura={modoSoloLectura}
      />
    </div>
  );
};

export default CierreProgresoNomina;
