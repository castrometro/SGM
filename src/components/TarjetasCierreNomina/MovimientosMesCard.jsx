import { useState, useRef, useEffect } from "react";
import { Download, Loader2 } from "lucide-react";
import { descargarPlantillaMovimientosMes } from "../../api/nomina";
import EstadoBadge from "../EstadoBadge";
import { createActivityLogger } from "../../utils/activityLogger";

const MovimientosMesCard = ({
  estado,
  archivoNombre,
  onSubirArchivo,
  onActualizarEstado,
  onEliminarArchivo,
  subiendo = false,
  disabled = false,
  cierreId, // Nueva prop necesaria para logging
  deberiaDetenerPolling = false,
}) => {
  const fileInputRef = useRef();
  const pollingRef = useRef(null);
  const [error, setError] = useState("");
  const [eliminando, setEliminando] = useState(false);
  
  // Activity Logger
  const activityLogger = useRef(null);
  
  // Inicializar logger cuando tengamos cierreId
  useEffect(() => {
    if (cierreId && !activityLogger.current) {
      activityLogger.current = createActivityLogger(cierreId, 'movimientos_mes');
      // Registrar inicio de sesión
      activityLogger.current.logSessionStart();
    }
  }, [cierreId]);

  // Definir variables de estado inmediatamente después de las declaraciones de estado
  const isProcesando = estado === "en_proceso" || estado === "procesando";
  const isDisabled = disabled || subiendo || isProcesando;
  const isProcessed = estado === "procesado" || estado === "procesado_parcial";
  const puedeSubirArchivo = !isDisabled && 
    (estado === "no_subido" || estado === "pendiente" || estado === "con_error");
  const estadosConArchivoBloqueado = [
    "en_proceso",
    "procesado", 
    "con_errores_parciales"
  ];
  const archivoEsBloqueado = estadosConArchivoBloqueado.includes(estado);

  // Limpiar polling al desmontar
  useEffect(() => {
    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
        pollingRef.current = null;
      }
    };
  }, []);

  // Iniciar polling cuando el estado sea "en_proceso"
  useEffect(() => {
    console.log('🎯 MovimientosMes useEffect polling - estado actual:', estado, 'deberiaDetener:', deberiaDetenerPolling);
    
    // Detener polling si se debe detener globalmente
    if (deberiaDetenerPolling && pollingRef.current) {
      console.log('🛑 [MovimientosMesCard] Deteniendo polling - señal global de parada');
      if (activityLogger.current) {
        activityLogger.current.logPollingStop('señal global de parada');
      }
      clearInterval(pollingRef.current);
      pollingRef.current = null;
      return;
    }
    
    if (estado === "en_proceso" && !pollingRef.current && onActualizarEstado && !deberiaDetenerPolling) {
      console.log('🔄 Iniciando polling para monitorear procesamiento de movimientos...');
      
      // Logging: inicio de polling
      if (activityLogger.current) {
        activityLogger.current.logPollingStart(5);
      }
      
      console.log('🔄 [PAUSADO] Polling de MovimientosMesCard pausado temporalmente');
      
      // PAUSADO TEMPORALMENTE - COMENTADO
      // let contadorPolling = 0;
      // pollingRef.current = setInterval(async () => {
      //   contadorPolling++;
      //   try {
      //     console.log(`📡 MovimientosMes Polling #${contadorPolling} - Verificando estado...`);
      //     await onActualizarEstado();
      //   } catch (pollError) {
      //     console.error(`❌ Error en polling MovimientosMes #${contadorPolling}:`, pollError);
      //   }
      // }, 5000); // consultar cada 5 segundos (más frecuente que el libro)
      
    } else if ((estado !== "en_proceso" || deberiaDetenerPolling) && pollingRef.current) {
      console.log(`✅ MovimientosMes Estado cambió a "${estado}" o detención solicitada - deteniendo polling`);
      
      // Logging: detención de polling
      if (activityLogger.current) {
        activityLogger.current.logPollingStop(`estado cambió a ${estado} o detención solicitada`);
      }
      
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
  }, [estado, onActualizarEstado, deberiaDetenerPolling]);

  // 🧹 LIMPIEZA: Cleanup del polling al desmontar componente
  useEffect(() => {
    return () => {
      if (pollingRef.current) {
        console.log('🧹 [MovimientosMesCard] Limpiando polling al desmontar');
        clearInterval(pollingRef.current);
        pollingRef.current = null;
      }
    };
  }, []);

  const handleSeleccionArchivo = async (e) => {
    const archivo = e.target.files[0];
    if (!archivo) return;
    
    // Logging: selección de archivo
    if (activityLogger.current) {
      await activityLogger.current.logFileSelect(archivo.name, archivo.size);
    }
    
    setError("");
    try {
      await onSubirArchivo(archivo);
    } catch (err) {
      setError("Error al subir el archivo.");
    }
  };

  const handleEliminarArchivo = async () => {
    if (!onEliminarArchivo) return;
    
    setEliminando(true);
    try {
      await onEliminarArchivo();
    } catch (error) {
      console.error("Error al eliminar archivo:", error);
      setError("Error al eliminar archivo");
    } finally {
      setEliminando(false);
    }
  };

  return (
    <div className={`bg-gray-800 p-4 rounded-xl shadow-lg flex flex-col gap-3 ${isDisabled ? "opacity-60 pointer-events-none" : ""}`}>
      <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
        2. Movimientos del Mes
        {isProcesando && <Loader2 size={20} className="animate-spin text-blue-400" />}
      </h3>

      <div className="flex items-center gap-2 mb-2">
        <span className="font-semibold">Estado:</span>
        {isProcesando ? (
          <span className="text-blue-400 font-semibold flex items-center gap-1">
            <Loader2 size={16} className="animate-spin" /> Procesando...
          </span>
        ) : (
          <EstadoBadge estado={estado} />
        )}
      </div>

      <a
        href={descargarPlantillaMovimientosMes()}
        download
        className={`flex items-center gap-2 bg-gray-700 hover:bg-blue-600 px-3 py-1 rounded !text-white text-sm font-medium transition shadow w-fit mb-2 ${isDisabled ? "opacity-60 pointer-events-none" : ""}`}
        tabIndex={isDisabled ? -1 : 0}
        style={{ pointerEvents: isDisabled ? "none" : "auto" }}
        onClick={async () => {
          // Logging: descarga de plantilla
          if (activityLogger.current) {
            await activityLogger.current.logDownloadTemplate('movimientos_mes');
          }
        }}
      >
        <Download size={16} />
        Descargar Plantilla
      </a>

      <div className="flex gap-3 items-center">
        {/* Input de archivo oculto */}
        <input
          ref={fileInputRef}
          type="file"
          onChange={handleSeleccionArchivo}
          accept=".xlsx,.xls"
          className="hidden"
        />
        
        {/* ✅ BOTÓN DE SUBIDA CONDICIONAL */}
        {puedeSubirArchivo ? (
          <button
            type="button"
            onClick={async () => {
              // Logging: apertura de modal de selección
              if (activityLogger.current) {
                await activityLogger.current.logModalOpen('file_selector', {
                  trigger: 'user_click',
                  upload_type: 'movimientos_mes'
                });
              }
              
              fileInputRef.current.click();
            }}
            disabled={isDisabled}
            className={`bg-blue-600 hover:bg-blue-500 px-3 py-1 rounded text-sm font-medium transition ${isDisabled ? "opacity-60 cursor-not-allowed" : ""}`}
          >
            {isProcesando ? "Procesando..." : subiendo ? "Subiendo..." : "Elegir archivo .xlsx"}
          </button>
        ) : (
          <button
            type="button"
            disabled={true}
            className="bg-gray-600 px-3 py-1 rounded text-sm font-medium cursor-not-allowed opacity-60"
            title="El archivo ya fue procesado y no se puede cambiar"
          >
            Archivo bloqueado
          </button>
        )}
        
        <span className="text-gray-300 text-xs italic truncate max-w-xs">{archivoNombre || "Ningún archivo seleccionado"}</span>
        
        {/* Botón de eliminar/resubir solo si está procesado */}
        {isProcessed && onEliminarArchivo && (
          <button
            onClick={handleEliminarArchivo}
            disabled={eliminando || isDisabled}
            className="text-xs px-2 py-1 rounded bg-blue-600 hover:bg-blue-700 text-white ml-2"
            title="Eliminar archivo actual para permitir subir uno nuevo"
          >
            {eliminando ? "Eliminando..." : "Resubir archivo"}
          </button>
        )}
      </div>
      
      {/* ✅ INPUT DE ARCHIVO CONDICIONAL */}
      <input
        type="file"
        accept=".xlsx"
        ref={fileInputRef}
        style={{ display: "none" }}
        onChange={handleSeleccionArchivo}
        disabled={isDisabled || archivoEsBloqueado}
      />

      {error && <div className="text-xs text-red-400 mt-1">{error}</div>}

      {/* ✅ MENSAJE INFORMATIVO CUANDO EL ARCHIVO ESTÁ BLOQUEADO */}
      {archivoEsBloqueado && (
        <div className="text-xs text-yellow-400 mt-1 bg-yellow-900/20 p-2 rounded">
          ℹ️ El archivo ya fue procesado y no se puede cambiar. Si necesitas subir otro archivo, contacta al administrador.
        </div>
      )}

      <span className="text-xs text-gray-400 italic mt-2">
        {isProcesando
          ? "🔄 Procesando archivo, por favor espera…"
          : estado === "procesado" || estado === "con_errores_parciales"
          ? "✔ Archivo cargado correctamente y procesado."
          : estado === "error"
          ? "❌ Error al procesar el archivo."
          : "Aún no se ha subido el archivo."}
      </span>
    </div>
  );
};

export default MovimientosMesCard;
