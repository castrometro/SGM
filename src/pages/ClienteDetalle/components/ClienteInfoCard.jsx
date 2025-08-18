import EstadoBadge from "../../../components/EstadoBadge";

const ClienteInfoCard = ({ cliente, resumen, areaActiva }) => {
  // Determinar información del último cierre según el área activa
  const getCierreInfo = () => {
    if (!resumen) return { periodo: null, estado: null };
    
    if (areaActiva === "Payroll" || areaActiva === "Nomina") {
      // Para payroll: usar la estructura del API de payroll
      if (resumen.ultimo_cierre) {
        return {
          periodo: resumen.ultimo_cierre.periodo,
          estado: resumen.ultimo_cierre.estado
        };
      } else if (resumen.estadisticas_payroll) {
        return {
          periodo: resumen.estadisticas_payroll.ultimo_periodo,
          estado: resumen.estadisticas_payroll.estado_actual
        };
      }
      // Fallback para estructura simplificada de payroll
      return {
        periodo: resumen.ultimo_cierre || resumen.ultimo_periodo,
        estado: resumen.estado_cierre_actual || resumen.estado_ultimo_cierre
      };
    } else {
      // Para contabilidad: usar la estructura del API de contabilidad
      return {
        periodo: resumen.ultimo_cierre || resumen.ultimo_periodo,
        estado: resumen.estado_ultimo_cierre || resumen.estado_cierre_actual
      };
    }
  };

  const cierreInfo = getCierreInfo();

  return (
    <div className="bg-gray-800 p-6 rounded-lg shadow-lg">
      <div className="flex items-center gap-3 mb-2">
        <h2 className="text-2xl font-bold">{cliente.nombre}</h2>
        {cliente.bilingue && (
          <span className="ml-2 bg-blue-600 text-white text-xs px-2 py-1 rounded-full shadow font-semibold flex items-center gap-1">
            <svg className="inline-block w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v2m0 4v2m0 4v2m0 4v2m8-10h-2m-4 0H8m-4 0H2m18 0c0 4.418-3.582 8-8 8s-8-3.582-8-8 3.582-8 8-8 8 3.582 8 8z" />
            </svg>
            Bilingüe
          </span>
        )}
      </div>
      <p className="text-gray-300 mb-1">RUT: {cliente.rut}</p>
      <p className="text-gray-300 mb-1">
        Industria: {cliente.industria_nombre || cliente.industria?.nombre || "—"}
      </p>

      <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="bg-gray-700 p-4 rounded">
          <h3 className="text-sm text-gray-400">Último Cierre</h3>
          <p className="text-lg font-semibold">{cierreInfo.periodo || "Sin cierres"}</p>
        </div>
        <div className="bg-gray-700 p-4 rounded">
          <h3 className="text-sm text-gray-400">Estado</h3>
          <EstadoBadge estado={cierreInfo.estado || "sin_cierres"} />
        </div>
      </div>
    </div>
  );
};

export default ClienteInfoCard;
