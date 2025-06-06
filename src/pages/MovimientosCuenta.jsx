import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import CierreInfoBar from "../components/InfoCards/CierreInfoBar";
import { obtenerCierrePorId, obtenerMovimientosCuenta } from "../api/contabilidad";
import { obtenerCliente } from "../api/clientes";

const MovimientosCuenta = () => {
  const { cierreId, cuentaId } = useParams();
  const [cierre, setCierre] = useState(null);
  const [cliente, setCliente] = useState(null);
  const [detalle, setDetalle] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      if (!cierreId || !cuentaId) return;
      const cierreObj = await obtenerCierrePorId(cierreId);
      setCierre(cierreObj);
      const clienteObj = await obtenerCliente(cierreObj.cliente);
      setCliente(clienteObj);
      const data = await obtenerMovimientosCuenta(cierreId, cuentaId);
      setDetalle(data);
    };
    fetchData();
  }, [cierreId, cuentaId]);

  if (!cierre || !cliente || !detalle) {
    return <div className="text-white text-center mt-8">Cargando movimientos...</div>;
  }

  return (
    <div className="space-y-6">
      <CierreInfoBar cierre={cierre} cliente={cliente} />
      <Link to={`/menu/cierres/${cierreId}/analisis`} className="text-blue-400">
        ← Volver
      </Link>
      <h2 className="text-xl font-semibold text-white">
        {detalle.codigo} - {detalle.nombre}
      </h2>
      <div className="overflow-x-auto">
        <table className="w-full text-sm border-separate border-spacing-y-1">
          <thead>
            <tr className="bg-gray-700">
              <th className="px-4 py-2">Fecha</th>
              <th className="px-4 py-2">Descripción</th>
              <th className="px-4 py-2 text-right">Debe</th>
              <th className="px-4 py-2 text-right">Haber</th>
              <th className="px-4 py-2 text-right">Saldo</th>
            </tr>
          </thead>
          <tbody>
            {detalle.movimientos.map((m) => (
              <tr key={m.id} className="bg-gray-800">
                <td className="px-4 py-2">{m.fecha}</td>
                <td className="px-4 py-2">{m.descripcion}</td>
                <td className="px-4 py-2 text-right">{m.debe}</td>
                <td className="px-4 py-2 text-right">{m.haber}</td>
                <td className="px-4 py-2 text-right">{m.saldo}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default MovimientosCuenta;
