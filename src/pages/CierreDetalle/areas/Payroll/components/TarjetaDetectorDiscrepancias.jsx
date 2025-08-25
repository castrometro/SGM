import React, { useState, useEffect } from "react";

const TarjetaDetectorDiscrepancias = ({ 
  onEstadoChange, 
  bloqueada = false, 
  completada = false,
  pollingActivo = true 
}) => {
  
  // Estado interno de la tarjeta - SIMPLIFICADO para pruebas
  const [estadoInterno, setEstadoInterno] = useState({
    archivosTalana: {
      libroRemuneraciones: null,
      // movimientosDelMes: null // COMENTADO para simplificar
    },
    // archivosAnalista: { // COMENTADO para simplificar
    //   ingresos: null,
    //   finiquitos: null,
    //   ausentismos: null,
    //   novedades: null
    // },
    procesoActual: 'subida_archivos', // subida_archivos, mapeando_headers, verificando_discrepancias
    discrepancias: {
      intentos: 0,
      ultimoIntento: { total: 0, resueltas: 0 },
      historial: []
    },
    procesando: false
  });

  // Calcular progreso de la tarjeta - SIMPLIFICADO para 1 archivo
  const calcularProgreso = () => {
    const totalArchivos = 1; // Solo Libro de Remuneraciones
    const archivosSubidos = [
      ...Object.values(estadoInterno.archivosTalana),
      // ...Object.values(estadoInterno.archivosAnalista) // COMENTADO
    ].filter(archivo => archivo !== null).length;
    
    let progreso = (archivosSubidos / totalArchivos) * 60; // 60% por archivo
    
    if (estadoInterno.procesoActual === 'mapeando_headers') {
      progreso += 20; // 80% total
    }
    
    if (estadoInterno.procesoActual === 'verificando_discrepancias') {
      progreso += 30; // 90% base para verificación
      
      // Si la última verificación tiene 0 discrepancias, llegar al 100%
      if (estadoInterno.discrepancias.ultimoIntento.total === 0 && estadoInterno.discrepancias.intentos > 0) {
        progreso = 100;
      }
    }
    
    if (completada) progreso = 100;
    
    return Math.round(Math.max(0, Math.min(100, progreso)));
  };

  // Actualizar estado al componente padre - SIMPLIFICADO para 1 archivo
  const notificarCambio = () => {
    // Calcular estado actual directamente
    const todosArchivosSubidos = [
      ...Object.values(estadoInterno.archivosTalana),
      // ...Object.values(estadoInterno.archivosAnalista) // COMENTADO
    ].filter(archivo => archivo !== null).length === 1; // Solo 1 archivo ahora
    
    const haRealizadoVerificacion = estadoInterno.discrepancias.intentos > 0;
    const sinDiscrepancias = estadoInterno.discrepancias.ultimoIntento?.total === 0;
    const esCompleta = todosArchivosSubidos && haRealizadoVerificacion && sinDiscrepancias;
    
    console.log('[TARJETA 1] Calculando estado (SIMPLIFICADO):', {
      todosArchivosSubidos,
      haRealizadoVerificacion,
      intentos: estadoInterno.discrepancias.intentos,
      ultimoIntento: estadoInterno.discrepancias.ultimoIntento,
      sinDiscrepancias,
      esCompleta
    });
    
    if (onEstadoChange) {
      onEstadoChange({
        completada: esCompleta,
        progreso: esCompleta ? 100 : calcularProgreso()
      });
    }
  };

  // Manejar subida de archivos
  const manejarSubidaArchivo = (tipo, categoria, archivo) => {
    setEstadoInterno(prev => {
      const nuevoEstado = {
        ...prev,
        [tipo]: {
          ...prev[tipo],
          [categoria]: archivo
        }
      };
      
      // Actualizar proceso si todos los archivos están subidos - SIMPLIFICADO
      const totalArchivos = [
        ...Object.values(nuevoEstado.archivosTalana),
        // ...Object.values(nuevoEstado.archivosAnalista) // COMENTADO
      ].filter(archivo => archivo !== null).length;
      
      if (totalArchivos === 1 && prev.procesoActual === 'subida_archivos') { // Solo 1 archivo ahora
        nuevoEstado.procesoActual = 'mapeando_headers';
      }
      
      return nuevoEstado;
    });
    
    // Ya no necesitamos llamar notificarCambio porque useEffect lo detectará automáticamente
  };

  // Simular verificación de discrepancias
  const verificarDiscrepancias = async () => {
    console.log('[TARJETA 1] verificarDiscrepancias iniciado');
    setEstadoInterno(prev => ({ ...prev, procesando: true, procesoActual: 'verificando_discrepancias' }));
    
    try {
      // Simulación de verificación
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      setEstadoInterno(prev => {
        console.log('[TARJETA 1] Actualizando estado después de verificación, intentos previos:', prev.discrepancias.intentos);
        
        // Lógica de discrepancias: intento par = 1-3 discrepancias, impar = 0 discrepancias
        const numeroIntento = prev.discrepancias.intentos + 1;
        const esPar = numeroIntento % 2 === 0;
        const discrepanciasEncontradas = esPar ? Math.floor(Math.random() * 3) + 1 : 0; // Par: 1-3, Impar: 0
        
        console.log('[TARJETA 1] Nuevo intento:', { numeroIntento, esPar, discrepanciasEncontradas });
        
        const nuevoIntento = {
          intento: numeroIntento,
          total: discrepanciasEncontradas,
          resueltas: discrepanciasEncontradas,
          fecha: new Date().toLocaleString()
        };
        
        const nuevoEstado = {
          ...prev,
          procesando: false,
          discrepancias: {
            intentos: numeroIntento,
            ultimoIntento: { total: discrepanciasEncontradas, resueltas: discrepanciasEncontradas },
            historial: [...prev.discrepancias.historial, nuevoIntento]
          }
        };
        
        // Notificar inmediatamente con los valores calculados
        setTimeout(() => {
          console.log('[TARJETA 1] Notificando con valores calculados:', {
            intentos: numeroIntento,
            total: discrepanciasEncontradas
          });
          
          // Calcular estado de completado con los nuevos valores
          const todosArchivosSubidos = [
            ...Object.values(nuevoEstado.archivosTalana),
            ...Object.values(nuevoEstado.archivosAnalista)
          ].filter(archivo => archivo !== null).length === 6;
          
          const haRealizadoVerificacion = numeroIntento > 0;
          const sinDiscrepancias = discrepanciasEncontradas === 0;
          const esCompleta = todosArchivosSubidos && haRealizadoVerificacion && sinDiscrepancias;
          
          console.log('[TARJETA 1] Estado calculado directamente:', {
            todosArchivosSubidos,
            haRealizadoVerificacion,
            sinDiscrepancias,
            esCompleta
          });
          
          if (onEstadoChange) {
            onEstadoChange({
              completada: esCompleta,
              progreso: esCompleta ? 100 : calcularProgreso()
            });
          }
        }, 100);
        
        return nuevoEstado;
      });
      
    } catch (error) {
      console.error('Error verificando discrepancias:', error);
      setEstadoInterno(prev => ({ ...prev, procesando: false }));
    }
  };

  // Obtener icono según estado del archivo
  const getIconoArchivo = (archivo) => {
    if (archivo) {
      return (
        <svg className="w-5 h-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
        </svg>
      );
    }
    return (
      <svg className="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4" />
      </svg>
    );
  };

  if (bloqueada) {
    return (
      <div className="bg-gray-800 p-6 opacity-50">
        <div className="flex items-center gap-2 mb-4">
          <svg className="w-5 h-5 text-gray-500" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd" />
          </svg>
          <h4 className="text-lg font-bold text-gray-500">Detector de Discrepancias</h4>
          <span className="text-xs bg-gray-700 px-2 py-1 rounded text-gray-400">Bloqueada</span>
        </div>
        <p className="text-gray-500 text-sm">
          Esta fase se desbloqueará cuando se complete la fase anterior.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-gray-800">
      
      {/* Indicador de polling en debug */}
      {!pollingActivo && (
        <div className="bg-orange-900 text-orange-200 text-xs px-3 py-1 text-center">
          ⏸️ Polling pausado - Tarjeta en modo snapshot
        </div>
      )}
      
      <div className="p-6">
      
      {/* Header de la tarjeta */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          {completada ? (
            <svg className="w-6 h-6 text-green-500" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
            </svg>
          ) : (
            <div className="w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center">
              <span className="text-white text-sm font-bold">1</span>
            </div>
          )}
          <h4 className="text-lg font-bold text-white">Detector de Discrepancias</h4>
        </div>
        <div className="text-right">
          <div className="text-xl font-bold text-white">{calcularProgreso()}%</div>
          <div className="text-xs text-gray-400">Progreso</div>
        </div>
      </div>

      {/* Barra de progreso de la tarjeta */}
      <div className="mb-6">
        <div className="w-full bg-gray-700 rounded-full h-2">
          <div 
            className={`h-2 rounded-full transition-all duration-500 ${
              completada ? 'bg-green-500' : 'bg-blue-500'
            }`}
            style={{ width: `${calcularProgreso()}%` }}
          ></div>
        </div>
      </div>

      {/* Contenido principal - SIMPLIFICADO para 1 archivo */}
      <div className="space-y-6">
        
        {/* Sección: Solo Libro de Remuneraciones */}
        <div>
          <h5 className="text-md font-semibold text-white mb-3">📁 Archivo Principal</h5>
          <div className="bg-gray-700 p-4 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <span className="text-white font-medium">
                📊 Libro de Remuneraciones
              </span>
              <div className="flex items-center gap-2">
                {getIconoArchivo(estadoInterno.archivosTalana.libroRemuneraciones)}
                <button
                  onClick={() => manejarSubidaArchivo('archivosTalana', 'libroRemuneraciones', `libroRemuneraciones.xlsx`)}
                  className="text-sm bg-blue-600 hover:bg-blue-700 px-3 py-1.5 rounded text-white transition-colors"
                  disabled={estadoInterno.procesando}
                >
                  {estadoInterno.archivosTalana.libroRemuneraciones ? '🔄 Cambiar Archivo' : '⬆️ Subir Archivo'}
                </button>
              </div>
            </div>
            {estadoInterno.archivosTalana.libroRemuneraciones && (
              <div className="text-xs text-green-400 mt-2">
                ✅ Archivo cargado: {estadoInterno.archivosTalana.libroRemuneraciones}
              </div>
            )}
            <div className="text-xs text-gray-400 mt-2">
              💡 Archivo Excel (.xlsx) con datos de remuneraciones del período
            </div>
          </div>
        </div>

        {/* Comentamos las secciones de otros archivos */}
        {/*
        <div>
          <h5 className="text-md font-semibold text-white mb-3">Archivos Talana</h5>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {Object.entries(estadoInterno.archivosTalana).map(([key, archivo]) => (
              <div key={key} className="bg-gray-700 p-3 rounded flex items-center justify-between">
                <span className="text-sm text-gray-300">
                  {key === 'libroRemuneraciones' ? 'Libro Remuneraciones' : 'Movimientos del Mes'}
                </span>
                <div className="flex items-center gap-2">
                  {getIconoArchivo(archivo)}
                  <button
                    onClick={() => manejarSubidaArchivo('archivosTalana', key, `${key}.xlsx`)}
                    className="text-xs bg-blue-600 hover:bg-blue-700 px-2 py-1 rounded text-white"
                    disabled={estadoInterno.procesando}
                  >
                    {archivo ? 'Cambiar' : 'Subir'}
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
        */}

        {/* Comentamos la sección de archivos del analista para simplificar */}
        {/*
        <div>
          <h5 className="text-md font-semibold text-white mb-3">Archivos Analista</h5>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {Object.entries(estadoInterno.archivosAnalista).map(([key, archivo]) => (
              <div key={key} className="bg-gray-700 p-3 rounded flex items-center justify-between">
                <span className="text-sm text-gray-300 capitalize">{key}</span>
                <div className="flex items-center gap-2">
                  {getIconoArchivo(archivo)}
                  <button
                    onClick={() => manejarSubidaArchivo('archivosAnalista', key, `${key}.xlsx`)}
                    className="text-xs bg-blue-600 hover:bg-blue-700 px-2 py-1 rounded text-white"
                    disabled={estadoInterno.procesando}
                  >
                    {archivo ? 'Cambiar' : 'Subir'}
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
        */}

        {/* Sección: Verificación de Discrepancias */}
        {estadoInterno.procesoActual !== 'subida_archivos' && (
          <div className="border-t border-gray-700 pt-4">
            <div className="flex items-center justify-between mb-4">
              <h5 className="text-md font-semibold text-white">Verificación de Discrepancias</h5>
              <button
                onClick={verificarDiscrepancias}
                disabled={estadoInterno.procesando}
                className={`px-4 py-2 rounded font-semibold ${
                  estadoInterno.procesando
                    ? 'bg-gray-600 text-gray-400 cursor-not-allowed'
                    : 'bg-orange-600 hover:bg-orange-700 text-white'
                }`}
              >
                {estadoInterno.procesando ? 'Verificando...' : 'Verificar Discrepancias'}
              </button>
            </div>

            {/* Historial de intentos */}
            {estadoInterno.discrepancias.historial.length > 0 && (
              <div>
                <h6 className="text-sm font-semibold text-gray-300 mb-2">Historial de Verificaciones</h6>
                <div className="space-y-2">
                  {estadoInterno.discrepancias.historial.slice(-3).map((intento, idx) => (
                    <div key={idx} className={`p-3 rounded border-l-4 ${
                      intento.total === 0 
                        ? 'bg-green-900 border-green-500' 
                        : 'bg-yellow-900 border-yellow-500'
                    }`}>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-300">
                          Intento {intento.intento} {intento.intento % 2 === 0 ? '(Par)' : '(Impar)'}
                        </span>
                        <span className={`text-sm font-semibold ${
                          intento.total === 0 ? 'text-green-400' : 'text-yellow-400'
                        }`}>
                          {intento.total} discrepancias
                        </span>
                      </div>
                      <div className="text-xs text-gray-500 mt-1">{intento.fecha}</div>
                      {intento.total === 0 && (
                        <div className="text-xs text-green-400 mt-1 font-semibold">
                          ✅ ¡Sin discrepancias! Tarjeta completada.
                        </div>
                      )}
                    </div>
                  ))}
                </div>
                
                {/* Mensaje explicativo */}
                <div className="mt-3 p-3 bg-blue-900 rounded border border-blue-700">
                  <div className="text-xs text-blue-300">
                    <strong>Patrón de simulación:</strong><br/>
                    • Intentos <strong>pares</strong> (2, 4, 6...): 1-3 discrepancias aleatorias<br/>
                    • Intentos <strong>impares</strong> (1, 3, 5...): 0 discrepancias (sin problemas)
                  </div>
                </div>
              </div>
            )}

            {/* Estado de completitud */}
            {estadoInterno.discrepancias.ultimoIntento.total === 0 && estadoInterno.discrepancias.intentos > 0 && (
              <div className="mt-4 p-4 bg-green-900 rounded-lg border border-green-700">
                <div className="flex items-center gap-2 text-green-300">
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                  <span className="font-semibold">Fase Completada</span>
                </div>
                <p className="text-green-200 text-sm mt-1">
                  Sin discrepancias detectadas. La siguiente fase se ha desbloqueado automáticamente.
                </p>
              </div>
            )}
          </div>
        )}

      </div>
      
      </div>
    </div>
  );
};

export default TarjetaDetectorDiscrepancias;
