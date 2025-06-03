//src/components/TarjetasCierre/TipoDocumentoCard.jsx

import { useEffect, useState, useRef } from "react";
import ModalTabla from "../ModalTabla"; // Asegúrate que esté en components/
import { Download } from "lucide-react";
import { 
  descargarPlantillaTipoDocumento, 
  obtenerEstadoTipoDocumento, 
  obtenerTiposDocumentoCliente, 
  subirTipoDocumento, 
  eliminarTodosTiposDocumento 
} from "../../api/contabilidad"; // Ajusta path según tu estructura

const TipoDocumentoCard = ({ clienteId, onCompletado, disabled }) => {
  const [estado, setEstado] = useState("pendiente");
  const [archivoNombre, setArchivoNombre] = useState("");
  const [subiendo, setSubiendo] = useState(false);
  const [error, setError] = useState("");
  const [modalAbierto, setModalAbierto] = useState(false);
  const [tiposDocumento, setTiposDocumento] = useState([]);
  const [eliminando, setEliminando] = useState(false);
  const [errorEliminando, setErrorEliminando] = useState("");
  const fileInputRef = useRef();

  // Cargar estado del tipo de documento al montar
  useEffect(() => {
    const fetchEstado = async () => {
      try {
        const data = await obtenerEstadoTipoDocumento(clienteId);
        const estadoActual = typeof data === "string" ? data : data.estado;
        setEstado(estadoActual);
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
        setError("Error al subir el archivo.");
        onCompletado && onCompletado(false); // <- IMPORTANTE: lo agregas aquí
      } finally {
        setSubiendo(false);
      }
    };


  // Handler para abrir modal y cargar lista
  const handleVerTiposDocumento = async () => {
    try {
      const datos = await obtenerTiposDocumentoCliente(clienteId);
      setTiposDocumento(datos);
      setModalAbierto(true);
    } catch (err) {
      setTiposDocumento([]);
      setModalAbierto(true);
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
      setModalAbierto(false);
      setArchivoNombre("");
      if (onCompletado) onCompletado(false); // <- Solo una vez aquí
    } catch (err) {
      setErrorEliminando("Error eliminando los tipos de documento");
    } finally {
      setEliminando(false);
    }
  };


  return (
    <div className={`bg-gray-800 p-4 rounded-xl shadow-lg flex flex-col gap-3 ${disabled ? "opacity-60 pointer-events-none" : ""}`}>
        <h3 className="text-lg font-semibold mb-3">1. Tipo de Documento</h3>
            <div className="flex items-center gap-2 mb-2">
                <span className="font-semibold">Estado:</span>
                {estado === "subido" ? (
                    <span className="text-green-400 font-semibold">Subido</span>
                    ) : (
                    <span className="text-yellow-400 font-semibold">Pendiente</span>
                )}
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
                Descargar Plantilla
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
            {error && <div className="text-xs text-red-400 mt-1">{error}</div>}
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
                <ModalTabla
                abierto={modalAbierto}
                onClose={() => setModalAbierto(false)}
                titulo="Tipos de Documento cargados"
                columnas={[
                    { key: "codigo", label: "Código" },
                    { key: "descripcion", label: "Descripción" }
                ]}
                datos={tiposDocumento}
                editable={true}
                onEliminarTodos={handleEliminarTodos}
                eliminando={eliminando}
                errorEliminando={errorEliminando}
                />
                <span className="text-xs text-gray-400 italic mt-2">
                {estado === "subido"
                    ? "✔ Archivo cargado correctamente"
                    : "Aún no se ha subido el archivo."}
                </span>
    </div>
);
}
export default TipoDocumentoCard;
