import { useState, useEffect } from "react";
import CreatableSelect from "react-select/creatable";
import {
  obtenerConceptosRemuneracionNovedades,
} from "../api/nomina";

const categorias = ["haber", "descuento", "informacion"];

const nombresCategorias = {
  pendiente: "Pendientes",
  haber: "Haberes",
  descuento: "Descuentos",
  informacion: "Información",
};

const ModalClasificacionNovedades = ({
  isOpen,
  onClose,
  clienteId,
  headersSinClasificar = [],
  onGuardarClasificaciones,
  soloLectura = false,
}) => {
  const [headers, setHeaders] = useState({
    pendiente: [],
    haber: [],
    descuento: [],
    informacion: [],
  });
  const [hashtags, setHashtags] = useState({});
  const [hashtagsDisponibles, setHashtagsDisponibles] = useState([]);
  const [seleccionado, setSeleccionado] = useState(null);
  const [originalClasificados, setOriginalClasificados] = useState(new Set());

  const categoriaDe = (header) => {
    for (const c of categorias) {
      if (headers[c].includes(header)) return c;
    }
    return null;
  };

  const clasificados = categorias.flatMap((c) => headers[c]);

  useEffect(() => {
    if (!isOpen || !clienteId) return;

    const cargarDatos = async () => {
      try {
        const conceptos = await obtenerConceptosRemuneracionNovedades(clienteId);

        const clasificados = {};
        const hashtagsIniciales = {};
        const setHashtagsUnicos = new Set();

        const setOriginal = new Set();
        conceptos.forEach(({ nombre_concepto, clasificacion, hashtags }) => {
          clasificados[nombre_concepto] = { clasificacion, hashtags };
          hashtags?.forEach(tag => setHashtagsUnicos.add(tag));
          hashtagsIniciales[nombre_concepto] = hashtags?.join(", ") || "";
          setOriginal.add(nombre_concepto);
        });

        const nuevoHeaders = {
          pendiente: [],
          haber: [],
          descuento: [],
          informacion: [],
        };

        const todosHeaders = new Set([
          ...headersSinClasificar,
          ...Object.keys(clasificados),
        ]);

        todosHeaders.forEach((h) => {
          const info = clasificados[h];
          const destino =
            info && nuevoHeaders[info.clasificacion]
              ? info.clasificacion
              : "pendiente";
          nuevoHeaders[destino].push(h);
        });

        setHeaders(nuevoHeaders);
        setHashtags(hashtagsIniciales);
        setHashtagsDisponibles([...setHashtagsUnicos].sort());
        setOriginalClasificados(setOriginal);
      } catch (e) {
        console.error("Error al cargar datos de clasificación novedades:", e);
      }
    };

    cargarDatos();
  }, [isOpen, clienteId, headersSinClasificar]);

  const mover = (header, destino) => {
    if (soloLectura) return;
    setHeaders((prev) => {
      const nuevo = { ...prev };
      for (const key in nuevo) {
        nuevo[key] = nuevo[key].filter((h) => h !== header);
      }
      nuevo[destino].push(header);
      return nuevo;
    });
  };

  const eliminarClasificacion = (header) => {
    if (soloLectura) return;
    mover(header, "pendiente");
    setHashtags((prev) => {
      const nuevo = { ...prev };
      delete nuevo[header];
      return nuevo;
    });
    if (seleccionado === header) setSeleccionado(null);
  };

  const handleGuardar = async () => {
    if (soloLectura) return;
    
    // Para novedades, enviamos las clasificaciones en el formato esperado por la API
    const clasificaciones = [];
    
    for (const [categoria, headersEnCat] of Object.entries(headers)) {
      if (categoria === "pendiente") continue;
      headersEnCat.forEach((h) => {
        clasificaciones.push({
          header: h,
          clasificacion: categoria,
          hashtags: hashtags[h]?.split(",").map(t => t.trim()).filter(Boolean) || [],
        });
      });
    }

    await onGuardarClasificaciones(clasificaciones);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-60 z-50 flex justify-center items-center">
      <div className="bg-gray-900 rounded-lg shadow-lg p-4 w-full max-w-6xl max-h-[90vh] relative flex flex-col">
        <button
          onClick={onClose}
          className="absolute top-2 right-3 text-gray-400 hover:text-white text-xl"
        >
          &times;
        </button>

        <h2 className="text-lg font-semibold mb-4 text-white">
          Clasificación de Headers - Novedades
          {soloLectura && (
            <span className="text-sm text-gray-400 ml-2">(Solo lectura)</span>
          )}
        </h2>

        <div className="flex flex-1 gap-4 overflow-hidden">
          {Object.entries(headers).map(([categoria, items]) => (
            <div key={categoria} className="flex-1 flex flex-col min-h-0">
              <h3 className="font-medium mb-2 text-center text-white">
                {nombresCategorias[categoria]} ({items.length})
              </h3>
              <div
                className={`flex-1 border-2 border-dashed rounded-lg p-2 overflow-y-auto min-h-0 ${
                  categoria === "pendiente"
                    ? "border-red-400 bg-red-50 bg-opacity-10"
                    : categoria === "haber"
                    ? "border-green-400 bg-green-50 bg-opacity-10"
                    : categoria === "descuento"
                    ? "border-yellow-400 bg-yellow-50 bg-opacity-10"
                    : "border-blue-400 bg-blue-50 bg-opacity-10"
                }`}
                onDragOver={(e) => e.preventDefault()}
                onDrop={(e) => {
                  e.preventDefault();
                  if (soloLectura) return;
                  const header = e.dataTransfer.getData("text/plain");
                  mover(header, categoria);
                }}
              >
                {items.map((header) => (
                  <div
                    key={header}
                    draggable={!soloLectura}
                    onDragStart={(e) => e.dataTransfer.setData("text/plain", header)}
                    onClick={() => setSeleccionado(header)}
                    className={`p-2 mb-2 text-sm rounded cursor-pointer transition-colors ${
                      seleccionado === header
                        ? "bg-blue-600 text-white"
                        : "bg-gray-700 text-gray-100 hover:bg-gray-600"
                    }`}
                  >
                    {header}
                    {categoria !== "pendiente" && !soloLectura && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          eliminarClasificacion(header);
                        }}
                        className="ml-2 text-red-300 hover:text-red-100 text-xs"
                      >
                        ✕
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        {seleccionado && categoriaDe(seleccionado) !== "pendiente" && (
          <div className="mt-4 p-3 bg-gray-800 rounded-lg">
            <h4 className="font-medium mb-2 text-white">
              Hashtags para: {seleccionado}
            </h4>
            <CreatableSelect
              isMulti
              isDisabled={soloLectura}
              value={(hashtags[seleccionado] || "")
                .split(",")
                .map(tag => tag.trim())
                .filter(Boolean)
                .map(tag => ({ value: tag, label: tag }))}
              onChange={(selectedOptions) => {
                if (soloLectura) return;
                setHashtags(prev => ({
                  ...prev,
                  [seleccionado]: selectedOptions.map(opt => opt.value).join(", ")
                }));
              }}
              options={hashtagsDisponibles.map(tag => ({ value: tag, label: tag }))}
              placeholder="Agregar hashtags..."
              className="text-sm"
              classNames={{
                control: () => "bg-gray-700 border-gray-600",
                menu: () => "bg-gray-700",
                option: () => "hover:bg-gray-600",
                multiValue: () => "bg-blue-600",
                multiValueLabel: () => "text-white",
                input: () => "text-white",
                placeholder: () => "text-gray-400",
              }}
            />
          </div>
        )}

        <div className="flex justify-between items-center mt-4 pt-3 border-t border-gray-700">
          <div className="text-sm text-gray-400">
            {headers.pendiente.length} headers pendientes • {clasificados.length} clasificados
          </div>
          <div className="flex gap-2">
            <button
              onClick={onClose}
              className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-500 transition-colors"
            >
              {soloLectura ? "Cerrar" : "Cancelar"}
            </button>
            {!soloLectura && (
              <button
                onClick={handleGuardar}
                disabled={headers.pendiente.length > 0}
                className={`px-4 py-2 rounded transition-colors ${
                  headers.pendiente.length > 0
                    ? "bg-gray-500 text-gray-300 cursor-not-allowed"
                    : "bg-blue-600 text-white hover:bg-blue-500"
                }`}
              >
                Guardar Clasificaciones
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ModalClasificacionNovedades;
