import { useState, useRef, useEffect } from "react";
import { Download, CheckCircle2, Loader2 } from "lucide-react";
import { descargarPlantillaLibroRemuneraciones } from "../../../api/nomina";
import { consolidarDatosTalana } from "../../../api/nomina";
import EstadoBadge from "../../EstadoBadge";
import { corregirLibroRemuneraciones } from "../../../api/nomina";

// Copia del componente original con título y textos ajustados para "Corrección"
const LibroRemuneracionesCardCorreccion = ({
  cierreId,
  estado,
  archivoNombre,
  onSubirArchivo,
  onProcesar,
  onActualizarEstado,
  subiendo = false,
  disabled = false,
  mensaje = "",
  onEliminarArchivo,
}) => {
  const fileInputRef = useRef();
  const pollingRef = useRef(null);

  const [error, setError] = useState("");
  const [eliminando, setEliminando] = useState(false);
  const [procesandoLocal, setProcesandoLocal] = useState(false);
  // Estados locales para el nuevo flujo solicitado
  const [selectedFile, setSelectedFile] = useState(null);
  const [showConfirmDelete, setShowConfirmDelete] = useState(false);
  const [libroBorradoFlag, setLibroBorradoFlag] = useState(false);
  const [enviandoCorreccion, setEnviandoCorreccion] = useState(false);
  // Flag para encadenar consolidación automática tras procesar
  const [autoConsolidar, setAutoConsolidar] = useState(false);
  const [mensajeConsolidacion, setMensajeConsolidacion] = useState("");

  useEffect(() => {
    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
        pollingRef.current = null;
      }
    };
  }, []);

  useEffect(() => {
    const estadosQueRequierenPolling = [
      "no_subido",
      "pendiente",
      "analizando_hdrs",
      "hdrs_analizados",
      "clasif_en_proceso",
      "clasificado",
      "procesando",
    ];
    const hacerPolling = estadosQueRequierenPolling.includes(estado);
    if (hacerPolling && !pollingRef.current && onActualizarEstado) {
      pollingRef.current = setInterval(async () => {
        try {
          await onActualizarEstado();
        } catch {
          // ignorar errores intermitentes del polling
        }
      }, 3000);
    } else if (!hacerPolling && pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
      setProcesandoLocal(false);
    }
  }, [estado, onActualizarEstado]);

  const handleSeleccionArchivo = (e) => {
    const archivo = e.target.files?.[0];
    if (!archivo) return;
    setError("");
    setSelectedFile(archivo);
    setShowConfirmDelete(true);
  };

  const handleEliminarArchivo = async () => {
    setEliminando(true);
    setError("");
    try {
      await onEliminarArchivo?.();
    } catch (err) {
      setError("Error eliminando el archivo.");
    } finally {
      setEliminando(false);
    }
  };

  const handleProcesar = async () => {
    if (!onProcesar) return;
    setProcesandoLocal(true);
    setError("");
    try {
      await onProcesar();
      // Marcar que, una vez termine y pase a "procesado", debemos consolidar datos
      setAutoConsolidar(true);
    } catch (err) {
      setProcesandoLocal(false);
      setError("Error al procesar el archivo.");
    }
  };

  const isDisabled = disabled || procesandoLocal || subiendo;
  const isProcessed = estado === "procesado";
  const isProcesando = estado === "procesando" || procesandoLocal;
  const puedeInteractuarConArchivo = !isDisabled && !isProcesando;
  const tieneArchivo = Boolean(archivoNombre) || Boolean(selectedFile);
  const puedeProcesar = tieneArchivo && estado === "clasificado" && !isProcesando && !isProcessed;

  // Efecto: cuando el procesamiento termine y el estado pase a 'procesado', disparar consolidación
  useEffect(() => {
    const lanzarConsolidacion = async () => {
      if (!cierreId) return;
      try {
        setMensajeConsolidacion("Iniciando consolidación de datos...");
        await consolidarDatosTalana(cierreId, { modo: 'optimizado' });
        setMensajeConsolidacion("Consolidación iniciada. Puedes seguir trabajando; el sistema actualizará el estado automáticamente.");
      } catch (e) {
        // No bloquear la UI por errores de consolidación; mostrar feedback
        const msg = e?.response?.data?.error || e?.message || "No se pudo iniciar la consolidación";
        setMensajeConsolidacion(`No se pudo iniciar la consolidación: ${msg}`);
      } finally {
        setAutoConsolidar(false);
      }
    };

    if (autoConsolidar && estado === "procesado") {
      lanzarConsolidacion();
    }
  }, [autoConsolidar, estado, cierreId]);

  return (
    <div className={`bg-gray-800 p-4 rounded-xl shadow-lg flex flex-col gap-3 ${isDisabled ? "opacity-60 pointer-events-none" : ""}`}>
      <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
        Corrección del Libro de Remuneraciones
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
        {puedeInteractuarConArchivo ? (
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            disabled={isDisabled}
            className={`px-3 py-1 rounded text-sm font-medium transition ${
              isDisabled ? "opacity-60 cursor-not-allowed" : ""
            } bg-green-600 hover:bg-green-700`}
            title="Adjuntar archivo Excel (.xlsx)"
          >
            {selectedFile ? "Cambiar archivo" : "Adjuntar archivo"}
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
          {selectedFile?.name || archivoNombre || "Ningún archivo seleccionado"}
        </span>
        {libroBorradoFlag && (
          <span className="text-xs bg-red-700/30 border border-red-600 text-red-300 px-2 py-0.5 rounded">
            Libro borrado
          </span>
        )}
      </div>

      <input
        type="file"
        accept=".xlsx"
        ref={fileInputRef}
        style={{ display: "none" }}
        onChange={handleSeleccionArchivo}
        disabled={isDisabled || !puedeInteractuarConArchivo}
      />

      {showConfirmDelete && (
        <div className="mt-2 p-3 rounded border border-yellow-500/40 bg-yellow-900/20">
          <div className="text-sm text-yellow-300 font-medium mb-2">
            Advertencia
          </div>
          <div className="text-xs text-yellow-200 mb-3">
            Subir este archivo implica eliminar todos los registros de libro anteriores. ¿Deseas continuar?
          </div>
          <div className="flex gap-2">
            <button
              type="button"
              className="px-3 py-1 rounded bg-red-600 hover:bg-red-700 text-white text-sm disabled:opacity-60 disabled:cursor-not-allowed"
              disabled={enviandoCorreccion}
              onClick={async () => {
                setError("");
                if (!cierreId || !selectedFile) {
                  setError("Falta el archivo o el cierre para continuar");
                  return;
                }
                try {
                  setEnviandoCorreccion(true);
                  await corregirLibroRemuneraciones(cierreId, selectedFile);
                  // Solo si valida OK, marcamos 'Libro borrado' y cerramos advertencia
                  setLibroBorradoFlag(true);
                  setShowConfirmDelete(false);
                  // Iniciar flujo estándar: subir archivo para análisis de headers
                  if (typeof onSubirArchivo === 'function') {
                    try {
                      await onSubirArchivo(selectedFile);
                      if (typeof onActualizarEstado === 'function') {
                        setTimeout(() => onActualizarEstado(), 500);
                      }
                    } catch (upErr) {
                      let msgUp = "Error al subir el archivo tras la validación";
                      const dataUp = upErr?.response?.data;
                      if (dataUp) {
                        msgUp = dataUp.detail || dataUp.message || dataUp.error || (Array.isArray(dataUp) ? dataUp[0] : (typeof dataUp === 'string' ? dataUp : msgUp));
                      } else if (upErr?.message) {
                        msgUp = upErr.message;
                      }
                      setError(msgUp);
                    }
                  }
                } catch (err) {
                  let msg = "Error enviando archivo";
                  const data = err?.response?.data;
                  if (data) {
                    msg = data.detail || data.message || data.error || (Array.isArray(data) ? data[0] : (typeof data === 'string' ? data : msg));
                  } else if (err?.message) {
                    msg = err.message;
                  }
                  setError(msg);
                } finally {
                  setEnviandoCorreccion(false);
                }
              }}
            >
              {enviandoCorreccion ? 'Enviando…' : 'Sí, borrar libro anterior'}
            </button>
            <button
              type="button"
              className="px-3 py-1 rounded bg-gray-600 hover:bg-gray-700 text-white text-sm"
              onClick={() => {
                setSelectedFile(null);
                setShowConfirmDelete(false);
              }}
            >
              Cancelar
            </button>
          </div>
        </div>
      )}

      {error && (
        <div className="text-xs text-red-400 mt-1 bg-red-900/20 p-2 rounded border-l-2 border-red-400">
          ❌ <strong>Error:</strong> {error}
        </div>
      )}

      {(estado === "no_subido" || estado === "pendiente") && (
        <div className="text-xs text-blue-400 mt-1 bg-blue-900/20 p-2 rounded">
          📋 <strong>Formato requerido:</strong> AAAAMM_libro_remuneraciones_RUT.xlsx
          <br />
          <span className="text-blue-300">Ejemplo: 202508_libro_remuneraciones_12345678.xlsx</span>
        </div>
      )}

      {isProcesando && (
        <div className="text-xs text-orange-400 mt-1 bg-orange-900/20 p-2 rounded border-l-2 border-orange-400">
          ⏳ <strong>Procesamiento en curso:</strong> El archivo se está procesando actualmente.
          <br />
          <span className="text-orange-300">Espera a que termine para poder cambiar el archivo si es necesario.</span>
        </div>
      )}

      {puedeProcesar ? (
        <button
          onClick={handleProcesar}
          disabled={isDisabled}
          className="mt-2 bg-blue-700 hover:bg-blue-600 px-3 py-1 rounded text-white text-sm font-medium transition shadow w-fit disabled:opacity-60 disabled:cursor-not-allowed flex items-center gap-2"
          title="Procesar archivo clasificado"
        >
          {isProcesando && <Loader2 size={16} className="animate-spin" />}
          {isProcesando ? "Procesando..." : "Procesar"}
        </button>
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

      {mensajeConsolidacion && (
        <div className="mt-2 text-xs text-blue-300 bg-blue-900/20 p-2 rounded border border-blue-700/40">
          {mensajeConsolidacion}
        </div>
      )}

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

export default LibroRemuneracionesCardCorreccion;
