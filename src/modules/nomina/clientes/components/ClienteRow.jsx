// src/modules/nomina/clientes/components/ClienteRow.jsx
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { obtenerResumenNomina } from "../api/clientes.api";
import { ANIMATION_CONFIG, URLS } from "../constants/clientes.constants";
import EstadoBadge from "./EstadoBadge";
import ClienteActions from "./ClienteActions";

/**
 * 📋 Componente ClienteRow - Fila/Card de cliente para Nómina
 * Renderiza vista adaptativa: Card en móvil/tablet, Fila en desktop
 */
const ClienteRow = ({ cliente, areaActiva, index = 0 }) => {
  const [resumen, setResumen] = useState({
    ultimo_cierre: null,
    estado_cierre_actual: null,
    usuario_cierre: null,
  });
  const [cargando, setCargando] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchResumen = async () => {
      setCargando(true);
      try {
        const data = await obtenerResumenNomina(cliente.id);
        setResumen(data);
      } catch (error) {
        setResumen({ ultimo_cierre: null, estado_cierre_actual: null, usuario_cierre: null });
        console.error("Error al cargar resumen de nómina:", error);
      } finally {
        setCargando(false);
      }
    };
    fetchResumen();
  }, [cliente.id]);

  const handleVerCliente = () => {
    navigate(`/menu/clientes/${cliente.id}`);
  };

  const handleVerDashboard = () => {
    navigate(URLS.DASHBOARD_NOMINA(cliente.id));
  };

  return (
    <>
      {/* Vista Card - Móvil y Tablet (< 1024px) */}
      <motion.div
        initial={{ opacity: ANIMATION_CONFIG.INITIAL_OPACITY, y: ANIMATION_CONFIG.INITIAL_Y }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ 
          delay: index * ANIMATION_CONFIG.CARD_DELAY_STEP, 
          duration: ANIMATION_CONFIG.CARD_DURATION 
        }}
        className="lg:hidden bg-gray-800 rounded-lg p-4 mb-3 border border-gray-700 hover:border-gray-600 transition-all shadow-lg hover:shadow-xl"
      >
        {/* Header del Card */}
        <div className="flex items-start justify-between mb-3 pb-3 border-b border-gray-700">
          <div className="flex-1">
            <h3 className="text-white font-semibold text-base mb-1">
              {cliente.nombre}
            </h3>
            <p className="text-gray-400 text-sm">
              RUT: {cliente.rut}
            </p>
          </div>
          <div className="ml-3">
            {cargando ? (
              <div className="animate-pulse h-6 bg-gray-700 rounded-full w-20"></div>
            ) : (
              <EstadoBadge estado={resumen.estado_cierre_actual} />
            )}
          </div>
        </div>

        {/* Info del Card */}
        <div className="space-y-2 mb-4">
          <div className="flex justify-between items-center">
            <span className="text-gray-400 text-sm">Último Cierre:</span>
            {cargando ? (
              <div className="animate-pulse h-4 bg-gray-700 rounded w-20"></div>
            ) : (
              <span className="text-gray-300 text-sm font-medium">
                {resumen.ultimo_cierre || "—"}
              </span>
            )}
          </div>
          <div className="flex justify-between items-center">
            <span className="text-gray-400 text-sm">Responsable:</span>
            {cargando ? (
              <div className="animate-pulse h-4 bg-gray-700 rounded w-24"></div>
            ) : (
              <span className="text-gray-300 text-sm font-medium">
                {resumen.usuario_cierre || "—"}
              </span>
            )}
          </div>
        </div>

        {/* Acciones del Card */}
        <ClienteActions 
          onVerCliente={handleVerCliente}
          onVerDashboard={handleVerDashboard}
          mobile={true}
        />
      </motion.div>

      {/* Vista Tabla - Desktop (≥ 1024px) */}
      <motion.tr
        initial={{ opacity: ANIMATION_CONFIG.INITIAL_OPACITY, x: ANIMATION_CONFIG.INITIAL_X }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ 
          delay: index * ANIMATION_CONFIG.CARD_DELAY_STEP, 
          duration: ANIMATION_CONFIG.CARD_DURATION 
        }}
        key={cliente.id}
        className="hidden lg:table-row border-b border-gray-700 hover:bg-gray-700/30 transition-colors group"
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
            <EstadoBadge estado={resumen.estado_cierre_actual} />
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
          <ClienteActions 
            onVerCliente={handleVerCliente}
            onVerDashboard={handleVerDashboard}
            mobile={false}
          />
        </td>
      </motion.tr>
    </>
  );
};

export default ClienteRow;
