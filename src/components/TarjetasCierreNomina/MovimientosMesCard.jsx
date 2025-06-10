import { useState, useRef, useEffect } from "react";
import { Download, Loader2 } from "lucide-react";
import { descargarPlantillaMovimientosMes } from "../../api/nomina";
import EstadoBadge from "../EstadoBadge";

const MovimientosMesCard = ({
  estado,
  archivoNombre,
  onSubirArchivo,
  onActualizarEstado,
  subiendo = false,
  disabled = false,
}) => {
  const fileInputRef = useRef();
  const pollingRef = useRef(null);
  const [error, setError] = useState("");

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
    console.log('🎯 MovimientosMes useEffect polling - estado actual:', estado);
    
    if (estado === "en_proceso" && !pollingRef.current && onActualizarEstado) {
      console.log('🔄 Iniciando polling para monitorear procesamiento de movimientos...');
      
      let contadorPolling = 0;
      pollingRef.current = setInterval(async () => {
        contadorPolling++;
        try {
          console.log(`📡 MovimientosMes Polling #${contadorPolling} - Verificando estado...`);
          await onActualizarEstado();
        } catch (pollError) {
          console.error(`❌ Error en polling MovimientosMes #${contadorPolling}:`, pollError);
        }
      }, 5000); // consultar cada 5 segundos (más frecuente que el libro)
      
    } else if (estado !== "en_proceso" && pollingRef.current) {
      console.log(`✅ MovimientosMes Estado cambió a "${estado}" - deteniendo polling`);
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
  }, [estado, onActualizarEstado]);

  const handleSeleccionArchivo = async (e) => {
    const archivo = e.target.files[0];
    if (!archivo) return;
    setError("");
    try {
      await onSubirArchivo(archivo);
    } catch (err) {
      setError("Error al subir el archivo.");
    }
  };

  // Determinar si la tarjeta está deshabilitada
  const isDisabled = disabled || subiendo || estado === "en_proceso";
  
  // Determinar si está procesando
  const isProcesando = estado === "en_proceso";

  // ✅ NUEVA LÓGICA: Determinar si se puede subir archivo
  const puedeSubirArchivo = !isDisabled && 
    (estado === "no_subido" || estado === "pendiente" || estado === "con_error");
  
  // Estados donde NO se puede cambiar el archivo
  const estadosConArchivoBloqueado = [
    "en_proceso",
    "procesado",
    "con_errores_parciales"
  ];
  
  const archivoEsBloqueado = estadosConArchivoBloqueado.includes(estado);

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
      >
        <Download size={16} />
        Descargar Plantilla
      </a>

      <div className="flex gap-3 items-center">
        {/* ✅ BOTÓN DE SUBIDA CONDICIONAL */}
        {puedeSubirArchivo ? (
          <button
            type="button"
            onClick={() => fileInputRef.current.click()}
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
