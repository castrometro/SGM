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
  eliminarTodosNombresIngles
} from "../../api/contabilidad";

const NombresEnInglesCard = ({
  cierreId,
  clienteId,
  clasificacionReady,
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
      if (!cierreId || !clienteId || !clasificacionReady) {
        setEstado("pendiente");
        if (onCompletado) onCompletado(false);
        return;
      }
      try {
        const data = await obtenerEstadoNombresIngles(clienteId, cierreId);
        const estadoActual = typeof data === "string" ? data : data.estado;
        setEstado(estadoActual);
        
        // Si hay datos, cargar también los nombres en inglés para el conteo
        if (estadoActual === "subido") {
          try {
            const nombres = await obtenerNombresInglesCliente(clienteId);
            setNombresIngles(nombres);
          } catch (err) {
            console.error("Error cargando nombres en inglés:", err);
          }
        }
        
        if (onCompletado) onCompletado(estadoActual === "subido");
      } catch (err) {
        setEstado("pendiente");
        if (onCompletado) onCompletado(false);
      }
    };
    if (clienteId && !disabled) fetchEstado();
  }, [cierreId, clienteId, clasificacionReady, disabled, onCompletado]);

  // Handler de subida de archivo
  const handleSeleccionArchivo = async (e) => {
    const archivo = e.target.files[0];
    if (!archivo) return;
    setArchivoNombre(archivo.name);
    setSubiendo(true);
    setError("");
    try {
      const formData = new FormData();
      formData.append('cliente_id', clienteId);
      formData.append('cierre', cierreId);
      formData.append('archivo', archivo);
      
      await subirNombresIngles(formData);

      // Espera backend/process
      await new Promise(r => setTimeout(r, 1500));
      let nuevoEstado = "";
      for (let i = 0; i < 10; i++) {
        await new Promise((r) => setTimeout(r, 1200));
        const data = await obtenerEstadoNombresIngles(clienteId, cierreId);
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
        setError("Ya hay archivos de nombres en inglés existentes para este cierre. Para subir un nuevo archivo, primero debe eliminar los archivos anteriores usando el botón 'Eliminar todos'.");
        mostrarNotificacion("warning", "Archivo rechazado: Ya existen nombres en inglés. Use 'Eliminar todos' primero.");
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
  const handleVerNombresIngles = async () => {
    try {
      // Registrar que se abrió el modal manualmente
      await registrarVistaNombresIngles(clienteId);
      
      // Cargar los datos
      const datos = await obtenerNombresInglesCliente(clienteId);
      setNombresIngles(datos);
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
      setNombresIngles(datos);
    } catch (err) {
      console.error("Error al actualizar nombres en inglés:", err);
    }
  };

  // Handler para eliminar todos los nombres en inglés
  const handleEliminarTodos = async () => {
    setEliminando(true);
    setErrorEliminando("");
    try {
      await eliminarTodosNombresIngles(clienteId);
      setEstado("pendiente");
      setNombresIngles([]);
      setArchivoNombre("");
      if (onCompletado) onCompletado(false);
    } catch (err) {
      setErrorEliminando("Error eliminando los nombres en inglés");
    } finally {
      setEliminando(false);
    }
  };

  return (
    <div className={`bg-gray-800 p-4 rounded-xl shadow-lg flex flex-col gap-3 ${!clasificacionReady || disabled ? "opacity-60 pointer-events-none" : ""}`}>
      <h3 className="text-lg font-semibold mb-3">{numeroPaso}. Nombres en inglés de cuentas</h3>
      
      <div className="flex items-center gap-2 mb-2">
        <span className="font-semibold">Estado:</span>
        <EstadoBadge estado={estado === "subido" ? "subido" : "pendiente"} />
      </div>
      
      {/* Botón estilizado de descarga */}
      <a
        href={descargarPlantillaNombresEnIngles()}
        download
        className={`flex items-center gap-2 bg-gray-700 hover:bg-blue-600 px-3 py-1 rounded !text-white text-sm font-medium transition shadow w-fit mb-2 ${!clasificacionReady || disabled ? 'opacity-60 pointer-events-none' : ''}`}
        tabIndex={!clasificacionReady || disabled ? -1 : 0}
        style={{ pointerEvents: !clasificacionReady || disabled ? "none" : "auto" }}
      >
        <Download size={16} />
        Descargar Plantilla
      </a>
      
      <div className="flex gap-3 items-center">
        <button
          type="button"
          onClick={() => fileInputRef.current.click()}
          disabled={subiendo || !clasificacionReady || disabled}
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
        disabled={subiendo || !clasificacionReady || disabled}
      />
      
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
        cierreId={cierreId}
        nombresIngles={nombresIngles}
        onActualizar={handleActualizarNombresIngles}
        onEliminarTodos={handleEliminarTodos}
        eliminando={eliminando}
        errorEliminando={errorEliminando}
        onNotificacion={mostrarNotificacion}
      />

      <span className="text-xs text-gray-400 italic mt-2">
        {estado === "subido"
          ? `✔ Archivo cargado correctamente${nombresIngles.length > 0 ? ` (${nombresIngles.length} nombres en inglés)` : ""}`
          : "Aún no se ha subido el archivo de nombres en inglés."}
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
