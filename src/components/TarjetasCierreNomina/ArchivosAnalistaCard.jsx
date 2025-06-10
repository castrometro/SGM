import { useState, useRef, useEffect } from "react";
import { Download, Loader2, Upload, FileText, UserCheck, LogOut } from "lucide-react";
import { 
  descargarPlantillaFiniquitos, 
  descargarPlantillaIncidencias, 
  descargarPlantillaIngresos,
  subirArchivoAnalista,
  obtenerEstadoArchivoAnalista,
  reprocesarArchivoAnalista
} from "../../api/nomina";
import EstadoBadge from "../EstadoBadge";

const ArchivosAnalistaCard = ({
  cierreId,
  disabled = false,
}) => {
  const [archivos, setArchivos] = useState({
    finiquitos: { estado: "no_subido", archivo: null, error: "" },
    incidencias: { estado: "no_subido", archivo: null, error: "" },
    ingresos: { estado: "no_subido", archivo: null, error: "" }
  });
  const [subiendo, setSubiendo] = useState({});
  const fileInputRefs = {
    finiquitos: useRef(),
    incidencias: useRef(),
    ingresos: useRef()
  };
  const pollingRefs = useRef({});

  // Configuración de tipos de archivo
  const tiposArchivo = {
    finiquitos: {
      titulo: "Finiquitos",
      icono: LogOut,
      plantilla: descargarPlantillaFiniquitos,
      descripcion: "Datos de empleados con finiquito"
    },
    incidencias: {
      titulo: "Incidencias/Ausentismos", 
      icono: UserCheck,
      plantilla: descargarPlantillaIncidencias,
      descripcion: "Licencias médicas, permisos, etc."
    },
    ingresos: {
      titulo: "Ingresos",
      icono: Upload,
      plantilla: descargarPlantillaIngresos,
      descripcion: "Nuevos empleados que ingresan"
    }
  };

  // Limpiar polling al desmontar
  useEffect(() => {
    return () => {
      Object.values(pollingRefs.current).forEach(interval => {
        if (interval) clearInterval(interval);
      });
    };
  }, []);

  // Cargar estado inicial de archivos
  useEffect(() => {
    const cargarEstados = async () => {
      if (!cierreId) return;
      
      for (const tipo of Object.keys(tiposArchivo)) {
        try {
          const data = await obtenerEstadoArchivoAnalista(cierreId, tipo);
          if (data && data.length > 0) {
            const archivo = data[0]; // Obtener el último archivo subido
            setArchivos(prev => ({
              ...prev,
              [tipo]: {
                ...prev[tipo],
                estado: archivo.estado,
                archivo: {
                  id: archivo.id,
                  nombre: archivo.archivo ? archivo.archivo.split('/').pop() : '',
                  fecha_subida: archivo.fecha_subida
                }
              }
            }));
            
            // Iniciar polling si está en proceso
            if (archivo.estado === "en_proceso") {
              iniciarPolling(tipo);
            }
          }
        } catch (error) {
          console.error(`Error cargando estado de ${tipo}:`, error);
        }
      }
    };

    cargarEstados();
  }, [cierreId]);

  const iniciarPolling = (tipo) => {
    if (pollingRefs.current[tipo]) return;
    
    console.log(`🔄 Iniciando polling para ${tipo}...`);
    pollingRefs.current[tipo] = setInterval(async () => {
      try {
        const data = await obtenerEstadoArchivoAnalista(cierreId, tipo);
        if (data && data.length > 0) {
          const archivo = data[0];
          setArchivos(prev => ({
            ...prev,
            [tipo]: {
              ...prev[tipo],
              estado: archivo.estado,
              archivo: {
                id: archivo.id,
                nombre: archivo.archivo ? archivo.archivo.split('/').pop() : '',
                fecha_subida: archivo.fecha_subida
              }
            }
          }));
          
          // Detener polling si ya no está en proceso
          if (archivo.estado !== "en_proceso") {
            console.log(`✅ ${tipo} completado - deteniendo polling`);
            clearInterval(pollingRefs.current[tipo]);
            pollingRefs.current[tipo] = null;
          }
        }
      } catch (error) {
        console.error(`Error en polling de ${tipo}:`, error);
      }
    }, 5000);
  };

  const handleSeleccionArchivo = async (tipo, archivo) => {
    if (!archivo) return;
    
    setArchivos(prev => ({
      ...prev,
      [tipo]: { ...prev[tipo], error: "" }
    }));
    
    setSubiendo(prev => ({ ...prev, [tipo]: true }));
    
    try {
      const formData = new FormData();
      formData.append('archivo', archivo);
      
      const response = await subirArchivoAnalista(cierreId, tipo, formData);
      
      setArchivos(prev => ({
        ...prev,
        [tipo]: {
          ...prev[tipo],
          estado: response.estado,
          archivo: {
            id: response.id,
            nombre: response.archivo_nombre,
            fecha_subida: response.fecha_subida
          }
        }
      }));
      
      // Iniciar polling si está en proceso
      if (response.estado === "en_proceso") {
        iniciarPolling(tipo);
      }
      
    } catch (error) {
      console.error(`Error subiendo ${tipo}:`, error);
      setArchivos(prev => ({
        ...prev,
        [tipo]: { 
          ...prev[tipo], 
          error: error.response?.data?.error || "Error al subir el archivo" 
        }
      }));
    } finally {
      setSubiendo(prev => ({ ...prev, [tipo]: false }));
    }
  };

  const handleReprocesar = async (tipo) => {
    const archivo = archivos[tipo].archivo;
    if (!archivo?.id) return;
    
    try {
      await reprocesarArchivoAnalista(archivo.id);
      setArchivos(prev => ({
        ...prev,
        [tipo]: { ...prev[tipo], estado: "en_proceso" }
      }));
      iniciarPolling(tipo);
    } catch (error) {
      console.error(`Error reprocesando ${tipo}:`, error);
      setArchivos(prev => ({
        ...prev,
        [tipo]: { 
          ...prev[tipo], 
          error: "Error al reprocesar el archivo" 
        }
      }));
    }
  };

  const renderArchivoCard = (tipo) => {
    const config = tiposArchivo[tipo];
    const estado = archivos[tipo];
    const isSubiendo = subiendo[tipo];
    const isProcesando = estado.estado === "en_proceso";
    const isDisabled = disabled || isSubiendo || isProcesando;
    
    const puedeSubirArchivo = !isDisabled && 
      (estado.estado === "no_subido" || estado.estado === "pendiente" || estado.estado === "con_error");
    
    const estadosConArchivoBloqueado = ["en_proceso", "procesado"];
    const archivoEsBloqueado = estadosConArchivoBloqueado.includes(estado.estado);
    
    const Icono = config.icono;

    return (
      <div key={tipo} className={`bg-gray-700 p-4 rounded-lg ${isDisabled ? "opacity-60" : ""}`}>
        <div className="flex items-center gap-2 mb-3">
          <Icono size={18} className="text-blue-400" />
          <h4 className="font-semibold text-white">{config.titulo}</h4>
          {isProcesando && <Loader2 size={16} className="animate-spin text-blue-400" />}
        </div>
        
        <p className="text-gray-300 text-xs mb-3">{config.descripcion}</p>
        
        <div className="flex items-center gap-2 mb-3">
          <span className="text-sm font-medium">Estado:</span>
          {isProcesando ? (
            <span className="text-blue-400 text-sm flex items-center gap-1">
              <Loader2 size={14} className="animate-spin" /> Procesando...
            </span>
          ) : (
            <EstadoBadge estado={estado.estado} />
          )}
        </div>

        <a
          href={config.plantilla()}
          download
          className={`flex items-center gap-2 bg-gray-700 hover:bg-blue-600 px-3 py-1 rounded !text-white text-sm font-medium transition shadow w-fit mb-2 ${isDisabled ? "opacity-60 pointer-events-none" : ""}`}
          tabIndex={isDisabled ? -1 : 0}
          style={{ pointerEvents: isDisabled ? "none" : "auto" }}
        >
          <Download size={16} />
          Descargar Plantilla
        </a>

        <div className="flex flex-col gap-2">
          {puedeSubirArchivo ? (
            <button
              type="button"
              onClick={() => fileInputRefs[tipo].current?.click()}
              disabled={isDisabled}
              className={`bg-blue-600 hover:bg-blue-500 px-3 py-1 rounded text-sm font-medium transition ${isDisabled ? "opacity-60 cursor-not-allowed" : ""}`}
            >
              {isProcesando ? "Procesando..." : isSubiendo ? "Subiendo..." : "Elegir archivo .xlsx"}
            </button>
          ) : (
            <div className="flex gap-2">
              <button
                type="button"
                disabled={true}
                className="bg-gray-600 px-3 py-1 rounded text-sm font-medium cursor-not-allowed opacity-60 flex-1"
                title="El archivo ya fue procesado"
              >
                Archivo bloqueado
              </button>
              {estado.estado === "con_error" && estado.archivo?.id && (
                <button
                  type="button"
                  onClick={() => handleReprocesar(tipo)}
                  className="bg-yellow-600 hover:bg-yellow-500 px-3 py-1 rounded text-sm font-medium transition"
                >
                  Reprocesar
                </button>
              )}
            </div>
          )}
          
          {estado.archivo?.nombre && (
            <span className="text-gray-300 text-sm italic truncate">
              {estado.archivo.nombre}
            </span>
          )}
        </div>
        
        <input
          type="file"
          accept=".xlsx,.xls"
          ref={fileInputRefs[tipo]}
          style={{ display: "none" }}
          onChange={(e) => handleSeleccionArchivo(tipo, e.target.files[0])}
          disabled={isDisabled || archivoEsBloqueado}
        />

        {estado.error && (
          <div className="text-sm text-red-400 mt-2 bg-red-900/20 p-2 rounded">
            {estado.error}
          </div>
        )}

        {archivoEsBloqueado && (
          <div className="text-sm text-yellow-400 mt-2 bg-yellow-900/20 p-2 rounded">
            ℹ️ Archivo procesado correctamente
          </div>
        )}
      </div>
    );
  };

  return (
    <div className={`bg-gray-800 p-4 rounded-xl shadow-lg flex flex-col gap-4 ${disabled ? "opacity-60 pointer-events-none" : ""}`}>
      <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
        <FileText size={20} className="text-blue-400" />
        3. Archivos del Analista
      </h3>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {Object.keys(tiposArchivo).map(renderArchivoCard)}
      </div>

      <p className="text-xs text-gray-400 italic mt-2">
        Sube los archivos específicos con datos adicionales del analista para complementar la nómina.
      </p>
    </div>
  );
};

export default ArchivosAnalistaCard;
