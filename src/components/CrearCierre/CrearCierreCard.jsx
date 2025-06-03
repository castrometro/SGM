import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  obtenerCierreMensual as obtenerCierreContabilidad,
  crearCierreMensual as crearCierreContabilidad,
} from "../../api/contabilidad";
import {
  obtenerCierreMensual as obtenerCierreNomina,
  crearCierreMensual as crearCierreNomina,
} from "../../api/nomina";

const areaLabels = {
  Contabilidad: "Crear Cierre Mensual de Contabilidad",
  Nomina: "Crear Cierre Mensual de Nómina",
};



const CrearCierreCard = ({ clienteId, areaActiva }) => {
  const [periodo, setPeriodo] = useState("");
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  // Para nómina: checklist solo durante creación
  const [tareas, setTareas] = useState([{ descripcion: "" }]);
  const navigate = useNavigate();

  // Manejar checklist SOLO si es nómina
  const handleAddTarea = () => setTareas([...tareas, { descripcion: "" }]);
  const handleRemoveTarea = idx => setTareas(tareas.filter((_, i) => i !== idx));
  const handleChangeTarea = (idx, value) =>
    setTareas(tareas.map((t, i) => i === idx ? { ...t, descripcion: value } : t));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    if (!periodo) {
      setError("Debes seleccionar el periodo.");
      return;
    }
    
    // Checklist: validar solo para nómina
    if (
      areaActiva === "Nomina" &&
      (tareas.length === 0 || tareas.some((t) => !t.descripcion.trim()))
    ) {
      setError("Debes agregar al menos una tarea y que todas tengan descripción.");
      return;
    }

    if (
      !window.confirm(
        `¿Crear cierre para el periodo ${periodo}? Una vez creado, la lista de tareas no podrá ser editada.`
      )
    ) {
      return;
    }

    setLoading(true);
    try {
      let cierreExistente, cierre;
      if (areaActiva === "Contabilidad") {
        cierreExistente = await obtenerCierreContabilidad(clienteId, periodo);
      } else if (areaActiva === "Nomina") {
        cierreExistente = await obtenerCierreNomina(clienteId, periodo);
      }

      if (cierreExistente) {
        setError("Ya existe un cierre para este periodo.");
        setLoading(false);
        return;
      }
      console.log("Cierre existente:", cierreExistente);
      


      if (areaActiva === "Contabilidad") {
        cierre = await crearCierreContabilidad(clienteId, periodo);
        navigate(`/menu/cierres/${cierre.id}`);
      } else if (areaActiva === "Nomina") {
        // Enviamos tareas como array de strings al backend
        cierre = await crearCierreNomina(
          clienteId,
          periodo,
          tareas // <- manda el array tal cual, [{ descripcion: ... }]
        );

        navigate(`/menu/nomina/cierres/${cierre.id}`);
      }
    } catch (err) {
        console.log("Error detalle:", err.response?.data); // <- agrega esto
        setError("Error creando el cierre.");
      }

    setLoading(false);
  };

  return (
    <div className="bg-gray-800 p-6 rounded-lg shadow-lg mt-4">
      <h2 className="text-xl font-bold text-white mb-4">
        {areaLabels[areaActiva] || "Crear Cierre Mensual"}
      </h2>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-gray-300 font-semibold mb-1">
            Periodo (AAAA-MM)
          </label>
          <input
            type="month"
            value={periodo}
            onChange={(e) => setPeriodo(e.target.value)}
            className="w-full border rounded p-2 bg-gray-900 text-white"
            required
          />
        </div>
        {areaActiva === "Nomina" && (
          <div>
            <label className="block text-gray-300 font-semibold mb-1">
              Tareas a comprometer para este cierre
            </label>
            <div className="space-y-2">
              {tareas.map((tarea, idx) => (
                <div key={idx} className="flex gap-2">
                  <input
                    type="text"
                    className="flex-1 p-2 rounded bg-gray-900 text-white"
                    placeholder="Nombre Tarea"
                    value={tarea.descripcion}
                    onChange={e => handleChangeTarea(idx, e.target.value)}
                    required
                  />
                  <button
                    type="button"
                    onClick={() => handleRemoveTarea(idx)}
                    disabled={tareas.length === 1}
                    className="px-2 text-red-400 hover:text-red-600"
                    tabIndex={-1}
                  >
                    X
                  </button>
                </div>
              ))}
              <button
                type="button"
                onClick={handleAddTarea}
                className="text-blue-400 mt-2"
              >
                + Agregar Tarea
              </button>
            </div>
          </div>
        )}
        {error && <div className="text-red-400">{error}</div>}
        <button
          type="submit"
          className="bg-blue-600 text-white px-4 py-2 rounded-xl shadow hover:bg-blue-800 transition"
          disabled={loading}
        >
          {loading ? "Creando..." : "Crear Cierre"}
        </button>
      </form>
    </div>
  );
};

export default CrearCierreCard;
