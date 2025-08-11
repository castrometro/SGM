import { useState, useEffect, useMemo } from "react";
// import { obtenerConceptosRemuneracionPorCierre } from "../api/nomina"; // DESHABILITADO - Funcionalidad de nómina removida

const ModalMapeoNovedades = ({
  isOpen,
  onClose,
  cierreId,
  headersSinClasificar = [],
  headersClasificados = [],
  mapeosExistentes = {},
  onGuardarMapeos,
  soloLectura = false,
}) => {
  // Combine headers based on mode
  const allHeaders = useMemo(
    () => (soloLectura ? [...headersSinClasificar, ...headersClasificados] : [...headersSinClasificar]),
    [headersSinClasificar, headersClasificados, soloLectura]
  );

  // Local map state, initialized from props
  const [mapeos, setMapeos] = useState({});
  // Selected header to map
  const [headerSeleccionado, setHeaderSeleccionado] = useState(null);
  // Concepts from backend
  const [conceptosLibro, setConceptosLibro] = useState([]);
  // Filter text
  const [filtroConceptos, setFiltroConceptos] = useState("");
  const [loading, setLoading] = useState(false);
  
  // Estados para selección múltiple
  const [modoSeleccionMultiple, setModoSeleccionMultiple] = useState(false);
  const [headersSeleccionados, setHeadersSeleccionados] = useState(new Set());
  const [conceptoParaMapeoMasivo, setConceptoParaMapeoMasivo] = useState(null);

  // IDs already used (excludes null so multiple "sin asignación" allowed)
  const usedConceptIds = useMemo(
    () => new Set(Object.values(mapeos).map(c => c.id).filter(id => id !== null)),
    [mapeos]
  );

  // Compute headers without mapping yet
  const headersPendientes = useMemo(
    () => allHeaders.filter(h => !mapeos[h]),
    [allHeaders, mapeos]
  );

  // Auto-select first pending header when list or mapeos change
  useEffect(() => {
    if (!soloLectura && isOpen) {
      setHeaderSeleccionado(prev => {
        // If previous still pending, keep
        if (prev && !mapeos[prev]) return prev;
        // Else pick first pending
        return headersPendientes[0] || null;
      });
    }
  }, [headersPendientes, soloLectura, isOpen]);

  // Load conceptos y mapeosExistentes when modal opens
  useEffect(() => {
    if (!isOpen || !cierreId) return;

    const cargarDatos = async () => {
      setLoading(true);
      try {
        const conceptos = await obtenerConceptosRemuneracionPorCierre(cierreId);
        setConceptosLibro(conceptos);

        // initialize map transformando mapeosExistentes
        const convertidos = {};
        Object.entries(mapeosExistentes).forEach(([header, data]) => {
          if (data.concepto_libro_id === null || data.concepto_libro_id === undefined) {
            convertidos[header] = { id: null, nombre_concepto: "Sin asignación" };
          } else {
            convertidos[header] = { id: data.concepto_libro_id, nombre_concepto: data.concepto_libro_nombre };
          }
        });
        setMapeos(convertidos);
      } catch (error) {
        console.error("Error al cargar datos para mapeo:", error);
      } finally {
        setLoading(false);
      }
    };

    cargarDatos();
  }, [isOpen, cierreId, mapeosExistentes]);

  const seleccionarHeader = header => {
    if (soloLectura) return;
    if (!mapeos[header]) setHeaderSeleccionado(header);
  };

  // Funciones para selección múltiple
  const toggleSeleccionHeader = (header) => {
    if (soloLectura || mapeos[header]) return; // No permitir seleccionar headers ya mapeados
    
    const nuevaSeleccion = new Set(headersSeleccionados);
    if (nuevaSeleccion.has(header)) {
      nuevaSeleccion.delete(header);
    } else {
      nuevaSeleccion.add(header);
    }
    setHeadersSeleccionados(nuevaSeleccion);
  };

  const seleccionarTodosHeaders = () => {
    if (soloLectura) return;
    
    const headersPendientes = allHeaders.filter(h => !mapeos[h]);
    setHeadersSeleccionados(new Set(headersPendientes));
  };

  const limpiarSeleccionHeaders = () => {
    setHeadersSeleccionados(new Set());
  };

  const aplicarMapeoMasivo = () => {
    if (!conceptoParaMapeoMasivo || headersSeleccionados.size === 0) return;

    const nuevosMapeos = { ...mapeos };
    headersSeleccionados.forEach(header => {
      nuevosMapeos[header] = conceptoParaMapeoMasivo;
    });

    setMapeos(nuevosMapeos);
    
    // Limpiar selección y modo masivo
    setHeadersSeleccionados(new Set());
    setConceptoParaMapeoMasivo(null);
    setModoSeleccionMultiple(false);
  };

  const aplicarSinAsignacionMasivo = () => {
    if (headersSeleccionados.size === 0) return;

    const nuevosMapeos = { ...mapeos };
    const sinAsignacion = { id: null, nombre_concepto: "Sin asignación" };
    
    headersSeleccionados.forEach(header => {
      nuevosMapeos[header] = sinAsignacion;
    });

    setMapeos(nuevosMapeos);
    
    // Limpiar selección y modo masivo
    setHeadersSeleccionados(new Set());
    setConceptoParaMapeoMasivo(null);
    setModoSeleccionMultiple(false);
  };

  const cancelarSeleccionMasiva = () => {
    setHeadersSeleccionados(new Set());
    setConceptoParaMapeoMasivo(null);
    setModoSeleccionMultiple(false);
  };

  const eliminarMapeo = header => {
    if (soloLectura) return;
    setMapeos(prev => {
      const nuevo = { ...prev };
      delete nuevo[header];
      return nuevo;
    });
  };

  const mapearHeaderConConcepto = concepto => {
    if (soloLectura) return;
    
    // Si estamos en modo selección múltiple, preparar para mapeo masivo
    if (modoSeleccionMultiple && headersSeleccionados.size > 0) {
      setConceptoParaMapeoMasivo(concepto);
      return;
    }
    
    // Mapeo individual normal
    if (!headerSeleccionado) return;
    if (usedConceptIds.has(concepto.id)) return;

    setMapeos(prev => ({
      ...prev,
      [headerSeleccionado]: concepto,
    }));
  };

  const mapearSinAsignacion = () => {
    if (!headerSeleccionado || soloLectura) return;
    setMapeos(prev => ({
      ...prev,
      [headerSeleccionado]: { id: null, nombre_concepto: "Sin asignación" },
    }));
  };

  const conceptosFiltrados = useMemo(
    () => conceptosLibro.filter(c =>
      c.nombre_concepto.toLowerCase().includes(filtroConceptos.toLowerCase())
    ),
    [conceptosLibro, filtroConceptos]
  );

  const handleGuardar = async () => {
    if (soloLectura) return;
    const arr = Object.entries(mapeos).map(([header, concepto]) => ({
      header_novedades: header,
      concepto_libro_id: concepto.id,
    }));
    await onGuardarMapeos(arr);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-60 z-50 flex justify-center items-center">
      <div className="bg-gray-900 rounded-lg shadow-lg p-6 w-full max-w-6xl max-h-[90vh] relative flex flex-col">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-400 hover:text-white text-xl"
        >
          &times;
        </button>

        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold text-white">
            Mapeo de Headers: Novedades ↔ Libro de Remuneraciones
            {soloLectura && <span className="text-sm text-gray-400 ml-2">(Solo lectura)</span>}
          </h2>
          
          {/* Controles de selección múltiple */}
          {!soloLectura && (
            <div className="flex items-center gap-3">
              {headersSeleccionados.size > 0 && (
                <span className="text-blue-400 font-medium text-sm">
                  🔵 {headersSeleccionados.size} seleccionados
                </span>
              )}
              
              <button
                onClick={() => setModoSeleccionMultiple(!modoSeleccionMultiple)}
                className={`px-3 py-1 rounded text-sm transition ${
                  modoSeleccionMultiple 
                    ? "bg-blue-600 text-white" 
                    : "bg-gray-700 text-gray-300 hover:bg-gray-600"
                }`}
                title="Activar/desactivar modo de selección múltiple"
              >
                Selección múltiple
              </button>
              
              {modoSeleccionMultiple && (
                <>
                  <button
                    onClick={seleccionarTodosHeaders}
                    className="px-2 py-1 text-xs bg-gray-700 hover:bg-gray-600 text-gray-300 rounded"
                    title="Seleccionar todos los headers pendientes"
                  >
                    Todos
                  </button>
                  <button
                    onClick={limpiarSeleccionHeaders}
                    className="px-2 py-1 text-xs bg-gray-700 hover:bg-gray-600 text-gray-300 rounded"
                    title="Limpiar selección"
                  >
                    Ninguno
                  </button>
                </>
              )}
            </div>
          )}
        </div>

        {/* Panel de mapeo masivo */}
        {modoSeleccionMultiple && headersSeleccionados.size > 0 && !soloLectura && (
          <div className="bg-blue-900/30 border border-blue-700/50 rounded-lg p-4 mb-4">
            <div className="flex items-center gap-4 flex-wrap">
              <span className="text-blue-300 font-medium">
                Mapear {headersSeleccionados.size} headers seleccionados:
              </span>
              
              {conceptoParaMapeoMasivo && (
                <div className="flex items-center gap-2 bg-green-800/30 px-3 py-1 rounded border border-green-600">
                  <span className="text-green-300 text-sm">
                    ➤ {conceptoParaMapeoMasivo.nombre_concepto}
                  </span>
                </div>
              )}
              
              <div className="flex gap-2">
                <button
                  onClick={aplicarMapeoMasivo}
                  disabled={!conceptoParaMapeoMasivo}
                  className="px-3 py-1 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-600 disabled:opacity-50 text-white rounded text-sm font-medium transition"
                >
                  Aplicar Mapeo
                </button>
                
                <button
                  onClick={aplicarSinAsignacionMasivo}
                  className="px-3 py-1 bg-red-600 hover:bg-red-500 text-white rounded text-sm font-medium transition"
                >
                  Sin Asignación
                </button>
                
                <button
                  onClick={cancelarSeleccionMasiva}
                  className="px-3 py-1 bg-gray-600 hover:bg-gray-500 text-white rounded text-sm font-medium transition"
                >
                  Cancelar
                </button>
              </div>
            </div>
            
            {conceptoParaMapeoMasivo ? (
              <div className="text-xs text-blue-200 mt-2">
                ✓ Concepto seleccionado. Haz clic en "Aplicar Mapeo" para mapear todos los headers seleccionados.
              </div>
            ) : (
              <div className="text-xs text-blue-200 mt-2">
                👆 Haz clic en un concepto de la lista para mapearlo a todos los headers seleccionados.
              </div>
            )}
          </div>
        )}

        {loading ? (
          <div className="text-center py-8 text-white">Cargando...</div>
        ) : (
          <div className="flex gap-6 flex-1 overflow-hidden">
            {/* Headers Panel */}
            <div className="flex-1 flex flex-col min-h-0">
              <h3 className="font-medium mb-3 text-center text-white">
                Headers ({allHeaders.length})
              </h3>
              <div className="flex-1 border-2 border-dashed border-blue-400 bg-opacity-10 rounded-lg p-3 overflow-y-auto bg-blue-50">
                {allHeaders.map(header => {
                  const isMapped = !!mapeos[header];
                  const isSelected = header === headerSeleccionado;
                  const isChecked = headersSeleccionados.has(header);
                  return (
                    <div
                      key={header}
                      className={`p-3 mb-2 text-sm rounded-lg border-2 transition-all duration-200
                        ${
                          isChecked
                            ? "bg-blue-600 text-white border-blue-400 shadow-lg"
                            : isSelected
                            ? "bg-blue-600 text-white border-blue-400 shadow-lg"
                            : isMapped
                            ? "bg-green-600 text-white border-green-400"
                            : "bg-gray-700 text-gray-100 hover:bg-gray-600 border-gray-600 hover:border-gray-500"
                        }
                      `}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2 flex-1">
                          {/* Checkbox para selección múltiple */}
                          {modoSeleccionMultiple && !soloLectura && !isMapped && (
                            <input
                              type="checkbox"
                              checked={isChecked}
                              onChange={(e) => {
                                e.stopPropagation();
                                toggleSeleccionHeader(header);
                              }}
                              className="w-4 h-4 text-blue-600 bg-gray-700 border-gray-600 rounded focus:ring-blue-500"
                            />
                          )}
                          
                          <span 
                            className="flex-1 cursor-pointer"
                            onClick={() => {
                              if (!modoSeleccionMultiple) {
                                seleccionarHeader(header);
                              }
                            }}
                          >
                            {header}
                          </span>
                        </div>
                        
                        {!soloLectura && !isMapped && !modoSeleccionMultiple && (
                          <span className="text-xs text-gray-400">
                            {isSelected ? "📍" : "↗️"}
                          </span>
                        )}
                      </div>
                      {isMapped && (
                        <div className="text-xs mt-2 pt-2 border-t border-green-500">
                          → {mapeos[header].nombre_concepto}
                          {!soloLectura && (
                            <button
                              onClick={e => { e.stopPropagation(); eliminarMapeo(header); }}
                              className="mt-2 text-red-300 hover:text-red-100 text-xs bg-red-900/30 px-2 py-1 rounded"
                            >
                              ✖ Eliminar
                            </button>
                          )}
                        </div>
                      )}
                      {isSelected && !isMapped && !modoSeleccionMultiple && (
                        <div className="text-xs mt-2 pt-2 border-t border-blue-400 text-blue-200">
                          Haz clic en un concepto para mapear
                        </div>
                      )}
                      
                      {isChecked && modoSeleccionMultiple && (
                        <div className="text-xs mt-2 pt-2 border-t border-blue-400 text-blue-200">
                          ✓ Seleccionado para mapeo masivo
                        </div>
                      )}
                    </div>
                  );
                })}

                {allHeaders.length === 0 && (
                  <div className="text-center text-gray-400 py-8">No hay headers</div>
                )}
              </div>
            </div>

            {/* Conceptos Panel */}
            <div className="flex-1 flex flex-col min-h-0">
              <h3 className="font-medium mb-3 text-center text-white">
                Conceptos ({conceptosFiltrados.length})
                {!soloLectura && modoSeleccionMultiple && headersSeleccionados.size > 0 && (
                  <div className="text-xs text-blue-400 mt-1">
                    Selecciona un concepto para mapear {headersSeleccionados.size} headers
                  </div>
                )}
                {!soloLectura && !modoSeleccionMultiple && headerSeleccionado && (
                  <div className="text-xs text-green-400 mt-1">
                    Mapeando: "{headerSeleccionado}"
                  </div>
                )}
              </h3>
              <input
                type="text"
                placeholder="Buscar..."
                value={filtroConceptos}
                onChange={e => setFiltroConceptos(e.target.value)}
                className="mb-3 px-3 py-2 bg-gray-700 text-white rounded-lg border border-gray-600 focus:border-blue-500 focus:outline-none"
              />
              {!soloLectura && (
                <button
                  type="button"
                  onClick={mapearSinAsignacion}
                  disabled={!headerSeleccionado}
                  className={`mb-3 px-3 py-2 rounded text-sm border-2 transition-colors ${
                    headerSeleccionado ? 'bg-red-600 hover:bg-red-500 border-red-500 text-white' : 'bg-gray-700 text-gray-400 border-gray-600 cursor-not-allowed'
                  }`}
                >
                  Sin asignación
                </button>
              )}
              <div className="flex-1 border-2 border-dashed border-green-400 bg-opacity-10 rounded-lg p-3 overflow-y-auto bg-green-50">
                {conceptosFiltrados.map(concepto => {
                  const used = usedConceptIds.has(concepto.id);
                  const canMapIndividual = !soloLectura && headerSeleccionado && !used && !modoSeleccionMultiple;
                  const canMapMasivo = !soloLectura && modoSeleccionMultiple && headersSeleccionados.size > 0 && !used;
                  const canMap = canMapIndividual || canMapMasivo;
                  const isSelectedForMasivo = conceptoParaMapeoMasivo?.id === concepto.id;
                  
                  return (
                    <div
                      key={concepto.id}
                      onClick={() => canMap && mapearHeaderConConcepto(concepto)}
                      className={`p-3 mb-2 text-sm rounded-lg transition-all duration-200 border-2
                        ${
                          isSelectedForMasivo
                            ? "bg-green-600 text-white border-green-400 shadow-lg"
                            : used
                            ? "bg-gray-600 text-gray-400 cursor-not-allowed"
                            : canMap
                            ? "bg-gray-700 text-white hover:bg-green-600 cursor-pointer border-gray-600 hover:border-green-500"
                            : "bg-gray-700 text-gray-100 cursor-default border-gray-600"
                        }
                      `}
                    >
                      <div className="flex items-center justify-between">
                        <span className="flex-1">{concepto.nombre_concepto}</span>
                        {used && <span className="text-xs text-yellow-400">✓ Usado</span>}
                        {isSelectedForMasivo && <span className="text-xs text-green-200">🎯 Para mapeo masivo</span>}
                      </div>
                      <div className="text-xs mt-2 pt-2 border-t border-gray-600">
                        <span className="px-2 py-1 rounded text-xs font-medium"
                          >{concepto.clasificacion}</span>
                      </div>
                    </div>
                  );
                })}

                {conceptosFiltrados.length === 0 && (
                  <div className="text-center text-gray-400 py-8">
                    {filtroConceptos ? 'No se encontraron conceptos' : 'No hay conceptos disponibles'}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        <div className="flex justify-between items-center mt-6 pt-4 border-t border-gray-700">
          <div className="text-sm text-gray-400">
            ✅ {Object.keys(mapeos).length} mapeos • ⏳ {allHeaders.length - Object.keys(mapeos).length} pendientes
          </div>
          <div className="flex gap-2">
            <button
              onClick={onClose}
              className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-500"
            >
              {soloLectura ? 'Cerrar' : 'Cancelar'}
            </button>
            {!soloLectura && (
              <button
                onClick={handleGuardar}
                disabled={Object.keys(mapeos).length === 0}
                className={`px-4 py-2 rounded transition-colors
                  ${Object.keys(mapeos).length === 0 ? 'bg-gray-500 text-gray-300 cursor-not-allowed' : 'bg-blue-600 text-white hover:bg-blue-500'}`}
              >
                Guardar ({Object.keys(mapeos).length})
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ModalMapeoNovedades;
