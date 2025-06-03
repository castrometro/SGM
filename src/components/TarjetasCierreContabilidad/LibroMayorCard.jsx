import { useEffect, useState, useRef } from "react";
import { obtenerLibrosMayor, subirLibroMayor } from "../../api/contabilidad";

const LibroMayorCard = ({ cierreId, disabled, onCompletado }) => {
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
      <h3 className="text-lg font-semibold mb-3">2. Libro Mayor</h3>

      <div className="flex items-center gap-2 mb-2">
        <span className="font-semibold">Estado:</span>
        {estado === "subido" ? (
          <span className="text-green-400 font-semibold">Subido</span>
        ) : estado === "procesando" ? (
          <span className="text-blue-400 font-semibold flex items-center gap-1">
            Procesando...
            <svg className="animate-spin h-4 w-4 text-blue-400 inline" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"></path></svg>
          </span>
        ) : estado === "error" ? (
          <span className="text-red-400 font-semibold">Error</span>
        ) : (
          <span className="text-yellow-400 font-semibold">Pendiente</span>
        )}
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
          ? "✔ Libro mayor cargado correctamente"
          : "Aún no se ha subido el libro mayor."}
      </span>
    </div>
  );
};

export default LibroMayorCard;
