import { useEffect, useState } from "react";
import LibroRemuneracionesCard from "./LibroRemuneracionesCard";
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
    if (sinClasificar && !libroListo) {
      setLibroListo(true);
    } else if (!sinClasificar && libroListo) {
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

  const headersSinClasificar = Array.isArray(libro?.header_json?.headers_sin_clasificar)
    ? libro.header_json.headers_sin_clasificar
    : [];

  const headersClasificados =
    Array.isArray(libro?.header_json?.headers_clasificados)
      ? libro.header_json.headers_clasificados.reduce((acc, header) => {
          acc[header] = {
            clasificacion: "haber", // por defecto si no tienes info real
            hashtags: [],
          };
          return acc;
        }, {})
      : {};

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
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      <LibroRemuneracionesCard
        estado={
          libroListo ? "clasificado" : libro?.estado || "no_subido"
        }
        archivoNombre={libro?.archivo_nombre}
        subiendo={subiendo}
        onSubirArchivo={handleSubirArchivo}
        onVerClasificacion={handleVerClasificacion}
        onProcesar={handleProcesarLibro}
        onActualizarEstado={handleActualizarEstado}
        libroId={libro?.id} // ← Agregar verificación de nulidad
        headersSinClasificar={headersSinClasificar}
        headerClasificados={Object.keys(headersClasificados)}
        mensaje={mensajeLibro}
        disabled={libro?.estado === "procesando"}
      />
      <MovimientosMesCard
        estado={estadoMovimientos}
        archivoNombre={movimientos?.archivo_nombre}
        subiendo={subiendoMov}
        onSubirArchivo={handleSubirMovimientos}
        disabled={false}
      />
      <ModalClasificacionHeaders
        isOpen={modalAbierto}
        onClose={() => setModalAbierto(false)}
        clienteId={cliente.id}
        headersSinClasificar={headersSinClasificar}
        onGuardarClasificaciones={handleGuardarClasificaciones}
        soloLectura={modoSoloLectura}
      />
      {/* Botón temporal para debug */}
      <button onClick={debugEstado} className="bg-red-500 p-2">
        DEBUG Estado
      </button>
    </div>
  );
};

export default CierreProgresoNomina;
