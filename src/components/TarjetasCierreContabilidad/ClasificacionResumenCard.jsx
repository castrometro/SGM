import { useEffect, useState } from "react";
import { obtenerProgresoClasificacionTodosLosSets } from "../../api/contabilidad";
import { useNavigate } from "react-router-dom";
import EstadoBadge from "../EstadoBadge";

const ClasificacionResumenCard = ({
  cierreId,
  libroMayorReady,         // <-- Recibe este prop
  onCompletado
}) => {
  const [progreso, setProgreso] = useState(null);
  const [loading, setLoading] = useState(true);

  const navigate = useNavigate();

  useEffect(() => {
    let isMounted = true;
    const cargarProgreso = async () => {
      setLoading(true);
      try {
        const data = await obtenerProgresoClasificacionTodosLosSets(cierreId);
        if (!isMounted) return;
        setProgreso(data);
        // "Completo" solo si hay sets y TODOS están completos
        const completo =
          data.sets_progreso &&
          data.sets_progreso.length > 0 &&
          data.sets_progreso.every((s) => s.estado === "Completo");
        if (onCompletado) onCompletado(completo);
      } catch (e) {
        if (!isMounted) return;
        setProgreso(null);
        if (onCompletado) onCompletado(false);
      }
      if (isMounted) setLoading(false);
    };

    if (cierreId && libroMayorReady) {
      cargarProgreso();
    } else {
      setLoading(false);
      setProgreso(null);
      if (onCompletado) onCompletado(false);
    }

    return () => {
      isMounted = false;
    };
  }, [cierreId, libroMayorReady, onCompletado]);

  const handleClasificarClick = () => {
    navigate(`/menu/cierres/${cierreId}/clasificacion`);
  };

  return (
    <div
      className={`bg-gray-800 p-4 rounded-xl shadow-lg flex flex-col gap-3 ${
        !libroMayorReady ? "opacity-60 pointer-events-none" : ""
      }`}
    >
      <h3 className="text-lg font-semibold mb-3">
        3. Clasificación de cuentas
      </h3>
      {loading || !progreso ? (
        <span className="text-xs text-gray-400">Cargando...</span>
      ) : progreso.sets_progreso && progreso.sets_progreso.length === 0 ? (
        <div className="flex flex-col gap-2">
          <span className="text-yellow-400 font-semibold">
            Debes crear un set de clasificación antes de continuar.
          </span>
          <button
            className="bg-blue-700 hover:bg-blue-600 px-3 py-1 rounded text-white text-sm font-medium transition shadow w-fit"
            onClick={handleClasificarClick}
            disabled={!libroMayorReady}
          >
            Crear set y clasificar
          </button>
        </div>
      ) : (
        <>
          {/* Estado global */}
          <div className="flex items-center gap-2 mb-2">
            <span className="font-semibold">Estado global:</span>
            <EstadoBadge 
              estado={progreso.sets_progreso.every((s) => s.estado === "Completo") ? "completo" : "pendiente"} 
            />
          </div>

          {/* Tabla de sets */}
          <div className="overflow-x-auto">
            <table className="w-full text-sm border-separate border-spacing-y-1">
              <thead>
                <tr>
                  <th className="text-left px-2 py-1">Set</th>
                  <th className="text-left px-2 py-1">
                    Cuentas sin clasificar
                  </th>
                  <th className="text-left px-2 py-1">Total</th>
                  <th className="text-left px-2 py-1">Estado</th>
                </tr>
              </thead>
              <tbody>
                {progreso.sets_progreso.map((set) => (
                  <tr key={set.set_id} className="bg-gray-700 rounded">
                    <td className="px-2 py-1">{set.set_nombre}</td>
                    <td className="px-2 py-1">
                      {set.cuentas_sin_clasificar}
                    </td>
                    <td className="px-2 py-1">{set.total_cuentas}</td>
                    <td className="px-2 py-1">
                      <EstadoBadge 
                        estado={set.estado === "Completo" ? "completo" : "pendiente"} 
                        size="xs"
                      />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Botón siempre visible */}
          <button
            className="mt-3 bg-blue-700 hover:bg-blue-600 px-3 py-1 rounded text-white text-sm font-medium transition shadow w-fit"
            onClick={handleClasificarClick}
            disabled={!libroMayorReady}
          >
            {progreso.sets_progreso.some((s) => s.estado !== "Completo")
              ? "Clasificar cuentas"
              : "Ver clasificaciones"}
          </button>
        </>
      )}
    </div>
  );
};

export default ClasificacionResumenCard;
