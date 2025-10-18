import { useState, useEffect, useCallback, useRef } from "react";
import { Database, ChevronDown, ChevronRight, Lock } from "lucide-react";
import LibroRemuneracionesCard from "../LibroRemuneracionesCard";
import MovimientosMesCard from "../MovimientosMesCard";
import ModalClasificacionHeaders from "../../ModalClasificacionHeaders";
import {
  obtenerEstadoLibroRemuneraciones,
  subirLibroRemuneraciones,
  procesarLibroRemuneraciones,
  eliminarLibroRemuneraciones,
  obtenerEstadoMovimientosMes,
  subirMovimientosMes,
  eliminarMovimientosMes,
  // 🎯 NUEVAS: Para manejo de clasificaciones
  guardarConceptosRemuneracion,
  eliminarConceptoRemuneracion,
} from "../../../api/nomina";

const ArchivosTalanaSection_v2 = ({
  // 🎯 Props mínimas - Diseño autónomo
  cierreId,                    // ID del cierre
  cliente,                     // Datos del cliente (necesario para clasificaciones)
  disabled = false,            // Si está bloqueada la sección
  onEstadoChange,             // Callback para reportar cambios de estado al padre
  expandido = true,           // Control de acordeón
  onToggleExpansion,          // Handler de acordeón
}) => {
  // 🎯 Estados internos - La sección maneja todo su estado
  const [libro, setLibro] = useState(null);
  const [libroId, setLibroId] = useState(null);
  const [subiendo, setSubiendo] = useState(false);
  const [movimientos, setMovimientos] = useState(null);
  const [subiendoMov, setSubiendoMov] = useState(false);
  const [libroListo, setLibroListo] = useState(false);
  const [mensajeLibro, setMensajeLibro] = useState("");
  
  // 🎯 NUEVOS: Estados para modal de clasificación
  const [modalAbierto, setModalAbierto] = useState(false);
  const [modoSoloLectura, setModoSoloLectura] = useState(false);
  
  // Control de polling
  const isMountedRef = useRef(true);

  // 🎯 Efecto de inicialización - Cargar datos al montar
  useEffect(() => {
    if (!cierreId) return;
    
    const cargarDatosIniciales = async () => {
      try {
        // Cargar libro y movimientos en paralelo
        const [libroData, movimientosData] = await Promise.all([
          obtenerEstadoLibroRemuneraciones(cierreId),
          obtenerEstadoMovimientosMes(cierreId)
        ]);
        
        if (isMountedRef.current) {
          setLibro(libroData);
          if (libroData?.id) {
            setLibroId(libroData.id);
          }
          setMovimientos(movimientosData);
        }
      } catch (error) {
        console.error('❌ Error cargando datos de Archivos Talana:', error);
      }
    };

    cargarDatosIniciales();
  }, [cierreId]);

  // 🎯 Detectar cuando libro está listo para procesar
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

  // 🎯 Reportar cambios de estado al componente padre
  useEffect(() => {
    if (!onEstadoChange) return;

    const estadoLibro = libro?.estado === "procesando" || libro?.estado === "procesado"
      ? libro?.estado
      : libroListo
      ? "clasificado"
      : libro?.estado || "no_subido";
      
    const estadoMovimientos = movimientos?.estado || "pendiente";
    
    // Determinar estado general de la sección
    const estadoGeneral = (estadoLibro === "procesado" && estadoMovimientos === "procesado") 
      ? "procesado" 
      : "pendiente";
    
    onEstadoChange(estadoGeneral);
  }, [libro, movimientos, libroListo, onEstadoChange]);

  // 🎯 Handlers internos - Libro de Remuneraciones
  const handleSubirArchivo = useCallback(async (archivo) => {
    if (!cierreId) return;
    
    setSubiendo(true);
    try {
      const res = await subirLibroRemuneraciones(cierreId, archivo);
      if (res?.id) {
        setLibroId(res.id);
      }
      
      // Actualizar estado después de subir
      setTimeout(async () => {
        if (isMountedRef.current) {
          const nuevoEstado = await obtenerEstadoLibroRemuneraciones(cierreId);
          setLibro(nuevoEstado);
          if (nuevoEstado?.id) {
            setLibroId(nuevoEstado.id);
          }
        }
      }, 1000);
    } catch (error) {
      console.error('❌ Error subiendo archivo:', error);
    } finally {
      setSubiendo(false);
    }
  }, [cierreId]);

  const handleProcesarLibro = useCallback(async () => {
    const id = libro?.id || libroId;
    if (!id) return;
    
    try {
      // Forzar estado "procesando" antes de la llamada
      setLibro(prev => ({ ...prev, estado: "procesando" }));
      setLibroListo(false);
      
      await procesarLibroRemuneraciones(id);
    } catch (error) {
      console.error("❌ Error al procesar libro:", error);
      setMensajeLibro("Error al procesar libro");
      setLibro(prev => ({ ...prev, estado: "con_error" }));
    }
  }, [libro?.id, libroId]);

  const handleActualizarEstado = useCallback(async () => {
    if (!cierreId || !isMountedRef.current) return;
    
    try {
      const estadoActual = await obtenerEstadoLibroRemuneraciones(cierreId);
      if (isMountedRef.current) {
        setLibro(estadoActual);
      }
    } catch (error) {
      console.error('❌ Error actualizando estado libro:', error);
    }
  }, [cierreId]);

  const handleEliminarLibro = useCallback(async () => {
    if (!libro?.id) return;
    
    try {
      await eliminarLibroRemuneraciones(libro.id);
      setLibro(null);
      setLibroId(null);
      setLibroListo(false);
    } catch (error) {
      console.error("❌ Error eliminando libro:", error);
    }
  }, [libro?.id]);

  // 🎯 Handlers internos - Movimientos del Mes
  const handleSubirMovimientos = useCallback(async (archivo) => {
    if (!cierreId) return;
    
    setSubiendoMov(true);
    try {
      const formData = new FormData();
      formData.append("archivo", archivo);
      await subirMovimientosMes(cierreId, formData);
      
      setTimeout(async () => {
        if (isMountedRef.current) {
          const nuevoEstado = await obtenerEstadoMovimientosMes(cierreId);
          setMovimientos(nuevoEstado);
        }
      }, 1000);
    } catch (error) {
      console.error('❌ Error subiendo movimientos:', error);
    } finally {
      setSubiendoMov(false);
    }
  }, [cierreId]);

  const handleActualizarEstadoMovimientos = useCallback(async () => {
    if (!cierreId || !isMountedRef.current) return;
    
    try {
      const estado = await obtenerEstadoMovimientosMes(cierreId);
      if (isMountedRef.current) {
        setMovimientos(estado);
      }
    } catch (error) {
      console.error("❌ Error actualizando movimientos:", error);
    }
  }, [cierreId]);

  const handleEliminarMovimientos = useCallback(async () => {
    if (!movimientos?.id) return;
    
    try {
      await eliminarMovimientosMes(movimientos.id);
      setMovimientos(null);
    } catch (error) {
      console.error("❌ Error eliminando movimientos:", error);
    }
  }, [movimientos?.id]);

  // 🎯 Placeholder handlers para funciones que necesitan implementación adicional
  const handleVerClasificacion = useCallback((soloLectura = false) => {
    console.log('🎯 Abriendo modal de clasificación, modo solo lectura:', !!soloLectura);
    setModalAbierto(true);
    setModoSoloLectura(!!soloLectura);
  }, []);

  // 🎯 Handler para guardar clasificaciones
  const handleGuardarClasificaciones = useCallback(async ({ guardar, eliminar }) => {
    if (!cliente?.id || !cierreId) return;
    
    try {
      console.log('� Guardando clasificaciones:', { guardar, eliminar });
      
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

      // Refrescamos el estado del libro
      const nuevoEstado = await obtenerEstadoLibroRemuneraciones(cierreId);
      if (isMountedRef.current) {
        setLibro(nuevoEstado);
        if (nuevoEstado?.id) {
          setLibroId(nuevoEstado.id);
        }
      }
      
      console.log('✅ Clasificaciones guardadas exitosamente');
    } catch (error) {
      console.error("❌ Error al guardar clasificaciones:", error);
      setMensajeLibro("Error al guardar clasificaciones");
    }
  }, [cliente?.id, cierreId]);

  // Cleanup al desmontar
  useEffect(() => {
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  // 🎯 Estados calculados para renderizado
  // 🎯 Estados calculados para renderizado
  const estadoLibro = libro?.estado === "procesando" || libro?.estado === "procesado"
    ? libro?.estado
    : libroListo
    ? "clasificado"
    : libro?.estado || "no_subido";
    
  const estadoMovimientos = movimientos?.estado || "pendiente";
  
  // Determinar el estado general: Procesado si ambos están procesados, Pendiente en cualquier otro caso
  const estadoGeneral = (estadoLibro === "procesado" && estadoMovimientos === "procesado") 
    ? "Procesado" 
    : "Pendiente";
  
  const colorEstado = estadoGeneral === "Procesado" ? "text-green-400" : "text-yellow-400";

  // Headers sin clasificar para el componente hijo
  const headersSinClasificar = Array.isArray(libro?.header_json?.headers_sin_clasificar)
    ? libro.header_json.headers_sin_clasificar
    : [];

  return (
    <section className="w-full space-y-6">
      {/* Header de la sección - ahora clicable (solo si no está disabled) */}
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
            disabled ? 'bg-gray-600' : 'bg-blue-600'
          }`}>
            {disabled ? (
              <Lock size={20} className="text-white" />
            ) : (
              <Database size={20} className="text-white" />
            )}
          </div>
          <div>
            <h2 className={`text-xl font-semibold ${disabled ? 'text-gray-400' : 'text-white'}`}>
              Archivos Talana V2
              {disabled && (
                <span className="ml-2 text-sm font-normal text-gray-500">
                  (Bloqueado)
                </span>
              )}
            </h2>
            <p className="text-gray-400 text-sm">
              {disabled 
                ? 'Sección bloqueada'
                : 'Archivos principales del sistema Talana (Autónomo)'
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
          <LibroRemuneracionesCard
            estado={estadoLibro}
            archivoNombre={libro?.archivo_nombre}
            subiendo={subiendo}
            onSubirArchivo={handleSubirArchivo}
            onVerClasificacion={handleVerClasificacion}
            onProcesar={handleProcesarLibro}
            onActualizarEstado={handleActualizarEstado}
            onEliminarArchivo={handleEliminarLibro}
            libroId={libro?.id}
            headersSinClasificar={headersSinClasificar}
            headerClasificados={libro?.header_json?.headers_clasificados || []}
            mensaje={mensajeLibro}
            disabled={disabled || libro?.estado === "procesando"}
            deberiaDetenerPolling={disabled}
            cierreId={cierreId}
            clienteId={cliente?.id}
          />
          
          <MovimientosMesCard
            estado={estadoMovimientos}
            archivoNombre={movimientos?.archivo ? movimientos.archivo.split('/').pop() : null}
            subiendo={subiendoMov}
            onSubirArchivo={handleSubirMovimientos}
            onActualizarEstado={handleActualizarEstadoMovimientos}
            onEliminarArchivo={handleEliminarMovimientos}
            disabled={disabled}
            deberiaDetenerPolling={disabled}
            cierreId={cierreId}
          />
        </div>
      )}
      
      {/* 🎯 Modal de clasificación */}
      {modalAbierto && (
        <ModalClasificacionHeaders
          isOpen={modalAbierto}
          onClose={() => setModalAbierto(false)}
          clienteId={cliente?.id}
          headersSinClasificar={headersSinClasificar}
          onGuardarClasificaciones={handleGuardarClasificaciones}
          soloLectura={modoSoloLectura}
        />
      )}
    </section>
  );
};

export default ArchivosTalanaSection_v2;
