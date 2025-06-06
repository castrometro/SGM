import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { obtenerCierresCliente as obtenerCierresContabilidad } from "../api/contabilidad";
import { obtenerCierresCliente as obtenerCierresNomina } from "../api/nomina";

const HistorialCierres = ({ clienteId, areaActiva }) => {
  const [cierres, setCierres] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchCierres = async () => {
      let res = [];
      if (areaActiva === "Contabilidad") {
        res = await obtenerCierresContabilidad(clienteId);
      } else if (areaActiva === "Nomina") {
        res = await obtenerCierresNomina(clienteId);
      }
      setCierres(res);
    };
    if (clienteId) fetchCierres();
  }, [clienteId, areaActiva]);

  if (!cierres.length) return <p>No hay cierres registrados aún.</p>;

  return (
    <div className="mt-4">
      <h4 className="text-md font-bold mb-2">Historial de Cierres ({areaActiva})</h4>
      <div className="overflow-x-auto">
        <table className="w-full text-sm border-separate border-spacing-y-1">
          <thead>
            <tr className="bg-gray-700">
              <th className="px-4 py-2 text-left">Periodo</th>
              <th className="px-4 py-2 text-left">Estado</th>
              {areaActiva === "Contabilidad" && (
                <th className="px-4 py-2 text-left">Cuentas nuevas</th>
              )}
              <th className="px-4 py-2 text-left">Fecha creación</th>
              <th className="px-4 py-2 text-left" colSpan={2}>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {cierres.map(cierre => (
              <tr key={cierre.id} className="border-b border-gray-700 hover:bg-gray-600">
                <td className="px-4 py-2">{cierre.periodo}</td>
                <td className="px-4 py-2 capitalize">{cierre.estado}</td>
                {areaActiva === "Contabilidad" && (
                  <td className="px-4 py-2">{cierre.cuentas_nuevas}</td>
                )}
                <td className="px-4 py-2">{new Date(cierre.fecha_creacion).toLocaleDateString()}</td>
                <td className="px-4 py-2">
                  <button
                    className="text-blue-500 underline font-medium"
                    onClick={() => {
                      if (areaActiva === "Contabilidad") {
                        navigate(`/menu/cierres/${cierre.id}`);
                      } else {
                        navigate(`/menu/nomina/cierres/${cierre.id}`);
                      }
                    }}
                  >
                    Ver detalles
                  </button>
                </td>
                <td className="px-4 py-2">
                  {cierre.estado === "completo" && areaActiva === "Contabilidad" && (
                    <button
                      className="text-green-500 underline font-medium"
                    onClick={() => navigate(`/menu/cierres/${cierre.id}/libro`)}
                    >
                      Visualizar libro
                    </button>
                  )}
                  {/* Aquí puedes poner otras acciones para Nómina */}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default HistorialCierres;
