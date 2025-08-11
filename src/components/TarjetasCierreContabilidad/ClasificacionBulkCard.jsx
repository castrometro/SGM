import { useState, useRef, useEffect } from "react";
import EstadoBadge from "../EstadoBadge";
import ModalClasificacionRegistrosRaw from "./ModalClasificacionRegistrosRaw";
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
  obtenerClasificacionesPorUpload,
  obtenerEstadoUploadLog,
  // API para clasificaciones persistentes
  obtenerClasificacionesPersistentesDetalladas,
  crearClasificacionPersistente,
  obtenerCuentasCliente,
} from "../../api/contabilidad";

const ClasificacionBulkCard = ({
  clienteId,
  cierreId,
  cliente,
  onCompletado,
  disabled,
  numeroPaso,
}) => {
  console.log('🏗️ ClasificacionBulkCard props recibidos:', { 
    clienteId, 
    cierreId,
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

  // NUEVO: Estados para sincronización de cuentas nuevas
  const [sincronizandoCuentas, setSincronizandoCuentas] = useState(false);
  const [cuentasNuevasDisponibles, setCuentasNuevasDisponibles] = useState(0);
  const [evitarVerificacionCuentasNuevas, setEvitarVerificacionCuentasNuevas] = useState(false);

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
      console.log('🚀 INICIANDO CARGA DE ESTADO INICIAL - ClasificacionBulkCard');
      console.log(`Props recibidas: clienteId=${clienteId}, cierreId=${cierreId}, disabled=${disabled}`);
      
      try {
        const data = await obtenerEstadoClasificaciones(clienteId);
        console.log('📊 Estado de clasificaciones obtenido:', data);
        setEstado(data.estado);
        setArchivoNombre(data.archivo_nombre || "");
        
        // Verificar si hay clasificaciones persistentes en la base de datos
        let tieneClasificacionesPersistentes = false;
        try {
          const clasificacionesPersistentes = await obtenerClasificacionesPersistentesDetalladas(clienteId);
          tieneClasificacionesPersistentes = clasificacionesPersistentes && clasificacionesPersistentes.length > 0;
          console.log(`📊 Clasificaciones persistentes encontradas: ${clasificacionesPersistentes.length}`);
        } catch (persistentErr) {
          console.warn("Error verificando clasificaciones persistentes:", persistentErr);
        }
        
        // Si hay clasificaciones persistentes pero no archivo subido, marcar como "subido"
        const estadoFinal = (data.estado === "pendiente" && tieneClasificacionesPersistentes) ? "subido" : data.estado;
        setEstado(estadoFinal);
        
        // Marcar como completado si hay archivo subido O si hay clasificaciones persistentes
        const estaCompletado = estadoFinal === "subido";
        console.log(`✅ Estado de clasificaciones: archivo=${data.estado}, persistentes=${tieneClasificacionesPersistentes}, estadoFinal=${estadoFinal}, completado=${estaCompletado}`);
        
        if (onCompletado) onCompletado(estaCompletado);
        
        // Siempre cargar datos detallados para verificar uploads existentes
        await cargar();
        
        // NUEVO: Verificar cuentas nuevas del libro mayor
        console.log('🔍 Verificando cuentas nuevas del libro mayor...');
        await verificarCuentasNuevas('fetchEstadoInicial');
      } catch (err) {
        console.error('❌ Error en fetchEstadoInicial:', err);
        // Si hay error, verificar solo clasificaciones persistentes como fallback
        let tieneClasificacionesPersistentes = false;
        try {
          const clasificacionesPersistentes = await obtenerClasificacionesPersistentesDetalladas(clienteId);
          tieneClasificacionesPersistentes = clasificacionesPersistentes && clasificacionesPersistentes.length > 0;
          console.log(`📊 Fallback - Clasificaciones persistentes: ${clasificacionesPersistentes.length}`);
        } catch (persistentErr) {
          console.warn("Error en fallback de clasificaciones persistentes:", persistentErr);
        }
        
        setEstado(tieneClasificacionesPersistentes ? "subido" : "pendiente");
        if (onCompletado) onCompletado(tieneClasificacionesPersistentes);
        
        // Intentar cargar datos de uploads de todos modos
        try {
          await cargar();
        } catch (loadErr) {
          console.error("Error loading uploads:", loadErr);
        }
      }
      
      console.log('🏁 CARGA DE ESTADO INICIAL COMPLETADA');
      console.log('─'.repeat(80));
    };
    
    if (clienteId && !disabled) fetchEstadoInicial();
  }, [clienteId, disabled, onCompletado]);

  // NUEVO: Monitorear cambios en cuentasNuevasDisponibles para debugging
  useEffect(() => {
    console.log(`📊 CAMBIO EN ESTADO: cuentasNuevasDisponibles = ${cuentasNuevasDisponibles}`);
    if (cuentasNuevasDisponibles > 0) {
      console.log(`🔘 Botón "Añadir ${cuentasNuevasDisponibles} cuentas nuevas" aparecerá`);
    } else {
      console.log(`🔘 Botón de cuentas nuevas está oculto`);
    }
  }, [cuentasNuevasDisponibles]);

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
          console.log('🎉 ===== UPLOAD COMPLETADO - POSIBLE TRIGGER DE CUENTAS NUEVAS =====');
          console.log('📋 UploadLog completado, esto puede disparar detección de cuentas nuevas');
          
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
          
          console.log('🔄 Llamando a cargar() después de upload completado...');
          cargar();
          console.log('🎯 ===== FIN TRIGGER UPLOAD COMPLETADO =====');
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
          const registros = await obtenerClasificacionesPorUpload(last.id);
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
      
      // NUEVO: Verificar cuentas nuevas después de cargar datos
      await verificarCuentasNuevas('cargar_datos');
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

  // NUEVO: Función para verificar cuentas nuevas del libro mayor
  const verificarCuentasNuevas = async (origen = 'DESCONOCIDO') => {
    console.log(`🔍 ===== VERIFICACIÓN DE CUENTAS NUEVAS INICIADA =====`);
    console.log(`📍 ORIGEN: ${origen}`);
    console.log(`🕒 TIMESTAMP: ${new Date().toISOString()}`);
    
    // Solo verificar si hay un cierre activo
    if (!cierreId) {
      console.log('ℹ️ No hay cierre activo, no se verificarán cuentas nuevas');
      setCuentasNuevasDisponibles(0);
      console.log(`🔍 ===== VERIFICACIÓN TERMINADA (SIN CIERRE) =====`);
      return;
    }

    // Evitar verificación si acabamos de sincronizar cuentas
    if (evitarVerificacionCuentasNuevas) {
      console.log('⏸️ Verificación de cuentas nuevas evitada temporalmente después de sincronización');
      console.log(`🔍 ===== VERIFICACIÓN EVITADA =====`);
      return;
    }
    
    try {
      console.log('🔍 INICIANDO VERIFICACIÓN DE CUENTAS NUEVAS');
      console.log(`Cliente ID: ${clienteId}, Cierre ID: ${cierreId}`);
      
      // Obtener cuentas del cliente
      const cuentasCliente = await obtenerCuentasCliente(clienteId);
      console.log(`📊 Total cuentas del cliente: ${cuentasCliente.length}`);
      
      // Log de todas las cuentas del cliente
      console.log('📋 TODAS LAS CUENTAS DEL CLIENTE:');
      cuentasCliente.forEach((cuenta, index) => {
        console.log(`  ${index + 1}. ${cuenta.codigo} - ${cuenta.nombre}`);
      });
      
      // Obtener clasificaciones existentes (incluyendo temporales)
      const clasificacionesExistentes = await obtenerClasificacionesPersistentesDetalladas(clienteId);
      console.log(`📊 Total clasificaciones existentes: ${clasificacionesExistentes.length}`);
      
      // Log de todas las clasificaciones existentes
      console.log('📋 TODAS LAS CLASIFICACIONES EXISTENTES:');
      clasificacionesExistentes.forEach((clasif, index) => {
        console.log(`  ${index + 1}. ${clasif.cuenta_codigo} - ${clasif.cuenta_nombre || 'Sin nombre'}`);
      });
      
      // Crear set de cuentas que ya tienen clasificación
      const cuentasClasificadas = new Set(
        clasificacionesExistentes.map(c => c.cuenta_codigo)
      );
      
      console.log('🔗 SET DE CUENTAS CLASIFICADAS:', Array.from(cuentasClasificadas));
      
      // Filtrar cuentas sin clasificación
      const cuentasSinClasificar = cuentasCliente.filter(
        cuenta => !cuentasClasificadas.has(cuenta.codigo)
      );
      
      console.log('🆕 CUENTAS SIN CLASIFICAR DETECTADAS:');
      if (cuentasSinClasificar.length === 0) {
        console.log('  ✅ No hay cuentas sin clasificar');
      } else {
        cuentasSinClasificar.forEach((cuenta, index) => {
          console.log(`  ${index + 1}. CÓDIGO: ${cuenta.codigo} | NOMBRE: ${cuenta.nombre}`);
          console.log(`     → Esta cuenta NO está en el set de clasificaciones`);
        });
      }
      
      setCuentasNuevasDisponibles(cuentasSinClasificar.length);
      console.log(`🔍 RESULTADO FINAL: ${cuentasSinClasificar.length} cuentas nuevas detectadas`);
      console.log(`📊 ESTADO ACTUALIZADO: cuentasNuevasDisponibles = ${cuentasSinClasificar.length}`);
      console.log(`🔍 ===== VERIFICACIÓN TERMINADA (${origen}) =====`);
      console.log('─'.repeat(80));
    } catch (error) {
      console.error(`❌ Error verificando cuentas nuevas desde ${origen}:`, error);
      setCuentasNuevasDisponibles(0);
      console.log(`🔍 ===== VERIFICACIÓN TERMINADA CON ERROR (${origen}) =====`);
    }
  };

  // NUEVO: Función para sincronizar cuentas nuevas
  const sincronizarCuentasNuevas = async () => {
    if (!cierreId) {
      mostrarNotificacion('error', 'No hay cierre activo para sincronizar cuentas');
      return;
    }
    
    setSincronizandoCuentas(true);
    console.log('🔄 INICIANDO SINCRONIZACIÓN DE CUENTAS NUEVAS');
    
    try {
      // Obtener cuentas del cliente
      const cuentasCliente = await obtenerCuentasCliente(clienteId);
      console.log(`📊 Total cuentas del cliente: ${cuentasCliente.length}`);
      
      // Obtener clasificaciones existentes (incluyendo temporales)
      const clasificacionesExistentes = await obtenerClasificacionesPersistentesDetalladas(clienteId);
      console.log(`📊 Total clasificaciones existentes: ${clasificacionesExistentes.length}`);
      
      // Crear set de cuentas que ya tienen clasificación
      const cuentasClasificadas = new Set(
        clasificacionesExistentes.map(c => c.cuenta_codigo)
      );
      
      // Filtrar cuentas sin clasificación
      const cuentasSinClasificar = cuentasCliente.filter(
        cuenta => !cuentasClasificadas.has(cuenta.codigo)
      );
      
      console.log('🆕 CUENTAS A SINCRONIZAR:');
      console.log(`📊 Estado actual: cuentasNuevasDisponibles = ${cuentasNuevasDisponibles}`);
      console.log(`📊 Cuentas sin clasificar detectadas: ${cuentasSinClasificar.length}`);
      
      if (cuentasNuevasDisponibles !== cuentasSinClasificar.length) {
        console.warn(`⚠️ INCONSISTENCIA: botón muestra ${cuentasNuevasDisponibles} pero detectamos ${cuentasSinClasificar.length}`);
      }
      
      cuentasSinClasificar.forEach((cuenta, index) => {
        console.log(`  ${index + 1}. ${cuenta.codigo} - ${cuenta.nombre}`);
      });
      
      if (cuentasSinClasificar.length === 0) {
        console.log('ℹ️ No hay cuentas nuevas para sincronizar');
        mostrarNotificacion('info', 'No hay cuentas nuevas para sincronizar');
        return;
      }
      
      // Crear registros de clasificación vacíos para las cuentas nuevas
      let cuentasAñadidas = 0;
      const cuentasAñadidasExitosamente = [];
      
      for (const cuenta of cuentasSinClasificar) {
        try {
          console.log(`➕ Añadiendo cuenta: ${cuenta.codigo} - ${cuenta.nombre}`);
          
          const datosAEnviar = {
            cliente: clienteId,
            numero_cuenta: cuenta.codigo,
            cuenta_nombre: cuenta.nombre,
            clasificaciones: {} // Sin clasificación inicial
          };
          
          console.log(`📤 Datos a enviar:`, datosAEnviar);
          
          const resultado = await crearClasificacionPersistente(datosAEnviar);
          console.log(`✅ Cuenta ${cuenta.codigo} añadida correctamente:`, resultado);
          
          cuentasAñadidas++;
          cuentasAñadidasExitosamente.push({
            codigo: cuenta.codigo,
            nombre: cuenta.nombre
          });
        } catch (error) {
          console.error(`❌ Error añadiendo cuenta ${cuenta.codigo}:`, error);
          
          // Log adicional del error
          if (error.response) {
            console.error(`   Status: ${error.response.status}`);
            console.error(`   Data:`, error.response.data);
          }
        }
      }
      
      console.log(`📊 RESULTADO DE SINCRONIZACIÓN:`);
      console.log(`   Total cuentas procesadas: ${cuentasSinClasificar.length}`);
      console.log(`   Cuentas añadidas exitosamente: ${cuentasAñadidas}`);
      console.log(`   Errores: ${cuentasSinClasificar.length - cuentasAñadidas}`);
      
      if (cuentasAñadidas > 0) {
        mostrarNotificacion(
          'success', 
          `✅ ${cuentasAñadidas} cuentas nuevas añadidas al sistema de clasificaciones`
        );
        
        // Evitar verificación automática de cuentas nuevas temporalmente
        setEvitarVerificacionCuentasNuevas(true);
        
        // Actualizar estado inmediatamente
        setCuentasNuevasDisponibles(0);
        
        // Esperar un poco para que las transacciones de base de datos se completen
        console.log('⏳ Esperando 1 segundo para que se procesen las transacciones...');
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // Recargar datos
        await cargar();
        
        // Notificar al padre para actualizar el estado
        if (onCompletado) onCompletado(true);
        
        // NUEVO: Abrir el modal automáticamente para mostrar las cuentas añadidas
        // Guardar las cuentas recién añadidas en el estado para pasarlas al modal
        setCuentasRecienAñadidas(cuentasAñadidasExitosamente);
        console.log('💾 Cuentas recién añadidas guardadas para el modal:', cuentasAñadidasExitosamente);
        
        // Después de 3 segundos, permitir verificaciones de nuevo y hacer una verificación final
        setTimeout(async () => {
          setEvitarVerificacionCuentasNuevas(false);
          console.log('🔄 Realizando verificación final de cuentas nuevas después de sincronización...');
          await verificarCuentasNuevas('post_sincronizacion_final');
          console.log('✅ Sincronización completada - el botón debería haberse ocultado');
        }, 3000);
        
        setTimeout(() => {
          console.log('🚀 ABRIENDO MODAL para mostrar cuentas recién añadidas');
          console.log('📊 Estado antes de abrir modal:');
          console.log('  - cuentasRecienAñadidas:', cuentasAñadidasExitosamente);
          console.log('  - modalRegistrosRaw será:', true);
          setModalRegistrosRaw(true);
          mostrarNotificacion(
            'info',
            '📋 Las cuentas nuevas se han añadido. Ahora puede clasificarlas en el modal.'
          );
        }, 500);
      } else {
        mostrarNotificacion('error', 'No se pudieron añadir las cuentas nuevas');
      }
      
    } catch (error) {
      console.error('❌ Error sincronizando cuentas:', error);
      mostrarNotificacion('error', 'Error al sincronizar cuentas nuevas');
    } finally {
      setSincronizandoCuentas(false);
      console.log('🏁 SINCRONIZACIÓN FINALIZADA');
      console.log('─'.repeat(80));
    }
  };

  // NUEVO: Estado para rastrear cuentas recién añadidas
  const [cuentasRecienAñadidas, setCuentasRecienAñadidas] = useState([]);

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

      {/* Botón único para gestionar clasificaciones */}
      <div className="flex gap-2 mt-2 flex-wrap">
        <button
          onClick={() => setModalRegistrosRaw(true)}
          className="px-3 py-1 rounded text-sm font-medium transition flex items-center gap-2 bg-blue-700 hover:bg-blue-600 text-white"
          title="Ver y gestionar clasificaciones"
        >
          <Database size={16} />
          Gestionar clasificaciones
        </button>
        
        {/* NUEVO: Botón para sincronizar cuentas nuevas - Solo si hay cierre activo */}
        {cuentasNuevasDisponibles > 0 && cierreId && (
          <button
            onClick={sincronizarCuentasNuevas}
            disabled={sincronizandoCuentas}
            className={`px-3 py-1 rounded text-sm font-medium transition flex items-center gap-2 ${
              sincronizandoCuentas 
                ? 'bg-gray-600 cursor-not-allowed' 
                : 'bg-green-600 hover:bg-green-500'
            } text-white`}
            title={`Añadir ${cuentasNuevasDisponibles} cuentas nuevas del libro mayor al sistema de clasificaciones`}
          >
            <RefreshCw size={16} className={sincronizandoCuentas ? 'animate-spin' : ''} />
            {sincronizandoCuentas 
              ? 'Sincronizando...' 
              : `Añadir ${cuentasNuevasDisponibles} cuentas nuevas`
            }
          </button>
        )}
  </div>

  {/* Información del estado y resumen */}
  <div className="text-xs text-gray-400 italic mt-2">
              {/* NUEVO: Mostrar información de cuentas nuevas - Solo si hay cierre activo */}
              {cuentasNuevasDisponibles > 0 && cierreId && (
                <div className="bg-yellow-900/20 border border-yellow-500/30 rounded p-2 mb-2">
                  <div className="text-yellow-300 font-medium mb-1">
                    🆕 {cuentasNuevasDisponibles} cuentas nuevas detectadas
                  </div>
                  <div className="text-xs space-y-1">
                    <div>• Estas cuentas aparecieron en el último procesamiento del libro mayor</div>
                    <div>• Use el botón "Añadir cuentas nuevas" para incluirlas en el sistema de clasificaciones</div>
                    <div>• Podrá clasificarlas después usando el botón "Gestionar clasificaciones"</div>
                  </div>
                </div>
              )}
              
              {estado === "subido" ? (
                <div className="space-y-2">
                  {archivoNombre ? (
                    <>
                      <div className="text-green-400">
                        ✔ Archivo subido correctamente
                      </div>
                      <div className="text-gray-300">
                        📄 Archivo: {archivoNombre}
                      </div>
                    </>
                  ) : (
                    <div className="text-green-400">
                      ✔ Clasificaciones persistentes disponibles
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
              ) : estado === "persistente" ? (
                <div className="space-y-2">
                  <div className="text-green-400">
                    ✔ Clasificaciones disponibles en la base de datos
                  </div>
                  <div className="bg-green-900/20 border border-green-500/30 rounded p-2">
                    <div className="text-green-300 font-medium mb-1">📊 Datos persistentes:</div>
                    <div className="text-xs space-y-1">
                      <div>• Las clasificaciones están guardadas permanentemente en la base de datos</div>
                      <div>• Puede gestionar, editar y agregar más clasificaciones en cualquier momento</div>
                      <div>• No necesita subir archivo para tener clasificaciones funcionales</div>
                    </div>
                  </div>
                </div>
              ) : (
                <div>
                  <div className="mb-2">Aún no se ha subido el archivo.</div>
                  <div className="bg-yellow-900/20 border border-yellow-500/30 rounded p-2">
                    <div className="text-yellow-300 font-medium mb-1">💡 Sobre la gestión de clasificaciones:</div>
                    <div className="text-xs space-y-1">
                      <div>• <strong>Opción 1:</strong> Subir archivo Excel para mapeo masivo inicial</div>
                      <div>• <strong>Opción 2:</strong> Gestionar clasificaciones directamente (botón verde)</div>
                      <div>• Las clasificaciones persistentes siempre están disponibles para edición</div>
                    </div>
                  </div>
                </div>
              )}
            </div>

      {/* Modal para gestión de clasificaciones - datos persistentes */}
      <ModalClasificacionRegistrosRaw
        isOpen={modalRegistrosRaw}
        onClose={() => {
          console.log('🔒 CERRANDO MODAL');
          console.log('📊 Cuentas recién añadidas antes de cerrar:', cuentasRecienAñadidas);
          
          setModalRegistrosRaw(false);
          
          // Si había cuentas recién añadidas, verificar estado después del cierre
          const habianCuentasRecientes = cuentasRecienAñadidas.length > 0;
          
          // Limpiar cuentas recién añadidas al cerrar
          setCuentasRecienAñadidas([]);
          
          if (habianCuentasRecientes) {
            console.log('⏳ Había cuentas recién añadidas, programando verificación...');
            
            // Dar tiempo para que se procesen los cambios del modal
            setTimeout(async () => {
              console.log('🔄 Verificando cuentas nuevas después del cierre del modal...');
              await verificarCuentasNuevas('post_modal_close');
            }, 1000);
          }
        }}
        uploadId={null} // Ya no usar uploadId, cargar directo desde AccountClassification
        clienteId={clienteId}
        cierreId={cierreId}
        cliente={cliente}
        onDataChanged={async () => {
          console.log('🔄 Modal reportó cambios, recargando datos...');
          await cargar(); // Recargar datos después de cambios CRUD
          
          // Solo verificar cuentas nuevas si no estamos evitando la verificación
          if (!evitarVerificacionCuentasNuevas) {
            await verificarCuentasNuevas('modal_onDataChanged'); // Verificar cuentas nuevas
          } else {
            console.log('⏸️ Verificación de cuentas nuevas evitada desde onDataChanged');
          }
        }}
        // NUEVO: Pasar información sobre cuentas recién añadidas
        cuentasRecienAñadidas={cuentasRecienAñadidas}
      />

      {/* DEBUG: Estado actual de cuentas recién añadidas */}
      {process.env.NODE_ENV === 'development' && cuentasRecienAñadidas.length > 0 && (
        <div className="text-xs bg-green-900/20 border border-green-600 rounded p-2 mt-2">
          <div className="text-green-300 font-medium mb-1">🆕 DEBUG - Cuentas Recién Añadidas:</div>
          <div className="text-green-200 space-y-1">
            {cuentasRecienAñadidas.map((cuenta, index) => (
              <div key={`debug-${cuenta.codigo}-${index}`}>
                {cuenta.codigo} - {cuenta.nombre}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* DEBUG: Mostrar información del upload actual */}
      {process.env.NODE_ENV === 'development' && ultimoUpload && (
        <div className="text-xs bg-gray-900 border border-gray-600 rounded p-2 mt-2">
          <div className="text-yellow-300 font-medium mb-1">🔧 DEBUG - Upload Info:</div>
          <div className="text-gray-300 space-y-1">
            <div>Upload ID: {ultimoUpload.id}</div>
            <div>Archivo: {ultimoUpload.archivo}</div>
            <div>Estado: {ultimoUpload.estado}</div>
            <div>Fecha: {ultimoUpload.fecha_subida}</div>
            <div>Registros Raw: {registrosRaw.length}</div>
          </div>
        </div>
      )}

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
