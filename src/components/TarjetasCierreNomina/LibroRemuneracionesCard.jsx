import { useState, useRef, useEffect } from "react";
import { Download, FileBarChart2, CheckCircle2, Loader2 } from "lucide-react";
import { descargarPlantillaLibroRemuneraciones } from "../../api/nomina";
import EstadoBadge from "../EstadoBadge";

const LibroRemuneracionesCard = ({
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
  libroId,
  deberiaDetenerPolling = false,
}) => {
  const fileInputRef = useRef();
  const pollingRef = useRef(null);

  // Estado local para errores y procesamiento
  const [error, setError] = useState("");
  const [eliminando, setEliminando] = useState(false);
  const [procesandoLocal, setProcesandoLocal] = useState(false);

  // Limpiar polling al desmontar
  useEffect(() => {
    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
        pollingRef.current = null;
      }
    };
  }, []);

  // 🔄 POLLING REACTIVADO: Iniciar polling cuando el archivo esté en procesamiento o análisis
  useEffect(() => {
    console.log('🎯 useEffect polling - estado actual:', estado, 'deberiaDetener:', deberiaDetenerPolling);
    
    // Detener polling si se debe detener globalmente
    if (deberiaDetenerPolling && pollingRef.current) {
      console.log('🛑 [LibroRemuneracionesCard] Deteniendo polling - señal global de parada');
      clearInterval(pollingRef.current);
      pollingRef.current = null;
      setProcesandoLocal(false);
      return;
    }
    
    // 🚀 ESTADOS QUE REQUIEREN POLLING
    const estadosQueRequierenPolling = [
      "no_subido",           // ⚠️ NUEVO: Para monitorear cuando se sube por primera vez
      "pendiente",           // Esperando análisis inicial
      "analizando_hdrs",     // Analizando headers
      "hdrs_analizados",     // Headers analizados, esperando clasificación
      "clasif_en_proceso",   // Clasificando
      "procesando"           // Procesamiento final
    ];
    
    const deberiaHacerPolling = estadosQueRequierenPolling.includes(estado);
    
    if (deberiaHacerPolling && !pollingRef.current && onActualizarEstado && !deberiaDetenerPolling) {
      console.log(`� Iniciando polling para estado: "${estado}" (archivo: ${archivoNombre || 'ninguno'})`);
      
      let contadorPolling = 0;
      let contadorErrores = 0;
      
      pollingRef.current = setInterval(async () => {
        contadorPolling++;
        try {
          console.log(`📡 Polling #${contadorPolling} - Verificando estado desde "${estado}"...`);
          await onActualizarEstado();
          
          // Reset error counter on success
          contadorErrores = 0;
          
        } catch (pollError) {
          contadorErrores++;
          console.error(`❌ Error en polling #${contadorPolling} (${contadorErrores}/3):`, pollError);
          
          // Si hay 3 errores consecutivos, parar el polling por seguridad
          if (contadorErrores >= 3) {
            console.log('🛑 Demasiados errores consecutivos, deteniendo polling por seguridad');
            clearInterval(pollingRef.current);
            pollingRef.current = null;
          }
        }
      }, 3000); // Consultar cada 3 segundos para mejor UX
      
    } else if ((!deberiaHacerPolling || deberiaDetenerPolling) && pollingRef.current) {
      console.log(`✅ Estado cambió a "${estado}" o detención solicitada - deteniendo polling`);
      clearInterval(pollingRef.current);
      pollingRef.current = null;
      setProcesandoLocal(false);
    }
  }, [estado, onActualizarEstado, deberiaDetenerPolling]);

  // 🧹 LIMPIEZA: Cleanup del polling al desmontar componente
  useEffect(() => {
    return () => {
      if (pollingRef.current) {
        console.log('🧹 [LibroRemuneracionesCard] Limpiando polling al desmontar');
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
      console.log('📁 Iniciando subida de archivo:', archivo.name);
      await onSubirArchivo(archivo);
      console.log('✅ Archivo subido exitosamente');
      
      // 🔄 FORZAR ACTUALIZACIÓN: Llamar al callback de actualización para activar el polling
      if (onActualizarEstado) {
        console.log('🔄 Forzando actualización de estado post-subida...');
        setTimeout(() => {
          onActualizarEstado();
        }, 500); // Pequeño delay para dar tiempo al backend
      }
      
    } catch (err) {
      // Capturar el mensaje específico del backend
      console.log('🔍 Error completo:', err);
      console.log('🔍 Error response:', err?.response);
      console.log('🔍 Error response data:', err?.response?.data);
      
      let errorMessage = "Error al subir el archivo.";
      
      if (err?.response?.data) {
        const data = err.response.data;
        // Diferentes formatos posibles de ValidationError
        if (data.detail) {
          errorMessage = data.detail;
        } else if (data.message) {
          errorMessage = data.message;
        } else if (data.error) {
          errorMessage = data.error;
        } else if (Array.isArray(data)) {
          // ValidationError a veces viene como array
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
      console.error('Error subiendo archivo:', err);
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

  // Handler de procesar simplificado
  const handleProcesar = async () => {
    if (!onProcesar) return;
    
    setProcesandoLocal(true);
    setError("");
    
    try {
      console.log('🔄 Iniciando procesamiento...');
      await onProcesar();
      console.log('✅ Procesamiento iniciado exitosamente');
      // El polling se iniciará automáticamente cuando el estado cambie a "procesando"
      
    } catch (err) {
      setProcesandoLocal(false);
      setError("Error al procesar el archivo.");
      console.error('❌ Error al procesar:', err);
    }
  };

  // Determinar si la tarjeta está deshabilitada
  const isDisabled = disabled || procesandoLocal || subiendo;
  
  // Determinar si ya está procesado
  const isProcessed = estado === "procesado";
  
  // Determinar si está procesando (estado del servidor O estado local)
  const isProcesando = estado === "procesando" || procesandoLocal;

  // 🚀 LÓGICA SIMPLIFICADA: Un solo botón que cambia según si hay archivo
  const puedeInteractuarConArchivo = !isDisabled && !isProcesando;
  
  // Determinar si hay archivo
  const tieneArchivo = Boolean(archivoNombre);
  
  // 🎯 NUEVA LÓGICA: Determinar si puede procesar
  const puedeProcesr = tieneArchivo && estado === "clasificado" && !isProcesando && !isProcessed;

  return (
    <div className={`bg-gray-800 p-4 rounded-xl shadow-lg flex flex-col gap-3 ${isDisabled ? "opacity-60 pointer-events-none" : ""}`}>
      <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
        1. Libro de Remuneraciones
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
        href={descargarPlantillaLibroRemuneraciones()}
        download
        className={`flex items-center gap-2 bg-gray-700 hover:bg-blue-600 px-3 py-1 rounded !text-white text-sm font-medium transition shadow w-fit mb-2 ${isDisabled ? "opacity-60 pointer-events-none" : ""}`}
        tabIndex={isDisabled ? -1 : 0}
        style={{ pointerEvents: isDisabled ? "none" : "auto" }}
      >
        <Download size={16} />
        Descargar Plantilla
      </a>

      <div className="flex gap-3 items-center">
        {/* 🚀 BOTÓN ÚNICO INTELIGENTE */}
        {puedeInteractuarConArchivo ? (
          <button
            type="button"
            onClick={() => {
              if (tieneArchivo && onEliminarArchivo) {
                // Si hay archivo, eliminar primero
                handleEliminarArchivo();
              } else {
                // Si no hay archivo, abrir selector
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
      
      {/* 🚀 INPUT DE ARCHIVO SIMPLIFICADO */}
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

      {/* ✅ MENSAJE INFORMATIVO DEL FORMATO ESPERADO */}
      {(estado === "no_subido" || estado === "pendiente") && (
        <div className="text-xs text-blue-400 mt-1 bg-blue-900/20 p-2 rounded">
          📋 <strong>Formato requerido:</strong> AAAAMM_libro_remuneraciones_RUT.xlsx
          <br />
          <span className="text-blue-300">Ejemplo: 202508_libro_remuneraciones_12345678.xlsx</span>
        </div>
      )}

      {/* 🚀 MENSAJE INFORMATIVO MEJORADO CUANDO EL ARCHIVO ESTÁ EN PROCESAMIENTO */}
      {isProcesando && (
        <div className="text-xs text-orange-400 mt-1 bg-orange-900/20 p-2 rounded border-l-2 border-orange-400">
          ⏳ <strong>Procesamiento en curso:</strong> El archivo se está procesando actualmente. 
          <br />
          <span className="text-orange-300">Espera a que termine para poder cambiar el archivo si es necesario.</span>
        </div>
      )}

      <div className="flex flex-col gap-1 mt-3">
        <button
          onClick={() => onVerClasificacion(false)} // ← Siempre editable; permite re-mapeo aun procesado
          disabled={isDisabled}
          className="px-3 py-1 rounded text-sm font-medium transition bg-blue-700 hover:bg-blue-600 text-white w-fit disabled:opacity-60"
        >
          {isProcessed ? "Re-mapear Clasificaciones" : "Administrar Clasificaciones"}
        </button>

        {true && (
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

      {/* 🎯 BOTÓN PROCESAR - Solo aparece cuando se puede procesar */}
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
    </div>
  );
};

export default LibroRemuneracionesCard;
