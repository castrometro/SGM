import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { obtenerResumenContable } from "../api/contabilidad";
import { obtenerResumenNomina } from "../api/nomina";
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
        <Link
          to={`/menu/clientes/${cliente.id}`}
          className="!text-white hover:text-gray-300 font-medium px-3 py-1 rounded hover:bg-white/10 transition"
        >
          Ver Cliente
        </Link>
      </td>
    </tr>
  );
};

export default ClienteRow;
