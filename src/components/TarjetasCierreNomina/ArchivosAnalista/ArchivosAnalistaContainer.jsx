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
  onCierreActualizado = null, // Callback para refrescar el cierre padre
  deberiaDetenerPolling = false,
}) => {
  const [archivos, setArchivos] = useState({
    finiquitos: { estado: "no_subido", archivo: null, error: "" },
    incidencias: { estado: "no_subido", archivo: null, error: "" },
    ingresos: { estado: "no_subido", archivo: null, error: "" },
    novedades: { estado: "no_subido", archivo: null, error: "" }
  });
  const [subiendo, setSubiendo] = useState({});
  const [pollingActivo, setPollingActivo] = useState(false);
  const pollingRef = useRef(null);
  const pollCounterRef = useRef(0);

  // Función para verificar si hay archivos en proceso o si necesitamos hacer polling
  const necesitaPolling = useCallback(() => {
    const estadosQueNecesitanPolling = [
      "en_proceso", 
      "procesando", 
      "subiendo",
      "analizando",
      "validando"
    ];
    
    const tieneArchivosEnProceso = Object.values(archivos).some(archivo => 
      estadosQueNecesitanPolling.includes(archivo.estado)
    );
    
    const tieneSubidas = Object.values(subiendo).some(estado => estado === true);
    
    return tieneArchivosEnProceso || tieneSubidas;
  }, [archivos, subiendo]);

  // Función para manejar el polling mejorado
  const manejarPolling = useCallback(async () => {
    pollCounterRef.current += 1;
    console.log(`📡 [Polling #${pollCounterRef.current}] Verificando estados archivos analista...`);
    
    let cambiosDetectados = false;
    
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
              console.log(`🔄 [${tipo}] Estado cambió: ${estadoAnterior} → ${archivo.estado}`);
              cambiosDetectados = true;
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
        console.error(`❌ Error polling ${tipo}:`, error);
      }
    }
    
    if (cambiosDetectados) {
      console.log(`✅ [Polling #${pollCounterRef.current}] Cambios detectados y aplicados`);
      
      // Notificar estados al componente padre después de los cambios
      if (onEstadosChange) {
        setArchivos(currentArchivos => {
          const estadosParaPadre = Object.fromEntries(
            Object.entries(currentArchivos).map(([tipo, datos]) => [tipo, datos.estado])
          );
          onEstadosChange(estadosParaPadre);
          return currentArchivos; // No modificar, solo notificar
        });
      }

      // Si hay cambios en estados críticos, refrescar el cierre padre
      if (onCierreActualizado) {
        console.log('🔄 [ArchivosAnalistaContainer] Cambios detectados, refrescando cierre padre');
        onCierreActualizado();
      }
    }
  }, [cierreId]);

  // Efecto para manejar el polling mejorado
  useEffect(() => {
    const deberiaHacerPolling = necesitaPolling();
    
    console.log('🎯 [ArchivosAnalista] Evaluando necesidad de polling:', {
      deberiaHacerPolling,
      pollingActivo,
      archivos: Object.entries(archivos).map(([tipo, arch]) => ({ tipo, estado: arch.estado })),
      subiendo: Object.entries(subiendo).filter(([_, estado]) => estado).map(([tipo]) => tipo)
    });
    
    // Verificar si se debe detener el polling globalmente
    if (deberiaDetenerPolling && pollingActivo) {
      console.log('🛑 [ArchivosAnalista] Deteniendo polling - señal global de parada');
      setPollingActivo(false);
      
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
        pollingRef.current = null;
      }
      return;
    }
    
    if (deberiaHacerPolling && !pollingActivo && !deberiaDetenerPolling) {
      console.log('🔄 Iniciando polling para archivos analista...');
      setPollingActivo(true);
      pollCounterRef.current = 0;
      
      // Primera consulta inmediata
      manejarPolling();
      
      // Configurar intervalo
      pollingRef.current = setInterval(manejarPolling, 3000); // Cada 3 segundos
      
    } else if ((!deberiaHacerPolling || deberiaDetenerPolling) && pollingActivo) {
      console.log('✅ [ArchivosAnalista] Deteniendo polling - archivos completados o detención solicitada');
      setPollingActivo(false);
      
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
        pollingRef.current = null;
      }
    }
    
    // Cleanup al desmontar
    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
        pollingRef.current = null;
        setPollingActivo(false);
      }
    };
  }, [necesitaPolling, pollingActivo, manejarPolling, deberiaDetenerPolling]);

  // Función para iniciar polling manualmente (usado cuando se sube un archivo)
  const iniciarPolling = useCallback(() => {
    console.log('🚀 [ArchivosAnalista] Iniciando polling manual...');
    
    // No iniciar si se debe detener globalmente
    if (deberiaDetenerPolling) {
      console.log('🛑 [ArchivosAnalista] No se inicia polling manual - señal global de parada');
      return;
    }
    
    if (!pollingActivo) {
      console.log('🔄 Iniciando polling manual para archivos analista...');
      setPollingActivo(true);
      pollCounterRef.current = 0;
      
      // Primera consulta inmediata
      manejarPolling();
      
      // Configurar intervalo si no existe
      if (!pollingRef.current) {
        pollingRef.current = setInterval(manejarPolling, 3000);
      }
    }
  }, [pollingActivo, manejarPolling, deberiaDetenerPolling]);

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
    
    console.log(`📤 [${tipo}] Iniciando subida de archivo...`);
    
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
      
      console.log(`✅ [${tipo}] Archivo subido con estado: ${response.estado}`);
      
      // Activar polling automáticamente después de subir
      setTimeout(() => {
        iniciarPolling();
      }, 1000);
      
    } catch (error) {
      console.error(`❌ [${tipo}] Error subiendo:`, error);
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
    
    console.log(`🔄 [${tipo}] Iniciando reprocesamiento...`);
    
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
      
      console.log(`✅ [${tipo}] Reprocesamiento iniciado`);
      
      // Activar polling automáticamente después de reprocesar
      setTimeout(() => {
        iniciarPolling();
      }, 1000);
      
    } catch (error) {
      console.error(`❌ [${tipo}] Error reprocesando:`, error);
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
