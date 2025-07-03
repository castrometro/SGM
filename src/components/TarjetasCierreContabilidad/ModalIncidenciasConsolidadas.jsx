import { useState, useEffect } from 'react';
import { X, RefreshCw, ChevronRight, ChevronDown, CheckCircle, Trash2, Play, Bug } from 'lucide-react';
import { reprocesarConExcepciones, marcarCuentaNoAplica, eliminarExcepcionNoAplica, obtenerIncidenciasConsolidadasOptimizado, obtenerIncidenciasConsolidadasLibroMayor } from '../../api/contabilidad';
import CacheDebugPanel from '../Debug/CacheDebugPanel';

const getSeverityColor = (severidad) => {
  const colors = {
    critica: 'text-red-400',
    alta: 'text-orange-400',
    media: 'text-yellow-400',
    baja: 'text-blue-400'
  };
  return colors[severidad] || 'text-gray-400';
};

const ModalIncidenciasConsolidadas = ({ abierto, onClose, incidencias: incidenciasProp, cierreId, onReprocesar }) => {
  const [expandida, setExpandida] = useState(null);
  const [cuentasDetalle, setCuentasDetalle] = useState({});
  const [reprocesando, setReprocesando] = useState(false);
  const [incidenciasActuales, setIncidenciasActuales] = useState(incidenciasProp || []);
  const [recargando, setRecargando] = useState(false);
  const [excepcionesLocales, setExcepcionesLocales] = useState([]); // Nuevo estado para excepciones pendientes
  const [debugCacheVisible, setDebugCacheVisible] = useState(false);

  // Efecto para actualizar incidencias cuando cambian las props
  useEffect(() => {
    setIncidenciasActuales(incidenciasProp || []);
  }, [incidenciasProp]);

  const recargarIncidencias = async (forzarActualizacion = false) => {
    if (!cierreId) return;
    
    setRecargando(true);
    try {
      let data;
      
      if (forzarActualizacion) {
        // DESPUÉS del reprocesamiento, usar SIEMPRE datos actuales de la tabla Incidencia
        console.log('🔄 Recargando incidencias con datos FRESCOS desde tabla Incidencia...');
        data = await obtenerIncidenciasConsolidadasLibroMayor(cierreId);
      } else {
        // Para recargas normales, usar el endpoint optimizado
        console.log('📊 Recargando incidencias con endpoint optimizado...');
        data = await obtenerIncidenciasConsolidadasOptimizado(cierreId, false);
      }
      
      const incidenciasArray = Array.isArray(data) ? data : (data.incidencias || []);
      setIncidenciasActuales(incidenciasArray);
      
      console.log(`📊 Incidencias recargadas (forzar: ${forzarActualizacion}):`, incidenciasArray.length);
      
      // Logging adicional para debugging
      if (data._fuente) {
        console.log(`📍 Fuente de datos: ${data._fuente}`);
      }
      if (data._debug) {
        console.log(`🐛 Debug info:`, data._debug);
      }
      if (data._timestamp) {
        console.log(`⏰ Timestamp de datos: ${data._timestamp}`);
      }
      
    } catch (error) {
      console.error('Error recargando incidencias:', error);
    } finally {
      setRecargando(false);
    }
  };

  // Nueva función para sincronizar excepciones locales con el backend
  const sincronizarExcepcionesLocales = async () => {
    if (excepcionesLocales.length === 0) {
      console.log('📋 No hay excepciones locales pendientes de sincronización');
      return true;
    }

    console.log(`🔄 Sincronizando ${excepcionesLocales.length} excepciones locales con el servidor...`);
    
    try {
      for (const excepcion of excepcionesLocales) {
        const { codigoCuenta, tipoIncidencia, setId, motivo, accion } = excepcion;
        
        if (accion === 'crear') {
          console.log(`➕ Creando excepción: ${codigoCuenta} (${tipoIncidencia})`);
          await marcarCuentaNoAplica(cierreId, codigoCuenta, tipoIncidencia, motivo || 'Marcado como no aplica', setId);
        } else if (accion === 'eliminar') {
          console.log(`➖ Eliminando excepción: ${codigoCuenta} (${tipoIncidencia})`);
          await eliminarExcepcionNoAplica(cierreId, codigoCuenta, tipoIncidencia, setId);
        }
      }
      
      // Limpiar excepciones locales después de sincronizar
      setExcepcionesLocales([]);
      console.log('✅ Todas las excepciones locales han sido sincronizadas');
      return true;
      
    } catch (error) {
      console.error('❌ Error sincronizando excepciones:', error);
      throw new Error(`Error sincronizando excepciones: ${error.response?.data?.error || error.message}`);
    }
  };

  // Función completa de reprocesamiento
  const handleReprocesar = async () => {
    if (!cierreId) {
      alert('❌ Error: ID de cierre no disponible');
      return;
    }

    const totalExcepcionesLocales = excepcionesLocales.length;
    
    const confirmar = window.confirm(
      `¿Está seguro de que desea reprocesar el Libro Mayor?\n\n` +
      `${totalExcepcionesLocales > 0 ? 
        `Se sincronizarán ${totalExcepcionesLocales} excepciones locales y ` : 
        ''
      }se generará una nueva iteración del libro.\n\n` +
      'Este proceso puede tomar varios minutos.'
    );
    
    if (!confirmar) return;

    setReprocesando(true);
    try {
      // 1. Sincronizar excepciones locales si las hay
      if (totalExcepcionesLocales > 0) {
        await sincronizarExcepcionesLocales();
        alert(`✅ ${totalExcepcionesLocales} excepciones sincronizadas correctamente`);
      }
      
      // 2. Reprocesar el libro mayor
      console.log('🔄 Iniciando reprocesamiento del Libro Mayor...');
      const resultado = await reprocesarConExcepciones(cierreId);
      console.log('✅ Reprocesamiento completado:', resultado);
      
      // 3. Recargar incidencias FORZANDO uso de datos actuales de tabla Incidencia
      console.log('🔄 Recargando incidencias con datos FRESCOS (no snapshot)...');
      await recargarIncidencias(true); // ← FORZAR datos frescos de la tabla Incidencia
      
      // 4. Limpiar detalles expandidos para forzar recarga completa
      setCuentasDetalle({});
      setExpandida(null);
      
      console.log('✅ Modal de incidencias actualizado con datos post-reprocesamiento');
      
      alert(
        `✅ Reprocesamiento completado exitosamente!\n\n` +
        `Nueva iteración: ${resultado.nueva_iteracion}\n` +
        `Estado: ${resultado.estado}\n\n` +
        'El modal se ha actualizado con las incidencias más recientes.'
      );
      
      // 5. Notificar al componente padre
      if (onReprocesar) {
        console.log('📡 Notificando al componente padre para actualizar...');
        onReprocesar();
      }
      
    } catch (error) {
      console.error('❌ Error en reprocesamiento:', error);
      alert(`❌ Error en el reprocesamiento: ${error.message}`);
    } finally {
      setReprocesando(false);
    }
  };

  if (!abierto) return null;

  const handleActualizar = async () => {
    if (!cierreId) return;
    
    setReprocesando(true);
    try {
      // Recargar las incidencias desde el servidor
      await recargarIncidencias();
      
      // NO limpiar excepciones locales - preservar cambios pendientes
      // NO limpiar detalles expandidos completamente - solo actualizar datos del servidor
      
      alert('✅ Incidencias actualizadas desde el servidor. Los cambios locales se han preservado.');
      
    } catch (error) {
      console.error('Error al actualizar incidencias:', error);
      alert(`❌ Error al actualizar: ${error.response?.data?.error || error.message}`);
    } finally {
      setReprocesando(false);
    }
  };

  const handleExpandir = async (index, tipoIncidencia) => {
    if (expandida === index) {
      setExpandida(null);
      return;
    }

    setExpandida(index);
    
    // Siempre recargar datos del servidor al expandir para obtener estado actual de excepciones
    const incidencia = incidenciasActuales[index];
    if (incidencia && incidencia.elementos_afectados) {
      // Transform elementos_afectados to match the expected structure
      const cuentasFromSnapshot = incidencia.elementos_afectados.map(elemento => {
        return {
          codigo: elemento.codigo,
          nombre: elemento.descripcion || `Cuenta ${elemento.codigo}`,
          descripcion: elemento.descripcion,
          set_nombre: elemento.set_nombre || null, // Nombre del set específico faltante
          set_id: elemento.set_id || null, // ID del set específico faltante
          tiene_excepcion: elemento.tiene_excepcion || false // Usar valor del servidor si está disponible
        };
      });
      
      setCuentasDetalle(prev => ({
        ...prev,
        [tipoIncidencia]: {
          cuentas: cuentasFromSnapshot,
          total: incidencia.cantidad_afectada || cuentasFromSnapshot.length
        }
      }));
      
      console.log(`📋 Expandido ${tipoIncidencia}: ${cuentasFromSnapshot.length} cuentas, ${cuentasFromSnapshot.filter(c => c.tiene_excepcion).length} con excepciones`);
    }
  };

  // Función para determinar si se puede marcar "No aplica" según el tipo de incidencia
  const puedeMarcarNoAplica = (tipoIncidencia) => {
    // Solo permitir "No aplica" para:
    // - DOC_NULL: movimientos sin tipo de documento
    // - CUENTA_NO_CLAS o CUENTA_NO_CLASIFICADA: cuentas sin clasificación (para sets específicos)
    return tipoIncidencia === 'DOC_NULL' || 
           tipoIncidencia === 'CUENTA_NO_CLAS' || 
           tipoIncidencia === 'CUENTA_NO_CLASIFICADA';
  };

  const handleMarcarNoAplica = async (codigoCuenta, tipoIncidencia, setId = null, motivo = '') => {
    try {
      // Actualizar estado local inmediatamente
      setCuentasDetalle(prev => ({
        ...prev,
        [tipoIncidencia]: {
          ...prev[tipoIncidencia],
          cuentas: prev[tipoIncidencia].cuentas.map(cuenta =>
            cuenta.codigo === codigoCuenta
              ? { ...cuenta, tiene_excepcion: true, motivo_excepcion: motivo }
              : cuenta
          )
        }
      }));
      
      // Agregar a excepciones locales pendientes
      setExcepcionesLocales(prev => {
        const nuevaExcepcion = {
          codigoCuenta,
          tipoIncidencia,
          setId,
          motivo,
          accion: 'crear'
        };
        
        // Evitar duplicados - si ya existe, reemplazar
        const filtradas = prev.filter(exc => 
          !(exc.codigoCuenta === codigoCuenta && 
            exc.tipoIncidencia === tipoIncidencia && 
            exc.setId === setId)
        );
        
        return [...filtradas, nuevaExcepcion];
      });
      
      console.log(`📝 Excepción agregada localmente: ${codigoCuenta} (${tipoIncidencia}) - Pendiente de sincronización`);
      
    } catch (error) {
      console.error('Error marcando cuenta como no aplica:', error);
      alert(`❌ Error al marcar la cuenta: ${error.message}`);
    }
  };

  const handleEliminarExcepcion = async (codigoCuenta, tipoIncidencia, setId = null) => {
    try {
      const confirmar = window.confirm(
        `¿Está seguro de que desea eliminar la excepción "No aplica" para la cuenta ${codigoCuenta}?\n\n` +
        'Esta cuenta volverá a aparecer como incidencia hasta que se resuelva correctamente.'
      );
      
      if (!confirmar) return;
      
      // Actualizar el estado local inmediatamente
      setCuentasDetalle(prev => ({
        ...prev,
        [tipoIncidencia]: {
          ...prev[tipoIncidencia],
          cuentas: prev[tipoIncidencia].cuentas.map(cuenta =>
            cuenta.codigo === codigoCuenta
              ? { ...cuenta, tiene_excepcion: false }
              : cuenta
          )
        }
      }));
      
      // Verificar si es una excepción local pendiente o una que existe en el servidor
      const excepcionLocalIndex = excepcionesLocales.findIndex(exc => 
        exc.codigoCuenta === codigoCuenta && 
        exc.tipoIncidencia === tipoIncidencia && 
        exc.setId === setId
      );
      
      if (excepcionLocalIndex >= 0) {
        // Es una excepción local - simplemente quitarla de la lista
        setExcepcionesLocales(prev => prev.filter((_, index) => index !== excepcionLocalIndex));
        console.log(`🗑️ Excepción local eliminada: ${codigoCuenta} (${tipoIncidencia})`);
      } else {
        // Es una excepción del servidor - marcar para eliminación
        setExcepcionesLocales(prev => [...prev, {
          codigoCuenta,
          tipoIncidencia,
          setId,
          accion: 'eliminar'
        }]);
        console.log(`🗑️ Excepción marcada para eliminación: ${codigoCuenta} (${tipoIncidencia}) - Pendiente de sincronización`);
      }
      
    } catch (error) {
      console.error('Error eliminando excepción:', error);
      alert(`❌ Error al eliminar la excepción: ${error.message}`);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 rounded-xl max-w-4xl w-full max-h-[90vh] flex flex-col shadow-xl">
        {/* Header */}
        <div className="p-4 border-b border-gray-700 flex justify-between items-center">
          <div className="flex items-center gap-3">
            <h3 className="text-lg font-semibold text-white">Incidencias Detectadas</h3>
            {excepcionesLocales.length > 0 && (
              <span className="bg-orange-600 text-white text-xs px-2 py-1 rounded-full">
                {excepcionesLocales.length} cambios pendientes
              </span>
            )}
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => setDebugCacheVisible(true)}
              className="bg-gray-600 hover:bg-gray-700 text-white px-2 py-1 rounded text-xs flex items-center gap-1 transition-colors"
              title="Debug del caché Redis"
            >
              <Bug size={14} />
              Debug
            </button>
            <button
              onClick={handleActualizar}
              disabled={reprocesando}
              className="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-800 disabled:opacity-50 text-white px-3 py-1 rounded text-sm flex items-center gap-2 transition-colors"
              title="Actualizar incidencias desde el servidor"
            >
              <RefreshCw size={16} className={reprocesando ? 'animate-spin' : ''} />
              {reprocesando ? 'Actualizando...' : 'Actualizar'}
            </button>
            <button
              onClick={handleReprocesar}
              disabled={reprocesando}
              className="bg-green-600 hover:bg-green-700 disabled:bg-green-800 disabled:opacity-50 text-white px-3 py-1 rounded text-sm flex items-center gap-2 transition-colors font-medium"
              title={excepcionesLocales.length > 0 ? 
                `Sincronizar ${excepcionesLocales.length} excepciones y reprocesar` : 
                'Reprocesar el Libro Mayor'
              }
            >
              <Play size={16} className={reprocesando ? 'animate-spin' : ''} />
              {reprocesando ? 'Reprocesando...' : 'Reprocesar'}
            </button>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-white transition-colors"
            >
              <X size={20} />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-4 overflow-y-auto flex-1">
          {!incidenciasActuales || incidenciasActuales.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-gray-400 text-lg">No se encontraron incidencias.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {incidenciasActuales.map((incidencia, index) => (
                <div
                  key={index}
                  className="bg-gray-800 rounded-lg border border-gray-700"
                >
                  {/* Header de la incidencia */}
                  <div className="p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className={`font-semibold ${getSeverityColor(incidencia.severidad)}`}>
                          {incidencia.severidad?.toUpperCase() || 'DESCONOCIDA'}
                        </span>
                        <span className="text-gray-400">•</span>
                        <span className="text-white">
                          {incidencia.mensaje_usuario || 'Sin mensaje'}
                        </span>
                      </div>
                      
                      {/* Botón expandir */}
                      <button
                        onClick={() => handleExpandir(index, incidencia.tipo_incidencia)}
                        className="flex items-center gap-2 text-blue-400 hover:text-blue-300 transition-colors"
                      >
                        <span className="text-sm">Ver detalles</span>
                        {expandida === index ? 
                          <ChevronDown size={16} /> : 
                          <ChevronRight size={16} />
                        }
                      </button>
                    </div>

                    {/* Información básica */}
                    <div className="mt-3 space-y-2 text-sm">
                      <div className="text-gray-300">
                        <span className="text-gray-400">Elementos afectados:</span> {incidencia.cantidad_afectada || 0}
                      </div>
                      
                      {/* Estadísticas adicionales */}
                      {incidencia.estadisticas_adicionales && Object.keys(incidencia.estadisticas_adicionales).length > 0 && (
                        <div className="grid grid-cols-2 gap-2 text-xs bg-gray-700 p-2 rounded">
                          {Object.entries(incidencia.estadisticas_adicionales).map(([key, value]) => (
                            <div key={key} className="text-gray-300">
                              <span className="text-gray-400">{key.replace(/_/g, ' ')}:</span> {' '}
                              <span className="text-white">
                                {typeof value === 'number' ? value.toLocaleString() : value}
                              </span>
                            </div>
                          ))}
                        </div>
                      )}

                      {/* Acción sugerida */}
                      {incidencia.accion_sugerida && (
                        <div className="p-2 bg-blue-900/30 border border-blue-700 rounded">
                          <div className="text-blue-300 text-sm">
                            💡 <span className="font-medium">Acción sugerida:</span>
                          </div>
                          <div className="text-blue-200 text-sm mt-1">
                            {incidencia.accion_sugerida}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Panel expandido con detalle de cuentas */}
                  {expandida === index && (
                    <div className="border-t border-gray-700 p-4 bg-gray-700/50">
                      {cuentasDetalle[incidencia.tipo_incidencia] ? (
                        <div>
                          <h4 className="text-white font-medium mb-3">
                            Cuentas afectadas ({cuentasDetalle[incidencia.tipo_incidencia].cuentas?.length || 0})
                            {incidencia.tipo_incidencia === 'CUENTA_NO_CLAS' && (
                              <span className="text-sm text-gray-400 font-normal ml-2">
                                - Falta clasificación en sets específicos
                              </span>
                            )}
                            {incidencia.tipo_incidencia === 'CUENTA_NO_CLASIFICADA' && (
                              <span className="text-sm text-gray-400 font-normal ml-2">
                                - Falta clasificación en sets específicos
                              </span>
                            )}
                          </h4>
                          <div className="space-y-2 max-h-60 overflow-y-auto">
                            {cuentasDetalle[incidencia.tipo_incidencia].cuentas?.map((cuenta, idx) => {
                              // Verificar si esta cuenta tiene cambios locales pendientes
                              const tieneExcepcionLocal = excepcionesLocales.some(exc => 
                                exc.codigoCuenta === cuenta.codigo && 
                                exc.tipoIncidencia === incidencia.tipo_incidencia &&
                                exc.setId === cuenta.set_id
                              );
                              
                              return (
                              <div 
                                key={idx}
                                className={`bg-gray-800 p-3 rounded border flex items-center justify-between ${
                                  tieneExcepcionLocal ? 'border-orange-500 bg-orange-900/20' : 'border-gray-600'
                                }`}
                              >
                                <div className="flex-1">
                                  <div className="flex items-center gap-2">
                                    <div className="text-white font-medium">
                                      {cuenta.codigo} - {cuenta.nombre}
                                    </div>
                                    {tieneExcepcionLocal && (
                                      <span className="bg-orange-600 text-white text-xs px-2 py-1 rounded">
                                        Cambio local
                                      </span>
                                    )}
                                  </div>
                                  {cuenta.descripcion && (
                                    <div className="text-gray-400 text-sm mt-1">
                                      {cuenta.descripcion}
                                    </div>
                                  )}                          {/* Mostrar información específica del set para clasificaciones */}
                          {(incidencia.tipo_incidencia === 'CUENTA_NO_CLAS' || incidencia.tipo_incidencia === 'CUENTA_NO_CLASIFICADA') && cuenta.set_nombre && (
                            <div className="text-yellow-400 text-sm mt-1 bg-yellow-900/20 px-2 py-1 rounded">
                              <span className="font-medium">Set faltante:</span> {cuenta.set_nombre}
                            </div>
                          )}
                                  {cuenta.monto > 0 && (
                                    <div className="text-green-400 text-sm">
                                      Monto: ${cuenta.monto.toLocaleString()}
                                    </div>
                                  )}
                                </div>
                                
                                <div className="ml-4">
                                  {cuenta.tiene_excepcion ? (
                                    <div className="flex items-center gap-2">
                                      <div className="flex items-center gap-2 text-green-400">
                                        <CheckCircle size={16} />
                                        <span className="text-sm">No aplica</span>
                                      </div>
                                      <button
                                        onClick={() => handleEliminarExcepcion(
                                          cuenta.codigo, 
                                          incidencia.tipo_incidencia,
                                          cuenta.set_id
                                        )}
                                        className="px-2 py-1 bg-red-600 hover:bg-red-700 text-white text-xs rounded transition-colors flex items-center gap-1"
                                        title="Eliminar excepción - volverá a aparecer como incidencia"
                                      >
                                        <Trash2 size={12} />
                                        Eliminar
                                      </button>
                                    </div>
                                  ) : puedeMarcarNoAplica(incidencia.tipo_incidencia) ? (
                                    <button
                                      onClick={() => handleMarcarNoAplica(
                                        cuenta.codigo, 
                                        incidencia.tipo_incidencia,
                                        cuenta.set_id // Pasar el set_id específico para clasificaciones
                                      )}
                                      className="px-3 py-1 bg-orange-600 hover:bg-orange-700 text-white text-sm rounded transition-colors"
                                      title={
                                        incidencia.tipo_incidencia === 'DOC_NULL' 
                                          ? 'Marcar que esta cuenta no requiere tipo de documento'
                                          : (incidencia.tipo_incidencia === 'CUENTA_NO_CLAS' || incidencia.tipo_incidencia === 'CUENTA_NO_CLASIFICADA')
                                          ? `Marcar que esta cuenta no aplica para el set: ${cuenta.set_nombre || 'clasificación'}`
                                          : 'Marcar como no aplica'
                                      }
                                    >
                                      {incidencia.tipo_incidencia === 'DOC_NULL' 
                                        ? 'No requiere tipo doc'
                                        : (incidencia.tipo_incidencia === 'CUENTA_NO_CLAS' || incidencia.tipo_incidencia === 'CUENTA_NO_CLASIFICADA')
                                        ? `No aplica en "${cuenta.set_nombre || 'Set'}"`
                                        : 'Marcar "No aplica"'
                                      }
                                    </button>
                                  ) : (
                                    <div className="text-gray-400 text-xs">
                                      {incidencia.tipo_incidencia === 'CUENTA_INGLES' 
                                        ? 'Requiere nombre en inglés'
                                        : incidencia.tipo_incidencia === 'DOC_NO_REC'
                                        ? 'Requiere configurar tipo documento'
                                        : 'Acción requerida'
                                      }
                                    </div>
                                  )}
                                </div>
                              </div>
                            )})}
                          </div>
                        </div>
                      ) : (
                        <div className="text-gray-400 text-center py-4">
                          {incidencia.elementos_afectados && incidencia.elementos_afectados.length > 0 
                            ? "Expandiendo detalles..." 
                            : "No hay elementos afectados para mostrar"
                          }
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Debug Panel */}
      <CacheDebugPanel 
        visible={debugCacheVisible} 
        onClose={() => setDebugCacheVisible(false)} 
      />
    </div>
  );
};

export default ModalIncidenciasConsolidadas;
