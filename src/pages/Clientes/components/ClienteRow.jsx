import { Link } from "react-router-dom";
import EstadoBadge from "../../../components/EstadoBadge";

const ClienteRow = ({ cliente, areaActiva, tipoModulo }) => {
  // Determinar qué información de cierre mostrar según el módulo
  const getCierreInfo = () => {
    if (tipoModulo === 'payroll') {
      return cliente.ultimo_cierre_payroll || {};
    } else if (tipoModulo === 'contabilidad') {
      // Para contabilidad, esperamos ultimo_cierre_contabilidad de la API enriquecida
      return cliente.ultimo_cierre_contabilidad || {};
    }
    return {};
  };

  const cierreInfo = getCierreInfo();
  
  // Determinar qué mostrar en "Último Cierre"
  const getUltimoCierreDisplay = () => {
    if (!cierreInfo.periodo) {
      return "Sin cierres";
    }
    return cierreInfo.periodo;
  };
  
  // Determinar el estado para el badge
  const getEstadoCierre = () => {
    if (!cierreInfo.estado) {
      return "sin_cierres";
    }
    return cierreInfo.estado;
  };

  // Determinar las acciones según el módulo
  const getAcciones = () => {
    if (tipoModulo === 'payroll') {
      return (
        <>
          <Link
            to={`/menu/clientes/${cliente.id}`}
            className="!text-white hover:text-gray-300 font-medium px-3 py-1 rounded hover:bg-white/10 transition"
          >
            Ver Cliente
          </Link>
          <Link
            to={`/menu/clientes/${cliente.id}/payroll`}
            className="!text-blue-400 hover:text-blue-300 font-medium px-3 py-1 rounded hover:bg-blue-400/10 transition"
          >
            Gestionar Nómina
          </Link>
        </>
      );
    } else if (tipoModulo === 'contabilidad') {
      return (
        <>
          <Link
            to={`/menu/clientes/${cliente.id}`}
            className="!text-white hover:text-gray-300 font-medium px-3 py-1 rounded hover:bg-white/10 transition"
          >
            Ver Cliente
          </Link>
          <Link
            to={`/menu/clientes/${cliente.id}/contabilidad`}
            className="!text-green-400 hover:text-green-300 font-medium px-3 py-1 rounded hover:bg-green-400/10 transition"
          >
            Gestionar Contabilidad
          </Link>
        </>
      );
    }
    
    // Fallback genérico
    return (
      <Link
        to={`/menu/clientes/${cliente.id}`}
        className="!text-white hover:text-gray-300 font-medium px-3 py-1 rounded hover:bg-white/10 transition"
      >
        Ver Cliente
      </Link>
    );
  };

  return (
    <tr key={cliente.id} className="border-b border-gray-700">
      <td className="p-2">{cliente.nombre}</td>
      <td className="p-2">{cliente.rut}</td>
      <td className="p-2 text-center">
        {getUltimoCierreDisplay()}
      </td>
      <td className="p-2 text-center">
        <EstadoBadge estado={getEstadoCierre()} />
      </td>
      <td className="p-2 text-center">
        <div className="flex items-center justify-center gap-2">
          {getAcciones()}
        </div>
      </td>
    </tr>
  );
};

export default ClienteRow;
