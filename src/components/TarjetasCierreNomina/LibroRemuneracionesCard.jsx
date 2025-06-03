import { useState, useRef } from "react";
import { Download, FileBarChart2, CheckCircle2 } from "lucide-react";
import { descargarPlantillaLibroRemuneraciones } from "../../api/nomina"; // Ajusta el path según tu estructura

const LibroRemuneracionesCard = ({
  estado, // "no_subido" | "procesando" | "procesado"
  archivoNombre,
  onSubirArchivo,
  onVerClasificacion,
  headersSinClasificar = [],
  headerClasificados = [],
  subiendo = false,
  disabled = false,
  mensaje = "",
  onEliminarArchivo,
}) => {
  const fileInputRef = useRef();

  // Estado local para errores
  const [error, setError] = useState("");
  const [eliminando, setEliminando] = useState(false);

  // Handler de subida (simula lo que te va a llegar por props)
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

  // Handler de eliminar (opcional)
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

  return (
    <div className={`bg-gray-800 p-4 rounded-xl shadow-lg flex flex-col gap-3 ${disabled ? "opacity-60 pointer-events-none" : ""}`}>
      <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
        {/* <FileBarChart2 size={22} className="text-blue-300" /> */}
        1. Libro de Remuneraciones
      </h3>

      <div className="flex items-center gap-2 mb-2">
        <span className="font-semibold">Estado:</span>
        {estado === "clasificado" && (
          <span className="text-green-400 font-semibold flex items-center gap-1">
            <CheckCircle2 size={16} /> Clasificado
          </span>
        )}
        {estado === "clasif_pendiente" && (
          <span className="text-red-400 font-semibold">Clasificación pendiente</span>
        )}

        {estado === "no_subido" && (
          <span className="text-red-400 font-semibold">Pendiente</span>
        )}
        {estado === "analizando_hdrs" && (
          <span className="text-yellow-400 font-semibold">Analizando Headers...</span>
        )}
        {estado === "con_error" && (
          <span className="text-red-400 font-semibold">Error en procesamiento</span>
        )}
        {estado === "hdrs_analizados" && (
          <span className="text-green-400 font-semibold">Headers Analizados</span>
        )}
        {estado === "clasif_en_proceso" && (
          <span className="text-yellow-400 font-semibold">Clasificando...</span>
        )}
      </div>

      {/* Botón estilizado de descarga de plantilla */}
      <a
        href={descargarPlantillaLibroRemuneraciones()}
        download
        className={`flex items-center gap-2 bg-gray-700 hover:bg-blue-600 px-3 py-1 rounded !text-white text-sm font-medium transition shadow w-fit mb-2 ${disabled ? "opacity-60 pointer-events-none" : ""}`}
        tabIndex={disabled ? -1 : 0}
        style={{ pointerEvents: disabled ? "none" : "auto" }}
      >
        <Download size={16} />
        Descargar Plantilla
      </a>

      {/* Subida de archivo */}
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
        {estado === "procesado" && onEliminarArchivo && (
          <button
            onClick={handleEliminarArchivo}
            disabled={eliminando}
            className="text-xs px-2 py-1 rounded bg-red-600 hover:bg-red-700 text-white ml-2"
          >
            {eliminando ? "Eliminando..." : "Eliminar"}
          </button>
        )}
      </div>
      <input
        type="file"
        accept=".xlsx"
        ref={fileInputRef}
        style={{ display: "none" }}
        onChange={handleSeleccionArchivo}
      />

      {error && <div className="text-xs text-red-400 mt-1">{error}</div>}

      {/* Acceso a modal de headers para clasificar */}
      <div className="flex flex-col gap-1 mt-3">
        <button
          onClick={onVerClasificacion}
          className="px-3 py-1 rounded text-sm font-medium transition bg-blue-700 hover:bg-blue-600 text-white w-fit"
        >
          Administrar Clasificaciones
        </button>

        {true  && (
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



      {mensaje && (
        <span className="text-xs text-gray-400 italic mt-2">{mensaje}</span>
      )}

      {/* Estado visual informativo */}
      <span className="text-xs text-gray-400 italic mt-2">
        {estado === "procesado"
          ? "✔ Archivo cargado correctamente y procesado."
          : estado === "procesando"
          ? "Procesando archivo, por favor espera…"
          : "Aún no se ha subido el archivo."}
      </span>
    </div>
  );
};

export default LibroRemuneracionesCard;
