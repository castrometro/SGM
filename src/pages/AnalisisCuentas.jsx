import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import CierreInfoBar from "../components/InfoCards/CierreInfoBar";
import {
  obtenerCierrePorId,
  obtenerMovimientosResumen,
} from "../api/contabilidad";
import { obtenerCliente } from "../api/clientes";
import { formatMoney } from "../utils/format";

const AnalisisCuentas = () => {
  const { cierreId } = useParams();
  const navigate = useNavigate();
  const [cierre, setCierre] = useState(null);
  const [cliente, setCliente] = useState(null);
  const [resumen, setResumen] = useState(null);
  const [filtros, setFiltros] = useState({ texto: "" });

  useEffect(() => {
    const fetchData = async () => {
      if (!cierreId) return;
      const cierreObj = await obtenerCierrePorId(cierreId);
      setCierre(cierreObj);
      const clienteObj = await obtenerCliente(cierreObj.cliente);
      setCliente(clienteObj);
      const movResumen = await obtenerMovimientosResumen(cierreId);
      setResumen(movResumen);
    };
    fetchData();
  }, [cierreId]);

  if (!cierre || !cliente || !resumen) {
    return (
      <div className="text-white text-center mt-8">Cargando análisis de cuentas...</div>
    );
  }

  const { texto } = filtros;
  const resumenFiltrado = resumen.filter((r) =>
    `${r.codigo} ${r.nombre}`.toLowerCase().includes(texto.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <CierreInfoBar cierre={cierre} cliente={cliente} />
      <div className="bg-gray-800 p-4 rounded-md flex flex-col gap-4 md:flex-row md:items-end">
        <div className="flex flex-col flex-grow">
          <label className="text-sm text-gray-300" htmlFor="texto">Buscar</label>
          <input
            id="texto"
            type="text"
            placeholder="Cuenta..."
            className="bg-gray-700 text-white rounded px-2 py-1"
            value={texto}
            onChange={(e) =>
              setFiltros((f) => ({ ...f, texto: e.target.value }))
            }
          />
        </div>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm border-separate border-spacing-y-1">
          <thead>
            <tr className="bg-gray-700">
              <th className="px-4 py-2 text-left">Cuenta</th>
              <th className="px-4 py-2 text-right">Saldo anterior</th>
              <th className="px-4 py-2 text-right">Total debe</th>
              <th className="px-4 py-2 text-right">Total haber</th>
              <th className="px-4 py-2 text-right">Saldo final</th>
            </tr>
          </thead>
          <tbody>
            {resumenFiltrado.map((r) => (
              <tr
                key={r.cuenta_id}
                className="bg-gray-800 hover:bg-gray-700 cursor-pointer"
                onClick={() =>
                  navigate(`/menu/cierres/${cierreId}/cuentas/${r.cuenta_id}`)
                }
              >
                <td className="px-4 py-2">
                  {r.codigo} - {r.nombre}
                </td>
                <td className="px-4 py-2 text-right">{formatMoney(r.saldo_anterior)}</td>
                <td className="px-4 py-2 text-right">{formatMoney(r.total_debe)}</td>
                <td className="px-4 py-2 text-right">{formatMoney(r.total_haber)}</td>
                <td className="px-4 py-2 text-right">{formatMoney(r.saldo_final)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default AnalisisCuentas;
