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
  archivosIniciales = null, // 🎯 Nuevos estados iniciales desde el padre
}) => {
  // 🎯 ESTADO INICIAL MEJORADO: Usar estados del padre si están disponibles
  const [archivos, setArchivos] = useState(() => {
    // Si tenemos estados iniciales del padre, usarlos
    if (archivosIniciales) {
      return {
        finiquitos: { 
          estado: archivosIniciales.finiquitos?.estado || "no_subido", 
          archivo: archivosIniciales.finiquitos?.archivo || null, 
          error: "" 
        },
        incidencias: { 
          estado: archivosIniciales.incidencias?.estado || "no_subido", 
          archivo: archivosIniciales.incidencias?.archivo || null, 
          error: "" 
        },
        ingresos: { 
          estado: archivosIniciales.ingresos?.estado || "no_subido", 
          archivo: archivosIniciales.ingresos?.archivo || null, 
          error: "" 
        },
        novedades: { 
          estado: archivosIniciales.novedades?.estado || "no_subido", 
          archivo: archivosIniciales.novedades?.archivo || null, 
          error: "" 
        }
      };
    }
    
    // Si no, usar loading como antes
    return {
      finiquitos: { estado: "loading", archivo: null, error: "" },
      incidencias: { estado: "loading", archivo: null, error: "" },
      ingresos: { estado: "loading", archivo: null, error: "" },
      novedades: { estado: "loading", archivo: null, error: "" }
    };
  });
  const [subiendo, setSubiendo] = useState({});
  const [pollingActivo, setPollingActivo] = useState(false);
  const pollingRef = useRef(null);
  const pollCounterRef = useRef(0);

  // Función para verificar si hay archivos en proceso o si necesitamos hacer polling
  // 🔄 POLLING MEJORADO: Implementar igual que LibroRemuneracionesCard
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

    // 🔄 POLLING MEJORADO: Implementar igual que LibroRemuneracionesCard
  useEffect(() => {
    // Detener polling si se debe detener globalmente
    if (deberiaDetenerPolling && pollingRef.current) {
      console.log('🛑 [ArchivosAnalista] Deteniendo polling - señal global de parada');
      clearInterval(pollingRef.current);
      pollingRef.current = null;
      setPollingActivo(false);
      return;
    }

    // 🚀 ESTADOS QUE REQUIEREN POLLING (excluye "loading" para evitar polling prematuro)
    const estadosQueRequierenPolling = [
      "no_subido",           // Solo cuando realmente no hay archivo
      "pendiente", 
      "analizando_hdrs",
      "hdrs_analizados",
      "clasif_en_proceso",
      "procesando",
      "en_proceso",
      "subiendo",
      "analizando",
      "validando"
      // NOTA: "loading" no está incluido para evitar polling prematuro
    ];
    
    // Verificar si algún archivo necesita polling
    const tieneArchivosEnProceso = Object.values(archivos).some(archivo => 
      estadosQueRequierenPolling.includes(archivo.estado)
    );
    
    // 🛡️ NO HACER POLLING si hay archivos en estado "loading" (aún cargando estados iniciales)
    const tieneArchivosLoading = Object.values(archivos).some(archivo => 
      archivo.estado === "loading"
    );
    
    // Verificar si hay subidas en proceso
    const tieneSubidas = Object.values(subiendo).some(estado => estado === true);
    
    const deberiaHacerPolling = (tieneArchivosEnProceso || tieneSubidas) && !tieneArchivosLoading;

    // 🎯 LOG DESPUÉS de declarar todas las variables
    console.log('🎯 [ArchivosAnalista] useEffect polling - evaluando necesidad...', {
      archivos: Object.entries(archivos).map(([tipo, arch]) => ({ tipo, estado: arch.estado })),
      deberiaDetenerPolling,
      pollingActivo,
      tieneArchivosEnProceso,
      tieneArchivosLoading,
      tieneSubidas,
      deberiaHacerPolling
    });

    if (deberiaHacerPolling && !pollingRef.current && !deberiaDetenerPolling) {
      console.log('🔄 [ArchivosAnalista] Iniciando polling - archivos en proceso detectados');
      setPollingActivo(true);
      pollCounterRef.current = 0;
      
      let contadorErrores = 0;
      
      // Primera consulta inmediata
      manejarPolling();
      
      // Configurar intervalo
      pollingRef.current = setInterval(async () => {
        pollCounterRef.current += 1;
        try {
          console.log(`📡 [ArchivosAnalista] Polling #${pollCounterRef.current} - Verificando estados...`);
          await manejarPolling();
          
          // Reset error counter on success
          contadorErrores = 0;
          
        } catch (pollError) {
          contadorErrores++;
          console.error(`❌ [ArchivosAnalista] Error en polling #${pollCounterRef.current} (${contadorErrores}/3):`, pollError);
          
          // Si hay 3 errores consecutivos, parar el polling por seguridad
          if (contadorErrores >= 3) {
            console.log('🛑 [ArchivosAnalista] Demasiados errores consecutivos, deteniendo polling por seguridad');
            clearInterval(pollingRef.current);
            pollingRef.current = null;
            setPollingActivo(false);
          }
        }
      }, 3000); // Cada 3 segundos
      
    } else if ((!deberiaHacerPolling || deberiaDetenerPolling) && pollingRef.current) {
      console.log('✅ [ArchivosAnalista] Todos los archivos procesados o detención solicitada - deteniendo polling');
      clearInterval(pollingRef.current);
      pollingRef.current = null;
      setPollingActivo(false);
    }

    // Cleanup al desmontar
    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
        pollingRef.current = null;
        setPollingActivo(false);
      }
    };
  }, [
    // 🎯 DEPENDENCIAS ESPECÍFICAS: Solo cuando cambian estados de archivos individuales
    JSON.stringify(Object.entries(archivos).map(([tipo, arch]) => ({ tipo, estado: arch.estado }))),
    JSON.stringify(subiendo),
    deberiaDetenerPolling,
    manejarPolling
  ]);

  // Función para iniciar polling manualmente (usado cuando se sube un archivo)
  // 🎯 SIMPLIFICADO: Solo forzar una actualización inmediata, el useEffect se encarga del polling
  const iniciarPolling = useCallback(() => {
    console.log('🚀 [ArchivosAnalista] Solicitud de polling manual...');
    
    // No iniciar si se debe detener globalmente
    if (deberiaDetenerPolling) {
      console.log('🛑 [ArchivosAnalista] No se ejecuta polling manual - señal global de parada');
      return;
    }
    
    // Solo ejecutar una consulta inmediata, el useEffect se encarga del polling continuo
    console.log('📡 [ArchivosAnalista] Ejecutando consulta inmediata por solicitud manual...');
    manejarPolling().catch(error => {
      console.error('❌ [ArchivosAnalista] Error en consulta manual:', error);
    });
  }, [manejarPolling, deberiaDetenerPolling]);

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

  // Cargar estado inicial de archivos - Solo si no se pasaron estados iniciales
  useEffect(() => {
    const cargarEstados = async () => {
      if (!cierreId) return;
      
      // 🎯 Solo cargar estados si tenemos archivos en "loading" (sin estados iniciales)
      const tieneArchivosLoading = Object.values(archivos).some(archivo => 
        archivo.estado === "loading"
      );
      
      if (!tieneArchivosLoading) {
        console.log('🎯 [ArchivosAnalistaContainer] Estados iniciales ya disponibles, saltando carga inicial');
        return;
      }
      
      console.log('🔄 [ArchivosAnalistaContainer] Cargando estados iniciales...');
      
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
          } else {
            // 🎯 IMPORTANTE: Si no hay archivos, cambiar de "loading" a "no_subido"
            setArchivos(prev => ({
              ...prev,
              [tipo]: {
                ...prev[tipo],
                estado: "no_subido",
                archivo: null
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
