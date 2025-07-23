import { useState, useEffect, useCallback, useRef } from "react";
import { FileText } from "lucide-react";
import {
  subirArchivoAnalista,
  obtenerEstadoArchivoAnalista,
  reprocesarArchivoAnalista,
  eliminarArchivoAnalista,
  subirArchivoNovedades,
  obtenerEstadoArchivoNovedades,
  reprocesarArchivoNovedades,
  eliminarArchivoNovedades,
} from "../../../api/nomina";

// Importar componentes atomizados
import FiniquitosCard from "./FiniquitosCard";
import IncidenciasCard from "./IncidenciasCard";
import IngresosCard from "./IngresosCard";
import NovedadesCard from "./NovedadesCard";

const ArchivosAnalistaContainer = ({
  cierreId,
  disabled = false,
  cliente = null,
  onEstadosChange = null, // Callback para reportar estados al componente padre
}) => {
  const [archivos, setArchivos] = useState({
    finiquitos: { estado: "no_subido", archivo: null, error: "" },
    incidencias: { estado: "no_subido", archivo: null, error: "" },
    ingresos: { estado: "no_subido", archivo: null, error: "" },
    novedades: { estado: "no_subido", archivo: null, error: "" }
  });
  const [subiendo, setSubiendo] = useState({});
  const pollingRef = useRef(null);

  // Función para verificar si hay archivos en proceso
  const verificarArchivoEnProceso = useCallback(() => {
    return Object.values(archivos).some(archivo => 
      archivo.estado === "en_proceso" || archivo.estado === "procesando"
    );
  }, [archivos]);

  // Función para manejar el polling
  const manejarPolling = useCallback(async () => {
    console.log('📡 Polling archivos analista...');
    
    for (const tipo of ['finiquitos', 'incidencias', 'ingresos', 'novedades']) {
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
    
    if (tieneArchivosEnProceso && !pollingRef.current) {
      console.log('🔄 Iniciando polling para archivos analista...');
      pollingRef.current = setInterval(manejarPolling, 2000);
    } else if (!tieneArchivosEnProceso && pollingRef.current) {
      console.log('✅ Deteniendo polling - no hay archivos en proceso');
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
    
    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
        pollingRef.current = null;
      }
    };
  }, [verificarArchivoEnProceso, manejarPolling]);

  // useEffect para reportar estados al componente padre
  useEffect(() => {
    if (onEstadosChange) {
      const estados = {};
      Object.entries(archivos).forEach(([tipo, archivo]) => {
        estados[tipo] = archivo.estado;
      });
      onEstadosChange(estados);
    }
  }, [archivos, onEstadosChange]);

  // Cargar estado inicial de archivos
  useEffect(() => {
    const cargarEstados = async () => {
      if (!cierreId) return;
      
      for (const tipo of ['finiquitos', 'incidencias', 'ingresos', 'novedades']) {
        try {
          let data;
          if (tipo === 'novedades') {
            data = await obtenerEstadoArchivoNovedades(cierreId);
            if (data && data.id) {
              data = [data];
            } else {
              data = [];
            }
          } else {
            data = await obtenerEstadoArchivoAnalista(cierreId, tipo);
          }
          
          if (data && data.length > 0) {
            const archivo = data[0];
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

  // Limpiar polling al desmontar
  useEffect(() => {
    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
        pollingRef.current = null;
      }
    };
  }, []);

  // Función para actualizar estado de un archivo específico
  const actualizarEstadoArchivo = async (tipo) => {
    try {
      let data;
      if (tipo === 'novedades') {
        data = await obtenerEstadoArchivoNovedades(cierreId);
        if (data && data.id) {
          data = [data];
        } else {
          data = [];
        }
      } else {
        data = await obtenerEstadoArchivoAnalista(cierreId, tipo);
      }
      
      if (data && data.length > 0) {
        const archivo = data[0];
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
      console.error(`Error actualizando estado de ${tipo}:`, error);
    }
  };

  // Handler para subir archivos
  const handleSubirArchivo = async (tipo, archivo) => {
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
            nombre: response.archivo_nombre || response.archivo?.split('/').pop() || '',
            fecha_subida: response.fecha_subida
          }
        }
      }));
      
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

  // Handler para reprocesar archivos
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

  // Handler para eliminar archivos
  const handleEliminarArchivo = async (tipo) => {
    const archivo = archivos[tipo].archivo;
    if (!archivo?.id) return;
    
    try {
      if (tipo === 'novedades') {
        await eliminarArchivoNovedades(archivo.id);
      } else {
        await eliminarArchivoAnalista(archivo.id);
      }
      
      // Resetear estado del archivo completamente
      setArchivos(prev => ({
        ...prev,
        [tipo]: {
          estado: "no_subido",
          archivo: null,
          error: ""
        }
      }));
      
      // Reportar cambio de estado al componente padre
      if (onEstadosChange) {
        const nuevosEstados = {
          ...Object.fromEntries(
            Object.entries(archivos).map(([key, value]) => [
              key,
              key === tipo ? "no_subido" : value.estado
            ])
          )
        };
        onEstadosChange(nuevosEstados);
      }
      
      console.log(`✅ Archivo ${tipo} eliminado correctamente`);
      
    } catch (error) {
      console.error(`Error eliminando ${tipo}:`, error);
      setArchivos(prev => ({
        ...prev,
        [tipo]: { 
          ...prev[tipo], 
          error: "Error al eliminar el archivo" 
        }
      }));
    }
  };

  return (
    <div className={`bg-gray-800 p-4 rounded-xl shadow-lg flex flex-col gap-4 ${disabled ? "opacity-60 pointer-events-none" : ""}`}>
      <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
        <FileText size={20} className="text-blue-400" />
        3. Archivos del Analista
      </h3>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <FiniquitosCard
          estado={archivos.finiquitos.estado}
          archivo={archivos.finiquitos.archivo}
          error={archivos.finiquitos.error}
          subiendo={subiendo.finiquitos}
          disabled={disabled}
          onSubirArchivo={(archivo) => handleSubirArchivo('finiquitos', archivo)}
          onReprocesar={() => handleReprocesar('finiquitos')}
          onEliminarArchivo={() => handleEliminarArchivo('finiquitos')}
        />
        
        <IncidenciasCard
          estado={archivos.incidencias.estado}
          archivo={archivos.incidencias.archivo}
          error={archivos.incidencias.error}
          subiendo={subiendo.incidencias}
          disabled={disabled}
          onSubirArchivo={(archivo) => handleSubirArchivo('incidencias', archivo)}
          onReprocesar={() => handleReprocesar('incidencias')}
          onEliminarArchivo={() => handleEliminarArchivo('incidencias')}
        />
        
        <IngresosCard
          estado={archivos.ingresos.estado}
          archivo={archivos.ingresos.archivo}
          error={archivos.ingresos.error}
          subiendo={subiendo.ingresos}
          disabled={disabled}
          onSubirArchivo={(archivo) => handleSubirArchivo('ingresos', archivo)}
          onReprocesar={() => handleReprocesar('ingresos')}
          onEliminarArchivo={() => handleEliminarArchivo('ingresos')}
        />
        
        <NovedadesCard
          estado={archivos.novedades.estado}
          archivo={archivos.novedades.archivo}
          error={archivos.novedades.error}
          subiendo={subiendo.novedades}
          disabled={disabled}
          onSubirArchivo={(archivo) => handleSubirArchivo('novedades', archivo)}
          onReprocesar={() => handleReprocesar('novedades')}
          onEliminarArchivo={() => handleEliminarArchivo('novedades')}
          onActualizarEstado={() => actualizarEstadoArchivo('novedades')}
          cierreId={cierreId}
          cliente={cliente}
        />
      </div>

      <p className="text-xs text-gray-400 italic mt-2">
        Sube los archivos específicos con datos adicionales del analista para complementar la nómina.
      </p>
    </div>
  );
};

export default ArchivosAnalistaContainer;
