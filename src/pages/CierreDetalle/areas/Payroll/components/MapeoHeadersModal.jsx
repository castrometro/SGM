import React, { useState, useEffect } from "react";

const MapeoHeadersModal = ({ 
  isOpen, 
  onClose, 
  onMapeoCompleto,
  cierreId 
}) => {
  
  const [itemsNovedades, setItemsNovedades] = useState([]);
  const [itemsLibro, setItemsLibro] = useState([]);
  const [mapeo, setMapeo] = useState({});
  const [loading, setLoading] = useState(true);

  // Cargar datos al abrir modal
  useEffect(() => {
    if (isOpen && cierreId) {
      cargarDatos();
    }
  }, [isOpen, cierreId]);

  const cargarDatos = async () => {
    setLoading(true);
    try {
      // Simular datos reales (puedes conectar al backend después)
      const fakeNovedades = [
        { id: 1, nombre_concepto: "Sueldo Base", codigo_columna: "E" },
        { id: 2, nombre_concepto: "Gratificación", codigo_columna: "F" },
        { id: 3, nombre_concepto: "Bono Productividad", codigo_columna: "G" },
        { id: 4, nombre_concepto: "Descuento AFP", codigo_columna: "H" },
        { id: 5, nombre_concepto: "Descuento Salud", codigo_columna: "I" },
        { id: 6, nombre_concepto: "Anticipos", codigo_columna: "J" },
        { id: 7, nombre_concepto: "Líquido a Pagar", codigo_columna: "K" },
        { id: 8, nombre_concepto: "Horas Extras", codigo_columna: "L" }
      ];

      const fakeLibro = [
        { id: 11, nombre_concepto: "Sueldo Base", codigo_columna: "H" },
        { id: 12, nombre_concepto: "Gratificación Legal", codigo_columna: "I" },
        { id: 13, nombre_concepto: "Bono Variable", codigo_columna: "J" },
        { id: 14, nombre_concepto: "AFP - Descuento", codigo_columna: "K" },
        { id: 15, nombre_concepto: "ISAPRE - Descuento", codigo_columna: "L" },
        { id: 16, nombre_concepto: "Anticipos Sueldo", codigo_columna: "M" },
        { id: 17, nombre_concepto: "Total Líquido", codigo_columna: "N" },
        { id: 18, nombre_concepto: "Sobretiempo", codigo_columna: "O" }
      ];

      setItemsNovedades(fakeNovedades);
      setItemsLibro(fakeLibro);
    } catch (error) {
      console.error('Error cargando datos:', error);
    }
    setLoading(false);
  };

  const actualizarMapeo = (itemNovedadId, itemLibroId) => {
    setMapeo(prev => ({
      ...prev,
      [itemNovedadId]: itemLibroId
    }));
  };

  const limpiarMapeo = (itemNovedadId) => {
    setMapeo(prev => {
      const nuevo = { ...prev };
      delete nuevo[itemNovedadId];
      return nuevo;
    });
  };

  const calcularProgreso = () => {
    const mapeados = Object.keys(mapeo).length;
    const total = itemsNovedades.length;
    return { mapeados, total, porcentaje: total > 0 ? (mapeados / total) * 100 : 0 };
  };

  const puedeGuardar = () => {
    return Object.keys(mapeo).length === itemsNovedades.length;
  };

  const guardarMapeo = () => {
    console.log('Mapeo guardado:', mapeo);
    onMapeoCompleto(mapeo);
    onClose();
  };

  if (!isOpen) return null;

  const progreso = calcularProgreso();

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-gray-800 rounded-lg w-[90%] max-w-6xl h-[80%] flex flex-col">
        
        {/* Header */}
        <div className="p-6 border-b border-gray-600">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-2xl font-bold text-white">🗺️ Mapeo de Headers</h2>
              <p className="text-gray-400 mt-1">
                Asocia cada concepto de Novedades con su equivalente en el Libro
              </p>
            </div>
            <button 
              onClick={onClose}
              className="text-gray-400 hover:text-white text-3xl"
            >
              ×
            </button>
          </div>
          
          {/* Barra de progreso */}
          <div className="mt-4">
            <div className="flex justify-between text-sm text-gray-300 mb-2">
              <span>Progreso: {progreso.mapeados}/{progreso.total}</span>
              <span className="font-bold">{Math.round(progreso.porcentaje)}%</span>
            </div>
            <div className="w-full bg-gray-700 rounded-full h-3">
              <div 
                className="bg-green-600 h-3 rounded-full transition-all duration-500"
                style={{ width: `${progreso.porcentaje}%` }}
              />
            </div>
          </div>
        </div>

        {/* Contenido */}
        <div className="flex-1 p-6 overflow-hidden">
          {loading ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-white text-xl">⏳ Cargando datos...</div>
            </div>
          ) : (
            <div className="h-full grid grid-cols-2 gap-6">
              
              {/* Lista de Novedades */}
              <div className="flex flex-col">
                <h3 className="text-lg font-semibold text-white mb-4">
                  📝 Conceptos de Novedades ({itemsNovedades.length})
                </h3>
                
                <div className="flex-1 overflow-y-auto space-y-3">
                  {itemsNovedades.map(item => {
                    const mapeadoA = mapeo[item.id];
                    const itemLibroMapeado = itemsLibro.find(lib => lib.id === mapeadoA);
                    
                    return (
                      <div 
                        key={item.id}
                        className={`p-4 border-2 rounded-lg transition-all ${
                          mapeadoA 
                            ? 'border-green-500 bg-green-900/30' 
                            : 'border-gray-600 bg-gray-700/50'
                        }`}
                      >
                        <div className="flex justify-between items-start">
                          <div className="flex-1">
                            <div className="font-semibold text-white">
                              <span className="text-blue-400">[{item.codigo_columna}]</span> {item.nombre_concepto}
                            </div>
                            {mapeadoA && itemLibroMapeado && (
                              <div className="text-sm text-green-400 mt-2">
                                ✅ → [{itemLibroMapeado.codigo_columna}] {itemLibroMapeado.nombre_concepto}
                              </div>
                            )}
                          </div>
                          
                          {mapeadoA && (
                            <button
                              onClick={() => limpiarMapeo(item.id)}
                              className="text-red-400 hover:text-red-300 ml-3 text-xl"
                              title="Limpiar"
                            >
                              ×
                            </button>
                          )}
                        </div>
                        
                        {!mapeadoA && (
                          <div className="mt-3">
                            <select
                              value=""
                              onChange={(e) => e.target.value && actualizarMapeo(item.id, parseInt(e.target.value))}
                              className="w-full bg-gray-600 text-white p-3 rounded border border-gray-500"
                            >
                              <option value="">👆 Seleccionar...</option>
                              {itemsLibro
                                .filter(lib => !Object.values(mapeo).includes(lib.id))
                                .map(lib => (
                                  <option key={lib.id} value={lib.id}>
                                    [{lib.codigo_columna}] {lib.nombre_concepto}
                                  </option>
                                ))
                              }
                            </select>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Lista del Libro */}
              <div className="flex flex-col">
                <h3 className="text-lg font-semibold text-white mb-4">
                  📊 Conceptos del Libro ({itemsLibro.length})
                </h3>
                
                <div className="flex-1 overflow-y-auto space-y-3">
                  {itemsLibro.map(item => {
                    const estaUsado = Object.values(mapeo).includes(item.id);
                    
                    return (
                      <div 
                        key={item.id}
                        className={`p-4 border-2 rounded-lg transition-all ${
                          estaUsado 
                            ? 'border-blue-500 bg-blue-900/30' 
                            : 'border-gray-600 bg-gray-700/50'
                        }`}
                      >
                        <div className="font-semibold text-white">
                          <span className="text-orange-400">[{item.codigo_columna}]</span> {item.nombre_concepto}
                        </div>
                        {estaUsado && (
                          <div className="text-sm text-blue-400 mt-2">
                            ✅ En uso
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-gray-600 flex justify-between items-center">
          <div className="text-sm">
            {puedeGuardar() ? (
              <span className="text-green-400 font-semibold">✅ ¡Completo!</span>
            ) : (
              <span className="text-yellow-400">⏳ Faltan {itemsNovedades.length - Object.keys(mapeo).length}</span>
            )}
          </div>
          
          <div className="flex gap-3">
            <button 
              onClick={onClose}
              className="px-5 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded"
            >
              Cancelar
            </button>
            <button 
              onClick={guardarMapeo}
              disabled={!puedeGuardar()}
              className={`px-6 py-2 rounded font-semibold transition-all ${
                puedeGuardar()
                  ? 'bg-green-600 hover:bg-green-700 text-white'
                  : 'bg-gray-600 text-gray-400 cursor-not-allowed'
              }`}
            >
              {puedeGuardar() ? '🚀 Guardar' : '⏳ Completar'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MapeoHeadersModal;
