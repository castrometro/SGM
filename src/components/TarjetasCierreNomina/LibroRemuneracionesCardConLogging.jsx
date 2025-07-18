import { useState, useRef, useEffect } from "react";
import { Download, FileBarChart2, CheckCircle2, Loader2 } from "lucide-react";
import { descargarPlantillaLibroRemuneraciones, obtenerEstadoUploadLogNomina } from "../../api/nomina";
import EstadoBadge from "../EstadoBadge";
import Notificacion from "../Notificacion";
import { createActivityLogger } from "../../utils/activityLogger";

const LibroRemuneracionesCardConLogging = ({
  estado,
  archivoNombre,
  onSubirArchivo,
  onVerClasificacion,
  onProcesar,
  onActualizarEstado,
  headersSinClasificar = [],
  headerClasificados = [],
  subiendo = false,
  disabled = false,
  mensaje = "",
  onEliminarArchivo,
  libroId,
  onCompletado,
  numeroPaso = 1,
  cierreId, // Nueva prop necesaria para logging
}) => {
  // Logging de renders para detectar re-renders innecesarios
  console.log('🔄 LibroRemuneracionesCardConLogging RENDER:', {
    timestamp: new Date().toISOString(),
    estado,
    subiendo,
    disabled,
    archivoNombre,
    libroId,
    headersSinClasificar: headersSinClasificar?.length,
    headerClasificados: headerClasificados?.length
  });

  const fileInputRef = useRef();
  const pollingRef = useRef(null);
  
  // Activity Logger
  const activityLogger = useRef(null);
  
  // Inicializar logger cuando tengamos cierreId
  useEffect(() => {
    if (cierreId && !activityLogger.current) {
      activityLogger.current = createActivityLogger(cierreId, 'libro_remuneraciones');
      // Registrar inicio de sesión
      activityLogger.current.logSessionStart();
    }
  }, [cierreId]);

  // Estado local para errores y procesamiento
  const [error, setError] = useState("");
  const [eliminando, setEliminando] = useState(false);
  const [procesandoLocal, setProcesandoLocal] = useState(false);
  const [notificacion, setNotificacion] = useState({ visible: false, tipo: "", mensaje: "" });

  // Estados para UploadLog
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

  // Limpiar polling al desmontar
  useEffect(() => {
    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
        pollingRef.current = null;
      }
    };
  }, []);

  // Monitorear el estado del UploadLog cuando está en proceso
  useEffect(() => {
    if (!uploadLogId || !subiendo) return;

    const monitorearUpload = async () => {
      try {
        const logData = await obtenerEstadoUploadLogNomina(uploadLogId);
        setUploadEstado(logData);
        
                // Actualizar el progreso visible
        if (logData.estado === 'procesando') {
          setUploadProgreso("Procesando archivo...");
          
          // Mostrar notificación amarilla solo la primera vez que entra en procesando
          if (uploadEstado?.estado !== 'procesando') {
            mostrarNotificacion("warning", "📊 Procesando archivo... Por favor espere.");
            
            // Logging: cambio a estado procesando
            if (activityLogger.current) {
              activityLogger.current.logStateChange(
                uploadEstado?.estado || 'inicial',
                'procesando',
                'upload_log_update'
              );
              activityLogger.current.logProgressUpdate(50, 'Procesando archivo en segundo plano');
            }
          }
          
        } else if (logData.estado === 'completado') {
          setUploadProgreso("¡Procesamiento completado!");
          
          // Actualizar estado local y notificar al componente padre
          if (onCompletado) onCompletado(true);
          
          mostrarNotificacion("success", `✅ Archivo procesado exitosamente. ${logData.resumen?.registros_procesados || 0} registros procesados.`);
          
          // Logging: completado exitoso
          if (activityLogger.current) {
            activityLogger.current.logStateChange('procesando', 'completado', 'upload_log_update');
            activityLogger.current.logProgressUpdate(100, `Procesamiento completado: ${logData.resumen?.registros_procesados || 0} registros`);
          }
          
        } else if (logData.estado === 'error') {
          setUploadProgreso("Error en el procesamiento");
          setError(logData.errores || "Error desconocido en el procesamiento");
          if (onCompletado) onCompletado(false);
          mostrarNotificacion("error", `❌ Error: ${logData.errores || "Error desconocido"}`);
          
          // Logging: error en procesamiento
          if (activityLogger.current) {
            activityLogger.current.logStateChange('procesando', 'error', 'upload_log_update');
          }
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
    
  }, [uploadLogId, subiendo, onCompletado]);

  // Iniciar polling cuando el estado sea "procesando"
  useEffect(() => {
    console.log('🎯 useEffect polling - estado actual:', estado);
    
    if (estado === "procesando" && !pollingRef.current && onActualizarEstado) {
      console.log('🔄 Iniciando polling para monitorear procesamiento...');
      
      // Logging: inicio de polling
      if (activityLogger.current) {
        activityLogger.current.logPollingStart(40);
      }
      
      let contadorPolling = 0;
      pollingRef.current = setInterval(async () => {
        contadorPolling++;
        try {
          console.log(`📡 Polling #${contadorPolling} - Verificando estado...`);
          await onActualizarEstado();
        } catch (pollError) {
          console.error(`❌ Error en polling #${contadorPolling}:`, pollError);
        }
      }, 40000); // consultar cada 40 segundos
      
    } else if (estado !== "procesando" && pollingRef.current) {
      console.log(`✅ Estado cambió a "${estado}" - deteniendo polling`);
      
      // Logging: detención de polling
      if (activityLogger.current) {
        activityLogger.current.logPollingStop(`estado cambió a ${estado}`);
      }
      
      clearInterval(pollingRef.current);
      pollingRef.current = null;
      setProcesandoLocal(false);
    }
  }, [estado, onActualizarEstado]);

  // Handler de subida con logging
  const handleSeleccionArchivo = async (e) => {
    console.log('🎯 handleSeleccionArchivo EJECUTADO:', {
      timestamp: new Date().toISOString(),
      hasFile: !!e.target.files[0],
    });

    const file = e.target.files[0];
    if (!file) return;

    // Logging: selección de archivo
    if (activityLogger.current) {
      await activityLogger.current.logFileSelect(file.name, file.size);
    }

    console.log('📁 Archivo seleccionado:', {
      fileName: file.name,
      size: file.size,
      subiendo: subiendo,
      stackTrace: new Error().stack
    });
    
    if (!file) {
      console.log('❌ No hay archivo seleccionado');
      return;
    }
    
    // Prevenir dobles uploads
    if (subiendo) {
      console.warn('⚠️ Upload ya en progreso, ignorando archivo seleccionado');
      return;
    }
    
    console.log('📤 Iniciando proceso de upload para:', file.name);
    
    setError("");
    setUploadProgreso("Subiendo archivo...");
    setUploadLogId(null);
    setUploadEstado(null);
    
    try {
      console.log('🚀 Llamando a onSubirArchivo...');
      const response = await onSubirArchivo(file);
      console.log('✅ Respuesta recibida de onSubirArchivo:', response);
      
      // Logging: validación del archivo
      if (activityLogger.current) {
        const hasErrors = !response?.upload_log_id;
        await activityLogger.current.logFileValidate(
          file.name, 
          hasErrors ? ['Error en la respuesta del servidor'] : []
        );
      }
      
      // Obtener el ID del UploadLog para monitoreo
      if (response?.upload_log_id) {
        setUploadLogId(response.upload_log_id);
        setUploadProgreso("Archivo recibido, iniciando procesamiento...");
        mostrarNotificacion("info", "📤 Archivo subido correctamente. Procesando...");
        
        // Logging: inicio de procesamiento
        if (activityLogger.current) {
          await activityLogger.current.logProgressUpdate(10, 'Archivo subido, iniciando análisis');
        }
      } else {
        // Si no hay upload_log_id, seguir con el flujo normal
        mostrarNotificacion("success", "✅ Archivo subido correctamente.");
      }
      
    } catch (err) {
      setError("Error al subir el archivo.");
      mostrarNotificacion("error", "❌ Error al subir el archivo.");
      console.error('❌ Error en upload:', err);
      
      // Logging: error en upload
      if (activityLogger.current) {
        await activityLogger.current.logFileValidate(
          file.name, 
          [err.message || 'Error desconocido en upload']
        );
      }
    } finally {
      // Limpiar el input para permitir reseleccionar el mismo archivo si es necesario
      e.target.value = '';
    }
  };

  // Handler de eliminar
  const handleEliminarArchivo = async () => {
    setEliminando(true);
    setError("");
    try {
      await onEliminarArchivo();
      mostrarNotificacion("success", "✅ Archivo eliminado correctamente.");
    } catch (err) {
      setError("Error eliminando el archivo.");
      mostrarNotificacion("error", "❌ Error al eliminar el archivo.");
    } finally {
      setEliminando(false);
    }
  };

  // Handler de procesar simplificado
  const handleProcesar = async () => {
    if (!onProcesar) return;
    
    setProcesandoLocal(true);
    setError("");
    
    try {
      console.log('🔄 Iniciando procesamiento...');
      await onProcesar();
      console.log('✅ Procesamiento iniciado exitosamente');
      mostrarNotificacion("info", "🔄 Procesamiento iniciado. Monitoreando progreso...");
      
    } catch (err) {
      setProcesandoLocal(false);
      setError("Error al procesar el archivo.");
      mostrarNotificacion("error", "❌ Error al procesar el archivo.");
      console.error('❌ Error al procesar:', err);
    }
  };

  // Determinar si la tarjeta está deshabilitada
  const isDisabled = disabled || procesandoLocal || subiendo;
  
  // Determinar si ya está procesado
  const isProcessed = estado === "procesado";
  
  // Determinar si está procesando (estado del servidor O estado local)
  const isProcesando = estado === "procesando" || procesandoLocal;

  // Determinar si se puede subir archivo
  const puedeSubirArchivo = !isDisabled && 
    (estado === "no_subido" || estado === "con_error");
  
  // Estados donde NO se puede cambiar el archivo
  const estadosConArchivoBloqueado = [
    "analizando_hdrs",
    "hdrs_analizados", 
    "clasif_pendiente",
    "clasif_en_proceso",
    "clasificado",
    "procesando",
    "procesado"
  ];
  
  const archivoEsBloqueado = estadosConArchivoBloqueado.includes(estado);

  return (
    <>
      <div className={`bg-gray-800 p-4 rounded-xl shadow-lg flex flex-col gap-3 ${isDisabled ? "opacity-60 pointer-events-none" : ""}`}>
        <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
          {numeroPaso}. Libro de Remuneraciones
          {isProcesando && <Loader2 size={20} className="animate-spin text-blue-400" />}
        </h3>

        <div className="flex items-center gap-2 mb-2">
          <span className="font-semibold">Estado:</span>
          {isProcesando ? (
            <span className="text-blue-400 font-semibold flex items-center gap-1">
              <Loader2 size={16} className="animate-spin" /> Procesando...
            </span>
          ) : (
            <EstadoBadge estado={estado} />
          )}
        </div>

        {/* Mostrar progreso del upload log */}
        {uploadProgreso && (
          <div className="bg-gray-700 p-2 rounded text-sm text-gray-300">
            {uploadProgreso}
          </div>
        )}

        {/* Mostrar errores */}
        {error && (
          <div className="bg-red-900/20 border border-red-500 p-2 rounded text-red-300 text-sm">
            {error}
          </div>
        )}

        {/* Mostrar mensaje personalizado */}
        {mensaje && (
          <div className="bg-blue-900/20 border border-blue-500 p-2 rounded text-blue-300 text-sm">
            {mensaje}
          </div>
        )}

        {/* Contenido principal de la tarjeta */}
        <div className="flex-1 flex flex-col gap-3">
          {/* Botón de descarga de plantilla */}
          <button
            onClick={async () => {
              // Logging: descarga de plantilla
              if (activityLogger.current) {
                await activityLogger.current.logDownloadTemplate('libro_remuneraciones');
              }
              descargarPlantillaLibroRemuneraciones();
            }}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white p-2 rounded flex items-center justify-center gap-2 transition-colors"
            disabled={isDisabled}
          >
            <Download size={16} />
            Descargar Plantilla
          </button>

          {/* Botón de subida o información del archivo */}
          {puedeSubirArchivo ? (
            <div className="flex flex-col gap-2">
              <input
                ref={fileInputRef}
                type="file"
                accept=".xlsx,.xls,.csv"
                onChange={(e) => {
                  console.log('📁 INPUT FILE onChange DISPARADO:', {
                    timestamp: new Date().toISOString(),
                    filesLength: e.target.files?.length,
                    fileName: e.target.files[0]?.name,
                    currentSubiendo: subiendo
                  });
                  handleSeleccionArchivo(e);
                }}
                className="hidden"
              />
              <button
                onClick={async () => {
                  console.log('🖱️ BOTÓN SELECCIONAR ARCHIVO CLICKEADO:', {
                    timestamp: new Date().toISOString(),
                    isDisabled,
                    subiendo,
                    canClick: !isDisabled && !subiendo
                  });
                  
                  if (!isDisabled && !subiendo) {
                    console.log('📂 Abriendo file picker...');
                    
                    // Logging: apertura de modal de selección
                    if (activityLogger.current) {
                      await activityLogger.current.logModalOpen('file_selector', {
                        trigger: 'user_click'
                      });
                    }
                    
                    fileInputRef.current?.click();
                  } else {
                    console.log('❌ Click ignorado - botón deshabilitado o subiendo');
                  }
                }}
                className={`w-full p-2 rounded flex items-center justify-center gap-2 transition-colors ${
                  isDisabled || subiendo 
                    ? "bg-gray-600 cursor-not-allowed text-gray-400" 
                    : "bg-green-600 hover:bg-green-700 text-white"
                }`}
                disabled={isDisabled || subiendo}
              >
                <FileBarChart2 size={16} />
                {subiendo ? "Subiendo..." : "Seleccionar Archivo"}
              </button>
            </div>
          ) : archivoNombre ? (
            <div className="bg-gray-700 p-2 rounded text-sm">
              <strong>Archivo:</strong> {archivoNombre}
              {!archivoEsBloqueado && (
                <button
                  onClick={handleEliminarArchivo}
                  className="ml-2 text-red-400 hover:text-red-300 text-xs"
                  disabled={eliminando}
                >
                  {eliminando ? "Eliminando..." : "Eliminar"}
                </button>
              )}
            </div>
          ) : null}

          {/* Información de headers */}
          {headersSinClasificar?.length > 0 && (
            <div className="bg-gray-700 p-2 rounded text-sm">
              <div className="flex justify-between items-center">
                <span>Headers sin clasificar: {headersSinClasificar.length}</span>
                <button
                  onClick={async () => {
                    // Logging: apertura de modal de clasificación
                    if (activityLogger.current) {
                      await activityLogger.current.logModalOpen('classification_modal', {
                        headers_count: headersSinClasificar?.length,
                        classified_count: headerClasificados?.length
                      });
                      
                      await activityLogger.current.logViewClassification(
                        headersSinClasificar?.length,
                        headerClasificados?.length
                      );
                    }
                    
                    onVerClasificacion();
                  }}
                  className="text-blue-400 hover:text-blue-300 text-xs"
                >
                  Ver Clasificación
                </button>
              </div>
            </div>
          )}

          {/* Botón de procesar */}
          {estado === "clasificado" && (
            <button
              onClick={async () => {
                // Logging: inicio de procesamiento
                if (activityLogger.current) {
                  await activityLogger.current.logStateChange('clasificado', 'procesando', 'user_action');
                  await activityLogger.current.logProgressUpdate(0, 'Iniciando procesamiento');
                }
                
                handleProcesar();
              }}
              className="w-full bg-purple-600 hover:bg-purple-700 text-white p-2 rounded flex items-center justify-center gap-2 transition-colors"
              disabled={isDisabled}
            >
              <CheckCircle2 size={16} />
              {procesandoLocal ? "Procesando..." : "Procesar Libro"}
            </button>
          )}

          {/* Mensaje de completado */}
          {isProcessed && (
            <div className="bg-green-900/20 border border-green-500 p-2 rounded text-green-300 text-sm text-center">
              ✅ Procesamiento completado
            </div>
          )}
        </div>
      </div>

      {/* Notificaciones */}
      <Notificacion
        visible={notificacion.visible}
        tipo={notificacion.tipo}
        mensaje={notificacion.mensaje}
        onClose={cerrarNotificacion}
      />
    </>
  );
};

export default LibroRemuneracionesCardConLogging;
