import { useState, useRef, useEffect } from "react";
import { Download, Loader2, CheckCircle2 } from "lucide-react";
import EstadoBadge from "../../EstadoBadge";

const ArchivoAnalistaBase = ({
  tipo,
  titulo,
  icono: Icono,
  descripcion,
  plantilla,
  estado,
  archivo,
  error,
  subiendo = false,
  disabled = false,
  onSubirArchivo,
  onReprocesar,
  onEliminarArchivo,
  children, // Para botones personalizados
}) => {
  const fileInputRef = useRef();
  const [eliminando, setEliminando] = useState(false);
  
  // 🚀 VARIABLES DE ESTADO UNIFICADAS
  const isProcesando = estado === "en_proceso" || estado === "procesando";
  const isDisabled = disabled || subiendo || isProcesando;
  const isProcessed = estado === "procesado" || estado === "con_errores_parciales";
  const hasError = estado === "con_error" || estado === "error";
  
  // 🚀 LÓGICA SIMPLIFICADA: Un solo botón que cambia según si hay archivo
  const puedeInteractuarConArchivo = !isDisabled && !isProcesando;
  
  // Determinar si hay archivo
  const tieneArchivo = Boolean(archivo?.id);
  const nombreArchivoActual = archivo?.nombre;

  const handleSeleccionArchivo = async (e) => {
    const archivoSeleccionado = e.target.files[0];
    if (!archivoSeleccionado || !onSubirArchivo) return;
    
    await onSubirArchivo(archivoSeleccionado);
    
    // Limpiar el input para permitir seleccionar el mismo archivo nuevamente
    e.target.value = '';
  };

  const handleEliminarArchivo = async () => {
    if (!onEliminarArchivo) return;
    
    setEliminando(true);
    try {
      await onEliminarArchivo();
    } catch (error) {
      console.error("Error al eliminar archivo:", error);
    } finally {
      setEliminando(false);
    }
  };

  return (
    <div className={`bg-gray-700 p-4 rounded-lg ${isDisabled ? "opacity-60" : ""}`}>
      <div className="flex items-center gap-2 mb-3">
        <Icono size={18} className="text-blue-400" />
        <h4 className="font-semibold text-white">{titulo}</h4>
        {isProcesando && <Loader2 size={16} className="animate-spin text-blue-400" />}
      </div>
      
      <p className="text-gray-300 text-xs mb-3">{descripcion}</p>
      
      <div className="flex items-center gap-2 mb-3">
        <span className="text-sm font-medium">Estado:</span>
        {isProcesando ? (
          <span className="text-blue-400 text-sm flex items-center gap-1">
            <Loader2 size={14} className="animate-spin" /> Procesando...
          </span>
        ) : (
          <EstadoBadge estado={estado} />
        )}
      </div>

      {/* Botón de descarga de plantilla */}
      <a
        href={plantilla()}
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
          {nombreArchivoActual || "Ningún archivo seleccionado"}
        </span>
      </div>
      
      {/* Botones personalizados (para novedades principalmente) */}
      {children}
      
      {/* 🚀 INPUT DE ARCHIVO SIMPLIFICADO */}
      <input
        type="file"
        accept=".xlsx,.xls"
        ref={fileInputRef}
        style={{ display: "none" }}
        onChange={handleSeleccionArchivo}
        disabled={isDisabled || !puedeInteractuarConArchivo}
      />

      {/* Mensajes de error */}
      {error && (
        <div className="text-xs text-red-400 mt-1 bg-red-900/20 p-2 rounded border-l-2 border-red-400">
          ❌ <strong>Error:</strong> {error}
        </div>
      )}

      {/* ✅ MENSAJE INFORMATIVO DEL FORMATO ESPERADO */}
      {(estado === "no_subido" || estado === "pendiente") && (
        <div className="text-xs text-blue-400 mt-1 bg-blue-900/20 p-2 rounded">
          📋 <strong>Formato requerido:</strong> AAAAAMM_{tipo}_{`{RUT}`}.xlsx
          <br />
          <span className="text-blue-300">Ejemplo: 202503_{tipo}_12345678.xlsx</span>
        </div>
      )}

      {/* ✅ MENSAJE INFORMATIVO CUANDO EL ARCHIVO ESTÁ BLOQUEADO */}
      {!puedeInteractuarConArchivo && tieneArchivo && (
        <div className="text-xs text-yellow-400 mt-1 bg-yellow-900/20 p-2 rounded border-l-2 border-yellow-400">
          🔒 <strong>Archivo procesado:</strong> Este archivo ya fue procesado exitosamente.
          <br />
          <span className="text-yellow-300">Si necesitas cambiar el archivo, contacta al administrador.</span>
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

      {/* ✅ MENSAJE CUANDO EL ARCHIVO ESTÁ PROCESADO */}
      {isProcessed && tieneArchivo && (
        <div className="mt-2 text-xs text-green-400 bg-green-900/20 p-2 rounded flex items-center gap-2">
          <CheckCircle2 size={16} />
          <strong>Archivo procesado:</strong> El procesamiento se completó exitosamente
        </div>
      )}

      {/* 📄 MENSAJE DE ESTADO FINAL */}
      <span className="text-xs text-gray-400 italic mt-2 block">
        {isProcesando
          ? "🔄 Procesando archivo, por favor espera..."
          : isProcessed
          ? "✅ Archivo procesado exitosamente"
          : hasError
          ? "❌ Error al procesar el archivo. Revisa los detalles arriba."
          : estado === "pendiente"
          ? `📋 Archivo listo: ${nombreArchivoActual} - Esperando procesamiento`
          : "📁 Ningún archivo seleccionado aún"}
      </span>
    </div>
  );
};

export default ArchivoAnalistaBase;
