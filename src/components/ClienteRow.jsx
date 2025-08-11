import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { obtenerResumenContable } from "../api/contabilidad";
// import { obtenerResumenNomina } from "../api/nomina"; // REMOVIDO - Limpieza de nómina
import EstadoBadge from "./EstadoBadge";

const ClienteRow = ({ cliente, areaActiva }) => {
  const [resumen, setResumen] = useState({
    ultimo_cierre: null,
    estado_cierre_actual: null,
  });

  // Determinar el estado del cierre según el área activa
  const getEstadoCierre = () => {
    if (!resumen) return null;
    
    // Para nómina usamos estado_cierre_actual
    if (areaActiva === "Nomina") {
      return resumen.estado_cierre_actual;
    }
    
    // Para contabilidad usamos estado_ultimo_cierre
    if (areaActiva === "Contabilidad") {
      return resumen.estado_ultimo_cierre;
    }
    
    // Fallback: intentar cualquiera de los dos campos
    return resumen.estado_cierre_actual || resumen.estado_ultimo_cierre;
  };

  useEffect(() => {
    const fetchResumen = async () => {
      try {
        let data = {};
        if (areaActiva === "Contabilidad") {
          data = await obtenerResumenContable(cliente.id);
        } else if (areaActiva === "Nomina") {
          data = await obtenerResumenNomina(cliente.id);
        } else {
          data = {}; // O puedes mostrar “No aplica”
        }
        setResumen(data);
      } catch (error) {
        setResumen({ ultimo_cierre: null, estado_cierre_actual: null });
        console.error("Error al cargar resumen:", error);
      }
    };

    fetchResumen();
  }, [cliente.id, areaActiva]);

  return (
    <tr key={cliente.id} className="border-b border-gray-700">
      <td className="p-2">{cliente.nombre}</td>
      <td className="p-2">{cliente.rut}</td>
      <td className="p-2 text-center">
        {resumen.ultimo_cierre || "—"}
      </td>
      <td className="p-2 text-center">
        <EstadoBadge estado={getEstadoCierre()} />
      </td>
      <td className="p-2 text-center">
        <div className="flex items-center justify-center gap-2">
          <Link
            to={`/menu/clientes/${cliente.id}`}
            className="!text-white hover:text-gray-300 font-medium px-3 py-1 rounded hover:bg-white/10 transition"
          >
            Ver Cliente
          </Link>
          
          {/* Botón Dashboard según área activa */}
          {areaActiva === "Contabilidad" && (
            <button
              onClick={() => {
                const streamlitUrl = `http://172.17.11.18:8502/?cliente_id=${cliente.id}`;
                window.open(streamlitUrl, '_blank');
              }}
              className="bg-indigo-600 hover:bg-indigo-700 text-white px-3 py-1 rounded font-medium text-sm transition-colors flex items-center gap-1"
              title="Ver Dashboard Contable"
            >
              <svg className="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              Dashboard
            </button>
          )}
          
          {areaActiva === "Nomina" && (
            <button
              onClick={() => {
                const streamlitUrl = `http://172.17.11.18:8503/?cliente_id=${cliente.id}`;
                window.open(streamlitUrl, '_blank');
              }}
              className="bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded font-medium text-sm transition-colors flex items-center gap-1"
              title="Ver Dashboard Nómina"
            >
              <svg className="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
              Dashboard
            </button>
          )}
        </div>
      </td>
    </tr>
  );
};

export default ClienteRow;
