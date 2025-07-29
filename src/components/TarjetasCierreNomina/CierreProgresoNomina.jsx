import { useEffect, useState } from "react";
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

  const esEstadoPosteriorAConsolidacion = (estado) => {
    const estadosPosteriores = [
      'datos_consolidados', 'con_incidencias', 'incidencias_resueltas', 'validacion_final', 'finalizado'
    ];
    return estadosPosteriores.includes(estado);
  };

  const esEstadoFinalizado = (estado) => {
    return estado === 'finalizado';
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
            disabled={esEstadoFinalizado(cierre.estado)}
          />
          
          {/* Sección 2: Archivos del Analista */}
          <ArchivosAnalistaSection
            cierreId={cierre.id}
            cliente={cliente}
            cierre={cierre}
            disabled={esEstadoPosteriorAConsolidacion(cierre.estado) || esEstadoFinalizado(cierre.estado)}
            onCierreActualizado={onCierreActualizado}
          />

          {/* Sección 3: Verificación de Datos (Discrepancias) */}
          <VerificadorDatosSection 
            cierre={cierre} 
            disabled={esEstadoPosteriorAConsolidacion(cierre.estado) || esEstadoFinalizado(cierre.estado)}
            onCierreActualizado={(nuevoCierre) => {
              // Callback para actualizar el cierre en el componente padre
              console.log('🔄 Cierre actualizado desde verificador:', nuevoCierre);
              // Aquí podrías refrescar el estado completo del cierre si fuera necesario
            }}
          />

          {/* Sección 4: Sistema de Incidencias */}
          <IncidenciasEncontradasSection 
            cierre={cierre} 
            disabled={esEstadoFinalizado(cierre.estado)}
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
