import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { obtenerResumenContable } from "../api/contabilidad";
import { obtenerResumenNomina } from "../api/nomina";
import EstadoBadge from "./EstadoBadge";

const ClienteRow = ({ cliente, areaActiva, index = 0 }) => {
  const [resumen, setResumen] = useState({
    ultimo_cierre: null,
    estado_cierre_actual: null,
    usuario_cierre: null,
  });
  const [cargando, setCargando] = useState(true);
  const navigate = useNavigate();

  const getEstadoCierre = () => {
    if (!resumen) return null;
    if (areaActiva === "Nomina") {
      return resumen.estado_cierre_actual;
    }
    if (areaActiva === "Contabilidad") {
      return resumen.estado_ultimo_cierre;
    }
    return resumen.estado_cierre_actual || resumen.estado_ultimo_cierre;
  };

  useEffect(() => {
    const fetchResumen = async () => {
      setCargando(true);
      try {
        let data = {};
        if (areaActiva === "Contabilidad") {
          data = await obtenerResumenContable(cliente.id);
        } else if (areaActiva === "Nomina") {
          data = await obtenerResumenNomina(cliente.id);
        }
        setResumen(data);
      } catch (error) {
        setResumen({ ultimo_cierre: null, estado_cierre_actual: null });
        console.error("Error al cargar resumen:", error);
      } finally {
        setCargando(false);
      }
    };
    fetchResumen();
  }, [cliente.id, areaActiva]);

  return (
    <motion.tr
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.05, duration: 0.3 }}
      key={cliente.id}
      className="border-b border-gray-700 hover:bg-gray-700/30 transition-colors group"
    >
      <td className="p-3">
        <span className="text-white font-medium group-hover:text-blue-400 transition-colors">
          {cliente.nombre}
        </span>
      </td>
      <td className="p-3 text-gray-300">{cliente.rut}</td>
      <td className="p-3 text-center">
        {cargando ? (
          <div className="flex justify-center">
            <div className="animate-pulse h-4 bg-gray-700 rounded w-16"></div>
          </div>
        ) : (
          <span className="text-gray-300">{resumen.ultimo_cierre || "—"}</span>
        )}
      </td>
      <td className="p-3 text-center">
        {cargando ? (
          <div className="flex justify-center">
            <div className="animate-pulse h-6 bg-gray-700 rounded-full w-20"></div>
          </div>
        ) : (
          <EstadoBadge estado={getEstadoCierre()} />
        )}
      </td>
      <td className="p-3 text-center">
        {cargando ? (
          <div className="flex justify-center">
            <div className="animate-pulse h-4 bg-gray-700 rounded w-24"></div>
          </div>
        ) : (
          <span className="text-gray-300">{resumen.usuario_cierre || "—"}</span>
        )}
      </td>
      <td className="p-3 text-center">
        <div className="flex items-center justify-center gap-2">
          <Link
            to={`/menu/clientes/${cliente.id}`}
            className="px-3 py-1.5 rounded-lg text-sm font-medium !text-white bg-blue-600 hover:bg-blue-700 transition-all hover:scale-105 active:scale-95"
          >
            Ver Cliente
          </Link>
          {areaActiva === "Contabilidad" && (
            <button
              onClick={() => {
                const streamlitUrl = `http://172.17.11.18:8502/?cliente_id=${cliente.id}`;
                window.open(streamlitUrl, '_blank');
              }}
              className="px-3 py-1.5 rounded-lg text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 transition-all hover:scale-105 active:scale-95 flex items-center gap-1.5 shadow-sm"
              title="Ver Dashboard Contable"
            >
              <svg className="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
              Dashboard
            </button>
          )}
          {areaActiva === "Nomina" && (
            <button
              onClick={() => navigate(`/menu/nomina/clientes/${cliente.id}/dashboard`)}
              className="px-3 py-1.5 rounded-lg text-sm font-medium text-white bg-gradient-to-r from-teal-500 to-emerald-500 hover:from-teal-600 hover:to-emerald-600 transition-all hover:scale-105 active:scale-95 flex items-center gap-1.5 shadow-sm"
              title="Abrir Dashboard Nómina"
            >
              <svg className="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 13h2l2 6 4-14 3 8h6" />
              </svg>
              Dashboard
            </button>
          )}
        </div>
      </td>
    </motion.tr>
  );
};

export default ClienteRow;
