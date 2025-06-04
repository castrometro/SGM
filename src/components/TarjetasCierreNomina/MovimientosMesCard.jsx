import { useState, useRef } from "react";
import { Download } from "lucide-react";
import { descargarPlantillaMovimientosMes } from "../../api/nomina";

const MovimientosMesCard = ({
  estado,
  archivoNombre,
  onSubirArchivo,
  subiendo = false,
  disabled = false,
}) => {
  const fileInputRef = useRef();
  const [error, setError] = useState("");

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

  return (
    <div className={`bg-gray-800 p-4 rounded-xl shadow-lg flex flex-col gap-3 ${disabled ? "opacity-60 pointer-events-none" : ""}`}>
      <h3 className="text-lg font-semibold mb-3">2. Movimientos del Mes</h3>

      <div className="flex items-center gap-2 mb-2">
        <span className="font-semibold">Estado:</span>
        {estado === "procesado" ? (
          <span className="text-green-400 font-semibold">Procesado</span>
        ) : estado === "en_proceso" ? (
          <span className="text-blue-400 font-semibold">Procesando...</span>
        ) : estado === "con_error" ? (
          <span className="text-red-400 font-semibold">Error</span>
        ) : (
          <span className="text-yellow-400 font-semibold">Pendiente</span>
        )}
      </div>

      <a
        href={descargarPlantillaMovimientosMes()}
        download
        className={`flex items-center gap-2 bg-gray-700 hover:bg-blue-600 px-3 py-1 rounded !text-white text-sm font-medium transition shadow w-fit mb-2 ${disabled ? "opacity-60 pointer-events-none" : ""}`}
        tabIndex={disabled ? -1 : 0}
        style={{ pointerEvents: disabled ? "none" : "auto" }}
      >
        <Download size={16} />
        Descargar Plantilla
      </a>

      <div className="flex gap-3 items-center">
        <button
          type="button"
          onClick={() => fileInputRef.current.click()}
          disabled={subiendo || disabled}
          className={`bg-blue-600 hover:bg-blue-500 px-3 py-1 rounded text-sm font-medium transition ${subiendo ? "opacity-60 cursor-not-allowed" : ""}`}
        >
          {subiendo ? "Subiendo..." : "Elegir archivo .xlsx"}
        </button>
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
      />

      {error && <div className="text-xs text-red-400 mt-1">{error}</div>}

      <span className="text-xs text-gray-400 italic mt-2">
        {estado === "procesado"
          ? "✔ Archivo cargado correctamente y procesado."
          : estado === "en_proceso"
          ? "Procesando archivo, por favor espera…"
          : "Aún no se ha subido el archivo."}
      </span>
    </div>
  );
};

export default MovimientosMesCard;
