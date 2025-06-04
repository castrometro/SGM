import { useEffect, useState, useRef } from "react";
import { obtenerEstadoNombresIngles, subirNombresIngles } from "../../api/contabilidad";

const NombresEnInglesCard = ({
  cierreId,
  clienteId,
  clasificacionReady,
  onCompletado
}) => {
  const [estado, setEstado] = useState("pendiente");
  const [archivoNombre, setArchivoNombre] = useState("");
  const [subiendo, setSubiendo] = useState(false);
  const [error, setError] = useState("");
  const [faltantes, setFaltantes] = useState(0);
  const [totalCuentas, setTotalCuentas] = useState(0);
  const fileInputRef = useRef();

  useEffect(() => {

      const fetchEstado = async () => {
         
        if (!cierreId || !clienteId || !clasificacionReady) {
          setEstado("pendiente");
          setFaltantes(0);
          setTotalCuentas(0);
          if (onCompletado) onCompletado(false);
          return;
        }
        try {
          const data = await obtenerEstadoNombresIngles(clienteId, cierreId);

          // Nuevo log más explícito
          const total = data.total || 0;
          const faltantes = data.faltantes ? data.faltantes.length : 0;
          const traducidas = total - faltantes;

          // Si no hay cuentas (total === 0) o faltantes === 0, se considera completado.
          const esCompletado = (faltantes === 0 && total > 0) || data.estado === "subido";
          setEstado(esCompletado ? "subido" : "pendiente");
          setFaltantes(faltantes);
          setTotalCuentas(total);
          if (onCompletado) onCompletado(esCompletado);
        } catch (err) {
          setEstado("pendiente");
          setFaltantes(0);
          setTotalCuentas(0);
          if (onCompletado) onCompletado(false);
        }
      };
      fetchEstado();
  }, [cierreId, clienteId, clasificacionReady, onCompletado]);


  const handleSeleccionArchivo = (e) => {
    const archivo = e.target.files[0];
    if (!archivo) return;
    setArchivoNombre(archivo.name);
  };
   
  const handleSubir = async () => {
    setSubiendo(true);
    setError("");
    try {
      const file = fileInputRef.current.files[0];
      if (!file) {
        setError("Debes seleccionar un archivo .xlsx");
        setSubiendo(false);
        return;
      }
      await subirNombresIngles(clienteId, cierreId, file);
      setArchivoNombre("");
      // Refresca estado al subir
      setTimeout(() => {
        // Forzamos refetch rápido tras la subida
        if (typeof window !== "undefined") window.location.reload();
      }, 1000);
    } catch (err) {
      setError("Error al subir el archivo.");
      if (onCompletado) onCompletado(false);
    } finally {
      setSubiendo(false);
    }
  };

  // Render
  return (
    <div className={`bg-gray-800 p-4 rounded-xl shadow-lg flex flex-col gap-3 ${!clasificacionReady ? "opacity-60 pointer-events-none" : ""}`}>
      <h3 className="text-lg font-semibold mb-3">4. Nombres en inglés de cuentas</h3>

      {/* Estado global y progreso */}
      <div className="flex flex-col gap-1 mb-2">
        <span className="font-semibold text-lg">
          {totalCuentas === 0
            ? "No hay cuentas para traducir"
            : faltantes === 0
              ? "✔ Todas las cuentas traducidas"
              : `Faltan ${faltantes} de ${totalCuentas} cuentas por traducir`}
        </span>
        <span className="font-semibold">
          Estado:{" "}
          {estado === "subido"
            ? <span className="text-green-400 font-semibold">Completado</span>
            : <span className="text-yellow-400 font-semibold">Pendiente</span>
          }
        </span>
      </div>

      {/* Subida de archivo */}
      <button
        type="button"
        onClick={() => fileInputRef.current.click()}
        disabled={subiendo || !clasificacionReady}
        className={`bg-blue-600 hover:bg-blue-500 px-3 py-1 rounded text-sm font-medium transition ${subiendo ? "opacity-60 cursor-not-allowed" : ""}`}
      >
        {subiendo ? "Subiendo..." : "Elegir archivo .xlsx"}
      </button>
      <span className="text-gray-300 text-xs italic truncate max-w-xs">
        {archivoNombre || "Ningún archivo seleccionado"}
      </span>
      <input
        type="file"
        accept=".xlsx"
        ref={fileInputRef}
        style={{ display: "none" }}
        onChange={handleSeleccionArchivo}
        disabled={subiendo || !clasificacionReady}
      />
      <button
        onClick={handleSubir}
        disabled={subiendo || !archivoNombre || !clasificacionReady}
        className="px-3 py-1 rounded text-sm font-medium transition bg-blue-700 hover:bg-blue-600 text-white shadow w-fit"
      >
        {subiendo ? "Subiendo..." : "Subir archivo"}
      </button>
      {error && <div className="text-xs text-red-400 mt-1">{error}</div>}
      <span className="text-xs text-gray-400 italic mt-2">
        {estado === "subido"
          ? "✔ Archivo de nombres en inglés cargado correctamente"
          : "Aún no se ha subido el archivo de nombres en inglés."}
      </span>
    </div>
  );
};

export default NombresEnInglesCard;
