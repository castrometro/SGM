import { useState, useEffect } from "react";
import CreatableSelect from "react-select/creatable";
import { X, Hash, Check } from "lucide-react";
import {
  obtenerClasificacionesCliente,
} from "../api/nomina";

const categorias = [
  "haberes_imponibles",
  "haberes_no_imponibles", 
  "horas_extras",
  "descuentos_legales",
  "otros_descuentos",
  "aportes_patronales",
  "informacion_adicional",
  "impuestos"
];

const nombresCategorias = {
  pendiente: "🔄 Pendientes",
  haberes_imponibles: "💰 Haberes Imponibles",
  haberes_no_imponibles: "🎁 Haberes No Imponibles",
  horas_extras: "⏰ Horas Extras",
  descuentos_legales: "⚖️ Descuentos Legales",
  otros_descuentos: "📋 Otros Descuentos",
  aportes_patronales: "🏢 Aportes Patronales",
  informacion_adicional: "📝 Información Adicional",
  impuestos: "🏛️ Impuestos",
};

const iconosCategorias = {
  haberes_imponibles: "💰",
  haberes_no_imponibles: "🎁",
  horas_extras: "⏰",
  descuentos_legales: "⚖️",
  otros_descuentos: "📋",
  aportes_patronales: "🏢",
  informacion_adicional: "📝",
  impuestos: "🏛️",
};

const ModalClasificacionHeaders = ({
  isOpen,
  onClose,
  clienteId,
  headersSinClasificar = [],
  onGuardarClasificaciones,
  soloLectura = false,
}) => {
  const [conceptos, setConceptos] = useState([]);
  const [hashtagsDisponibles, setHashtagsDisponibles] = useState([]);
  const [modalConcepto, setModalConcepto] = useState(null);
  const [clasificacionSeleccionada, setClasificacionSeleccionada] = useState("");
  const [hashtagsSeleccionados, setHashtagsSeleccionados] = useState([]);
  const [originalClasificados, setOriginalClasificados] = useState(new Set());
  const [vista, setVista] = useState("lista"); // "lista" o "categorias"

  const totalConceptos = conceptos.length;
  const conceptosClasificados = conceptos.filter(c => c.clasificacion && c.clasificacion !== 'pendiente').length;

  useEffect(() => {
    if (!isOpen || !clienteId) return;

    const cargarDatos = async () => {
      try {
        const conceptosExistentes = await obtenerClasificacionesCliente(clienteId);
        const setHashtagsUnicos = new Set();
        const setOriginal = new Set();

        // Crear un mapa de conceptos existentes
        const mapaConceptos = {};
        conceptosExistentes.forEach(({ nombre_concepto, clasificacion, hashtags }) => {
          mapaConceptos[nombre_concepto] = { clasificacion, hashtags };
          hashtags?.forEach(tag => setHashtagsUnicos.add(tag));
          setOriginal.add(nombre_concepto);
        });

        // Combinar todos los conceptos
        const todosLosConceptos = new Set([
          ...headersSinClasificar,
          ...Object.keys(mapaConceptos),
        ]);

        // Crear lista de conceptos con su estado
        const listaConceptos = Array.from(todosLosConceptos).map(nombre => ({
          nombre,
          clasificacion: mapaConceptos[nombre]?.clasificacion || 'pendiente',
          hashtags: mapaConceptos[nombre]?.hashtags || []
        }));

        setConceptos(listaConceptos);
        setHashtagsDisponibles([...setHashtagsUnicos].sort());
        setOriginalClasificados(setOriginal);
      } catch (e) {
        console.error("Error al cargar datos de clasificación:", e);
      }
    };

    cargarDatos();
  }, [isOpen, clienteId, headersSinClasificar]);

  const abrirModalConcepto = (concepto) => {
    if (soloLectura) return;
    setModalConcepto(concepto);
    setClasificacionSeleccionada(concepto.clasificacion === 'pendiente' ? '' : concepto.clasificacion);
    setHashtagsSeleccionados(concepto.hashtags || []);
  };

  const cerrarModalConcepto = () => {
    setModalConcepto(null);
    setClasificacionSeleccionada('');
    setHashtagsSeleccionados([]);
  };

  const guardarClasificacionConcepto = () => {
    if (!modalConcepto || !clasificacionSeleccionada) return;

    // Actualizar la lista de conceptos
    const nuevosConceptos = conceptos.map(c => {
      if (c.nombre === modalConcepto.nombre) {
        return {
          ...c,
          clasificacion: clasificacionSeleccionada,
          hashtags: hashtagsSeleccionados
        };
      }
      return c;
    });

    setConceptos(nuevosConceptos);
    
    // Agregar hashtags nuevos a la lista disponible
    setHashtagsDisponibles(prev => {
      const nuevos = hashtagsSeleccionados.filter(tag => !prev.includes(tag));
      return [...prev, ...nuevos].sort();
    });

    cerrarModalConcepto();
  };

  const eliminarClasificacionConcepto = (nombreConcepto) => {
    if (soloLectura) return;
    
    const nuevosConceptos = conceptos.map(c => {
      if (c.nombre === nombreConcepto) {
        return {
          ...c,
          clasificacion: 'pendiente',
          hashtags: []
        };
      }
      return c;
    });

    setConceptos(nuevosConceptos);
  };

  const handleGuardar = async () => {
    if (soloLectura) return;
    
    const resultado = {};
    const eliminar = [];

    // Procesar conceptos clasificados
    conceptos.forEach(concepto => {
      if (concepto.clasificacion && concepto.clasificacion !== 'pendiente') {
        resultado[concepto.nombre] = {
          clasificacion: concepto.clasificacion,
          hashtags: concepto.hashtags || []
        };
      }
    });

    // Encontrar conceptos que fueron desclasificados
    Array.from(originalClasificados).forEach(nombreConcepto => {
      const concepto = conceptos.find(c => c.nombre === nombreConcepto);
      if (!concepto || concepto.clasificacion === 'pendiente') {
        eliminar.push(nombreConcepto);
      }
    });

    await onGuardarClasificaciones({ guardar: resultado, eliminar });
    onClose();
  };

  // Agrupar conceptos por categoría
  const conceptosPorCategoria = () => {
    const grupos = {
      pendiente: [],
      haberes_imponibles: [],
      haberes_no_imponibles: [],
      horas_extras: [],
      descuentos_legales: [],
      otros_descuentos: [],
      aportes_patronales: [],
      informacion_adicional: [],
      impuestos: []
    };

    conceptos.forEach(concepto => {
      const categoria = concepto.clasificacion || 'pendiente';
      if (grupos[categoria]) {
        grupos[categoria].push(concepto);
      }
    });

    return grupos;
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-60 z-50 flex justify-center items-center p-4">
      <div className="bg-gray-900 rounded-lg shadow-xl w-full max-w-7xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex justify-between items-center p-6 border-b border-gray-700">
          <div className="flex items-center gap-4">
            <h2 className="text-xl font-semibold text-white">
              Clasificación de Conceptos
              {soloLectura && <span className="text-sm text-gray-400 ml-2">(Solo lectura)</span>}
            </h2>
            <div className="flex items-center gap-2 text-sm text-gray-400">
              <span>📊 {conceptosClasificados} de {totalConceptos} clasificados</span>
              <div className="w-32 bg-gray-700 rounded-full h-2">
                <div 
                  className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${totalConceptos > 0 ? (conceptosClasificados / totalConceptos) * 100 : 0}%` }}
                />
              </div>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {/* Selector de vista */}
            <div className="flex bg-gray-800 rounded-lg p-1">
              <button
                onClick={() => setVista("lista")}
                className={`px-3 py-1 rounded text-sm transition ${
                  vista === "lista" 
                    ? "bg-blue-600 text-white" 
                    : "text-gray-400 hover:text-white"
                }`}
              >
                Lista
              </button>
              <button
                onClick={() => setVista("categorias")}
                className={`px-3 py-1 rounded text-sm transition ${
                  vista === "categorias" 
                    ? "bg-blue-600 text-white" 
                    : "text-gray-400 hover:text-white"
                }`}
              >
                Categorías
              </button>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-white transition-colors"
            >
              <X size={24} />
            </button>
          </div>
        </div>

        {/* Contenido */}
        <div className="flex-1 overflow-hidden">
          {vista === "lista" ? (
            <VistaLista 
              conceptos={conceptos}
              onAbrirModalConcepto={abrirModalConcepto}
              onEliminarClasificacion={eliminarClasificacionConcepto}
              soloLectura={soloLectura}
              nombresCategorias={nombresCategorias}
            />
          ) : (
            <VistaCategorias 
              conceptosPorCategoria={conceptosPorCategoria()}
              onAbrirModalConcepto={abrirModalConcepto}
              onEliminarClasificacion={eliminarClasificacionConcepto}
              soloLectura={soloLectura}
              nombresCategorias={nombresCategorias}
              categorias={categorias}
            />
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-gray-700 p-6">
          <div className="flex justify-end gap-3">
            <button
              onClick={onClose}
              className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition"
            >
              {soloLectura ? "Cerrar" : "Cancelar"}
            </button>
            {!soloLectura && (
              <button
                onClick={handleGuardar}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg transition"
              >
                Guardar Clasificaciones
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Modal de clasificación individual */}
      {modalConcepto && (
        <ModalClasificacionIndividual
          concepto={modalConcepto}
          clasificacionSeleccionada={clasificacionSeleccionada}
          setClasificacionSeleccionada={setClasificacionSeleccionada}
          hashtagsSeleccionados={hashtagsSeleccionados}
          setHashtagsSeleccionados={setHashtagsSeleccionados}
          hashtagsDisponibles={hashtagsDisponibles}
          categorias={categorias}
          nombresCategorias={nombresCategorias}
          iconosCategorias={iconosCategorias}
          onGuardar={guardarClasificacionConcepto}
          onCerrar={cerrarModalConcepto}
        />
      )}
    </div>
  );
};

// Componente para la vista de lista
const VistaLista = ({ conceptos, onAbrirModalConcepto, onEliminarClasificacion, soloLectura, nombresCategorias }) => {
  const [filtro, setFiltro] = useState("");
  const [soloSinClasificar, setSoloSinClasificar] = useState(false);

  const conceptosFiltrados = conceptos.filter(concepto => {
    const coincideTexto = concepto.nombre.toLowerCase().includes(filtro.toLowerCase());
    const coincideFiltro = soloSinClasificar ? concepto.clasificacion === 'pendiente' : true;
    return coincideTexto && coincideFiltro;
  });

  return (
    <div className="flex flex-col h-full">
      {/* Filtros */}
      <div className="p-4 border-b border-gray-700 bg-gray-800">
        <div className="flex gap-4 items-center">
          <div className="flex-1">
            <input
              type="text"
              placeholder="Buscar conceptos..."
              value={filtro}
              onChange={(e) => setFiltro(e.target.value)}
              className="w-full px-3 py-2 bg-gray-700 text-white rounded-lg border border-gray-600 focus:border-blue-500 focus:outline-none"
            />
          </div>
          <label className="flex items-center gap-2 text-sm text-gray-300">
            <input
              type="checkbox"
              checked={soloSinClasificar}
              onChange={(e) => setSoloSinClasificar(e.target.checked)}
              className="text-blue-600"
            />
            Solo pendientes
          </label>
        </div>
      </div>

      {/* Lista de conceptos */}
      <div className="flex-1 overflow-y-auto p-4">
        <div className="space-y-2">
          {conceptosFiltrados.map(concepto => (
            <div
              key={concepto.nombre}
              className={`p-4 bg-gray-800 rounded-lg border border-gray-700 transition-all ${
                !soloLectura ? "hover:border-blue-500 cursor-pointer" : ""
              }`}
              onClick={() => onAbrirModalConcepto(concepto)}
            >
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-medium text-white">{concepto.nombre}</span>
                    {concepto.clasificacion && concepto.clasificacion !== 'pendiente' && (
                      <span className="text-xs px-2 py-1 bg-blue-900 text-blue-300 rounded">
                        {iconosCategorias[concepto.clasificacion]} {nombresCategorias[concepto.clasificacion]}
                      </span>
                    )}
                  </div>
                  {concepto.hashtags && concepto.hashtags.length > 0 && (
                    <div className="flex gap-1 flex-wrap">
                      {concepto.hashtags.map(tag => (
                        <span key={tag} className="text-xs px-2 py-1 bg-gray-700 text-gray-300 rounded">
                          #{tag}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
                {concepto.clasificacion !== 'pendiente' && !soloLectura && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onEliminarClasificacion(concepto.nombre);
                    }}
                    className="text-red-400 hover:text-red-300 transition-colors"
                    title="Quitar clasificación"
                  >
                    <X size={16} />
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

// Componente para la vista de categorías
const VistaCategorias = ({ conceptosPorCategoria, onAbrirModalConcepto, onEliminarClasificacion, soloLectura, nombresCategorias, categorias }) => {
  return (
    <div className="h-full overflow-y-auto p-4">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {Object.entries(conceptosPorCategoria).map(([categoria, conceptos]) => (
          <div key={categoria} className="bg-gray-800 rounded-lg p-4 border border-gray-700">
            <h3 className="font-medium text-white mb-3 flex items-center gap-2">
              {nombresCategorias[categoria]}
              <span className="text-xs text-gray-400">({conceptos.length})</span>
            </h3>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {conceptos.map(concepto => (
                <div
                  key={concepto.nombre}
                  className={`p-2 bg-gray-700 rounded border border-gray-600 transition-all ${
                    !soloLectura ? "hover:border-blue-500 cursor-pointer" : ""
                  }`}
                  onClick={() => onAbrirModalConcepto(concepto)}
                >
                  <div className="flex justify-between items-start">
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium text-white truncate">{concepto.nombre}</div>
                      {concepto.hashtags && concepto.hashtags.length > 0 && (
                        <div className="flex gap-1 flex-wrap mt-1">
                          {concepto.hashtags.map(tag => (
                            <span key={tag} className="text-xs px-1 py-0.5 bg-gray-600 text-gray-300 rounded">
                              #{tag}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                    {categoria !== 'pendiente' && !soloLectura && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onEliminarClasificacion(concepto.nombre);
                        }}
                        className="text-red-400 hover:text-red-300 transition-colors ml-2"
                        title="Quitar clasificación"
                      >
                        <X size={14} />
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

// Modal para clasificación individual
const ModalClasificacionIndividual = ({
  concepto,
  clasificacionSeleccionada,
  setClasificacionSeleccionada,
  hashtagsSeleccionados,
  setHashtagsSeleccionados,
  hashtagsDisponibles,
  categorias,
  nombresCategorias,
  iconosCategorias,
  onGuardar,
  onCerrar
}) => {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-80 z-60 flex justify-center items-center p-4">
      <div className="bg-gray-900 rounded-lg shadow-xl w-full max-w-md border border-gray-700">
        <div className="p-6">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold text-white">Clasificar Concepto</h3>
            <button
              onClick={onCerrar}
              className="text-gray-400 hover:text-white transition-colors"
            >
              <X size={20} />
            </button>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Concepto:</label>
              <div className="p-3 bg-gray-800 rounded-lg border border-gray-700">
                <span className="text-white font-medium">{concepto.nombre}</span>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Categoría:</label>
              <div className="grid grid-cols-2 gap-2">
                {categorias.map(categoria => (
                  <button
                    key={categoria}
                    onClick={() => setClasificacionSeleccionada(categoria)}
                    className={`p-3 rounded-lg border-2 transition-all text-left ${
                      clasificacionSeleccionada === categoria
                        ? "border-blue-500 bg-blue-900/50 text-blue-300"
                        : "border-gray-600 bg-gray-800 text-gray-300 hover:border-gray-500"
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <span className="text-lg">{iconosCategorias[categoria]}</span>
                      <span className="text-sm">{nombresCategorias[categoria].split(' ').slice(1).join(' ')}</span>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Hashtags: <span className="text-gray-500">(opcional)</span>
              </label>
              <CreatableSelect
                isMulti
                value={hashtagsSeleccionados.map(tag => ({ label: tag, value: tag }))}
                onChange={(selectedOptions) => {
                  const tags = selectedOptions.map(opt => opt.value);
                  setHashtagsSeleccionados(tags);
                }}
                options={hashtagsDisponibles.map(tag => ({ label: tag, value: tag }))}
                placeholder="Agregar hashtags..."
                className="text-sm"
                classNamePrefix="react-select"
                styles={{
                  control: (provided) => ({
                    ...provided,
                    backgroundColor: '#374151',
                    borderColor: '#4B5563',
                    color: 'white'
                  }),
                  menu: (provided) => ({
                    ...provided,
                    backgroundColor: '#374151',
                  }),
                  option: (provided, state) => ({
                    ...provided,
                    backgroundColor: state.isSelected ? '#3B82F6' : state.isFocused ? '#4B5563' : '#374151',
                    color: 'white'
                  }),
                  multiValue: (provided) => ({
                    ...provided,
                    backgroundColor: '#1F2937',
                  }),
                  multiValueLabel: (provided) => ({
                    ...provided,
                    color: 'white'
                  }),
                  input: (provided) => ({
                    ...provided,
                    color: 'white'
                  }),
                  placeholder: (provided) => ({
                    ...provided,
                    color: '#9CA3AF'
                  })
                }}
              />
            </div>
          </div>

          <div className="flex justify-end gap-3 mt-6">
            <button
              onClick={onCerrar}
              className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition"
            >
              Cancelar
            </button>
            <button
              onClick={onGuardar}
              disabled={!clasificacionSeleccionada}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg transition flex items-center gap-2"
            >
              <Check size={16} />
              Guardar
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ModalClasificacionHeaders;
