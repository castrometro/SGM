import React, { useState } from "react";

const TarjetaConsolidacionDatos = ({ 
  onEstadoChange, 
  bloqueada = false, 
  completada = false,
  pollingActivo = true 
}) => {
  
  // Los 8 conceptos de payroll según tu workflow
  const CONCEPTOS_PAYROLL = [
    'Haberes Imponibles',
    'Haberes No Imponibles', 
    'Cantidad de Horas Extras',
    'Aportes Patronales',
    'Impuestos',
    'Otros Descuentos',
    'Descuentos Legales',
    'Información'
  ];

  // Estado interno de la tarjeta
  const [estadoInterno, setEstadoInterno] = useState({
    procesoActual: 'mapeo_headers', // mapeo_headers, consolidando_datos, datos_consolidados
    mapeoConceptos: {
      'Haberes Imponibles': { headers: [], mapeado: false },
      'Haberes No Imponibles': { headers: [], mapeado: false },
      'Cantidad de Horas Extras': { headers: [], mapeado: false },
      'Aportes Patronales': { headers: [], mapeado: false },
      'Impuestos': { headers: [], mapeado: false },
      'Otros Descuentos': { headers: [], mapeado: false },
      'Descuentos Legales': { headers: [], mapeado: false },
      'Información': { headers: [], mapeado: false }
    },
    headersLibroRemuneraciones: [
      'Sueldo Base', 'Bono Productividad', 'AFP', 'Salud', 'Impuesto Único',
      'Horas Extras 50%', 'Horas Extras 100%', 'Gratificación', 'Colación',
      'Préstamo Empresa', 'Descuento Varios', 'Seguro Cesantía'
    ],
    datosConsolidados: {
      empleados_procesados: 0,
      total_empleados: 150,
      conceptos_consolidados: 0
    },
    procesando: false
  });

  // Calcular progreso de la tarjeta
  const calcularProgreso = () => {
    const conceptosMapeados = Object.values(estadoInterno.mapeoConceptos)
      .filter(concepto => concepto.mapeado).length;
    
    let progreso = (conceptosMapeados / CONCEPTOS_PAYROLL.length) * 70; // 70% por mapeo
    
    if (estadoInterno.procesoActual === 'consolidando_datos') progreso += 20;
    if (estadoInterno.procesoActual === 'datos_consolidados' || completada) progreso = 100;
    
    return Math.round(progreso);
  };

  // Actualizar estado al componente padre
  const notificarCambio = (nuevoEstado = {}) => {
    setTimeout(() => {
      const progreso = calcularProgreso();
      const todosMapeados = Object.values(estadoInterno.mapeoConceptos)
        .every(concepto => concepto.mapeado);
      const esCompleta = progreso === 100 && todosMapeados;
      
      console.log('[TARJETA 2] Estado mapeo:', {
        progreso,
        todosMapeados,
        esCompleta,
        mapeoConceptos: estadoInterno.mapeoConceptos
      });
      
      if (onEstadoChange) {
        onEstadoChange({
          completada: esCompleta,
          progreso: progreso,
          ...nuevoEstado
        });
      }
    }, 0);
  };

  // Mapear header a concepto
  const mapearHeader = (concepto, header) => {
    setEstadoInterno(prev => {
      const nuevoMapeo = { ...prev.mapeoConceptos };
      
      // Remover header de otros conceptos primero
      Object.keys(nuevoMapeo).forEach(key => {
        nuevoMapeo[key].headers = nuevoMapeo[key].headers.filter(h => h !== header);
      });
      
      // Agregar header al concepto seleccionado
      if (!nuevoMapeo[concepto].headers.includes(header)) {
        nuevoMapeo[concepto].headers.push(header);
        nuevoMapeo[concepto].mapeado = true;
      }
      
      const nuevoEstado = {
        ...prev,
        mapeoConceptos: nuevoMapeo
      };
      
      // Calcular progreso con el nuevo estado
      setTimeout(() => {
        const conceptosMapeados = Object.values(nuevoMapeo)
          .filter(c => c.mapeado).length;
        
        let progreso = (conceptosMapeados / CONCEPTOS_PAYROLL.length) * 70; // 70% por mapeo
        
        if (nuevoEstado.procesoActual === 'consolidando_datos') progreso += 20;
        if (nuevoEstado.procesoActual === 'datos_consolidados' || completada) progreso = 100;
        
        const progresoFinal = Math.round(progreso);
        const todosMapeados = conceptosMapeados === CONCEPTOS_PAYROLL.length;
        const esCompleta = progresoFinal === 100 && todosMapeados;
        
        console.log('[TARJETA 2] Mapeo actualizado:', {
          concepto,
          header,
          conceptosMapeados,
          totalConceptos: CONCEPTOS_PAYROLL.length,
          progreso: progresoFinal,
          todosMapeados,
          esCompleta,
          nuevoMapeo
        });
        
        if (onEstadoChange) {
          onEstadoChange({
            completada: esCompleta,
            progreso: progresoFinal
          });
        }
      }, 0);
      
      return nuevoEstado;
    });
  };

  // Desmarcar mapeo de concepto
  const desmapearConcepto = (concepto) => {
    setEstadoInterno(prev => {
      const nuevoMapeo = {
        ...prev.mapeoConceptos,
        [concepto]: { headers: [], mapeado: false }
      };
      
      const nuevoEstado = {
        ...prev,
        mapeoConceptos: nuevoMapeo
      };
      
      // Calcular progreso con el nuevo estado
      setTimeout(() => {
        const conceptosMapeados = Object.values(nuevoMapeo)
          .filter(c => c.mapeado).length;
        
        let progreso = (conceptosMapeados / CONCEPTOS_PAYROLL.length) * 70;
        const progresoFinal = Math.round(progreso);
        
        console.log('[TARJETA 2] Concepto desmapeado:', {
          concepto,
          conceptosMapeados,
          progreso: progresoFinal
        });
        
        if (onEstadoChange) {
          onEstadoChange({
            completada: false,
            progreso: progresoFinal
          });
        }
      }, 0);
      
      return nuevoEstado;
    });
  };

  // Consolidar datos
  const consolidarDatos = async () => {
    setEstadoInterno(prev => ({ 
      ...prev, 
      procesando: true, 
      procesoActual: 'consolidando_datos' 
    }));
    
    try {
      // Simulación de consolidación
      for (let i = 0; i <= 150; i += 10) {
        await new Promise(resolve => setTimeout(resolve, 100));
        setEstadoInterno(prev => ({
          ...prev,
          datosConsolidados: {
            ...prev.datosConsolidados,
            empleados_procesados: Math.min(i, 150),
            conceptos_consolidados: CONCEPTOS_PAYROLL.length
          }
        }));
      }
      
      setEstadoInterno(prev => ({ 
        ...prev, 
        procesando: false,
        procesoActual: 'datos_consolidados'
      }));
      
      notificarCambio();
      
    } catch (error) {
      console.error('Error consolidando datos:', error);
      setEstadoInterno(prev => ({ ...prev, procesando: false }));
    }
  };

  // Verificar si todos los conceptos están mapeados
  const todosMapeados = () => {
    return Object.values(estadoInterno.mapeoConceptos).every(concepto => concepto.mapeado);
  };

  if (bloqueada) {
    return (
      <div className="bg-gray-800 p-6 rounded-lg shadow-lg opacity-50">
        <div className="flex items-center gap-2 mb-4">
          <svg className="w-5 h-5 text-gray-500" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd" />
          </svg>
          <h4 className="text-lg font-bold text-gray-500">Consolidación de Datos</h4>
          <span className="text-xs bg-gray-700 px-2 py-1 rounded text-gray-400">Bloqueada</span>
        </div>
        <p className="text-gray-500 text-sm">
          Esta fase se desbloqueará cuando se complete la verificación de discrepancias.
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
      
      <div className={`p-6 border-2 ${
        completada ? 'border-green-500' : 'border-indigo-500'
      }`}>
      
      {/* Header de la tarjeta */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          {completada ? (
            <svg className="w-6 h-6 text-green-500" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
            </svg>
          ) : (
            <div className="w-6 h-6 bg-indigo-500 rounded-full flex items-center justify-center">
              <span className="text-white text-sm font-bold">2</span>
            </div>
          )}
          <h4 className="text-lg font-bold text-white">Consolidación de Datos</h4>
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
              completada ? 'bg-green-500' : 'bg-indigo-500'
            }`}
            style={{ width: `${calcularProgreso()}%` }}
          ></div>
        </div>
      </div>

      {/* Contenido principal */}
      <div className="space-y-6">
        
        {/* Sección: Mapeo de Conceptos */}
        {estadoInterno.procesoActual === 'mapeo_headers' && (
          <div>
            <div className="flex items-center justify-between mb-4">
              <h5 className="text-md font-semibold text-white">Mapeo de Headers a Conceptos Payroll</h5>
              <span className="text-sm text-gray-400">
                {Object.values(estadoInterno.mapeoConceptos).filter(c => c.mapeado).length}/{CONCEPTOS_PAYROLL.length} mapeados
              </span>
            </div>
            
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              
              {/* Lista de Conceptos Payroll */}
              <div>
                <h6 className="text-sm font-semibold text-gray-300 mb-3">Conceptos Payroll</h6>
                <div className="space-y-2">
                  {CONCEPTOS_PAYROLL.map((concepto) => (
                    <div key={concepto} className={`p-3 rounded border ${
                      estadoInterno.mapeoConceptos[concepto].mapeado 
                        ? 'bg-indigo-900 border-indigo-500' 
                        : 'bg-gray-700 border-gray-600'
                    }`}>
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-white font-medium">{concepto}</span>
                        {estadoInterno.mapeoConceptos[concepto].mapeado && (
                          <button
                            onClick={() => desmapearConcepto(concepto)}
                            className="text-red-400 hover:text-red-300"
                          >
                            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                            </svg>
                          </button>
                        )}
                      </div>
                      {estadoInterno.mapeoConceptos[concepto].headers.length > 0 && (
                        <div className="mt-2 text-xs text-indigo-300">
                          Headers: {estadoInterno.mapeoConceptos[concepto].headers.join(', ')}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Headers del Libro de Remuneraciones */}
              <div>
                <h6 className="text-sm font-semibold text-gray-300 mb-3">Headers - Libro Remuneraciones</h6>
                <div className="space-y-2">
                  {estadoInterno.headersLibroRemuneraciones.map((header) => {
                    const yaAsignado = Object.values(estadoInterno.mapeoConceptos)
                      .some(concepto => concepto.headers.includes(header));
                    
                    return (
                      <div key={header} className="relative">
                        <select
                          value={yaAsignado ? 
                            Object.keys(estadoInterno.mapeoConceptos).find(key => 
                              estadoInterno.mapeoConceptos[key].headers.includes(header)
                            ) || '' : ''
                          }
                          onChange={(e) => e.target.value && mapearHeader(e.target.value, header)}
                          className="w-full bg-gray-700 text-white text-sm p-2 rounded border border-gray-600 focus:border-indigo-500"
                        >
                          <option value="">{header}</option>
                          {CONCEPTOS_PAYROLL.map((concepto) => (
                            <option key={concepto} value={concepto}>
                              → {concepto}
                            </option>
                          ))}
                        </select>
                        {yaAsignado && (
                          <div className="absolute right-2 top-1/2 transform -translate-y-1/2">
                            <svg className="w-4 h-4 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                            </svg>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* Botón para consolidar */}
            {todosMapeados() && (
              <div className="mt-6 text-center">
                <button
                  onClick={consolidarDatos}
                  disabled={estadoInterno.procesando}
                  className="px-6 py-3 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-lg"
                >
                  Consolidar Datos
                </button>
              </div>
            )}
          </div>
        )}

        {/* Sección: Progreso de Consolidación */}
        {(estadoInterno.procesoActual === 'consolidando_datos' || estadoInterno.procesoActual === 'datos_consolidados') && (
          <div>
            <h5 className="text-md font-semibold text-white mb-4">Progreso de Consolidación</h5>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-gray-700 p-4 rounded">
                <h6 className="text-sm text-gray-400 mb-2">Empleados Procesados</h6>
                <div className="text-2xl font-bold text-white mb-2">
                  {estadoInterno.datosConsolidados.empleados_procesados}/{estadoInterno.datosConsolidados.total_empleados}
                </div>
                <div className="w-full bg-gray-600 rounded-full h-2">
                  <div 
                    className="bg-indigo-500 h-2 rounded-full transition-all duration-300"
                    style={{ 
                      width: `${(estadoInterno.datosConsolidados.empleados_procesados / estadoInterno.datosConsolidados.total_empleados) * 100}%` 
                    }}
                  ></div>
                </div>
              </div>
              
              <div className="bg-gray-700 p-4 rounded">
                <h6 className="text-sm text-gray-400 mb-2">Conceptos Consolidados</h6>
                <div className="text-2xl font-bold text-white mb-2">
                  {estadoInterno.datosConsolidados.conceptos_consolidados}/{CONCEPTOS_PAYROLL.length}
                </div>
                <div className="w-full bg-gray-600 rounded-full h-2">
                  <div 
                    className="bg-green-500 h-2 rounded-full transition-all duration-300"
                    style={{ 
                      width: `${(estadoInterno.datosConsolidados.conceptos_consolidados / CONCEPTOS_PAYROLL.length) * 100}%` 
                    }}
                  ></div>
                </div>
              </div>
            </div>

            {estadoInterno.procesoActual === 'consolidando_datos' && (
              <div className="mt-4 text-center">
                <div className="inline-flex items-center gap-2 text-indigo-400">
                  <svg className="animate-spin w-5 h-5" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <span>Consolidando datos...</span>
                </div>
              </div>
            )}

            {estadoInterno.procesoActual === 'datos_consolidados' && (
              <div className="mt-4 p-4 bg-green-900 rounded-lg border border-green-700">
                <div className="flex items-center gap-2 text-green-300">
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                  <span className="font-semibold">Consolidación Completada</span>
                </div>
                <p className="text-green-200 text-sm mt-1">
                  Todos los datos han sido consolidados exitosamente. Puede continuar con la siguiente fase.
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

export default TarjetaConsolidacionDatos;
