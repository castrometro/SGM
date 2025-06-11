import { useState, useRef, useEffect, useCallback } from "react";
import { Download, Loader2, Upload, FileText, UserCheck, LogOut, AlertCircle, Settings } from "lucide-react";
import { 
  descargarPlantillaFiniquitos, 
  descargarPlantillaIncidencias, 
  descargarPlantillaIngresos,
  descargarPlantillaNovedades,
  subirArchivoAnalista,
  obtenerEstadoArchivoAnalista,
  reprocesarArchivoAnalista,
  subirArchivoNovedades,
  obtenerEstadoArchivoNovedades,
  reprocesarArchivoNovedades,
  obtenerHeadersNovedades,
  clasificarHeadersNovedades,
  procesarFinalNovedades
} from "../../api/nomina";
import EstadoBadge from "../EstadoBadge";
import ModalClasificacionNovedades from "../ModalClasificacionNovedades";

const ArchivosAnalistaCard = ({
  cierreId,
  disabled = false,
  cliente = null, // Agregar cliente como prop
}) => {
  const [archivos, setArchivos] = useState({
    finiquitos: { estado: "no_subido", archivo: null, error: "" },
    incidencias: { estado: "no_subido", archivo: null, error: "" },
    ingresos: { estado: "no_subido", archivo: null, error: "" },
    novedades: { estado: "no_subido", archivo: null, error: "" }
  });
  const [subiendo, setSubiendo] = useState({});
  
  // Estados para el modal de clasificación de novedades
  const [modalClasificacionAbierto, setModalClasificacionAbierto] = useState(false);
  const [headersNovedades, setHeadersNovedades] = useState({ clasificados: [], sin_clasificar: [] });
  const [archivoNovedadesId, setArchivoNovedadesId] = useState(null);
  
  const fileInputRefs = {
    finiquitos: useRef(),
    incidencias: useRef(),
    ingresos: useRef(),
    novedades: useRef()
  };
  // Cambiar a un solo polling ref ya que actualizaremos todos los archivos juntos
  const pollingRef = useRef(null);

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
    },
    novedades: {
      titulo: "Novedades",
      icono: AlertCircle,
      plantilla: descargarPlantillaNovedades,
      descripcion: "Cambios y actualizaciones de empleados"
    }
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

  // Función para verificar si hay archivos en proceso
  const verificarArchivoEnProceso = useCallback(() => {
    return Object.values(archivos).some(archivo => archivo.estado === "en_proceso");
  }, [archivos]);

  // Función para manejar el polling
  const manejarPolling = useCallback(async () => {
    console.log('📡 Polling archivos analista...');
    
    for (const tipo of ['finiquitos', 'incidencias', 'ingresos', 'novedades']) {
      try {
        let data;
        if (tipo === 'novedades') {
          data = await obtenerEstadoArchivoNovedades(cierreId);
          // La respuesta de novedades viene en formato diferente
          if (data && data.id) {
            data = [data]; // Convertir a array para mantener compatibilidad
          } else {
            data = [];
          }
        } else {
          data = await obtenerEstadoArchivoAnalista(cierreId, tipo);
        }
        
        if (data && data.length > 0) {
          const archivo = data[0];
          
          setArchivos(prev => {
            const estadoAnterior = prev[tipo]?.estado;
            
            if (estadoAnterior !== archivo.estado) {
              console.log(`🔄 ${tipo}: ${estadoAnterior} → ${archivo.estado}`);
            }
            
            return {
              ...prev,
              [tipo]: {
                ...prev[tipo],
                estado: archivo.estado,
                archivo: {
                  id: archivo.id,
                  nombre: archivo.archivo ? archivo.archivo.split('/').pop() : (archivo.archivo_nombre || ''),
                  fecha_subida: archivo.fecha_subida
                }
              }
            };
          });
        }
      } catch (error) {
        console.error(`Error polling ${tipo}:`, error);
      }
    }
  }, [cierreId]);

  // Efecto para manejar el polling
  useEffect(() => {
    const tieneArchivosEnProceso = verificarArchivoEnProceso();
    console.log('🎯 ArchivosAnalista - checking polling need:', tieneArchivosEnProceso);
    console.log('🎯 Estados:', Object.fromEntries(Object.entries(archivos).map(([k,v]) => [k, v.estado])));
    
    if (tieneArchivosEnProceso && !pollingRef.current) {
      console.log('🔄 Iniciando polling para archivos analista...');
      
      pollingRef.current = setInterval(manejarPolling, 2000);
      
    } else if (!tieneArchivosEnProceso && pollingRef.current) {
      console.log('✅ Deteniendo polling - no hay archivos en proceso');
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
    
    // Cleanup
    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
        pollingRef.current = null;
      }
    };
  }, [verificarArchivoEnProceso, manejarPolling]);

  // Función para actualizar todos los estados
  const actualizarTodosLosEstados = async () => {
    if (!cierreId) return;
    
    console.log('🔍 Actualizando estados de archivos analista...');
    
    for (const tipo of Object.keys(tiposArchivo)) {
      try {
        const data = await obtenerEstadoArchivoAnalista(cierreId, tipo);
        if (data && data.length > 0) {
          const archivo = data[0];
          const estadoAnterior = archivos[tipo]?.estado;
          
          console.log(`📊 ${tipo}: ${estadoAnterior} → ${archivo.estado}`);
          
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
          
          // Log adicional para cambios de estado
          if (estadoAnterior !== archivo.estado) {
            console.log(`🔄 ${tipo} cambió de "${estadoAnterior}" a "${archivo.estado}"`);
          }
        }
      } catch (error) {
        console.error(`Error actualizando estado de ${tipo}:`, error);
      }
    }
  };

  // Cargar estado inicial de archivos
  useEffect(() => {
    const cargarEstados = async () => {
      if (!cierreId) return;
      
      for (const tipo of Object.keys(tiposArchivo)) {
        try {
          let data;
          if (tipo === 'novedades') {
            data = await obtenerEstadoArchivoNovedades(cierreId);
            // Convertir a array para mantener compatibilidad
            if (data && data.id) {
              data = [data];
            } else {
              data = [];
            }
          } else {
            data = await obtenerEstadoArchivoAnalista(cierreId, tipo);
          }
          
          if (data && data.length > 0) {
            const archivo = data[0]; // Obtener el último archivo subido
            setArchivos(prev => ({
              ...prev,
              [tipo]: {
                ...prev[tipo],
                estado: archivo.estado,
                archivo: {
                  id: archivo.id,
                  nombre: archivo.archivo ? archivo.archivo.split('/').pop() : (archivo.archivo_nombre || ''),
                  fecha_subida: archivo.fecha_subida
                }
              }
            }));
          }
        } catch (error) {
          console.error(`Error cargando estado de ${tipo}:`, error);
        }
      }
    };

    cargarEstados();
  }, [cierreId]);

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
      
      let response;
      if (tipo === 'novedades') {
        response = await subirArchivoNovedades(cierreId, formData);
      } else {
        response = await subirArchivoAnalista(cierreId, tipo, formData);
      }
      
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
      
      // El polling se iniciará automáticamente por el useEffect cuando detecte estado "en_proceso"
      console.log(`✅ Archivo ${tipo} subido con estado: ${response.estado}`);
      
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

  // Funciones para la clasificación de novedades
  const handleClasificarNovedades = async () => {
    const archivo = archivos.novedades.archivo;
    if (!archivo?.id) return;
    
    try {
      const headers = await obtenerHeadersNovedades(archivo.id);
      setHeadersNovedades(headers);
      setArchivoNovedadesId(archivo.id);
      setModalClasificacionAbierto(true);
    } catch (error) {
      console.error("Error obteniendo headers de novedades:", error);
      setArchivos(prev => ({
        ...prev,
        novedades: { 
          ...prev.novedades, 
          error: "Error al obtener headers para clasificación" 
        }
      }));
    }
  };

  const handleGuardarClasificacionesNovedades = async (clasificaciones) => {
    try {
      await clasificarHeadersNovedades(archivoNovedadesId, clasificaciones);
      
      // Actualizar estado del archivo
      setArchivos(prev => ({
        ...prev,
        novedades: { ...prev.novedades, error: "" }
      }));
      
      // Recargar estado para verificar si está clasificado completamente
      const data = await obtenerEstadoArchivoNovedades(cierreId);
      if (data && data.id) {
        setArchivos(prev => ({
          ...prev,
          novedades: {
            ...prev.novedades,
            estado: data.estado,
          }
        }));
      }
      
    } catch (error) {
      console.error("Error guardando clasificaciones:", error);
      setArchivos(prev => ({
        ...prev,
        novedades: { 
          ...prev.novedades, 
          error: "Error al guardar clasificaciones" 
        }
      }));
    }
  };

  const handleProcesarFinalNovedades = async () => {
    const archivo = archivos.novedades.archivo;
    if (!archivo?.id) return;
    
    try {
      await procesarFinalNovedades(archivo.id);
      setArchivos(prev => ({
        ...prev,
        novedades: { ...prev.novedades, estado: "en_proceso", error: "" }
      }));
    } catch (error) {
      console.error("Error procesando novedades:", error);
      setArchivos(prev => ({
        ...prev,
        novedades: { 
          ...prev.novedades, 
          error: "Error al procesar archivo final" 
        }
      }));
    }
  };

  const handleReprocesar = async (tipo) => {
    const archivo = archivos[tipo].archivo;
    if (!archivo?.id) return;
    
    try {
      if (tipo === 'novedades') {
        await reprocesarArchivoNovedades(archivo.id);
      } else {
        await reprocesarArchivoAnalista(archivo.id);
      }
      
      setArchivos(prev => ({
        ...prev,
        [tipo]: { ...prev[tipo], estado: "en_proceso", error: "" }
      }));
      
      // El polling se iniciará automáticamente por el useEffect cuando detecte estado "en_proceso"
      console.log(`✅ Reprocesamiento de ${tipo} iniciado`);
      
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
          
          {/* Botones especiales para novedades */}
          {tipo === 'novedades' && estado.archivo?.id && (
            <div className="flex flex-col gap-2 mt-2">
              {estado.estado === 'clasif_pendiente' && (
                <button
                  type="button"
                  onClick={handleClasificarNovedades}
                  className="bg-orange-600 hover:bg-orange-500 px-3 py-1 rounded text-sm font-medium transition flex items-center gap-1"
                >
                  <Settings size={14} />
                  Clasificar Headers
                </button>
              )}
              
              {estado.estado === 'clasificado' && (
                <button
                  type="button"
                  onClick={handleProcesarFinalNovedades}
                  className="bg-green-600 hover:bg-green-500 px-3 py-1 rounded text-sm font-medium transition"
                >
                  Procesar Final
                </button>
              )}
              
              {estado.estado === 'hdrs_analizados' && (
                <div className="text-sm text-blue-400 bg-blue-900/20 p-2 rounded">
                  ℹ️ Headers analizados, esperando clasificación...
                </div>
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

        {archivoEsBloqueado && estado.estado === "procesado" && (
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

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {Object.keys(tiposArchivo).map(renderArchivoCard)}
      </div>

      <p className="text-xs text-gray-400 italic mt-2">
        Sube los archivos específicos con datos adicionales del analista para complementar la nómina.
      </p>

      <ModalClasificacionNovedades
        isOpen={modalClasificacionAbierto}
        onClose={() => setModalClasificacionAbierto(false)}
        clienteId={cliente?.id}
        headersSinClasificar={headersNovedades.headers_sin_clasificar || []}
        onGuardarClasificaciones={handleGuardarClasificacionesNovedades}
      />
    </div>
  );
};

export default ArchivosAnalistaCard;
