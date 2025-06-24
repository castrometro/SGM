import { useEffect, useState, useRef } from "react";
import {
  obtenerLibrosMayor,
  subirLibroMayor,
  obtenerEstadoUploadLog,
  obtenerMovimientosIncompletos,
} from "../../api/contabilidad";
import EstadoBadge from "../EstadoBadge";
import Notificacion from "../Notificacion";
import ModalMovimientosIncompletos from "./ModalMovimientosIncompletos";

const LibroMayorCard = ({
  cierreId,
  clienteId,
  cliente = null,
  disabled,
  onCompletado,
  tipoDocumentoReady,
  clasificacionReady,
  nombresInglesReady,
  numeroPaso,
}) => {
  const [estado, setEstado] = useState("pendiente");
  const [archivoNombre, setArchivoNombre] = useState("");
  const [subiendo, setSubiendo] = useState(false);
  const [error, setError] = useState("");
  const [uploadLogId, setUploadLogId] = useState(null);
  const [uploadEstado, setUploadEstado] = useState(null);
  const [uploadProgreso, setUploadProgreso] = useState("");
  const [movimientosProcesados, setMovimientosProcesados] = useState(0);
  const [incidenciasDetectadas, setIncidenciasDetectadas] = useState(0);
  const [notificacion, setNotificacion] = useState({ visible: false, tipo: "", mensaje: "" });
  const [modalIncompletoAbierto, setModalIncompletoAbierto] = useState(false);
  const [movimientosIncompletos, setMovimientosIncompletos] = useState([]);
  const fileInputRef = useRef();

  const mostrarNotificacion = (tipo, mensaje) => {
    setNotificacion({ visible: true, tipo, mensaje });
  };

  const cerrarNotificacion = () => {
    setNotificacion({ visible: false, tipo: "", mensaje: "" });
  };

  // Cargar último libro mayor al montar
  useEffect(() => {
    const cargarEstado = async () => {
      if (!cierreId) return;
      try {
        const data = await obtenerLibrosMayor(cierreId);
        const ultimo = data && data.length > 0 ? data[data.length - 1] : null;
        if (ultimo) {
          setEstado(ultimo.estado);
          if (ultimo.estado === "procesando" && ultimo.upload_log) {
            setUploadLogId(ultimo.upload_log);
            setSubiendo(true);
          } else if (ultimo.estado === "completado") {
            onCompletado && onCompletado(true);
          }
        } else {
          setEstado("pendiente");
        }
      } catch (e) {
        console.error("Error cargando libro mayor:", e);
      }
    };
    cargarEstado();
  }, [cierreId, onCompletado]);

  // Monitoreo en tiempo real
  useEffect(() => {
    if (!uploadLogId || !subiendo) return;

    const monitorear = async () => {
      try {
        const logData = await obtenerEstadoUploadLog(uploadLogId);
        setUploadEstado(logData);
        if (logData.estado === "procesando") {
          setEstado("procesando");
          setUploadProgreso("Procesando archivo...");
        } else if (logData.estado === "completado") {
          setEstado("completado");
          setSubiendo(false);
          setUploadProgreso("¡Procesamiento completado!");
          setMovimientosProcesados(logData.resumen?.movimientos_creados || 0);
          setIncidenciasDetectadas(logData.resumen?.incidencias_creadas || 0);
          mostrarNotificacion(
            "success",
            `✅ Archivo procesado exitosamente. ${logData.resumen?.movimientos_creados || 0} movimientos, ${logData.resumen?.incidencias_creadas || 0} incidencias.`
          );
          onCompletado && onCompletado(true);
        } else if (logData.estado === "error") {
          setEstado("error");
          setSubiendo(false);
          setError(logData.errores || "Error en el procesamiento");
          mostrarNotificacion("error", logData.errores || "Error en el procesamiento");
          onCompletado && onCompletado(false);
        }
      } catch (e) {
        console.error("Error monitoreando upload:", e);
      }
    };

    const interval = setInterval(monitorear, 2000);
    return () => clearInterval(interval);
  }, [uploadLogId, subiendo, onCompletado]);

  const handleSeleccionArchivo = async (e) => {
    const archivo = e.target.files[0];
    if (!archivo) return;
    setArchivoNombre(archivo.name);

    if (!validarNombreArchivo(archivo.name)) {
      setError("Nombre de archivo inválido");
      mostrarNotificacion(
        "warning",
        `❌ Nombre de archivo incorrecto. Formato esperado: ${cliente?.rut ? cliente.rut.replace(/\./g, '').replace('-', '') : 'RUT'}_LibroMayor_MMAAAA.xlsx`
      );
      return;
    }

    await handleSubirLibro(archivo);
  };

  const validarNombreArchivo = (nombre) => {
    const rut = cliente?.rut ? cliente.rut.replace(/\./g, '').replace('-', '') : '[A-Za-z0-9]+';
    const regex = new RegExp(`^${rut}_LibroMayor_(0[1-9]|1[0-2])\\d{4}\\.xlsx$`, 'i');
    return regex.test(nombre);
  };

  const handleSubirLibro = async (archivoParam = null) => {
    const archivo = archivoParam || fileInputRef.current.files[0];
    if (!archivo) {
      setError("Debes seleccionar un archivo .xlsx");
      return;
    }

    if (!validarNombreArchivo(archivo.name)) {
      setError("Nombre de archivo inválido");
      mostrarNotificacion(
        "warning",
        `❌ Nombre de archivo incorrecto. Formato esperado: ${cliente?.rut ? cliente.rut.replace(/\./g, '').replace('-', '') : 'RUT'}_LibroMayor_MMAAAA.xlsx`
      );
      return;
    }

    setSubiendo(true);
    setEstado("subiendo");
    setError("");
    setUploadProgreso("Subiendo archivo...");
    setUploadLogId(null);
    setUploadEstado(null);

    try {
      const res = await subirLibroMayor(clienteId, archivo, cierreId);
      if (res.upload_log_id) {
        setUploadLogId(res.upload_log_id);
        setEstado("procesando");
        setUploadProgreso("Archivo recibido, iniciando procesamiento...");
        mostrarNotificacion("info", "📤 Archivo subido correctamente. Procesando...");
      } else {
        setSubiendo(false);
        mostrarNotificacion("success", "✅ Archivo subido");
      }
    } catch (err) {
      console.error("Error al subir archivo:", err);
      setSubiendo(false);
      setEstado("error");
      if (err.response?.status === 400 && err.response.data?.formato_esperado) {
        const d = err.response.data;
        setError(`Formato de nombre incorrecto. Esperado: ${d.formato_esperado}, Recibido: ${d.archivo_recibido}`);
        mostrarNotificacion(
          "warning",
          `❌ Nombre de archivo incorrecto\n\n📋 Formato requerido: ${d.formato_esperado}\n📁 Archivo enviado: ${d.archivo_recibido}`
        );
      } else if (err.response?.data?.error) {
        setError(err.response.data.error);
        mostrarNotificacion("error", err.response.data.error);
      } else {
        setError("Error al subir el archivo.");
        mostrarNotificacion("error", "❌ Error al subir el archivo.");
      }
      onCompletado && onCompletado(false);
    }
  };

  const handleVerIncidencias = async () => {
    try {
      const data = await obtenerMovimientosIncompletos(cierreId);
      setMovimientosIncompletos(Array.isArray(data) ? data : []);
      setModalIncompletoAbierto(true);
    } catch (err) {
      console.error("Error cargando movimientos incompletos:", err);
    }
  };

  return (
    <div className={`bg-gray-800 p-4 rounded-xl shadow-lg flex flex-col gap-3 ${disabled ? 'opacity-60 pointer-events-none' : ''}`}>
      <h3 className="text-lg font-semibold mb-3">{numeroPaso}. Libro Mayor y Procesamiento</h3>

      {/* Información de prerequisitos */}
      <div className="text-xs text-gray-400 mb-2">
        <div className="flex items-center gap-2">
          <span>Prerequisitos:</span>
          <span className={tipoDocumentoReady ? 'text-green-400' : 'text-red-400'}>
            {tipoDocumentoReady ? '✓' : '✗'} Tipos de Documento
          </span>
          <span className={clasificacionReady ? 'text-green-400' : 'text-red-400'}>
            {clasificacionReady ? '✓' : '✗'} Clasificación
          </span>
          {nombresInglesReady !== undefined && (
            <span className={nombresInglesReady ? 'text-green-400' : 'text-red-400'}>
              {nombresInglesReady ? '✓' : '✗'} Nombres en Inglés
            </span>
          )}
        </div>
      </div>

      <div className="flex items-center gap-2 mb-2">
        <span className="font-semibold">Estado:</span>
        <EstadoBadge estado={estado === 'completado' ? 'subido' : estado} />
      </div>

      <div className="text-xs text-gray-400 bg-gray-900/50 border border-gray-600 rounded p-2 mb-2">
        <div className="font-medium text-gray-300 mb-1">📋 Formato de archivo requerido:</div>
        <div className="font-mono text-yellow-300">
          {cliente?.rut ? `${cliente.rut.replace(/\./g, '').replace('-', '')}_LibroMayor_MMAAAA.xlsx` : 'RUT_LibroMayor_MMAAAA.xlsx'}
        </div>
      </div>

      <div className="flex gap-3 items-center">
        <button
          type="button"
          onClick={() => fileInputRef.current.click()}
          disabled={subiendo || disabled}
          className={`bg-blue-600 hover:bg-blue-500 px-3 py-1 rounded text-sm font-medium transition ${subiendo ? 'opacity-60 cursor-not-allowed' : ''}`}
        >
          {subiendo ? uploadProgreso || 'Subiendo...' : 'Elegir archivo .xlsx'}
        </button>
        <span className="text-gray-300 text-xs italic truncate max-w-xs">
          {archivoNombre || 'Ningún archivo seleccionado'}
        </span>
      </div>
      <input
        type="file"
        accept=".xlsx"
        ref={fileInputRef}
        style={{ display: 'none' }}
        onChange={handleSeleccionArchivo}
        disabled={subiendo || disabled}
      />

      {subiendo && uploadEstado && (
        <div className="text-xs bg-blue-900/20 border border-blue-500/30 rounded p-2 mt-2">
          <div className="flex items-center justify-between mb-1">
            <span className="font-medium text-blue-200">Procesando:</span>
            <span className="text-blue-300">{uploadEstado.estado}</span>
          </div>
          {uploadEstado.tiempo_procesamiento && (
            <div className="text-blue-300">Tiempo: {uploadEstado.tiempo_procesamiento}</div>
          )}
        </div>
      )}

      {estado === 'completado' && (
        <div className="text-sm text-green-400 mt-2 space-y-1">
          <div>✅ Movimientos contables procesados: {movimientosProcesados}</div>
          <div>⚠️ Incidencias detectadas: {incidenciasDetectadas}</div>
          {incidenciasDetectadas > 0 && (
            <button
              type="button"
              onClick={handleVerIncidencias}
              className="text-blue-400 hover:text-blue-200 text-xs underline"
            >
              Ver movimientos con incidencias
            </button>
          )}
        </div>
      )}

      {error && (
        <div className="text-xs text-red-400 mt-1 p-2 bg-red-900/20 rounded border border-red-500/30">
          <p className="font-medium">⚠️ {error}</p>
        </div>
      )}

      <span className="text-xs text-gray-400 italic mt-2">
        {estado === 'completado'
          ? '✔ Libro mayor procesado correctamente'
          : estado === 'procesando'
          ? '🔄 Procesando libro mayor...'
          : 'Suba el libro mayor para completar el cierre'}
      </span>

      <Notificacion
        tipo={notificacion.tipo}
        mensaje={notificacion.mensaje}
        visible={notificacion.visible}
        onClose={cerrarNotificacion}
      />
      <ModalMovimientosIncompletos
        abierto={modalIncompletoAbierto}
        onClose={() => setModalIncompletoAbierto(false)}
        movimientos={movimientosIncompletos}
      />
    </div>
  );
};

export default LibroMayorCard;
