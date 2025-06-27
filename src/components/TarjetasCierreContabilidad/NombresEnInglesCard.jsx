import { useEffect, useState, useRef } from "react";
import ModalNombresInglesCRUD from "./ModalNombresInglesCRUD";
import Notificacion from "../Notificacion";
import { Download } from "lucide-react";
import EstadoBadge from "../EstadoBadge";
import { 
  descargarPlantillaNombresEnIngles,
  obtenerEstadoNombresIngles,
  obtenerNombresInglesCliente,
  registrarVistaNombresIngles,
  subirNombresIngles,
  eliminarTodosNombresIngles,
  obtenerEstadoUploadLog
} from "../../api/contabilidad";

const NombresEnInglesCard = ({
  clienteId,
  cliente = null,
  onCompletado,
  disabled,
  numeroPaso
}) => {
  const [estado, setEstado] = useState("pendiente");
  const [archivoNombre, setArchivoNombre] = useState("");
  const [subiendo, setSubiendo] = useState(false);
  const [error, setError] = useState("");
  const [modalAbierto, setModalAbierto] = useState(false);
  const [nombresIngles, setNombresIngles] = useState([]);
  const [eliminando, setEliminando] = useState(false);
  const [errorEliminando, setErrorEliminando] = useState("");
  const [notificacion, setNotificacion] = useState({ visible: false, tipo: "", mensaje: "" });
  const fileInputRef = useRef();

  // Estados para UploadLog (monitoreo en tiempo real)
  const [uploadLogId, setUploadLogId] = useState(null);
  const [uploadEstado, setUploadEstado] = useState(null);
  const [uploadProgreso, setUploadProgreso] = useState("");

  // Función para mostrar notificaciones
  const mostrarNotificacion = (tipo, mensaje) => {
    setNotificacion({ visible: true, tipo, mensaje });
  };

  const cerrarNotificacion = () => {
    setNotificacion({ visible: false, tipo: "", mensaje: "" });
  };

  // Cargar estado de nombres en inglés al montar
  useEffect(() => {
    const fetchEstado = async () => {
      if (!clienteId) {
        setEstado("pendiente");
        if (onCompletado) onCompletado(false);
        return;
      }
      try {
        const data = await obtenerEstadoNombresIngles(clienteId);
        const estadoActual = typeof data === "string" ? data : data.estado;
        setEstado(estadoActual);
        
        // Si hay datos, cargar también los nombres en inglés para el conteo
        if (estadoActual === "subido") {
          try {
            const nombres = await obtenerNombresInglesCliente(clienteId);
            setNombresIngles(Array.isArray(nombres) ? nombres : []);
          } catch (err) {
            console.error("Error cargando nombres en inglés:", err);
            setNombresIngles([]);
          }
        }

        if (onCompletado) onCompletado(estadoActual === "subido");
      } catch (err) {
        setEstado("pendiente");
        if (onCompletado) onCompletado(false);
      }
    };
    if (clienteId && !disabled) fetchEstado();
  }, [clienteId, disabled, onCompletado]);

  useEffect(() => {
    if (!uploadLogId || !subiendo) return;

    const monitorearUpload = async () => {
      try {
        const logData = await obtenerEstadoUploadLog(uploadLogId);
        setUploadEstado(logData);

        if (logData.estado === "procesando") {
          setUploadProgreso("Procesando archivo...");
        } else if (logData.estado === "completado") {
          setUploadProgreso("¡Procesamiento completado!");
          setSubiendo(false);
          setEstado("subido");
          if (onCompletado) onCompletado(true);

          try {
            const nombres = await obtenerNombresInglesCliente(clienteId);
            setNombresIngles(Array.isArray(nombres) ? nombres : []);
          } catch (err) {
            console.error("Error recargando nombres:", err);
            setNombresIngles([]);
          }

          const creados = logData.resumen?.nombres_creados || 0;
          mostrarNotificacion(
            "success",
            `✅ Archivo procesado exitosamente. ${creados} nombres almacenados.`
          );

        } else if (logData.estado === "error") {
          setUploadProgreso("Error en el procesamiento");
          setSubiendo(false);
          setEstado("error");
          const msg = logData.errores || "Error en el procesamiento";
          setError(msg);
          mostrarNotificacion("error", msg);
          if (onCompletado) onCompletado(false);
        }

      } catch (err) {
        console.error('Error monitoreando upload:', err);
        setUploadProgreso('Error monitoreando el proceso');
      }
    };

    const intervalo = setInterval(monitorearUpload, 2000);
    return () => clearInterval(intervalo);

  }, [uploadLogId, subiendo, clienteId, onCompletado, uploadEstado?.estado]);

  // Handler de subida de archivo
  const handleSeleccionArchivo = async (e) => {
    const archivo = e.target.files[0];
    if (!archivo) return;
    setArchivoNombre(archivo.name);
    setSubiendo(true);
    setError("");
    setUploadProgreso("Subiendo archivo...");
    setUploadLogId(null);
    setUploadEstado(null);
    let newUploadId = null;
    try {
      const formData = new FormData();
      formData.append('cliente_id', clienteId);
      formData.append('archivo', archivo);

      const response = await subirNombresIngles(formData);

      if (response.upload_log_id) {
        newUploadId = response.upload_log_id;
        setUploadLogId(newUploadId);
        setEstado("procesando");
        setUploadProgreso("Archivo recibido, iniciando procesamiento...");
        mostrarNotificacion("info", "📤 Archivo subido correctamente. Procesando...");
      } else {
        setEstado("procesando");
        setUploadProgreso("");
        setTimeout(() => {
          handleActualizarNombresIngles();
        }, 1000);
      }
    } catch (err) {
      console.error("Error al subir archivo:", err);
      
      // Manejo específico para error 409 - Datos existentes
      if (err.response?.status === 409) {
        const msg =
          '⚠️ Ya hay nombres en inglés existentes para este cliente. Para subir un nuevo archivo, primero debe eliminar los nombres en inglés anteriores usando el botón "Eliminar todos".';
        setError(msg);
        mostrarNotificacion("warning", msg);
      } else if (
        err.response?.status === 400 &&
        err.response.data?.formato_esperado
      ) {
        const errData = err.response.data;
        setError(
          `Formato de nombre incorrecto. Esperado: ${errData.formato_esperado}, Recibido: ${errData.archivo_recibido}`
        );
        mostrarNotificacion(
          "warning",
          `❌ Nombre de archivo incorrecto\n\n` +
            `📋 Formato requerido: ${errData.formato_esperado}\n` +
            `📁 Archivo enviado: ${errData.archivo_recibido}\n\n` +
            "💡 Asegúrese de que el archivo siga exactamente el formato indicado."
        );
      } else if (err.response?.data?.error) {
        setError(err.response.data.error);
        mostrarNotificacion("error", err.response.data.error);
      } else {
        setError("Error al subir el archivo. Verifique el formato.");
        mostrarNotificacion("error", "❌ Error al subir el archivo.");
      }
      
      onCompletado && onCompletado(false);
    } finally {
      if (!newUploadId) setSubiendo(false);
    }
  };

  // Handler para abrir modal y cargar lista
  const handleVerNombresIngles = async () => {
    try {
      // Registrar que se abrió el modal manualmente
      await registrarVistaNombresIngles(clienteId);
      
      // Cargar los datos
      const datos = await obtenerNombresInglesCliente(clienteId);
      setNombresIngles(Array.isArray(datos) ? datos : []);
      setModalAbierto(true);
    } catch (err) {
      console.error("Error al abrir modal o registrar vista:", err);
      setNombresIngles([]);
      setModalAbierto(true);
    }
  };

  // Handler para actualizar la lista de nombres en inglés
  const handleActualizarNombresIngles = async () => {
    try {
      const datos = await obtenerNombresInglesCliente(clienteId);
      setNombresIngles(Array.isArray(datos) ? datos : []);
    } catch (err) {
      console.error("Error al actualizar nombres en inglés:", err);
      setNombresIngles([]);
    }
  };

  // Handler para eliminar todos los nombres en inglés
  const handleEliminarTodos = async () => {
    setEliminando(true);
    setErrorEliminando("");
    try {
      const result = await eliminarTodosNombresIngles(clienteId);
      setEstado("pendiente");
      setNombresIngles([]);
      setArchivoNombre("");
      setUploadLogId(null);
      setUploadEstado(null);
      setUploadProgreso("");
      if (onCompletado) onCompletado(false);
      const mensaje = `Eliminados: ${result.registros_eliminados || 0} registros, ${result.upload_logs_conservados || 0} logs, ${result.archivos_eliminados || 0} archivos`;
      mostrarNotificacion("success", `🗑️ ${mensaje}`);
    } catch (err) {
      setErrorEliminando("Error eliminando los nombres en inglés");
      mostrarNotificacion("error", "❌ Error eliminando los nombres en inglés");
    } finally {
      setEliminando(false);
    }
  };

  return (
    <div className={`bg-gray-800 p-4 rounded-xl shadow-lg flex flex-col gap-3 ${disabled ? "opacity-60 pointer-events-none" : ""}`}>
      <h3 className="text-lg font-semibold mb-3">{numeroPaso}. Nombres en inglés de cuentas</h3>
      
      <div className="flex items-center gap-2 mb-2">
        <span className="font-semibold">Estado:</span>
        <EstadoBadge estado={estado === "subido" ? "subido" : "pendiente"} />
      </div>
      
      {/* Botón estilizado de descarga */}
      <a
        href={descargarPlantillaNombresEnIngles()}
        download
        className={`flex items-center gap-2 bg-gray-700 hover:bg-blue-600 px-3 py-1 rounded !text-white text-sm font-medium transition shadow w-fit mb-2 ${disabled ? 'opacity-60 pointer-events-none' : ''}`}
        tabIndex={disabled ? -1 : 0}
        style={{ pointerEvents: disabled ? "none" : "auto" }}
      >
        <Download size={16} />
        Descargar Plantilla
      </a>

      {/* Información del formato requerido */}
      <div className="text-xs text-gray-400 bg-gray-900/50 border border-gray-600 rounded p-2 mb-2">
        <div className="font-medium text-gray-300 mb-1">📋 Formato de archivo requerido:</div>
        <div className="font-mono text-yellow-300">
          {cliente?.rut
            ? `${cliente.rut.replace(/\./g, '').replace('-', '')}_NombresIngles.xlsx`
            : 'RUT_NombresIngles.xlsx'}
        </div>
      </div>
      
      <div className="flex gap-3 items-center">
        <button
          type="button"
          onClick={() => fileInputRef.current.click()}
          disabled={subiendo || disabled}
          className={`bg-blue-600 hover:bg-blue-500 px-3 py-1 rounded text-sm font-medium transition ${subiendo ? "opacity-60 cursor-not-allowed" : ""}`}
        >
          {subiendo ? uploadProgreso || "Subiendo..." : "Elegir archivo .xlsx"}
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

      {subiendo && uploadEstado && (
        <div className="text-xs bg-blue-900/20 border border-blue-500/30 rounded p-2 mt-2">
          <div className="flex items-center justify-between mb-1">
            <span className="font-medium text-blue-200">Procesando:</span>
            <span className="text-blue-300">{uploadEstado.estado}</span>
          </div>
          {uploadEstado.resumen?.nombres_creados !== undefined && (
            <div className="text-blue-300">
              Nombres: {uploadEstado.resumen.nombres_creados}
            </div>
          )}
          {uploadEstado.tiempo_procesamiento && (
            <div className="text-blue-300">
              Tiempo: {uploadEstado.tiempo_procesamiento}
            </div>
          )}
        </div>
      )}
      
      {error && (
        <div className="text-xs text-red-400 mt-1 p-2 bg-red-900/20 rounded border border-red-500/30">
          <p className="font-medium">⚠️ {error}</p>
          {error.includes("Ya hay") && (
            <p className="mt-1 text-gray-300">
              💡 Tip: Use el botón "Eliminar todos" para limpiar los datos existentes y luego suba el nuevo archivo.
            </p>
          )}
        </div>
      )}
      
      <div className="flex gap-2 mt-2">
        <button
          onClick={handleVerNombresIngles}
          disabled={estado !== "subido"}
          className={`px-3 py-1 rounded text-sm font-medium transition ${
            estado === "subido"
              ? "bg-blue-700 hover:bg-blue-600 text-white"
              : "bg-gray-700 text-gray-400 cursor-not-allowed"
          }`}
        >
          Ver nombres en inglés
        </button>
      </div>
      
      <ModalNombresInglesCRUD
        abierto={modalAbierto}
        onClose={() => setModalAbierto(false)}
        clienteId={clienteId}
        nombresIngles={nombresIngles}
        onActualizar={handleActualizarNombresIngles}
        onEliminarTodos={handleEliminarTodos}
        eliminando={eliminando}
        errorEliminando={errorEliminando}
        onNotificacion={mostrarNotificacion}
      />

      <span className="text-xs text-gray-400 italic mt-2">
        {estado === "subido" ? (
          <span className="text-green-400">
            {`✔ Archivo procesado correctamente${Array.isArray(nombresIngles) && nombresIngles.length > 0 ? ` (${nombresIngles.length} nombres en inglés)` : ""}`}
          </span>
        ) : estado === "procesando" ? (
          <span className="text-blue-400">🔄 {uploadProgreso || 'Procesando nombres en inglés…'}</span>
        ) : estado === "error" && error ? (
          <span className="text-red-400">❌ Error: {error}</span>
        ) : nombresIngles.length > 0 ? (
          <span className="text-yellow-400">📋 Archivo cargado con {nombresIngles.length} nombres en inglés</span>
        ) : (
          "Aún no se ha subido el archivo de nombres en inglés."
        )}
      </span>
      
      {/* Componente de notificación */}
      <Notificacion
        tipo={notificacion.tipo}
        mensaje={notificacion.mensaje}
        visible={notificacion.visible}
        onClose={cerrarNotificacion}
      />
    </div>
  );
};

export default NombresEnInglesCard;
