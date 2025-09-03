import { useState, useRef, useEffect } from "react";
import { Download, FileBarChart2, CheckCircle2, Loader2, Settings } from "lucide-react";
import { descargarPlantillaNovedades, obtenerHeadersNovedades, mapearHeadersNovedades } from "../../api/nomina";
import EstadoBadge from "../EstadoBadge";
import ModalMapeoNovedades from "../ModalMapeoNovedades";

const NovedadesCard = ({
  estado,
  archivoNombre,
  onSubirArchivo,
  onVerClasificacion,
  onProcesar,
  onActualizarEstado,
  headersSinClasificar = [],
  headerClasificados = [],
  subiendo = false,
  disabled = false,
  mensaje = "",
  onEliminarArchivo,
  novedadesId,
  cierreId,
  deberiaDetenerPolling = false,
}) => {
  const fileInputRef = useRef();
  const pollingRef = useRef(null);

  // Estado local para errores y procesamiento
  const [error, setError] = useState("");
  const [eliminando, setEliminando] = useState(false);
  const [procesandoLocal, setProcesandoLocal] = useState(false);

  // Estados para modal de mapeo
  const [modalMapeoAbierto, setModalMapeoAbierto] = useState(false);
  const [headersData, setHeadersData] = useState({
    headers_clasificados: [],
    headers_sin_clasificar: [],
    mapeos_existentes: {}
  });

  // Limpiar polling al desmontar
  useEffect(() => {
    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
        pollingRef.current = null;
      }
    };
  }, []);

  // Polling para estados que lo requieren
  useEffect(() => {
    console.log('🎯 Novedades useEffect polling - estado actual:', estado, 'deberiaDetener:', deberiaDetenerPolling);
    
    // Detener polling si se debe detener globalmente
    if (deberiaDetenerPolling && pollingRef.current) {
      console.log('🛑 [NovedadesCard] Deteniendo polling - señal global de parada');
      clearInterval(pollingRef.current);
      pollingRef.current = null;
      setProcesandoLocal(false);
      return;
    }
    
    const estadosQueRequierenPolling = [
      "no_subido",
      "pendiente",
      "analizando_hdrs",
      "hdrs_analizados", 
      "clasif_en_proceso",
      "procesando"
    ];
    
    const deberiaHacerPolling = estadosQueRequierenPolling.includes(estado);
    
    if (deberiaHacerPolling && !pollingRef.current && onActualizarEstado && !deberiaDetenerPolling) {
      console.log(`🚀 Iniciando polling para estado: "${estado}" (archivo: ${archivoNombre || 'ninguno'})`);
      
      let contadorPolling = 0;
      let contadorErrores = 0;
      
      pollingRef.current = setInterval(async () => {
        contadorPolling++;
        try {
          console.log(`📡 Novedades Polling #${contadorPolling} - Verificando estado desde "${estado}"...`);
          await onActualizarEstado();
          contadorErrores = 0;
        } catch (pollError) {
          contadorErrores++;
          console.error(`❌ Error en polling Novedades #${contadorPolling} (${contadorErrores}/3):`, pollError);
          
          if (contadorErrores >= 3) {
            console.log('🛑 Demasiados errores consecutivos, deteniendo polling por seguridad');
            clearInterval(pollingRef.current);
            pollingRef.current = null;
          }
        }
      }, 3000);
      
    } else if ((!deberiaHacerPolling || deberiaDetenerPolling) && pollingRef.current) {
      console.log(`✅ Novedades Estado cambió a "${estado}" o detención solicitada - deteniendo polling`);
      clearInterval(pollingRef.current);
      pollingRef.current = null;
      setProcesandoLocal(false);
      
      // ✅ MEJORA: Ejecutar una verificación final para asegurar que se actualizó el estado
      if (!deberiaDetenerPolling && onActualizarEstado) {
        console.log('🔄 Ejecutando verificación final tras detener polling...');
        setTimeout(() => {
          onActualizarEstado();
        }, 1000);
      }
    }
  }, [estado, onActualizarEstado, deberiaDetenerPolling]);

  // Cleanup del polling al desmontar componente
  useEffect(() => {
    return () => {
      if (pollingRef.current) {
        console.log('🧹 [NovedadesCard] Limpiando polling al desmontar');
        clearInterval(pollingRef.current);
        pollingRef.current = null;
      }
    };
  }, []);

  // Handler de subida
  const handleSeleccionArchivo = async (e) => {
    const archivo = e.target.files[0];
    if (!archivo) return;
    setError("");
    try {
      console.log('📁 Iniciando subida de archivo Novedades:', archivo.name);
      await onSubirArchivo(archivo);
      console.log('✅ Archivo Novedades subido exitosamente');
      
      if (onActualizarEstado) {
        console.log('🔄 Forzando actualización de estado post-subida Novedades...');
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
      console.error('Error subiendo archivo Novedades:', err);
    }
  };

  // Handler de eliminar
  const handleEliminarArchivo = async () => {
    setEliminando(true);
    setError("");
    try {
      await onEliminarArchivo();
    } catch (err) {
      setError("Error eliminando el archivo.");
    } finally {
      setEliminando(false);
    }
  };

  // Handler de procesar
  const handleProcesar = async () => {
    if (!onProcesar) return;
    
    setProcesandoLocal(true);
    setError("");
    
    try {
      console.log('🔄 Iniciando procesamiento Novedades...');
      await onProcesar();
      console.log('✅ Procesamiento Novedades iniciado exitosamente');
    } catch (err) {
      setProcesandoLocal(false);
      setError("Error al procesar el archivo.");
      console.error('❌ Error al procesar Novedades:', err);
    }
  };

  // Handlers del modal de mapeo
  const handleAbrirModalMapeo = async () => {
    if (!novedadesId) return;
    
    try {
      const data = await obtenerHeadersNovedades(novedadesId);
      setHeadersData(data);
      setModalMapeoAbierto(true);
    } catch (error) {
      console.error('Error obteniendo headers para mapeo:', error);
      setError('Error al cargar headers para mapeo');
    }
  };

  const handleGuardarMapeos = async (mapeos) => {
    try {
      await mapearHeadersNovedades(novedadesId, mapeos);
      
      // Actualizar estado después del mapeo
      if (onActualizarEstado) {
        setTimeout(() => {
          onActualizarEstado();
        }, 500);
      }
    } catch (error) {
      console.error('Error guardando mapeos:', error);
      throw error;
    }
  };

  // Determinar si la tarjeta está deshabilitada
  const isDisabled = disabled || procesandoLocal || subiendo;
  
  // Determinar si ya está procesado
  const isProcessed = estado === "procesado";
  
  // Determinar si está procesando (estado del servidor O estado local)
  const isProcesando = estado === "procesando" || procesandoLocal;

  // Lógica de interacción con archivo
  const puedeInteractuarConArchivo = !isDisabled && !isProcesando;
  
  // Determinar si hay archivo
  const tieneArchivo = Boolean(archivoNombre);
  
  // Determinar si puede procesar
  const puedeProcesr = tieneArchivo && estado === "clasificado" && !isProcesando && !isProcessed;

  return (
    <div className={`bg-gray-800 p-4 rounded-xl shadow-lg flex flex-col gap-3 ${isDisabled ? "opacity-60 pointer-events-none" : ""}`}>
      <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
        4. Novedades
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

      {/* Botón de descarga de plantilla */}
      <a
        href={descargarPlantillaNovedades()}
        download
        className={`flex items-center gap-2 bg-gray-700 hover:bg-blue-600 px-3 py-1 rounded !text-white text-sm font-medium transition shadow w-fit mb-2 ${isDisabled ? "opacity-60 pointer-events-none" : ""}`}
        tabIndex={isDisabled ? -1 : 0}
        style={{ pointerEvents: isDisabled ? "none" : "auto" }}
      >
        <Download size={16} />
        Descargar Plantilla
      </a>

      <div className="flex gap-3 items-center">
        {/* Botón único inteligente */}
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
      
      {/* Input de archivo */}
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

      {/* Mensaje informativo del formato esperado */}
      {(estado === "no_subido" || estado === "pendiente") && (
        <div className="text-xs text-blue-400 mt-1 bg-blue-900/20 p-2 rounded">
          📋 <strong>Formato requerido:</strong> AAAAMM_novedades_RUT.xlsx
          <br />
          <span className="text-blue-300">Ejemplo: 202508_novedades_12345678.xlsx</span>
        </div>
      )}

      {/* Mensaje cuando está procesando */}
      {isProcesando && (
        <div className="text-xs text-orange-400 mt-1 bg-orange-900/20 p-2 rounded border-l-2 border-orange-400">
          ⏳ <strong>Procesamiento en curso:</strong> El archivo se está procesando actualmente. 
          <br />
          <span className="text-orange-300">Espera a que termine para poder cambiar el archivo si es necesario.</span>
        </div>
      )}

      <div className="flex flex-col gap-1 mt-3">
        {/* Botón de mapeo de headers */}
        {(estado === "clasif_pendiente" || estado === "clasificado") && (
          <button
            onClick={handleAbrirModalMapeo}
            disabled={isDisabled || !novedadesId}
            className="px-3 py-1 rounded text-sm font-medium transition bg-purple-700 hover:bg-purple-600 text-white w-fit disabled:opacity-60 flex items-center gap-2"
            title="Mapear headers de novedades con conceptos del libro"
          >
            <Settings size={16} />
            {estado === "clasif_pendiente" ? "Completar Mapeo" : "Ver/Editar Mapeo"}
          </button>
        )}

        {/* Información de clasificación */}
        {(estado === "clasif_pendiente" || estado === "clasificado") && (
          <div className="text-xs text-gray-300 mt-1 ml-1">
            <span className="mr-4">
              <strong>Clasificados:</strong> {headerClasificados?.length || 0}
            </span>
            <span>
              <strong>Sin clasificar:</strong> {headersSinClasificar?.length || 0}
            </span>
          </div>
        )}
      </div>

      {/* Botón procesar - Solo aparece cuando se puede procesar */}
      {puedeProcesr ? (
        <button
          onClick={handleProcesar}
          disabled={headersSinClasificar?.length > 0 || isDisabled}
          className="mt-2 bg-blue-700 hover:bg-blue-600 px-3 py-1 rounded text-white text-sm font-medium transition shadow w-fit disabled:opacity-60 disabled:cursor-not-allowed flex items-center gap-2"
          title={headersSinClasificar?.length > 0 ? "Completa la clasificación antes de procesar" : "Procesar archivo clasificado"}
        >
          {isProcesando && <Loader2 size={16} className="animate-spin" />}
          {isProcesando ? "Procesando..." : "Procesar"}
        </button>
      ) : tieneArchivo && estado !== "clasificado" && estado !== "procesado" ? (
        <div className="mt-2 text-xs text-yellow-400 bg-yellow-900/20 p-2 rounded">
          ℹ️ <strong>Archivo en proceso:</strong> Espera a que termine la clasificación para poder procesar
        </div>
      ) : !tieneArchivo ? (
        <div className="mt-2 text-xs text-gray-400 bg-gray-900/20 p-2 rounded">
          📁 <strong>Sin archivo:</strong> Sube un archivo Excel para poder procesarlo
        </div>
      ) : isProcessed ? (
        <div className="mt-2 text-xs text-green-400 bg-green-900/20 p-2 rounded flex items-center gap-2">
          <CheckCircle2 size={16} />
          <strong>Archivo procesado:</strong> El procesamiento se completó exitosamente
        </div>
      ) : null}

      {mensaje && (
        <span className="text-xs text-gray-400 italic mt-2">{mensaje}</span>
      )}

      {/* Estado visual informativo con mejor feedback */}
      <span className="text-xs text-gray-400 italic mt-2">
        {estado === "pendiente" && "⏳ Archivo subido, iniciando análisis..."}
        {estado === "analizando_hdrs" && "🔍 Analizando estructura del archivo Excel..."}
        {estado === "hdrs_analizados" && "✅ Headers procesados, listo para clasificar"}
        {estado === "clasif_en_proceso" && "🏷️ Clasificando conceptos automáticamente..."}
        {estado === "clasificado" && "✔ Archivo analizado y listo para procesar"}
        {estado === "procesando" && "⚙️ Procesando datos finales, por favor espera... (puede tomar hasta 40 segundos)"}
        {estado === "procesado" && "✅ Archivo procesado exitosamente"}
        {estado === "con_error" && "❌ Error en el procesamiento"}
        {estado === "no_subido" && "📁 Aún no se ha subido el archivo"}
      </span>

      {/* Modal de mapeo de headers */}
      <ModalMapeoNovedades
        isOpen={modalMapeoAbierto}
        onClose={() => setModalMapeoAbierto(false)}
        cierreId={cierreId}
        headersSinClasificar={headersData.headers_sin_clasificar}
        headersClasificados={headersData.headers_clasificados}
        mapeosExistentes={headersData.mapeos_existentes}
        onGuardarMapeos={handleGuardarMapeos}
        soloLectura={estado === "procesado"}
      />
    </div>
  );
};

export default NovedadesCard;
