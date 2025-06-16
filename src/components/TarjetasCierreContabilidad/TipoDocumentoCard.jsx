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
  eliminarTodosTiposDocumento 
} from "../../api/contabilidad";

const TipoDocumentoCard = ({ clienteId, onCompletado, disabled, numeroPaso }) => {
  const [estado, setEstado] = useState("pendiente");
  const [archivoNombre, setArchivoNombre] = useState("");
  const [subiendo, setSubiendo] = useState(false);
  const [error, setError] = useState("");
  const [modalAbierto, setModalAbierto] = useState(false);
  const [tiposDocumento, setTiposDocumento] = useState([]);
  const [eliminando, setEliminando] = useState(false);
  const [errorEliminando, setErrorEliminando] = useState("");
  const [notificacion, setNotificacion] = useState({ visible: false, tipo: "", mensaje: "" });
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

  // Handler de subida de archivo
    const handleSeleccionArchivo = async (e) => {
      const archivo = e.target.files[0];
      if (!archivo) return;
      setArchivoNombre(archivo.name);
      setSubiendo(true);
      setError("");
      try {
        const formData = new FormData();
        formData.append("cliente_id", clienteId);
        formData.append("archivo", archivo);
        await subirTipoDocumento(formData);

        // Espera backend/process
        await new Promise(r => setTimeout(r, 1500));
        let nuevoEstado = "";
        for (let i = 0; i < 10; i++) {
          await new Promise((r) => setTimeout(r, 1200));
          const data = await obtenerEstadoTipoDocumento(clienteId);
          nuevoEstado = typeof data === "string" ? data : data.estado;
          if (nuevoEstado === "subido") break;
        }
        setEstado(nuevoEstado);
        if (nuevoEstado === "subido") {
          onCompletado && onCompletado(true);
        } else {
          setError("No se pudo verificar la subida. Intenta refrescar.");
          onCompletado && onCompletado(false);
        }
      } catch (err) {
        console.error("Error al subir archivo:", err);
        
        // Manejo específico para error 409 - Datos existentes
        if (err.response?.status === 409) {
          const errorData = err.response.data;
          setError(`Ya existen ${errorData.tipos_existentes || 'algunos'} tipos de documento. Debe eliminar todos los registros antes de subir un nuevo archivo.`);
          mostrarNotificacion("warning", 
            `Archivo rechazado: Ya existen ${errorData.tipos_existentes || 'algunos'} tipos de documento. Use "Eliminar todos" primero.`
          );
        } else if (err.response?.data?.error) {
          // Otros errores del backend
          setError(err.response.data.error);
          mostrarNotificacion("error", err.response.data.error);
        } else {
          // Error genérico
          setError("Error al subir el archivo.");
          mostrarNotificacion("error", "Error al subir el archivo.");
        }
        
        onCompletado && onCompletado(false);
      } finally {
        setSubiendo(false);
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
      await eliminarTodosTiposDocumento(clienteId);
      setEstado("pendiente");
      setTiposDocumento([]);
      setArchivoNombre("");
      if (onCompletado) onCompletado(false);
    } catch (err) {
      setErrorEliminando("Error eliminando los tipos de documento");
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
            <div className="flex gap-3 items-center">
                <button
                    type="button"
                    onClick={() => fileInputRef.current.click()}
                    disabled={subiendo || disabled}
                    className={`bg-blue-600 hover:bg-blue-500 px-3 py-1 rounded text-sm font-medium transition ${
                    subiendo ? "opacity-60 cursor-not-allowed" : ""
                    }`}
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
