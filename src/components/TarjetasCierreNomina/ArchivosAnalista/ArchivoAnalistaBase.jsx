import { useState, useRef, useEffect } from "react";
import { Download, Loader2 } from "lucide-react";
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
  
  const isProcesando = estado === "en_proceso" || estado === "procesando";
  const isDisabled = disabled || subiendo || isProcesando;
  const isProcessed = estado === "procesado" || estado === "procesado_parcial";
  const hasError = estado === "con_error";
  
  // Determinar si se puede subir un archivo nuevo (solo cuando no hay archivo)
  const puedeSubirArchivo = !isDisabled && 
    (estado === "no_subido" || estado === "pendiente") && !archivo?.id;
  
  // Determinar si se puede resubir (cuando ya hay archivo subido)
  const puedeResubir = archivo?.id && !isDisabled && onEliminarArchivo;
  
  const estadosConArchivoBloqueado = ["en_proceso", "procesando", "procesado"];
  const archivoEsBloqueado = estadosConArchivoBloqueado.includes(estado);

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

      <div className="flex flex-col gap-2">
        {/* Botón de subida de archivo - solo cuando no hay archivo */}
        {puedeSubirArchivo ? (
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            disabled={isDisabled}
            className={`bg-blue-600 hover:bg-blue-500 px-3 py-1 rounded text-sm font-medium transition ${isDisabled ? "opacity-60 cursor-not-allowed" : ""}`}
          >
            {isProcesando ? "Procesando..." : subiendo ? "Subiendo..." : "Elegir archivo .xlsx"}
          </button>
        ) : archivo?.id ? (
          /* Cuando hay archivo - mostrar estado y botón resubir */
          <div className="flex gap-2">
            <button
              type="button"
              disabled={true}
              className={`px-3 py-1 rounded text-sm font-medium cursor-not-allowed opacity-60 flex-1 ${
                hasError ? 'bg-red-600' : 
                isProcesando ? 'bg-orange-600' :
                isProcessed ? 'bg-gray-600' : 'bg-gray-600'
              }`}
              title={
                hasError ? "El archivo tuvo errores durante el procesamiento" :
                isProcesando ? "El archivo se está procesando" :
                isProcessed ? "El archivo ya fue procesado" :
                "Archivo subido"
              }
            >
              {hasError ? "Archivo con error" :
               isProcesando ? "Procesando..." :
               isProcessed ? "Archivo procesado" :
               "Archivo subido"}
            </button>
            
            {/* Botón Resubir - disponible desde que hay archivo */}
            {puedeResubir && (
              <button
                type="button"
                onClick={handleEliminarArchivo}
                disabled={eliminando}
                className="bg-blue-600 hover:bg-blue-700 px-3 py-1 rounded text-sm font-medium transition"
                title="Eliminar archivo actual para permitir subir uno nuevo"
              >
                {eliminando ? "Eliminando..." : "Resubir"}
              </button>
            )}
          </div>
        ) : null}
        
        {/* Botones personalizados (para novedades principalmente) */}
        {children}
        
        {/* Nombre del archivo */}
        {archivo?.nombre && (
          <span className="text-gray-300 text-sm italic truncate">
            {archivo.nombre}
          </span>
        )}
      </div>
      
      {/* Input de archivo oculto */}
      <input
        type="file"
        accept=".xlsx,.xls"
        ref={fileInputRef}
        style={{ display: "none" }}
        onChange={handleSeleccionArchivo}
        disabled={isDisabled || archivoEsBloqueado}
      />

      {/* Mensajes de error */}
      {error && (
        <div className="text-sm text-red-400 mt-2 bg-red-900/20 p-2 rounded">
          {error}
        </div>
      )}

      {/* Mensaje de éxito */}
      {archivoEsBloqueado && estado === "procesado" && (
        <div className="text-sm text-yellow-400 mt-2 bg-yellow-900/20 p-2 rounded">
          ℹ️ Archivo procesado correctamente
        </div>
      )}
    </div>
  );
};

export default ArchivoAnalistaBase;
