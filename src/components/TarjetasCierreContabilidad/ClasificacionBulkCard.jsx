import { useState, useRef, useEffect } from "react";
import EstadoBadge from "../EstadoBadge";
import ModalClasificacionRegistrosRaw from "../ModalClasificacionRegistrosRaw";
import Notificacion from "../Notificacion";
import {
  Download,
  FileText,
  Trash2,
  RefreshCw,
  Settings,
  Database,
} from "lucide-react";
import {
  subirClasificacionBulk,
  obtenerBulkClasificaciones,
  obtenerEstadoClasificaciones,
  descargarPlantillaClasificacionBulk,
  eliminarBulkClasificacion,
  eliminarTodosBulkClasificacion,
  reprocesarBulkClasificacionUpload,
  obtenerClasificacionesArchivo,
  obtenerEstadoUploadLog,
} from "../../api/contabilidad";

const ClasificacionBulkCard = ({
  clienteId,
  cliente,
  onCompletado,
  disabled,
  numeroPaso,
}) => {
  console.log('🏗️ ClasificacionBulkCard props recibidos:', { 
    clienteId, 
    clienteExiste: !!cliente,
    clienteBilingue: cliente?.bilingue,
    clienteCompleto: cliente ? { id: cliente.id, nombre: cliente.nombre, bilingue: cliente.bilingue } : null,
    disabled,
    numeroPaso 
  });
  const [archivoNombre, setArchivoNombre] = useState("");
  const [estado, setEstado] = useState("pendiente");
  const [subiendo, setSubiendo] = useState(false);
  const [uploads, setUploads] = useState([]);
  const [error, setError] = useState("");
  const [ultimoUpload, setUltimoUpload] = useState(null);
  const [eliminando, setEliminando] = useState(false);
  const [errorEliminando, setErrorEliminando] = useState("");
  const [registrosRaw, setRegistrosRaw] = useState([]);

  const [notificacion, setNotificacion] = useState({
    visible: false,
    tipo: "",
    mensaje: "",
  });

  // Estados para UploadLog
  const [uploadLogId, setUploadLogId] = useState(null);
  const [uploadEstado, setUploadEstado] = useState(null);
  const [uploadProgreso, setUploadProgreso] = useState("");

  const mostrarNotificacion = (tipo, mensaje) => {
    setNotificacion({ visible: true, tipo, mensaje });
  };

  const cerrarNotificacion = () => {
    setNotificacion({ visible: false, tipo: "", mensaje: "" });
  };

  const [modalRegistrosRaw, setModalRegistrosRaw] = useState(false);
  const fileInputRef = useRef();

  // Cargar estado inicial al montar el componente
  useEffect(() => {
    const fetchEstadoInicial = async () => {
      try {
        const data = await obtenerEstadoClasificaciones(clienteId);
        setEstado(data.estado);
        setArchivoNombre(data.archivo_nombre || "");
        
        // Si hay archivo subido, también notificar como completado
        if (onCompletado) onCompletado(data.estado === "subido");
        
        // Siempre cargar datos detallados para verificar uploads existentes
        await cargar();
      } catch (err) {
        setEstado("pendiente");
        if (onCompletado) onCompletado(false);
        // Intentar cargar datos de uploads de todos modos
        try {
          await cargar();
        } catch (loadErr) {
          console.error("Error loading uploads:", loadErr);
        }
      }
    };
    
    if (clienteId && !disabled) fetchEstadoInicial();
  }, [clienteId, disabled, onCompletado]);

  // Monitorear estado del UploadLog
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
          
          // Actualizar estado desde el servidor
          try {
            const data = await obtenerEstadoClasificaciones(clienteId);
            setEstado(data.estado);
            setArchivoNombre(data.archivo_nombre || "");
            if (onCompletado) onCompletado(data.estado === "subido");
          } catch (err) {
            setEstado("pendiente");
            if (onCompletado) onCompletado(false);
          }
          
          cargar();
        } else if (logData.estado === "error") {
          setUploadProgreso("Error en el procesamiento");
          setSubiendo(false);
          setEstado("error");
          setError(logData.errores || "Error en el procesamiento");
        }
      } catch (err) {
        console.error("Error monitoreando upload:", err);
      }
    };

    const interval = setInterval(monitorearUpload, 3000);
    return () => clearInterval(interval);
  }, [uploadLogId, subiendo]);

  const cargar = async () => {
    try {
      const data = await obtenerBulkClasificaciones(clienteId);
      console.log("📤 Cargando uploads:", data);
      setUploads(data);
      const last = data && data.length > 0 ? data[0] : null;
      console.log("📋 Último upload encontrado:", last);
      setUltimoUpload(last);
      
      if (last && last.id) {
        console.log("🔗 Intentando cargar registros para upload ID:", last.id);
        // Cargar registros raw para mostrar información
        try {
          const registros = await obtenerClasificacionesArchivo(last.id);
          console.log("📊 Registros cargados:", registros.length);
          setRegistrosRaw(registros);
        } catch (err) {
          console.log("⚠️ No hay registros raw o error cargándolos:", err);
          setRegistrosRaw([]);
        }
      } else {
        console.log("❌ No hay último upload válido");
        setRegistrosRaw([]);
      }
    } catch (e) {
      console.error("💥 Error al cargar uploads:", e);
      setRegistrosRaw([]);
    }
  };

  const handleSeleccionArchivo = async (e) => {
    const archivo = e.target.files[0];
    if (!archivo) return;

    setArchivoNombre(archivo.name);
    setSubiendo(true);
    setError("");
    setUploadProgreso("Subiendo archivo...");
    setUploadLogId(null);
    setUploadEstado(null);

    const form = new FormData();
    form.append("cliente_id", clienteId);
    form.append("archivo", archivo);

    try {
      const response = await subirClasificacionBulk(form);

      if (response.upload_log_id) {
        setUploadLogId(response.upload_log_id);
        setUploadProgreso("Archivo recibido, iniciando procesamiento...");
        mostrarNotificacion(
          "info",
          "📤 Archivo subido correctamente. Procesando...",
        );
      } else {
        setUploadProgreso("");
        setTimeout(async () => {
          try {
            const data = await obtenerEstadoClasificaciones(clienteId);
            setEstado(data.estado);
            setArchivoNombre(data.archivo_nombre || "");
            if (onCompletado) onCompletado(data.estado === "subido");
          } catch (err) {
            setEstado("pendiente");
            if (onCompletado) onCompletado(false);
          }
          cargar();
        }, 1000);
      }
    } catch (e) {
      console.error("Error al subir archivo:", e);
      setSubiendo(false);
      setUploadProgreso("");

      if (e.response?.status === 409) {
        const msg =
          '⚠️ Ya hay clasificaciones existentes para este cliente. Para subir un nuevo archivo, primero debe eliminar las clasificaciones anteriores usando el botón \"Eliminar todos\" del historial.';
        setError(msg);
        mostrarNotificacion("warning", msg);
      } else if (
        e.response?.status === 400 &&
        e.response.data?.formato_esperado
      ) {
        const errData = e.response.data;
        setError(
          `Formato de nombre incorrecto. Esperado: ${errData.formato_esperado}, Recibido: ${errData.archivo_recibido}`,
        );
        mostrarNotificacion(
          "warning",
          `❌ Nombre de archivo incorrecto\n\n` +
            `📋 Formato requerido: ${errData.formato_esperado}\n` +
            `📁 Archivo enviado: ${errData.archivo_recibido}\n\n` +
            "💡 Asegúrese de que el archivo siga exactamente el formato indicado.",
        );
      } else if (e.response?.data?.error) {
        setError(e.response.data.error);
        mostrarNotificacion("error", e.response.data.error);
      } else {
        setError("Error al subir el archivo. Verifique el formato.");
        mostrarNotificacion("error", "❌ Error al subir el archivo.");
      }
      onCompletado && onCompletado(false);
      return;
    }
  };

  // Handler para eliminar todos los uploads
  const handleEliminarTodos = async () => {
    setEliminando(true);
    setErrorEliminando("");
    try {
      await eliminarTodosBulkClasificacion(clienteId);
      
      // Actualizar estado desde el servidor
      try {
        const data = await obtenerEstadoClasificaciones(clienteId);
        setEstado(data.estado);
        setArchivoNombre(data.archivo_nombre || "");
        if (onCompletado) onCompletado(data.estado === "subido");
      } catch (err) {
        setEstado("pendiente");
        setArchivoNombre("");
        if (onCompletado) onCompletado(false);
      }
      
      setUploads([]);
      setRegistrosRaw([]);
    } catch (err) {
      setErrorEliminando("Error al eliminar los archivos.");
    } finally {
      setEliminando(false);
    }
  };

  return (
    <div
      className={`bg-gray-800 p-4 rounded-xl shadow-lg flex flex-col gap-3 ${disabled ? "opacity-60 pointer-events-none" : ""}`}
    >
      <h3 className="text-lg font-semibold mb-3">
        {numeroPaso}. Subir Clasificaciones de Cuentas
      </h3>
      <div className="flex items-center gap-2 mb-2">
        <span className="font-semibold">Estado:</span>
        <EstadoBadge estado={estado} />
      </div>
      <a
        href={descargarPlantillaClasificacionBulk()}
        download
        className={`flex items-center gap-2 bg-gray-700 hover:bg-blue-600 px-3 py-1 rounded !text-white text-sm font-medium transition shadow w-fit mb-2 ${disabled ? "opacity-60 pointer-events-none" : ""}`}
      >
        <Download size={16} />
        Descargar Estructura
      </a>
      <div className="text-xs text-gray-400 bg-gray-900/50 border border-gray-600 rounded p-2 mb-2">
        <div className="font-medium text-gray-300 mb-1">
          📋 Formato de archivo requerido:
        </div>
        <div className="font-mono text-yellow-300">
          {cliente?.rut
            ? `${cliente.rut.replace(/\./g, "").replace("-", "")}_Clasificacion.xlsx`
            : "RUT_Clasificacion.xlsx"}
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
      />
      {subiendo && uploadEstado && (
        <div className="text-xs bg-blue-900/20 border border-blue-500/30 rounded p-2 mt-2">
          <div className="flex items-center justify-between mb-1">
            <span className="font-medium text-blue-200">Procesando:</span>
            <span className="text-blue-300">{uploadEstado.estado}</span>
          </div>
          {uploadEstado.registros_procesados > 0 && (
            <div className="text-blue-300">
              Registros: {uploadEstado.registros_exitosos || 0} exitosos,{" "}
              {uploadEstado.registros_fallidos || 0} fallidos
            </div>
          )}
          {uploadEstado.tiempo_procesamiento_segundos && (
            <div className="text-blue-300">
              Tiempo: {uploadEstado.tiempo_procesamiento_segundos}s
            </div>
          )}
        </div>
      )}
      {error && (
        <div className="text-xs text-red-400 mt-1 p-2 bg-red-900/20 rounded border border-red-500/30">
          <p className="font-medium">⚠️ {error}</p>
          {error.includes("Eliminar todos") && (
            <p className="mt-1 text-gray-300">
              💡 Tip: Use el botón "Eliminar todos" para limpiar los datos
              existentes y luego suba el nuevo archivo.
            </p>
          )}
        </div>
      )}

      {/* Botones de acciones */}
      <div className="flex gap-2 mt-2">
        <button
          onClick={() => {
            console.log("🔘 Botón 'Ver clasificaciones' clickeado");
            console.log("📋 ultimoUpload:", ultimoUpload);
            console.log("🆔 ultimoUpload?.id:", ultimoUpload?.id);
            console.log("✅ Botón habilitado:", !!ultimoUpload?.id);
            
            if (!ultimoUpload?.id) {
              alert("⚠️ No hay datos de archivo para mostrar. Asegúrese de que el archivo se haya subido correctamente.");
              return;
            }
            
            setModalRegistrosRaw(true);
          }}
          className={`px-3 py-1 rounded text-sm font-medium transition flex items-center gap-2 ${
            !ultimoUpload?.id 
              ? 'bg-gray-600 text-gray-300 cursor-not-allowed' 
              : 'bg-blue-700 hover:bg-blue-600 text-white'
          }`}
          title={!ultimoUpload?.id ? "No hay datos de archivo disponibles" : "Ver y gestionar clasificaciones"}
        >
          <Settings size={16} />
          Ver clasificaciones
          {!ultimoUpload?.id && <span className="text-xs ml-1">(No disponible)</span>}
        </button>
      </div>

      {/* Información del estado y resumen */}
      <div className="text-xs text-gray-400 italic mt-2">
        {estado === "subido" ? (
          <div className="space-y-2">
            <div className="text-green-400">
              ✔ Archivo subido correctamente
            </div>
            {archivoNombre && (
              <div className="text-gray-300">
                📄 Archivo: {archivoNombre}
              </div>
            )}
            
            {/* Mostrar información de registros raw si están disponibles */}
            {registrosRaw.length > 0 && (
              <div className="text-blue-300">
                📋 {registrosRaw.length} registros disponibles para mapeo
              </div>
            )}
            
            {/* Mostrar resumen del procesamiento si está disponible */}
            {ultimoUpload?.resumen && (
              <div className="space-y-1">
                <div>
                  📊 {ultimoUpload.resumen.registros_guardados || 0} registros
                  guardados de {ultimoUpload.resumen.total_filas || 0} filas
                  {ultimoUpload.resumen.filas_vacias > 0 && (
                    <span className="text-gray-500">
                      {" "}
                      • {ultimoUpload.resumen.filas_vacias} filas vacías omitidas
                    </span>
                  )}
                </div>
                {ultimoUpload.resumen.sets_encontrados?.length > 0 && (
                  <div>
                    📋 Sets encontrados:{" "}
                    {ultimoUpload.resumen.sets_encontrados.join(", ")}
                  </div>
                )}
                {ultimoUpload.resumen.errores_count > 0 && (
                  <div className="text-yellow-400">
                    ⚠ {ultimoUpload.resumen.errores_count} errores encontrados en
                    el procesamiento
                  </div>
                )}
              </div>
            )}
          </div>
        ) : estado === "procesando" ? (
          <div className="text-blue-400">🔄 Procesando archivo…</div>
        ) : estado === "error" ? (
          <div className="text-red-400">❌ Error en el procesamiento</div>
        ) : (
          <div>Aún no se ha subido el archivo.</div>
        )}
      </div>

      {/* Modal de registros raw */}
      <ModalClasificacionRegistrosRaw
        isOpen={modalRegistrosRaw}
        onClose={() => setModalRegistrosRaw(false)}
        uploadId={ultimoUpload?.id}
        clienteId={clienteId}
        cliente={cliente}
        onDataChanged={() => {
          cargar(); // Recargar datos después de cambios CRUD
        }}
      />

      <Notificacion
        tipo={notificacion.tipo}
        mensaje={notificacion.mensaje}
        visible={notificacion.visible}
        onClose={cerrarNotificacion}
      />
    </div>
  );
};

export default ClasificacionBulkCard;
