import { useState, useEffect } from "react";
import CreatableSelect from "react-select/creatable";
import {
  obtenerClasificacionesCliente,
} from "../api/nomina";

const categorias = ["haber", "descuento", "informacion"];

const nombresCategorias = {
  pendiente: "Pendientes",
  haber: "Haberes",
  descuento: "Descuentos",
  informacion: "Información",
};

const ModalClasificacionHeaders = ({
  isOpen,
  onClose,
  clienteId,
  headersSinClasificar = [],
  onGuardarClasificaciones,
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
        const conceptos = await obtenerClasificacionesCliente(clienteId);

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
        console.error("Error al cargar datos de clasificación:", e);
      }
    };

    cargarDatos();
  }, [isOpen, clienteId, headersSinClasificar]);

  const mover = (header, destino) => {
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
    mover(header, "pendiente");
    setHashtags((prev) => {
      const nuevo = { ...prev };
      delete nuevo[header];
      return nuevo;
    });
    if (seleccionado === header) setSeleccionado(null);
  };


  const handleGuardar = async () => {
    const resultado = {};

    for (const [categoria, headersEnCat] of Object.entries(headers)) {
      if (categoria === "pendiente") continue;
      headersEnCat.forEach((h) => {
        resultado[h] = {
          clasificacion: categoria,
          hashtags: hashtags[h]?.split(",").map(t => t.trim()).filter(Boolean) || [],
        };
      });
    }

    const eliminar = Array.from(originalClasificados).filter(
      (h) => !resultado[h]
    );

    await onGuardarClasificaciones({ guardar: resultado, eliminar });
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

        <h2 className="text-xl font-semibold text-white mb-4">
          Clasificación de Headers
        </h2>

        <div className="grid grid-cols-5 gap-4 overflow-y-auto pr-2 flex-1">
          {Object.keys(headers).map((cat) => (
            <div key={cat} className="bg-gray-800 rounded p-3 flex flex-col">
              <h3 className="text-white text-sm font-semibold mb-2">
                {nombresCategorias[cat]}
              </h3>
              <div className="flex-1 space-y-2 overflow-y-auto">
                {headers[cat].map((header, idx) => (
                  <div
                    key={idx}
                    className={`text-xs bg-gray-700 px-2 py-1 rounded cursor-pointer relative ${
                      seleccionado === header ? "border border-blue-400" : ""
                    }`}
                    onClick={() => setSeleccionado(header)}
                  >
                    <div className="flex justify-between items-center">
                      <span>{header}</span>
                      {cat !== "pendiente" && (
                        <div className="flex gap-1">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              eliminarClasificacion(header);
                            }}
                            className="text-red-400 text-xs"
                            title="Quitar clasificación"
                          >
                            ✖
                          </button>
                        </div>
                      )}
                    </div>
                    {cat !== "pendiente" && (
                      <div className="text-[10px] text-blue-300 italic">
                        #{(hashtags[header] || "").split(",").join(" #")}
                      </div>
                    )}
                    {cat === "pendiente" && (
                      <div className="mt-1 flex gap-1 flex-wrap">
                        {categorias.map((dest) => (
                          <button
                            key={dest}
                            onClick={(e) => {
                              e.stopPropagation();
                              mover(header, dest);
                            }}
                            className="text-[10px] bg-blue-600 hover:bg-blue-500 px-2 py-0.5 rounded text-white"
                          >
                            {nombresCategorias[dest]}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))}

          <div className="bg-gray-800 rounded p-3 flex flex-col">
            <h3 className="text-white text-sm font-semibold mb-2">Hashtags</h3>
            <div className="flex-1 space-y-2 overflow-y-auto">
              {clasificados.map((h, idx) => (
                <div key={idx} className="text-xs bg-gray-700 px-2 py-1 rounded">
                  <div className="flex justify-between items-center">
                    <span>{h}</span>
                    <span className="text-[10px] text-gray-400">[
                      {nombresCategorias[categoriaDe(h)]}
                    ]</span>
                  </div>
                  <div className="text-[10px] text-blue-300 italic">
                    #{(hashtags[h] || "").split(",").join(" #")}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Panel Fijo Inferior */}
        <div className="sticky bottom-0 left-0 bg-gray-900 mt-3 pt-4 border-t border-gray-700">
          {seleccionado && (
            <div className="mb-3">
              <label className="text-sm text-white block mb-1">
                Hashtags para <strong>{seleccionado}</strong>:
              </label>
              <CreatableSelect
                isMulti
                value={(hashtags[seleccionado] || "")
                  .split(",")
                  .map(t => ({ label: t.trim(), value: t.trim() }))
                  .filter(t => t.value)}
                onChange={(selectedOptions) => {
                  const etiquetas = selectedOptions.map(opt => opt.value);
                  setHashtags((prev) => ({
                    ...prev,
                    [seleccionado]: etiquetas.join(", ")
                  }));
                  setHashtagsDisponibles((prev) => {
                    const nuevos = etiquetas.filter((tag) => !prev.includes(tag));
                    return [...prev, ...nuevos].sort();
                  });
                }}
                options={hashtagsDisponibles.map(tag => ({ label: tag, value: tag }))}
                placeholder="Ej: Bono, Legal, Fijo"
                className="text-sm text-black"
              />
            </div>
          )}

          <div className="flex justify-end gap-2 mt-2">
            <button
              onClick={onClose}
              className="bg-gray-700 hover:bg-gray-600 px-4 py-2 rounded text-sm text-white"
            >
              Cancelar
            </button>
            <button
              onClick={handleGuardar}
              className="bg-blue-600 hover:bg-blue-500 px-4 py-2 rounded text-sm text-white"
            >
              Guardar Clasificaciones
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ModalClasificacionHeaders;
