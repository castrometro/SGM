import { useEffect, useState, useRef } from "react";
import { 
  obtenerEstadoNombresIngles, 
  subirNombresInglesUpload,
  obtenerNombresInglesUploads,
  obtenerNombresInglesRegistros,
  descargarPlantillaNombresEnIngles,
  descargarCuentasSinNombreInglesFile
} from "../../api/contabilidad";
import EstadoBadge from "../EstadoBadge";
import HistorialCambios from '../HistorialCambios';
import ModalNombresInglesRegistros from '../ModalNombresInglesRegistros';
import { Download, Settings, History } from 'lucide-react';

const NombresEnInglesCard = ({
  cierreId,
  clienteId,
  clasificacionReady,
  onCompletado,
  disabled
}) => {
  const [estado, setEstado] = useState("pendiente");
  const [archivo, setArchivo] = useState(null);
  const [subiendo, setSubiendo] = useState(false);
  const [error, setError] = useState("");
  const [faltantes, setFaltantes] = useState(0);
  const [totalCuentas, setTotalCuentas] = useState(0);
  const [ultimoUpload, setUltimoUpload] = useState(null);
  const [registrosNombres, setRegistrosNombres] = useState([]);
  const [modalRegistrosAbierto, setModalRegistrosAbierto] = useState(false);
  const [historialAbierto, setHistorialAbierto] = useState(false);
  const fileInputRef = useRef();

  useEffect(() => { cargar(); }, []);
  
  // Polling para actualizar estado cuando está procesando
  useEffect(() => {
    let interval;
    if (estado === 'procesando') {
      interval = setInterval(() => {
        cargar();
      }, 3000); // Cada 3 segundos
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [estado]);
  
  const cargar = async () => {
    try {
      const data = await obtenerNombresInglesUploads(clienteId, cierreId);
      const last = data && data.length > 0 ? data[0] : null;
      setUltimoUpload(last);
      if (last) {
        setEstado(last.estado);
        // Cargar registros de nombres si existe el upload
        if (last.id) {
          try {
            const registros = await obtenerNombresInglesRegistros(last.id);
            setRegistrosNombres(registros);
          } catch (err) {
            console.log("No hay registros de nombres o error cargándolos:", err);
            setRegistrosNombres([]);
          }
        }
        if (onCompletado) onCompletado(last.estado === 'completado');
      } else {
        setEstado('pendiente');
        setRegistrosNombres([]);
        if (onCompletado) onCompletado(false);
      }
      
      // También actualizar el estado basado en las cuentas
      if (cierreId && clienteId) {
        try {
          const estadoData = await obtenerEstadoNombresIngles(clienteId, cierreId);
          const total = estadoData.total || 0;
          const faltantes = estadoData.faltantes ? estadoData.faltantes.length : 0;
          setFaltantes(faltantes);
          setTotalCuentas(total);
        } catch (err) {
          // Ignorar errores de estado
        }
      }
    } catch (e) {
      console.error('Error al cargar uploads:', e);
    }
  };

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
      const response = await subirNombresInglesUpload(formData);
      console.log('Archivo subido exitosamente:', response);
      setArchivo(null);
      setEstado('procesando'); // Cambiar estado inmediatamente
      // Recargar datos en 1 segundo para dar tiempo al backend
      setTimeout(() => {
        cargar();
      }, 1000);
    } catch (err) {
      console.error('Error al subir archivo:', err);
      
      // Manejo específico para error 409 (datos ya existentes)
      if (err.response?.status === 409) {
        setError(
          "⚠️ Ya hay archivos de nombres en inglés existentes para este cierre. " +
          "Para subir un nuevo archivo, primero debe eliminar los archivos anteriores " +
          "usando el botón 'Eliminar todos' del historial."
        );
      } else {
        setError("Error al subir el archivo. Verifique el formato.");
      }
      if (onCompletado) onCompletado(false);
    } finally {
      setSubiendo(false);
    }
  };

  // Render
  return (
    <div className={`bg-gray-800 p-4 rounded-xl shadow-lg flex flex-col gap-3 ${disabled ? "opacity-60 pointer-events-none" : ""}`}>
      <h3 className="text-lg font-semibold mb-3">3. Nombres en inglés de cuentas</h3>

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
          Estado: <EstadoBadge estado={estado === "completado" ? "completado" : "pendiente"} />
        </span>
      </div>

      {/* Botón de descarga de plantilla */}
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

      {/* Botón para descargar cuentas sin nombre en inglés (autenticado) */}
      <button
        type="button"
        onClick={async () => {
          if (!clienteId) return;
          try {
            await descargarCuentasSinNombreInglesFile(clienteId, `cuentas_sin_nombre_ingles_cliente_${clienteId}.xlsx`);
          } catch (e) {
            console.error('Error descargando cuentas sin nombre:', e);
          }
        }}
        className={`flex items-center gap-2 bg-gray-700 hover:bg-indigo-600 px-3 py-1 rounded text-white text-sm font-medium transition shadow w-fit mb-2 ${disabled || !clienteId ? 'opacity-40 cursor-not-allowed' : ''}`}
        disabled={disabled || !clienteId}
      >
        <Download size={16} />
        Cuentas sin nombre (xlsx)
      </button>

      {/* Subida de archivo */}
      <div className="flex gap-3 items-center">
        <button
          type="button"
          onClick={() => fileInputRef.current.click()}
          disabled={subiendo || disabled}
          className={`bg-blue-600 hover:bg-blue-500 px-3 py-1 rounded text-sm font-medium transition ${subiendo ? "opacity-60 cursor-not-allowed" : ""}`}
        >
          {subiendo ? "Subiendo..." : "Elegir archivo .xlsx"}
        </button>
        {archivo && (
          <button
            type="button"
            onClick={handleSubir}
            disabled={subiendo || disabled}
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
        disabled={subiendo || disabled}
      />
      
      {error && <div className="text-xs text-red-400 mt-1">{error}</div>}
      
      {/* Botones de acción */}
      <div className="flex gap-2 mt-2">
        <button
          onClick={() => setModalRegistrosAbierto(true)}
          className="px-3 py-1 rounded text-sm font-medium transition bg-green-700 hover:bg-green-600 text-white flex items-center gap-2"
          disabled={!ultimoUpload?.id}
        >
          <Settings size={16} />
          Ver clasificaciones
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
        {estado === "completado"
          ? "✔ Archivo de nombres en inglés cargado correctamente"
          : estado === "procesando"
          ? "🔄 Procesando archivo, por favor espera..."
          : estado === "error"
          ? "❌ Error al procesar el archivo"
          : "Aún no se ha subido el archivo de nombres en inglés."}
      </span>

      {/* Modal para ver registros de nombres */}
      <ModalNombresInglesRegistros
        isOpen={modalRegistrosAbierto}
        onClose={() => setModalRegistrosAbierto(false)}
        uploadId={ultimoUpload?.id}
        clienteId={clienteId}
        onDataChanged={() => {
          cargar(); // Recargar datos después de cambios CRUD
        }}
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

export default NombresEnInglesCard;
