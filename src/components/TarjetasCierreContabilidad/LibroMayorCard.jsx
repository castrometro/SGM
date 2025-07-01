import { useEffect, useState, useRef } from "react";
import {
  obtenerLibrosMayor,
  subirLibroMayor,
  obtenerEstadoUploadLog,
  obtenerMovimientosIncompletos,
  obtenerIncidenciasConsolidadas,
  obtenerIncidenciasConsolidadasOptimizado,
  obtenerHistorialIncidencias,
  reprocesarConExcepciones,
} from "../../api/contabilidad";
import EstadoBadge from "../EstadoBadge";
import Notificacion from "../Notificacion";
import ModalMovimientosIncompletos from "./ModalMovimientosIncompletos";
import ModalIncidenciasConsolidadas from "./ModalIncidenciasConsolidadas";
import ModalHistorialReprocesamiento from "./ModalHistorialReprocesamiento";

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
  const [incidenciasConsolidadas, setIncidenciasConsolidadas] = useState([]);
  const [sinIncidencias, setSinIncidencias] = useState(false);
  const [mensajeSinIncidencias, setMensajeSinIncidencias] = useState("");
  const [modalHistorialAbierto, setModalHistorialAbierto] = useState(false);
  const fileInputRef = useRef();

  const mostrarNotificacion = (tipo, mensaje) => {
    setNotificacion({ visible: true, tipo, mensaje });
  };

  const cerrarNotificacion = () => {
    setNotificacion({ visible: false, tipo: "", mensaje: "" });
  };

  // Función para cargar estado (se extrae para reutilizar)
  const cargarEstado = async () => {
    if (!cierreId) return;
    try {
      const data = await obtenerLibrosMayor(cierreId);
      const ultimo = data && data.length > 0 ? data[data.length - 1] : null;
      
      if (ultimo) {
        setEstado(ultimo.estado);
        setArchivoNombre(ultimo.archivo_nombre || ultimo.archivo || ultimo.nombre || "");
        
        if (ultimo.upload_log) {
          setUploadLogId(ultimo.upload_log);
          const logData = await obtenerEstadoUploadLog(ultimo.upload_log);
          setUploadEstado(logData);
          
          const movimientos = logData.resumen?.procesamiento?.movimientos || 0;
          const incidencias = logData.resumen?.incidencias?.creadas || 0;
          
          setMovimientosProcesados(movimientos);
          setIncidenciasDetectadas(incidencias);
          
          // Verificar snapshot de incidencias para determinar si hay incidencias
          const snapshot = logData.resumen?.incidencias_snapshot;
          if (snapshot) {
            setSinIncidencias(snapshot.sin_incidencias || false);
            setMensajeSinIncidencias(snapshot.mensaje_sin_incidencias || "");
          }
        }

        if (ultimo.estado === "procesando") {
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

  // Cargar último libro mayor al montar
  useEffect(() => {
    cargarEstado();
  }, [cierreId]);

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
          setMovimientosProcesados(logData.resumen?.procesamiento?.movimientos || 0);
          setIncidenciasDetectadas(logData.resumen?.incidencias?.creadas || 0);
          
          // Verificar snapshot de incidencias para determinar si hay incidencias
          const snapshot = logData.resumen?.incidencias_snapshot;
          if (snapshot) {
            setSinIncidencias(snapshot.sin_incidencias || false);
            setMensajeSinIncidencias(snapshot.mensaje_sin_incidencias || "");
          }
          
          // Mensaje específico con estadísticas como en otras tarjetas
          const movimientos = logData.resumen?.procesamiento?.movimientos || 0;
          const incidencias = logData.resumen?.incidencias?.creadas || 0;
          let mensaje = `✅ Archivo procesado correctamente (${movimientos} movimientos contables)`;
          if (incidencias > 0) {
            mensaje += ` • ${incidencias} incidencias detectadas`;
          } else {
            mensaje += ` • Sin incidencias detectadas`;
          }
          
          mostrarNotificacion("success", mensaje);
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
      // Intentar usar endpoint optimizado primero
      const data = await obtenerIncidenciasConsolidadasOptimizado(cierreId);
      
      // El backend devuelve un objeto con {incidencias: [...], estadisticas: {...}}
      // pero el modal espera el array de incidencias directamente
      const incidenciasArray = Array.isArray(data) ? data : (data.incidencias || []);
      
      setIncidenciasConsolidadas(incidenciasArray);
      setModalIncompletoAbierto(true);
      
      // Log performance info si está disponible
      if (data._performance) {
        console.log(`📊 Incidencias cargadas desde ${data._source} en ${data._performance.calculation_time}`);
      }
      
    } catch (err) {
      console.error("Error cargando incidencias optimizadas, intentando fallback:", err);
      
      // Fallback al método original
      try {
        const data = await obtenerIncidenciasConsolidadas(cierreId);
        const incidenciasArray = Array.isArray(data) ? data : (data.incidencias || []);
        setIncidenciasConsolidadas(incidenciasArray);
        setModalIncompletoAbierto(true);
      } catch (fallbackErr) {
        console.error("Error en fallback también:", fallbackErr);
        setIncidenciasConsolidadas([]);
        mostrarNotificacion("error", "Error al cargar las incidencias");
      }
    }
  };

  const handleReprocesar = async () => {
    if (!cierreId) return;
    
    const confirmar = window.confirm(
      "¿Está seguro de que desea reprocesar el Libro Mayor?\n\n" +
      "Esto creará una nueva iteración aplicando las excepciones marcadas como 'No aplica'. " +
      "El procesamiento puede tomar varios minutos."
    );
    
    if (!confirmar) return;
    
    try {
      setSubiendo(true);
      setEstado("procesando");
      mostrarNotificacion("info", "🔄 Iniciando reprocesamiento...");
      
      const resultado = await reprocesarConExcepciones(cierreId);
      
      setUploadLogId(resultado.upload_log_id);
      mostrarNotificacion("success", 
        `✅ Reprocesamiento iniciado. Nueva iteración: ${resultado.nueva_iteracion}`
      );
      
      // Iniciar polling más frecuente para reprocesamiento
      iniciarPollingReprocesamiento(resultado.upload_log_id);
      
    } catch (error) {
      console.error('Error reprocesando:', error);
      setSubiendo(false);
      setEstado("error");
      const mensaje = error.response?.data?.error || error.message || "Error desconocido";
      mostrarNotificacion("error", `❌ Error en reprocesamiento: ${mensaje}`);
    }
  };

  const iniciarPollingReprocesamiento = (uploadLogId) => {
    let intentos = 0;
    const maxIntentos = 30; // 30 intentos = 1 minuto máximo
    
    const verificarEstado = async () => {
      try {
        const estadoUpload = await obtenerEstadoUploadLog(uploadLogId);
        
        if (estadoUpload.estado === 'completado') {
          // Reprocesamiento completado
          setSubiendo(false);
          
          // Verificar snapshot de incidencias para determinar mensaje
          const snapshot = estadoUpload.resumen?.incidencias_snapshot;
          let mensaje = "✅ Reprocesamiento completado";
          
          if (snapshot?.sin_incidencias) {
            mensaje += " - Sin incidencias detectadas";
          } else {
            const incidencias = estadoUpload.resumen?.incidencias?.creadas || 0;
            if (incidencias > 0) {
              mensaje += ` - ${incidencias} incidencias detectadas`;
            }
          }
          
          mostrarNotificacion("success", mensaje);
          await cargarEstado(); // Recargar todo el estado
          return; // Detener polling
        } else if (estadoUpload.estado === 'error') {
          // Error en reprocesamiento
          setSubiendo(false);
          setEstado("error");
          mostrarNotificacion("error", "❌ Error en el reprocesamiento");
          return; // Detener polling
        }
        
        // Actualizar progreso si está disponible
        if (estadoUpload.resumen?.procesamiento) {
          const proc = estadoUpload.resumen.procesamiento;
          setUploadProgreso(`Procesando: ${proc.movimientos || 0} movimientos, ${proc.aperturas || 0} aperturas`);
        }
        
        // Continuar polling si no ha terminado
        intentos++;
        if (intentos < maxIntentos) {
          setTimeout(verificarEstado, 2000); // Verificar cada 2 segundos
        } else {
          // Timeout - recargar una vez más y detener
          setSubiendo(false);
          mostrarNotificacion("info", "⏱️ Reprocesamiento en curso, actualice la página para ver el progreso");
          cargarEstado();
        }
        
      } catch (error) {
        console.error("Error verificando estado del reprocesamiento:", error);
        intentos++;
        if (intentos < maxIntentos) {
          setTimeout(verificarEstado, 3000); // Retry en 3 segundos si hay error
        } else {
          setSubiendo(false);
          cargarEstado();
        }
      }
    };
    
    // Iniciar verificación después de 3 segundos
    setTimeout(verificarEstado, 3000);
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

      {error && (
        <div className="text-xs text-red-400 mt-1 p-2 bg-red-900/20 rounded border border-red-500/30">
          <p className="font-medium">⚠️ {error}</p>
        </div>
      )}

      {/* Información del estado y resumen similar a otras tarjetas */}
      <div className="text-xs text-gray-400 italic mt-2">
        {estado === 'completado' ? (
          <div className="space-y-2">
            <div className="text-green-400">
              ✔ Archivo procesado correctamente ({movimientosProcesados} movimientos contables)
            </div>
            {archivoNombre && (
              <div className="text-gray-300">
                📄 Archivo: {archivoNombre}
              </div>
            )}
            
            {/* Mostrar información detallada del procesamiento */}
            {uploadEstado?.resumen && (
              <div className="space-y-1">
                <div className="text-blue-300">
                  📊 {movimientosProcesados} movimientos procesados
                </div>
                {incidenciasDetectadas > 0 && (
                  <div className="text-yellow-400">
                    ⚠ {incidenciasDetectadas} incidencias detectadas
                  </div>
                )}
                {uploadEstado.resumen?.procesamiento?.cuentas_nuevas > 0 && (
                  <div className="text-blue-300">
                    🆕 {uploadEstado.resumen.procesamiento.cuentas_nuevas} cuentas nuevas creadas
                  </div>
                )}
              </div>
            )}
            
            {/* Botones de acción */}
            <div className="flex items-center gap-2 mt-2">
              {incidenciasDetectadas > 0 && (
                <button
                  type="button"
                  onClick={handleVerIncidencias}
                  className="text-blue-400 hover:text-blue-200 text-xs underline"
                >
                  Ver incidencias ({incidenciasDetectadas})
                </button>
              )}
              
              {sinIncidencias && incidenciasDetectadas === 0 && (
                <div className="text-green-400 text-xs flex items-center gap-1">
                  ✅ {mensajeSinIncidencias || "Sin incidencias detectadas"}
                </div>
              )}
              
              {/* Botón reprocesar - disponible cuando hay un procesamiento completado */}
              {sinIncidencias ? (
                <button
                  type="button"
                  disabled
                  className="bg-green-600 text-white text-xs px-2 py-1 rounded cursor-not-allowed opacity-75 flex items-center gap-1"
                  title="No hay incidencias que procesar"
                >
                  ✅ Sin Incidencias!
                </button>
              ) : (
                <button
                  type="button"
                  onClick={handleReprocesar}
                  className="bg-orange-600 hover:bg-orange-700 text-white text-xs px-2 py-1 rounded transition-colors flex items-center gap-1"
                  title="Crear nueva iteración aplicando excepciones marcadas"
                >
                  🔄 Reprocesar
                </button>
              )}
              
              {/* Botón historial */}
              <button
                type="button"
                onClick={() => setModalHistorialAbierto(true)}
                className="bg-gray-600 hover:bg-gray-700 text-white text-xs px-2 py-1 rounded transition-colors flex items-center gap-1"
                title="Ver historial de reprocesamiento"
              >
                📋 Historial
              </button>
            </div>
          </div>
        ) : estado === 'procesando' ? (
          <div className="text-blue-400">🔄 Procesando archivo...</div>
        ) : estado === 'error' ? (
          <div className="text-red-400">❌ Error en el procesamiento</div>
        ) : (
          <div>Suba el libro mayor para completar el cierre</div>
        )}
      </div>

      <Notificacion
        tipo={notificacion.tipo}
        mensaje={notificacion.mensaje}
        visible={notificacion.visible}
        onClose={cerrarNotificacion}
      />
      <ModalIncidenciasConsolidadas
        abierto={modalIncompletoAbierto}
        onClose={() => setModalIncompletoAbierto(false)}
        incidencias={incidenciasConsolidadas}
        cierreId={cierreId}
        onReprocesar={() => {
          // Recargar el estado del libro mayor después del reprocesamiento
          cargarEstado();
        }}
      />
      <ModalHistorialReprocesamiento
        abierto={modalHistorialAbierto}
        onClose={() => setModalHistorialAbierto(false)}
        cierreId={cierreId}
      />
    </div>
  );
};

export default LibroMayorCard;
