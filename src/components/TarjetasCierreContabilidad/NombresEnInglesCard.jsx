import { useEffect, useState, useRef } from "react";
import { 
  obtenerEstadoNombresIngles, 
  subirNombresInglesUpload,
  obtenerNombresInglesUploads,
  eliminarNombresInglesUpload,
  eliminarTodosNombresInglesUpload,
  reprocesarNombresInglesUpload,
  descargarPlantillaNombresEnIngles
} from "../../api/contabilidad";
import EstadoBadge from "../EstadoBadge";
import HistorialCambios from '../HistorialCambios';
import { Download, Eye, FileText, Trash2, RefreshCw, History } from 'lucide-react';

const NombresEnInglesCard = ({
  cierreId,
  clienteId,
  clasificacionReady,
  onCompletado,
  disabled,
  numeroPaso
}) => {
  const [estado, setEstado] = useState("pendiente");
  const [archivo, setArchivo] = useState(null);
  const [subiendo, setSubiendo] = useState(false);
  const [error, setError] = useState("");
  const [faltantes, setFaltantes] = useState(0);
  const [totalCuentas, setTotalCuentas] = useState(0);
  const [uploads, setUploads] = useState([]);
  const [modalAbierto, setModalAbierto] = useState(false);
  const [historialAbierto, setHistorialAbierto] = useState(false);
  const [eliminando, setEliminando] = useState(false);
  const [errorEliminando, setErrorEliminando] = useState("");
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

        const total = data.total || 0;
        const faltantes = data.faltantes ? data.faltantes.length : 0;
        
        // Lógica corregida: solo está completado si hay cuentas Y todas están traducidas
        const esCompletado = total > 0 && faltantes === 0 && data.estado === "subido";
        
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
  }, [cierreId, clienteId, clasificacionReady]); // Removido onCompletado de las dependencias

  const handleSeleccionArchivo = (e) => {
    const archivoSeleccionado = e.target.files[0];
    if (!archivoSeleccionado) return;
    setArchivo(archivoSeleccionado);
  };
   
  const handleSubir = async () => {
    if (!archivo) {
      setError("Debes seleccionar un archivo .xlsx");
      return;
    }
    
    setSubiendo(true);
    setError("");
    
    const formData = new FormData();
    formData.append('cliente', clienteId);
    formData.append('cierre', cierreId);
    formData.append('archivo', archivo);
    
    try {
      await subirNombresInglesUpload(formData);
      setArchivo(null);
      setEstado('procesando');
      
      // Refresca estado después de un momento
      setTimeout(() => {
        if (typeof window !== "undefined") window.location.reload();
      }, 1000);
    } catch (err) {
      console.error('Error al subir archivo:', err);
      
      // Manejo específico para error 409 (datos ya existentes)
      if (err.response?.status === 409) {
        setError(
          "⚠️ Ya hay archivos de nombres en inglés existentes para este cierre. " +
          "Para subir un nuevo archivo, primero debe eliminar los archivos anteriores " +
          "usando el botón 'Eliminar todos' en la sección 'Ver uploads'."
        );
      } else {
        setError("Error al subir el archivo.");
      }
      if (onCompletado) onCompletado(false);
    } finally {
      setSubiendo(false);
    }
  };

  // Handler para abrir modal y cargar lista
  const handleVerUploads = async () => {
    try {
      const datos = await obtenerNombresInglesUploads(clienteId, cierreId);
      setUploads(datos);
      setModalAbierto(true);
    } catch (err) {
      setUploads([]);
      setModalAbierto(true);
    }
  };

  // Handler para eliminar todos los uploads
  const handleEliminarTodos = async () => {
    setEliminando(true);
    setErrorEliminando("");
    try {
      await eliminarTodosNombresInglesUpload(clienteId);
      setEstado("pendiente");
      setUploads([]);
      setModalAbierto(false);
      // Actualizar el estado de la tarjeta
      setTimeout(async () => {
        // Refresca el estado después de eliminar
        if (cierreId && clienteId && clasificacionReady) {
          try {
            const data = await obtenerEstadoNombresIngles(clienteId, cierreId);
            const total = data.total || 0;
            const faltantes = data.faltantes ? data.faltantes.length : 0;
            const esCompletado = total > 0 && faltantes === 0 && data.estado === "subido";
            setEstado(esCompletado ? "subido" : "pendiente");
            setFaltantes(faltantes);
            setTotalCuentas(total);
          } catch (err) {
            setEstado("pendiente");
          }
        }
      }, 500);
      if (onCompletado) onCompletado(false);
    } catch (err) {
      setErrorEliminando("Error al eliminar los archivos.");
    } finally {
      setEliminando(false);
    }
  };

  // Handler para reprocesar un upload específico
  const handleReprocesar = async (uploadId) => {
    try {
      await reprocesarNombresInglesUpload(uploadId);
      // Actualizar la lista
      await handleVerUploads();
    } catch (err) {
      console.error('Error al reprocesar:', err);
    }
  };

  // Handler para eliminar un upload específico
  const handleEliminarUpload = async (uploadId) => {
    try {
      await eliminarNombresInglesUpload(uploadId);
      // Actualizar la lista
      await handleVerUploads();
    } catch (err) {
      console.error('Error al eliminar upload:', err);
    }
  };

  // Render
  return (
    <div className={`bg-gray-800 p-4 rounded-xl shadow-lg flex flex-col gap-3 ${!clasificacionReady || disabled ? "opacity-60 pointer-events-none" : ""}`}>
      <h3 className="text-lg font-semibold mb-3">{numeroPaso}. Nombres en inglés de cuentas</h3>

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
          Estado: <EstadoBadge estado={estado === "subido" ? "completado" : "pendiente"} />
        </span>
      </div>

      {/* Botón de descarga de plantilla */}
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

      {/* Subida de archivo */}
      <div className="flex gap-3 items-center">
        <button
          type="button"
          onClick={() => fileInputRef.current.click()}
          disabled={subiendo || !clasificacionReady || disabled}
          className={`bg-blue-600 hover:bg-blue-500 px-3 py-1 rounded text-sm font-medium transition ${subiendo ? "opacity-60 cursor-not-allowed" : ""}`}
        >
          {subiendo ? "Subiendo..." : "Elegir archivo .xlsx"}
        </button>
        {archivo && (
          <button
            type="button"
            onClick={handleSubir}
            disabled={subiendo || !clasificacionReady || disabled}
            className={`bg-green-600 hover:bg-green-500 px-3 py-1 rounded text-sm font-medium transition ${subiendo ? 'opacity-60 cursor-not-allowed' : ''}`}
          >
            Subir
          </button>
        )}
        <span className="text-gray-300 text-xs italic truncate max-w-xs">
          {archivo ? archivo.name : "Ningún archivo seleccionado"}
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
      
      {error && <div className="text-xs text-red-400 mt-1">{error}</div>}
      
      {/* Botón para ver uploads */}
      <div className="flex gap-2 mt-2">
        <button
          onClick={handleVerUploads}
          className="px-3 py-1 rounded text-sm font-medium transition bg-blue-700 hover:bg-blue-600 text-white flex items-center gap-2"
        >
          <Eye size={16} />
          Ver uploads
        </button>
        <button
          onClick={() => setHistorialAbierto(true)}
          className="px-3 py-1 rounded text-sm font-medium transition bg-gray-700 hover:bg-gray-600 text-white flex items-center gap-2"
        >
          <History size={16} />
          Historial
        </button>
      </div>
      
      <span className="text-xs text-gray-400 italic mt-2">
        {estado === "subido"
          ? "✔ Archivo de nombres en inglés cargado correctamente"
          : "Aún no se ha subido el archivo de nombres en inglés."}
      </span>

      {/* Modal CRUD para ver/gestionar uploads */}
      <ModalTablaUploadsNombres
        abierto={modalAbierto}
        onClose={() => setModalAbierto(false)}
        titulo="Uploads de Nombres en Inglés"
        uploads={uploads}
        onEliminar={handleEliminarUpload}
        onReprocesar={handleReprocesar}
        onEliminarTodos={handleEliminarTodos}
        eliminando={eliminando}
        errorEliminando={errorEliminando}
      />

      {/* Historial de cambios */}
      <HistorialCambios
        tipoUpload="nombres_ingles"
        clienteId={clienteId}
        cierreId={cierreId}
        abierto={historialAbierto}
        onClose={() => setHistorialAbierto(false)}
      />
    </div>
  );
};

// Componente modal especializado para uploads de nombres en inglés
const ModalTablaUploadsNombres = ({ 
  abierto, 
  onClose, 
  titulo, 
  uploads, 
  onEliminar, 
  onReprocesar, 
  onEliminarTodos, 
  eliminando, 
  errorEliminando 
}) => {
  const [confirmando, setConfirmando] = useState(false);
  const [procesandoId, setProcesandoId] = useState(null);

  if (!abierto) return null;

  const formatFecha = (fecha) => {
    if (!fecha) return '-';
    return new Date(fecha).toLocaleString('es-CL');
  };

  const formatEstado = (estado) => {
    const estados = {
      'pendiente': { text: 'Pendiente', color: 'text-yellow-400' },
      'procesando': { text: 'Procesando', color: 'text-blue-400' },
      'completado': { text: 'Completado', color: 'text-green-400' },
      'error': { text: 'Error', color: 'text-red-400' }
    };
    const info = estados[estado] || { text: estado, color: 'text-gray-400' };
    return <span className={info.color}>{info.text}</span>;
  };

  const formatResumen = (upload) => {
    if (!upload.resumen) return '-';
    const res = upload.resumen;
    return (
      <div className="text-xs">
        <div>Actualizadas: {res.nombres_actualizados || 0}</div>
        {res.errores_count > 0 && (
          <div className="text-red-400">Errores: {res.errores_count}</div>
        )}
      </div>
    );
  };

  const handleReprocesar = async (uploadId) => {
    setProcesandoId(uploadId);
    try {
      await onReprocesar(uploadId);
    } finally {
      setProcesandoId(null);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black bg-opacity-40 flex items-center justify-center">
      <div className="bg-gray-800 rounded-xl shadow-lg p-6 w-full max-w-5xl relative text-white">
        <h2 className="text-xl font-semibold mb-4">{titulo}</h2>
        <button
          className="absolute top-3 right-3 text-gray-400 hover:text-red-500"
          onClick={onClose}
        >✕</button>
        
        <div className="overflow-y-auto" style={{ maxHeight: "500px" }}>
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-gray-600">
                <th className="px-2 py-2">Archivo</th>
                <th className="px-2 py-2">Estado</th>
                <th className="px-2 py-2">Fecha</th>
                <th className="px-2 py-2">Resumen</th>
                <th className="px-2 py-2">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {uploads.length === 0 ? (
                <tr>
                  <td colSpan={5} className="text-center py-10 text-gray-400">
                    No hay uploads de nombres en inglés.
                  </td>
                </tr>
              ) : (
                uploads.map((upload) => (
                  <tr key={upload.id} className="hover:bg-gray-700 border-b border-gray-700">
                    <td className="px-2 py-2">
                      <div className="flex items-center gap-2">
                        <FileText size={16} />
                        <span className="truncate max-w-xs" title={upload.nombre_archivo}>
                          {upload.nombre_archivo}
                        </span>
                      </div>
                      {upload.tamaño_archivo && (
                        <div className="text-xs text-gray-400">
                          {(upload.tamaño_archivo / 1024).toFixed(1)} KB
                        </div>
                      )}
                    </td>
                    <td className="px-2 py-2">{formatEstado(upload.estado)}</td>
                    <td className="px-2 py-2 text-xs">{formatFecha(upload.fecha_subida)}</td>
                    <td className="px-2 py-2">{formatResumen(upload)}</td>
                    <td className="px-2 py-2">
                      <div className="flex gap-1">
                        {upload.estado === 'error' && (
                          <button
                            onClick={() => handleReprocesar(upload.id)}
                            disabled={procesandoId === upload.id}
                            className="p-1 text-blue-400 hover:text-blue-300 disabled:opacity-50"
                            title="Reprocesar"
                          >
                            <RefreshCw size={16} className={procesandoId === upload.id ? 'animate-spin' : ''} />
                          </button>
                        )}
                        <button
                          onClick={() => onEliminar(upload.id)}
                          className="p-1 text-red-400 hover:text-red-300"
                          title="Eliminar"
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        
        {/* Botón Eliminar Todos */}
        {uploads.length > 0 && (
          <div className="mt-5 flex justify-end">
            {confirmando ? (
              <div className="flex gap-2 items-center">
                <span>¿Confirmar eliminación de todos los uploads?</span>
                <button
                  className="bg-red-600 hover:bg-red-700 px-3 py-1 rounded font-bold flex items-center gap-2"
                  onClick={onEliminarTodos}
                  disabled={eliminando}
                >
                  {eliminando && (
                    <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"/>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
                    </svg>
                  )}
                  Sí, eliminar todos
                </button>
                <button
                  className="bg-gray-600 hover:bg-gray-500 px-3 py-1 rounded"
                  onClick={() => setConfirmando(false)}
                  disabled={eliminando}
                >Cancelar</button>
              </div>
            ) : (
              <button
                className="bg-red-600 hover:bg-red-700 px-4 py-2 rounded font-bold"
                onClick={() => setConfirmando(true)}
              >Eliminar todos</button>
            )}
          </div>
        )}
        
        {errorEliminando && (
          <div className="mt-2 text-red-400 text-xs text-right">{errorEliminando}</div>
        )}
      </div>
    </div>
  );
};

export default NombresEnInglesCard;
