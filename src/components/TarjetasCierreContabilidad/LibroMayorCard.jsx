import { useEffect, useState, useRef } from "react";
import { obtenerLibrosMayor, subirLibroMayor } from "../../api/contabilidad";
import EstadoBadge from "../EstadoBadge";

const LibroMayorCard = ({
  cierreId,
  disabled,
  onCompletado,
  tipoDocumentoReady,
  clasificacionReady,
  nombresInglesReady,
  numeroPaso
}) => {
  const [libroActual, setLibroActual] = useState(null);
  const [archivoNombre, setArchivoNombre] = useState("");
  const [subiendo, setSubiendo] = useState(false);
  const [error, setError] = useState("");
  const [polling, setPolling] = useState(false);
  const [processingTime, setProcessingTime] = useState(0);
  const fileInputRef = useRef();

  // Fetch libro mayor al montar y al hacer polling
  useEffect(() => {
    let interval;
    const fetchLibros = async () => {
      if (!cierreId) return;
      try {
        const librosData = await obtenerLibrosMayor(cierreId);
        const actual = librosData.length > 0 ? librosData[librosData.length - 1] : null;
        setLibroActual(actual);

        if (actual && actual.estado === "procesando" && !polling) {
          setPolling(true);
          setProcessingTime(0);
        }
        if (actual && ["completado", "error"].includes(actual.estado) && polling) {
          setPolling(false);
          setProcessingTime(0);
          if (actual.estado === "completado") {
            onCompletado && onCompletado();
          }
        }
      } catch (e) {
        setLibroActual(null);
        setPolling(false);
        setProcessingTime(0);
      }
    };

    fetchLibros();
    if (polling) {
      interval = setInterval(() => {
        fetchLibros();
        setProcessingTime(prev => prev + 4);
      }, 4000);
    }
    return () => clearInterval(interval);
    // eslint-disable-next-line
  }, [cierreId, polling, onCompletado]);

  // Reset processingTime al cambiar cierre
  useEffect(() => {
    setProcessingTime(0);
  }, [cierreId]);

  const handleSeleccionArchivo = (e) => {
    const archivo = e.target.files[0];
    if (!archivo) return;
    setArchivoNombre(archivo.name);
  };

  const handleSubirLibro = async () => {
    setSubiendo(true);
    setError("");
    try {
      const formFile = fileInputRef.current.files[0];
      if (!formFile) {
        setError("Debes seleccionar un archivo .xlsx");
        setSubiendo(false);
        return;
      }
      await subirLibroMayor(cierreId, formFile);
      setArchivoNombre("");
      setPolling(true);
    } catch (err) {
      setError("Error al subir el archivo.");
    } finally {
      setSubiendo(false);
    }
  };

  let estado = "pendiente";
  if (libroActual) {
    if (libroActual.estado === "completado") estado = "subido";
    else if (libroActual.estado === "procesando") estado = "procesando";
    else if (libroActual.estado === "error") estado = "error";
  }

  return (
    <div className={`bg-gray-800 p-4 rounded-xl shadow-lg flex flex-col gap-3 ${disabled ? "opacity-60 pointer-events-none" : ""}`}>
      <h3 className="text-lg font-semibold mb-3">{numeroPaso}. Libro Mayor y Procesamiento</h3>

      {/* Información de prerequisitos */}
      <div className="text-xs text-gray-400 mb-2">
        <div className="flex items-center gap-2">
          <span>Prerequisitos:</span>
          <span className={tipoDocumentoReady ? "text-green-400" : "text-red-400"}>
            {tipoDocumentoReady ? "✓" : "✗"} Tipos de Documento
          </span>
          <span className={clasificacionReady ? "text-green-400" : "text-red-400"}>
            {clasificacionReady ? "✓" : "✗"} Clasificación
          </span>
          {nombresInglesReady !== undefined && (
            <span className={nombresInglesReady ? "text-green-400" : "text-red-400"}>
              {nombresInglesReady ? "✓" : "✗"} Nombres en Inglés
            </span>
          )}
        </div>
      </div>

      <div className="flex items-center gap-2 mb-2">
        <span className="font-semibold">Estado:</span>
        <EstadoBadge estado={estado} />
      </div>

      {libroActual && libroActual.fecha_subida && (
        <span className="text-xs text-gray-400">
          Subido: {new Date(libroActual.fecha_subida).toLocaleString()}
        </span>
      )}
      {libroActual && libroActual.errores && (
        <div className="text-red-400 text-xs mt-1">
          Errores: {libroActual.errores}
        </div>
      )}
      {estado === "procesando" && processingTime > 120 && (
        <div className="text-orange-400 text-xs mt-1">
          El procesamiento está tardando más de lo habitual ({Math.round(processingTime/60)} min). Por favor, espera o revisa más tarde.
        </div>
      )}

      {(estado !== "subido") && (
        <div className="flex flex-col gap-2">
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
            disabled={subiendo || disabled}
          />
          <button
            onClick={handleSubirLibro}
            disabled={subiendo || !archivoNombre || disabled}
            className="px-3 py-1 rounded text-sm font-medium transition bg-blue-700 hover:bg-blue-600 text-white shadow w-fit"
          >
            {subiendo ? "Subiendo..." : "Subir libro mayor"}
          </button>
        </div>
      )}

      {error && <div className="text-xs text-red-400 mt-1">{error}</div>}
      <span className="text-xs text-gray-400 italic mt-2">
        {estado === "subido"
          ? "✔ Libro mayor procesado correctamente con toda la información previa"
          : estado === "procesando"
          ? "🔄 Procesando libro mayor con clasificaciones y configuraciones..."
          : disabled
          ? "Complete los pasos anteriores para procesar el libro mayor"
          : "Suba el libro mayor para completar el procesamiento del cierre"}
      </span>
    </div>
  );
};

export default LibroMayorCard;
