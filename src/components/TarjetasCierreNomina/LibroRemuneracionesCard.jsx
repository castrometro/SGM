import { useState, useRef, useEffect } from "react";
import { Download, FileBarChart2, CheckCircle2, Loader2 } from "lucide-react";
import { descargarPlantillaLibroRemuneraciones } from "../../api/nomina";
import EstadoBadge from "../EstadoBadge";

const LibroRemuneracionesCard = ({
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
}) => {
  const fileInputRef = useRef();
  const pollingRef = useRef(null);

  // Estado local para errores y procesamiento
  const [error, setError] = useState("");
  const [eliminando, setEliminando] = useState(false);
  const [procesandoLocal, setProcesandoLocal] = useState(false);

  // Limpiar polling al desmontar
  useEffect(() => {
    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
        pollingRef.current = null;
      }
    };
  }, []);

  // Iniciar polling cuando el estado sea "procesando"
  useEffect(() => {
    console.log('🎯 useEffect polling - estado actual:', estado);
    
    if (estado === "procesando" && !pollingRef.current && onActualizarEstado) {
      console.log('🔄 Iniciando polling para monitorear procesamiento...');
      
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
      clearInterval(pollingRef.current);
      pollingRef.current = null;
      setProcesandoLocal(false);
    }
  }, [estado, onActualizarEstado]);

  // Handler de subida
  const handleSeleccionArchivo = async (e) => {
    const archivo = e.target.files[0];
    if (!archivo) return;
    setError("");
    try {
      await onSubirArchivo(archivo);
    } catch (err) {
      setError("Error al subir el archivo.");
    }
  };

  // Handler de eliminar
  const handleEliminarArchivo = async () => {
    setEliminando(true);
    setError("");
    try {
      await onEliminarArchivo();
    } catch (err) {
      setError("Error eliminando el archivo.");
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
      // El polling se iniciará automáticamente cuando el estado cambie a "procesando"
      
    } catch (err) {
      setProcesandoLocal(false);
      setError("Error al procesar el archivo.");
      console.error('❌ Error al procesar:', err);
    }
  };

  // Determinar si la tarjeta está deshabilitada
  const isDisabled = disabled || procesandoLocal || subiendo;
  
  // Determinar si ya está procesado
  const isProcessed = estado === "procesado";
  
  // Determinar si está procesando (estado del servidor O estado local)
  const isProcesando = estado === "procesando" || procesandoLocal;

  // ✅ NUEVA LÓGICA: Determinar si se puede subir archivo
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
    <div className={`bg-gray-800 p-4 rounded-xl shadow-lg flex flex-col gap-3 ${isDisabled ? "opacity-60 pointer-events-none" : ""}`}>
      <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
        1. Libro de Remuneraciones
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

      {/* Botón de descarga de plantilla */}
      <a
        href={descargarPlantillaLibroRemuneraciones()}
        download
        className={`flex items-center gap-2 bg-gray-700 hover:bg-blue-600 px-3 py-1 rounded !text-white text-sm font-medium transition shadow w-fit mb-2 ${isDisabled ? "opacity-60 pointer-events-none" : ""}`}
        tabIndex={isDisabled ? -1 : 0}
        style={{ pointerEvents: isDisabled ? "none" : "auto" }}
      >
        <Download size={16} />
        Descargar Plantilla
      </a>

      <div className="flex gap-3 items-center">
        {/* ✅ BOTÓN DE SUBIDA CONDICIONAL */}
        {puedeSubirArchivo ? (
          <button
            type="button"
            onClick={() => fileInputRef.current.click()}
            disabled={isDisabled}
            className={`bg-blue-600 hover:bg-blue-500 px-3 py-1 rounded text-sm font-medium transition ${isDisabled ? "opacity-60 cursor-not-allowed" : ""}`}
          >
            {subiendo ? "Subiendo..." : "Elegir archivo .xlsx"}
          </button>
        ) : (
          <button
            type="button"
            disabled={true}
            className="bg-gray-600 px-3 py-1 rounded text-sm font-medium cursor-not-allowed opacity-60"
            title="El archivo ya fue procesado y no se puede cambiar"
          >
            Archivo bloqueado
          </button>
        )}
        
        <span className="text-gray-300 text-xs italic truncate max-w-xs">
          {archivoNombre || "Ningún archivo seleccionado"}
        </span>
        
        {/* ✅ BOTÓN DE ELIMINAR SOLO SI ESTÁ PROCESADO */}
        {isProcessed && onEliminarArchivo && (
          <button
            onClick={handleEliminarArchivo}
            disabled={eliminando || isDisabled}
            className="text-xs px-2 py-1 rounded bg-red-600 hover:bg-red-700 text-white ml-2"
          >
            {eliminando ? "Eliminando..." : "Eliminar"}
          </button>
        )}
      </div>
      
      {/* ✅ INPUT DE ARCHIVO CONDICIONAL */}
      <input
        type="file"
        accept=".xlsx"
        ref={fileInputRef}
        style={{ display: "none" }}
        onChange={handleSeleccionArchivo}
        disabled={isDisabled || archivoEsBloqueado}
      />

      {error && <div className="text-xs text-red-400 mt-1">{error}</div>}

      {/* ✅ MENSAJE INFORMATIVO CUANDO EL ARCHIVO ESTÁ BLOQUEADO */}
      {archivoEsBloqueado && (
        <div className="text-xs text-yellow-400 mt-1 bg-yellow-900/20 p-2 rounded">
          ℹ️ El archivo ya fue analizado y no se puede cambiar. Si necesitas subir otro archivo, contacta al administrador.
        </div>
      )}

      <div className="flex flex-col gap-1 mt-3">
        <button
          onClick={() => onVerClasificacion(isProcessed)} // ← Pasa true si está procesado
          disabled={isDisabled}
          className="px-3 py-1 rounded text-sm font-medium transition bg-blue-700 hover:bg-blue-600 text-white w-fit disabled:opacity-60"
        >
          {isProcessed ? "Ver Clasificaciones" : "Administrar Clasificaciones"}
        </button>

        {true && (
          <div className="text-xs text-gray-300 mt-1 ml-1">
            <span className="mr-4">
              <strong>Clasificados:</strong> {headerClasificados?.length || 0}
            </span>
            <span>
              <strong>Sin clasificar:</strong> {headersSinClasificar?.length || 0}
            </span>
          </div>
        )}
      </div>

      {/* Botón procesar con loader mejorado */}
      <button
        onClick={handleProcesar}
        disabled={headersSinClasificar?.length > 0 || isDisabled || isProcessed}
        className="mt-2 bg-blue-700 hover:bg-blue-600 px-3 py-1 rounded text-white text-sm font-medium transition shadow w-fit disabled:opacity-60 disabled:cursor-not-allowed flex items-center gap-2"
      >
        {isProcesando && <Loader2 size={16} className="animate-spin" />}
        {isProcesando ? "Procesando..." : "Procesar"}
      </button>

      {mensaje && (
        <span className="text-xs text-gray-400 italic mt-2">{mensaje}</span>
      )}

      {/* Estado visual informativo */}
      <span className="text-xs text-gray-400 italic mt-2">
        {isProcesando
          ? "🔄 Procesando archivo, por favor espera… (puede tomar hasta 40 segundos)"
          : estado === "procesado"
          ? "✔ Archivo cargado correctamente y procesado."
          : "Aún no se ha subido el archivo."}
      </span>
    </div>
  );
};

export default LibroRemuneracionesCard;
