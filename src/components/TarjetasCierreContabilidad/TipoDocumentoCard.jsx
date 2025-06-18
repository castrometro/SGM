import { useEffect, useState, useRef } from "react";
import ModalTipoDocumentoCRUD from "./ModalTipoDocumentoCRUD";
import Notificacion from "../Notificacion";
import { Download } from "lucide-react";
import EstadoBadge from "../EstadoBadge";
import { 
  descargarPlantillaTipoDocumento, 
  obtenerEstadoTipoDocumento, 
  obtenerTiposDocumentoCliente, 
  registrarVistaTiposDocumento,
  subirTipoDocumento, 
  eliminarTodosTiposDocumento,
  obtenerEstadoUploadLog
} from "../../api/contabilidad";

const TipoDocumentoCard = ({ clienteId, cliente, onCompletado, disabled, numeroPaso }) => {
  const [estado, setEstado] = useState("pendiente");
  const [archivoNombre, setArchivoNombre] = useState("");
  const [subiendo, setSubiendo] = useState(false);
  const [error, setError] = useState("");
  const [modalAbierto, setModalAbierto] = useState(false);
  const [tiposDocumento, setTiposDocumento] = useState([]);
  const [eliminando, setEliminando] = useState(false);
  const [errorEliminando, setErrorEliminando] = useState("");
  const [notificacion, setNotificacion] = useState({ visible: false, tipo: "", mensaje: "" });
  
  // Estados para UploadLog
  const [uploadLogId, setUploadLogId] = useState(null);
  const [uploadEstado, setUploadEstado] = useState(null);
  const [uploadProgreso, setUploadProgreso] = useState("");
  
  const fileInputRef = useRef();

  // Función para mostrar notificaciones
  const mostrarNotificacion = (tipo, mensaje) => {
    setNotificacion({ visible: true, tipo, mensaje });
  };

  const cerrarNotificacion = () => {
    setNotificacion({ visible: false, tipo: "", mensaje: "" });
  };

  // Cargar estado del tipo de documento al montar
  useEffect(() => {
    const fetchEstado = async () => {
      try {
        const data = await obtenerEstadoTipoDocumento(clienteId);
        const estadoActual = typeof data === "string" ? data : data.estado;
        setEstado(estadoActual);
        
        // Si hay datos, cargar también los tipos de documento para el conteo
        if (estadoActual === "subido") {
          try {
            const tipos = await obtenerTiposDocumentoCliente(clienteId);
            setTiposDocumento(tipos);
          } catch (err) {
            console.error("Error cargando tipos de documento:", err);
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

  // Monitorear el estado del UploadLog cuando está en proceso
  useEffect(() => {
    if (!uploadLogId || !subiendo) return;

    const monitorearUpload = async () => {
      try {
        const logData = await obtenerEstadoUploadLog(uploadLogId);
        setUploadEstado(logData);
        
        // Actualizar el progreso visible
        if (logData.estado === 'procesando') {
          setUploadProgreso("Procesando archivo...");
          
          // Mostrar notificación amarilla solo la primera vez que entra en procesando
          if (uploadEstado?.estado !== 'procesando') {
            mostrarNotificacion("warning", "📊 Procesando archivo... Por favor espere.");
          }
          
        } else if (logData.estado === 'completado') {
          setUploadProgreso("¡Procesamiento completado!");
          setSubiendo(false);
          setEstado("subido");
          if (onCompletado) onCompletado(true);
          
          // Recargar tipos de documento
          try {
            const tipos = await obtenerTiposDocumentoCliente(clienteId);
            setTiposDocumento(tipos);
          } catch (err) {
            console.error("Error recargando tipos:", err);
          }
          
          mostrarNotificacion("success", `✅ Archivo procesado exitosamente. ${logData.resumen?.tipos_documento_creados || 0} tipos de documento creados.`);
          
        } else if (logData.estado === 'error') {
          setUploadProgreso("Error en el procesamiento");
          setSubiendo(false);
          setError(logData.errores || "Error desconocido en el procesamiento");
          if (onCompletado) onCompletado(false);
          mostrarNotificacion("error", `❌ Error: ${logData.errores || "Error desconocido"}`);
        }
        
      } catch (err) {
        console.error("Error monitoreando upload:", err);
        setUploadProgreso("Error monitoreando el proceso");
      }
    };

    // Iniciar monitoreo
    const intervalo = setInterval(monitorearUpload, 2000); // Cada 2 segundos
    
    // Limpieza
    return () => clearInterval(intervalo);
    
  }, [uploadLogId, subiendo, clienteId, onCompletado]);

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
    
    try {
      const formData = new FormData();
      formData.append("cliente_id", clienteId);
      formData.append("archivo", archivo);
      
      const response = await subirTipoDocumento(formData);
      
      // Obtener el ID del UploadLog para monitoreo
      if (response.upload_log_id) {
        setUploadLogId(response.upload_log_id);
        setUploadProgreso("Archivo recibido, iniciando procesamiento...");
        mostrarNotificacion("info", "📤 Archivo subido correctamente. Procesando...");
        
        // El monitoreo se hace automáticamente en el useEffect
      } else {
        // Fallback al método anterior si no hay upload_log_id
        await new Promise(r => setTimeout(r, 1500));
        let nuevoEstado = "";
        for (let i = 0; i < 10; i++) {
          await new Promise((r) => setTimeout(r, 1200));
          const data = await obtenerEstadoTipoDocumento(clienteId);
          nuevoEstado = typeof data === "string" ? data : data.estado;
          if (nuevoEstado === "subido") break;
        }
        setEstado(nuevoEstado);
        setSubiendo(false);
        setUploadProgreso("");
        
        if (nuevoEstado === "subido") {
          onCompletado && onCompletado(true);
          mostrarNotificacion("success", "✅ Archivo procesado exitosamente");
        } else {
          setError("No se pudo verificar la subida. Intenta refrescar.");
          onCompletado && onCompletado(false);
          mostrarNotificacion("warning", "⚠️ No se pudo verificar el estado. Intenta refrescar.");
        }
      }
      
    } catch (err) {
      console.error("Error al subir archivo:", err);
      setSubiendo(false);
      setUploadProgreso("");
      
      // Manejo específico para error 409 - Datos existentes
      if (err.response?.status === 409) {
        const errorData = err.response.data;
        setError(`Ya existen ${errorData.tipos_existentes || 'algunos'} tipos de documento. Debe eliminar todos los registros antes de subir un nuevo archivo.`);
        mostrarNotificacion("warning", 
          `⚠️ Archivo rechazado: Ya existen ${errorData.tipos_existentes || 'algunos'} tipos de documento. Use "Eliminar todos" primero.`
        );
      } else if (err.response?.status === 400) {
        // Error 400 - Problemas de validación, incluyendo nombre de archivo
        const errorData = err.response.data;
        if (errorData.formato_esperado && errorData.archivo_recibido) {
          // Error específico de formato de nombre
          setError(`Formato de nombre incorrecto. Esperado: ${errorData.formato_esperado}, Recibido: ${errorData.archivo_recibido}`);
          mostrarNotificacion("warning", 
            `❌ Nombre de archivo incorrecto\n\n` +
            `📋 Formato requerido: ${errorData.formato_esperado}\n` +
            `📁 Archivo enviado: ${errorData.archivo_recibido}\n\n` +
            `💡 Asegúrese de que el archivo siga exactamente el formato indicado.`
          );
        } else if (errorData.error) {
          // Otros errores de validación
          setError(errorData.error);
          mostrarNotificacion("error", errorData.mensaje || errorData.error);
        } else {
          setError("Error de validación en el archivo");
          mostrarNotificacion("error", "❌ Error de validación en el archivo");
        }
      } else if (err.response?.data?.error) {
        // Otros errores del backend
        setError(err.response.data.error);
        mostrarNotificacion("error", err.response.data.error);
      } else {
        // Error genérico
        setError("Error al subir el archivo.");
        mostrarNotificacion("error", "❌ Error al subir el archivo.");
      }
      
      onCompletado && onCompletado(false);
    }
  };


  // Handler para abrir modal y cargar lista
  const handleVerTiposDocumento = async () => {
    try {
      // Registrar que se abrió el modal manualmente
      await registrarVistaTiposDocumento(clienteId);
      
      // Cargar los datos
      const datos = await obtenerTiposDocumentoCliente(clienteId);
      setTiposDocumento(datos);
      setModalAbierto(true);
    } catch (err) {
      console.error("Error al abrir modal o registrar vista:", err);
      setTiposDocumento([]);
      setModalAbierto(true);
    }
  };

  // Handler para actualizar la lista de tipos de documento
  const handleActualizarTiposDocumento = async () => {
    try {
      const datos = await obtenerTiposDocumentoCliente(clienteId);
      setTiposDocumento(datos);
    } catch (err) {
      console.error("Error al actualizar tipos de documento:", err);
    }
  };

  // Handler para eliminar todos los tipos de documento
  const handleEliminarTodos = async () => {
    setEliminando(true);
    setErrorEliminando("");
    try {
      const result = await eliminarTodosTiposDocumento(clienteId);
      setEstado("pendiente");
      setTiposDocumento([]);
      setArchivoNombre("");
      setUploadLogId(null);
      setUploadEstado(null);
      setUploadProgreso("");
      if (onCompletado) onCompletado(false);
      
      // Mostrar información sobre lo que se eliminó
      const mensaje = `Eliminados: ${result.registros_eliminados || 0} registros, ${result.upload_logs_eliminados || 0} logs, ${result.archivos_eliminados || 0} archivos`;
      mostrarNotificacion("success", `🗑️ ${mensaje}`);
    } catch (err) {
      setErrorEliminando("Error eliminando los tipos de documento");
      mostrarNotificacion("error", "❌ Error eliminando los tipos de documento");
    } finally {
      setEliminando(false);
    }
  };


  return (
    <div className={`bg-gray-800 p-4 rounded-xl shadow-lg flex flex-col gap-3 ${disabled ? "opacity-60 pointer-events-none" : ""}`}>
        <h3 className="text-lg font-semibold mb-3">{numeroPaso}. Tipo de Documento</h3>
            <div className="flex items-center gap-2 mb-2">
                <span className="font-semibold">Estado:</span>
                <EstadoBadge estado={estado === "subido" ? "subido" : "pendiente"} />
            </div>
            {/* Botón estilizado de descarga */}
            <a
                href={descargarPlantillaTipoDocumento()}
                download
                className={`flex items-center gap-2 bg-gray-700 hover:bg-blue-600 px-3 py-1 rounded !text-white text-sm font-medium transition shadow w-fit mb-2 ${disabled ? "opacity-60 pointer-events-none" : ""}`}
                tabIndex={disabled ? -1 : 0}
                style={{ pointerEvents: disabled ? "none" : "auto" }}
                >
                <Download size={16} />
                Descargar Estructura
                </a>
            
            {/* Información del formato requerido */}
            <div className="text-xs text-gray-400 bg-gray-900/50 border border-gray-600 rounded p-2 mb-2">
                <div className="font-medium text-gray-300 mb-1">📋 Formato de archivo requerido:</div>
                <div className="font-mono text-yellow-300">
                    {cliente?.rut ? 
                        `${cliente.rut.replace(/\./g, '').replace('-', '')}_TipoDocumento.xlsx` : 
                        'RUT_TipoDocumento.xlsx'
                    }
                </div>
            </div>
            <div className="flex gap-3 items-center">
                <button
                    type="button"
                    onClick={() => fileInputRef.current.click()}
                    disabled={subiendo || disabled}
                    className={`bg-blue-600 hover:bg-blue-500 px-3 py-1 rounded text-sm font-medium transition ${
                    subiendo ? "opacity-60 cursor-not-allowed" : ""
                    }`}
                >
                    {subiendo ? (uploadProgreso || "Subiendo...") : "Elegir archivo .xlsx"}
                </button>
                <span className="text-gray-300 text-xs italic truncate max-w-xs">
                    {archivoNombre || "Ningún archivo seleccionado"}
                </span>
            </div>
            
            {/* Indicador de progreso detallado */}
            {subiendo && uploadEstado && (
              <div className="text-xs bg-blue-900/20 border border-blue-500/30 rounded p-2 mt-2">
                <div className="flex items-center justify-between mb-1">
                  <span className="font-medium text-blue-200">Procesando:</span>
                  <span className="text-blue-300">{uploadEstado.estado}</span>
                </div>
                {uploadEstado.registros_procesados > 0 && (
                  <div className="text-blue-300">
                    Registros: {uploadEstado.registros_exitosos || 0} exitosos, {uploadEstado.registros_fallidos || 0} fallidos
                  </div>
                )}
                {uploadEstado.tiempo_procesamiento_segundos && (
                  <div className="text-blue-300">
                    Tiempo: {uploadEstado.tiempo_procesamiento_segundos}s
                  </div>
                )}
              </div>
            )}
            <input
            type="file"
            accept=".xlsx"
            ref={fileInputRef}
            style={{ display: "none" }}
            onChange={handleSeleccionArchivo}
            />
            {error && (
              <div className="text-xs text-red-400 mt-1 p-2 bg-red-900/20 rounded border border-red-500/30">
                <p className="font-medium">⚠️ {error}</p>
                {error.includes("Ya existen") && (
                  <p className="mt-1 text-gray-300">
                    💡 Tip: Use el botón "Eliminar todos" para limpiar los datos existentes y luego suba el nuevo archivo.
                  </p>
                )}
              </div>
            )}
                <div className="flex gap-2 mt-2">
                    <button
                        onClick={handleVerTiposDocumento}
                        disabled={estado !== "subido"}
                        className={`px-3 py-1 rounded text-sm font-medium transition ${
                        estado === "subido"
                            ? "bg-blue-700 hover:bg-blue-600 text-white"
                            : "bg-gray-700 text-gray-400 cursor-not-allowed"
                        }`}
                    >
                        Ver tipos de documento
                    </button>
                </div>
                <ModalTipoDocumentoCRUD
                    abierto={modalAbierto}
                    onClose={() => setModalAbierto(false)}
                    clienteId={clienteId}
                    tiposDocumento={tiposDocumento}
                    onActualizar={handleActualizarTiposDocumento}
                    onEliminarTodos={handleEliminarTodos}
                    eliminando={eliminando}
                    errorEliminando={errorEliminando}
                    onNotificacion={mostrarNotificacion}
                />

                <span className="text-xs text-gray-400 italic mt-2">
                {estado === "subido"
                    ? `✔ Archivo cargado correctamente${tiposDocumento.length > 0 ? ` (${tiposDocumento.length} tipos de documento)` : ""}`
                    : "Aún no se ha subido el archivo."}
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
}
export default TipoDocumentoCard;
