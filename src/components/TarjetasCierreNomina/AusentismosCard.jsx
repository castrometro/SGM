import { useState, useRef, useEffect } from "react";
import { Download, Loader2, CheckCircle2 } from "lucide-react";
import { descargarPlantillaAusentismos } from "../../api/nomina";
import EstadoBadge from "../EstadoBadge";
import { createActivityLogger } from "../../utils/activityLogger";

const AusentismosCard = ({
  estado,
  archivoNombre,
  onSubirArchivo,
  onActualizarEstado,
  onEliminarArchivo,
  subiendo = false,
  disabled = false,
  cierreId,
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
      activityLogger.current = createActivityLogger(cierreId, 'ausentismos');
      activityLogger.current.logSessionStart();
    }
  }, [cierreId]);

  // Variables de estado unificadas
  const isProcesando = estado === "en_proceso";
  const nombreArchivoActual = archivoNombre;
  
  // Determinar si la tarjeta está deshabilitada
  const isDisabled = disabled || subiendo || isProcesando;
  
  // Determinar si ya está procesado
  const isProcessed = estado === "procesado" || estado === "con_errores_parciales";
  
  // Lógica de interacción con archivo
  const puedeInteractuarConArchivo = !isDisabled && !isProcesando;
  
  // Determinar si hay archivo
  const tieneArchivo = Boolean(archivoNombre);

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
    console.log('🎯 Ausentismos useEffect polling - estado actual:', estado, 'deberiaDetener:', deberiaDetenerPolling);
    
    // Detener polling si se debe detener globalmente
    if (deberiaDetenerPolling && pollingRef.current) {
      console.log('🛑 [AusentismosCard] Deteniendo polling - señal global de parada');
      if (activityLogger.current) {
        activityLogger.current.logPollingStop('señal global de parada');
      }
      clearInterval(pollingRef.current);
      pollingRef.current = null;
      return;
    }
    
    if (estado === "en_proceso" && !pollingRef.current && onActualizarEstado && !deberiaDetenerPolling) {
      console.log('🔄 Iniciando polling para monitorear procesamiento de ausentismos...');
      
      if (activityLogger.current) {
        activityLogger.current.logPollingStart(5);
      }
      
      let contadorPolling = 0;
      let contadorErrores = 0;
      
      pollingRef.current = setInterval(async () => {
        contadorPolling++;
        try {
          console.log(`📡 Ausentismos Polling #${contadorPolling} - Verificando estado...`);
          await onActualizarEstado();
          contadorErrores = 0;
        } catch (pollError) {
          contadorErrores++;
          console.error(`❌ Error en polling Ausentismos #${contadorPolling} (${contadorErrores}/3):`, pollError);
          
          if (contadorErrores >= 3) {
            console.log('🛑 Demasiados errores consecutivos, deteniendo polling por seguridad');
            clearInterval(pollingRef.current);
            pollingRef.current = null;
          }
        }
      }, 5000);
      
    } else if ((estado !== "en_proceso" || deberiaDetenerPolling) && pollingRef.current) {
      console.log(`✅ Ausentismos Estado cambió a "${estado}" o detención solicitada - deteniendo polling`);
      
      if (activityLogger.current) {
        activityLogger.current.logPollingStop(`estado cambió a ${estado} o detención solicitada`);
      }
      
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
  }, [estado, onActualizarEstado, deberiaDetenerPolling]);

  const handleSeleccionArchivo = async (e) => {
    const archivo = e.target.files[0];
    if (!archivo) return;
    
    if (activityLogger.current) {
      await activityLogger.current.logFileSelect(archivo.name, archivo.size);
    }
    
    setError("");
    try {
      console.log('📁 Iniciando subida de archivo Ausentismos:', archivo.name);
      await onSubirArchivo(archivo);
      console.log('✅ Archivo Ausentismos subido exitosamente');
      
      if (onActualizarEstado) {
        console.log('🔄 Forzando actualización de estado post-subida Ausentismos...');
        setTimeout(() => {
          onActualizarEstado();
        }, 500);
      }
      
    } catch (err) {
      console.log('🔍 Error completo:', err);
      
      let errorMessage = "Error al subir el archivo.";
      
      if (err?.response?.data) {
        const data = err.response.data;
        if (data.detail) {
          errorMessage = data.detail;
        } else if (data.message) {
          errorMessage = data.message;
        } else if (data.error) {
          errorMessage = data.error;
        } else if (Array.isArray(data)) {
          errorMessage = data[0];
        } else if (typeof data === 'string') {
          errorMessage = data;
        } else if (data.non_field_errors) {
          errorMessage = Array.isArray(data.non_field_errors) 
            ? data.non_field_errors[0] 
            : data.non_field_errors;
        }
      } else if (err?.message) {
        errorMessage = err.message;
      }
      
      setError(errorMessage);
      console.error('Error subiendo archivo Ausentismos:', err);
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
        3. Ausentismos/Incidencias
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
        href={descargarPlantillaAusentismos()}
        download
        className={`flex items-center gap-2 bg-gray-700 hover:bg-blue-600 px-3 py-1 rounded !text-white text-sm font-medium transition shadow w-fit mb-2 ${isDisabled ? "opacity-60 pointer-events-none" : ""}`}
        tabIndex={isDisabled ? -1 : 0}
        style={{ pointerEvents: isDisabled ? "none" : "auto" }}
        onClick={async () => {
          if (activityLogger.current) {
            await activityLogger.current.logDownloadTemplate('ausentismos');
          }
        }}
      >
        <Download size={16} />
        Descargar Plantilla
      </a>

      <div className="flex gap-3 items-center">
        {puedeInteractuarConArchivo ? (
          <button
            type="button"
            onClick={() => {
              if (tieneArchivo && onEliminarArchivo) {
                handleEliminarArchivo();
              } else {
                fileInputRef.current.click();
              }
            }}
            disabled={isDisabled || eliminando}
            className={`px-3 py-1 rounded text-sm font-medium transition ${
              isDisabled ? "opacity-60 cursor-not-allowed" : ""
            } ${
              tieneArchivo 
                ? (isProcessed ? "bg-blue-600 hover:bg-blue-700" : "bg-orange-600 hover:bg-orange-700")
                : "bg-green-600 hover:bg-green-700"
            }`}
            title={
              tieneArchivo 
                ? (isProcessed ? "Resubir archivo - eliminará datos procesados" : "Reemplazar archivo actual")
                : "Seleccionar archivo Excel"
            }
          >
            {eliminando ? "Eliminando..." : 
             subiendo ? "Subiendo..." :
             tieneArchivo ? (isProcessed ? "Resubir archivo" : "Reemplazar archivo") : "Elegir archivo"}
          </button>
        ) : (
          <button
            type="button"
            disabled={true}
            className="bg-gray-600 px-3 py-1 rounded text-sm font-medium cursor-not-allowed opacity-75"
            title="Archivo en procesamiento, espera a que termine"
          >
            Procesando...
          </button>
        )}
        
        <span className="text-gray-300 text-xs italic truncate max-w-xs">
          {archivoNombre || "Ningún archivo seleccionado"}
        </span>
      </div>
      
      <input
        type="file"
        accept=".xlsx"
        ref={fileInputRef}
        style={{ display: "none" }}
        onChange={handleSeleccionArchivo}
        disabled={isDisabled || !puedeInteractuarConArchivo}
      />

      {error && (
        <div className="text-xs text-red-400 mt-1 bg-red-900/20 p-2 rounded border-l-2 border-red-400">
          ❌ <strong>Error:</strong> {error}
        </div>
      )}

      {(estado === "no_subido" || estado === "pendiente") && (
        <div className="text-xs text-blue-400 mt-1 bg-blue-900/20 p-2 rounded">
          📋 <strong>Formato requerido:</strong> AAAAAMM_ausentismos_RUT.xlsx
          <br />
          <span className="text-blue-300">Ejemplo: 202508_ausentismos_12345678.xlsx</span>
        </div>
      )}

      {!puedeInteractuarConArchivo && tieneArchivo && (
        <div className="text-xs text-yellow-400 mt-1 bg-yellow-900/20 p-2 rounded border-l-2 border-yellow-400">
          🔒 <strong>Archivo procesado:</strong> Este archivo ya fue procesado exitosamente.
          <br />
          <span className="text-yellow-300">Si necesitas cambiar el archivo, contacta al administrador.</span>
        </div>
      )}

      {isProcesando && (
        <div className="text-xs text-orange-400 mt-1 bg-orange-900/20 p-2 rounded border-l-2 border-orange-400">
          ⏳ <strong>Procesamiento en curso:</strong> El archivo se está procesando actualmente.
          <br />
          <span className="text-orange-300">Espera a que termine para poder cambiar el archivo si es necesario.</span>
        </div>
      )}

      {isProcessed && tieneArchivo && (
        <div className="mt-2 text-xs text-green-400 bg-green-900/20 p-2 rounded flex items-center gap-2">
          <CheckCircle2 size={16} />
          <strong>Archivo procesado:</strong> El procesamiento se completó exitosamente
        </div>
      )}

      <span className="text-xs text-gray-400 italic mt-2 block">
        {isProcesando
          ? "🔄 Procesando archivo, por favor espera..."
          : estado === "procesado" || estado === "con_errores_parciales"
          ? "✅ Archivo procesado exitosamente"
          : estado === "error"
          ? "❌ Error al procesar el archivo. Revisa los detalles arriba."
          : estado === "pendiente"
          ? `📋 Archivo listo: ${nombreArchivoActual} - Esperando procesamiento`
          : "📁 Ningún archivo seleccionado aún"}
      </span>
    </div>
  );
};

export default AusentismosCard;
