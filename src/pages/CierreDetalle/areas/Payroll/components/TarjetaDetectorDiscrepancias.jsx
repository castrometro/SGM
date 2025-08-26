import React, { useState, useEffect } from "react";
import LibroRemuneraciones from "./archivos/LibroRemuneraciones";
import MovimientosDelMes from "./archivos/MovimientosDelMes";
import Ingresos from "./archivos/Ingresos";
import Finiquitos from "./archivos/Finiquitos";
import Ausentismos from "./archivos/Ausentismos";
import Novedades from "./archivos/Novedades";

const TarjetaDetectorDiscrepancias = ({ 
  activa = false,
  onCompletada = () => {},
  cierre,
  cliente
}) => {
  
  // Estado interno simplificado
  const [estadoInterno, setEstadoInterno] = useState({
    archivosTalana: {
      libroRemuneraciones: null,
      movimientosDelMes: null
    },
    archivosAnalista: {
      ingresos: null,
      finiquitos: null,
      ausentismos: null,
      novedades: null
    },
    procesoActual: 'subida_archivos', // subida_archivos, mapeando_headers, verificando_discrepancias
    discrepancias: {
      intentos: 0,
      ultimoIntento: { total: 0, resueltas: 0 },
      historial: []
    },
    procesando: false
  });

  // Polling inteligente: solo cuando está activa
  useEffect(() => {
    if (!activa || !cierre?.id) return;
    
    console.log('[DETECTOR] Tarjeta activa - iniciando polling inteligente');
    
    const interval = setInterval(() => {
      // Solo hacer polling si hay procesos en curso
      if (estadoInterno.procesando || estadoInterno.procesoActual !== 'subida_archivos') {
        console.log('[DETECTOR] Polling activo - verificando estado');
        verificarEstadoProceso();
      }
    }, 3000); // Cada 3 segundos cuando está activa

    return () => {
      console.log('[DETECTOR] Tarjeta inactiva - deteniendo polling');
      clearInterval(interval);
    };
  }, [activa, cierre?.id, estadoInterno.procesando, estadoInterno.procesoActual]);

  // Verificar estado del proceso (simulado por ahora)
  const verificarEstadoProceso = async () => {
    if (!cierre?.id) return;
    
    try {
      // TODO: Implementar llamada real al backend
      console.log('[DETECTOR] Verificando estado del proceso para cierre:', cierre.id);
      
      // Simular respuesta del backend por ahora
      // En producción aquí iría:
      // const response = await fetch(`/api/payroll/cierres/${cierre.id}/detector-discrepancias/`);
      // const data = await response.json();
      
    } catch (error) {
      console.error('[DETECTOR] Error verificando estado:', error);
    }
  };

  // Verificar si el proceso está completado
  const verificarCompletitud = () => {
    const totalArchivos = 6;
    const archivosSubidos = [
      ...Object.values(estadoInterno.archivosTalana),
      ...Object.values(estadoInterno.archivosAnalista)
    ].filter(archivo => archivo !== null).length;
    
    // Completado si todos los archivos están subidos y no hay discrepancias
    const completado = archivosSubidos === totalArchivos && 
                     estadoInterno.procesoActual === 'verificando_discrepancias' &&
                     estadoInterno.discrepancias.ultimoIntento.total === 0 &&
                     estadoInterno.discrepancias.intentos > 0;
    
    if (completado) {
      console.log('[DETECTOR] Proceso completado - notificando al padre');
      onCompletada();
    }
  };

  // Efecto para verificar completitud cuando cambia el estado
  useEffect(() => {
    verificarCompletitud();
  }, [estadoInterno]);

  // Simular inicio del mapeo de headers
  const iniciarMapeoHeaders = async () => {
    if (!activa) return;
    
    setEstadoInterno(prev => ({ 
      ...prev, 
      procesoActual: 'mapeando_headers', 
      procesando: true 
    }));
    
    // Simular tiempo de mapeo
    setTimeout(() => {
      setEstadoInterno(prev => ({ 
        ...prev, 
        procesoActual: 'verificando_discrepancias', 
        procesando: false 
      }));
    }, 3000);
  };

  // Simular verificación de discrepancias
  const verificarDiscrepancias = async () => {
    if (!activa) return;
    
    setEstadoInterno(prev => ({ ...prev, procesando: true }));
    
    // Simular tiempo de verificación
    setTimeout(() => {
      const nuevoIntento = {
        total: Math.floor(Math.random() * 5), // 0-4 discrepancias aleatorias
        resueltas: 0,
        timestamp: Date.now()
      };
      
      setEstadoInterno(prev => ({
        ...prev,
        discrepancias: {
          ...prev.discrepancias,
          intentos: prev.discrepancias.intentos + 1,
          ultimoIntento: nuevoIntento,
          historial: [...prev.discrepancias.historial, nuevoIntento]
        },
        procesando: false
      }));
    }, 4000);
  };

  // Calcular progreso visual
  const calcularProgreso = () => {
    const totalArchivos = 6;
    const archivosSubidos = [
      ...Object.values(estadoInterno.archivosTalana),
      ...Object.values(estadoInterno.archivosAnalista)
    ].filter(archivo => archivo !== null).length;
    
    let progreso = (archivosSubidos / totalArchivos) * 60;
    
    if (estadoInterno.procesoActual === 'mapeando_headers') {
      progreso += 20;
    }
    
    if (estadoInterno.procesoActual === 'verificando_discrepancias') {
      progreso += 20;
      
      if (estadoInterno.discrepancias.ultimoIntento.total === 0 && estadoInterno.discrepancias.intentos > 0) {
        progreso = 100;
      }
    }
    
    return Math.round(Math.max(0, Math.min(100, progreso)));
  };

  // Si la tarjeta no está activa, mostrar versión comprimida
  if (!activa) {
    return (
      <div className="p-4 text-center text-gray-400">
        <div className="text-2xl mb-2">😴</div>
        <p className="text-sm">Tarjeta inactiva - No hay polling ni procesos en curso</p>
      </div>
    );
  }

  // Renderizado completo cuando está activa
  return (
    <div className="bg-gray-800 space-y-6">

      {/* Sección de archivos de Talana */}
      <div className="space-y-4 pt-4">
        <h4 className="text-white font-semibold border-b border-gray-600 pb-2">
          📊 Archivos de Talana (2/2)
        </h4>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <LibroRemuneraciones
            activa={activa}
            onArchivoSubido={(archivo) => {
              setEstadoInterno(prev => ({
                ...prev,
                archivosTalana: {
                  ...prev.archivosTalana,
                  libroRemuneraciones: archivo
                }
              }));
            }}
          />
          
          <MovimientosDelMes
            activa={activa}
            onArchivoSubido={(archivo) => {
              setEstadoInterno(prev => ({
                ...prev,
                archivosTalana: {
                  ...prev.archivosTalana,
                  movimientosDelMes: archivo
                }
              }));
            }}
          />
        </div>
      </div>

      {/* Sección de archivos del Analista */}
      <div className="space-y-4">
        <h4 className="text-white font-semibold border-b border-gray-600 pb-2">
          👤 Archivos del Analista (4/4)
        </h4>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Ingresos
            activa={activa}
            onArchivoSubido={(archivo) => {
              setEstadoInterno(prev => ({
                ...prev,
                archivosAnalista: {
                  ...prev.archivosAnalista,
                  ingresos: archivo
                }
              }));
            }}
          />
          
          <Finiquitos
            activa={activa}
            onArchivoSubido={(archivo) => {
              setEstadoInterno(prev => ({
                ...prev,
                archivosAnalista: {
                  ...prev.archivosAnalista,
                  finiquitos: archivo
                }
              }));
            }}
          />
          
          <Ausentismos
            activa={activa}
            onArchivoSubido={(archivo) => {
              setEstadoInterno(prev => ({
                ...prev,
                archivosAnalista: {
                  ...prev.archivosAnalista,
                  ausentismos: archivo
                }
              }));
            }}
          />
          
          <Novedades
            activa={activa}
            onArchivoSubido={(archivo) => {
              setEstadoInterno(prev => ({
                ...prev,
                archivosAnalista: {
                  ...prev.archivosAnalista,
                  novedades: archivo
                }
              }));
            }}
          />
        </div>
      </div>

      {/* Botones de acción */}
      <div className="flex gap-4">
        {estadoInterno.procesoActual === 'subida_archivos' && (
          <button 
            onClick={iniciarMapeoHeaders}
            disabled={estadoInterno.procesando || calcularProgreso() < 60}
            className="bg-green-600 hover:bg-green-700 disabled:bg-gray-600 text-white px-4 py-2 rounded font-medium"
          >
            Iniciar Mapeo de Headers
          </button>
        )}
        
        {estadoInterno.procesoActual === 'verificando_discrepancias' && (
          <button 
            onClick={verificarDiscrepancias}
            disabled={estadoInterno.procesando}
            className="bg-orange-600 hover:bg-orange-700 disabled:bg-gray-600 text-white px-4 py-2 rounded font-medium"
          >
            Verificar Discrepancias
          </button>
        )}
      </div>

      {/* Resultados de discrepancias */}
      {estadoInterno.discrepancias.intentos > 0 && (
        <div className="bg-gray-900 p-4 rounded-lg">
          <h4 className="text-white font-semibold mb-3">Resultados de Verificación</h4>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-gray-300">Intentos realizados:</span>
              <span className="text-white">{estadoInterno.discrepancias.intentos}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-300">Discrepancias detectadas:</span>
              <span className={estadoInterno.discrepancias.ultimoIntento.total === 0 ? 'text-green-400' : 'text-red-400'}>
                {estadoInterno.discrepancias.ultimoIntento.total}
              </span>
            </div>
            {estadoInterno.discrepancias.ultimoIntento.total === 0 && (
              <div className="text-green-400 text-sm mt-2">
                ✅ ¡Perfecto! No se detectaron discrepancias. El proceso está completado.
              </div>
            )}
          </div>
        </div>
      )}

      {/* Debug - Solo visible cuando activa */}
      <div className="bg-gray-900 p-3 rounded text-xs">
        <div className="text-gray-400 mb-1">Debug (Tarjeta Activa):</div>
        <div className="text-gray-300">
          🟢 Polling: {activa ? 'Activo' : 'Inactivo'} | 
          ⚡ Proceso: {estadoInterno.procesoActual} | 
          🎯 Progreso: {calcularProgreso()}%
        </div>
      </div>

    </div>
  );
};

export default TarjetaDetectorDiscrepancias;