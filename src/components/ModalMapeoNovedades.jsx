import { useState, useEffect, useMemo } from "react";
import { obtenerConceptosRemuneracionPorCierre } from "../api/nomina";

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

  const eliminarMapeo = header => {
    if (soloLectura) return;
    setMapeos(prev => {
      const nuevo = { ...prev };
      delete nuevo[header];
      return nuevo;
    });
  };

  const mapearHeaderConConcepto = concepto => {
    if (!headerSeleccionado || soloLectura) return;
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

        <h2 className="text-xl font-semibold mb-4 text-white">
          Mapeo de Headers: Novedades ↔ Libro de Remuneraciones
          {soloLectura && <span className="text-sm text-gray-400 ml-2">(Solo lectura)</span>}
        </h2>

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
                  return (
                    <div
                      key={header}
                      onClick={() => seleccionarHeader(header)}
                      className={`p-3 mb-2 text-sm rounded-lg cursor-pointer border-2 transition-all duration-200
                        ${
                          isSelected
                            ? "bg-blue-600 text-white border-blue-400 shadow-lg"
                            : isMapped
                            ? "bg-green-600 text-white border-green-400"
                            : "bg-gray-700 text-gray-100 hover:bg-gray-600 border-gray-600 hover:border-gray-500"
                        }
                      `}
                    >
                      <div className="flex items-center justify-between">
                        <span className="flex-1">{header}</span>
                        {!soloLectura && !isMapped && (
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
                      {isSelected && !isMapped && (
                        <div className="text-xs mt-2 pt-2 border-t border-blue-400 text-blue-200">
                          Haz clic en un concepto para mapear
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
                {!soloLectura && headerSeleccionado && (
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
                  const canMap = !soloLectura && headerSeleccionado && !used;
                  return (
                    <div
                      key={concepto.id}
                      onClick={() => canMap && mapearHeaderConConcepto(concepto)}
                      className={`p-3 mb-2 text-sm rounded-lg transition-all duration-200 border-2
                        ${
                          used
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
