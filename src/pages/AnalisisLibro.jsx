import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import CierreInfoBar from "../components/InfoCards/CierreInfoBar";
import {
  obtenerCierrePorId,
  obtenerMovimientosResumen,
  obtenerSetsClasificacion,
  obtenerOpcionesClasificacion,
} from "../api/contabilidad";
import { obtenerCliente } from "../api/clientes";
import { formatMoney } from "../utils/format";

const AnalisisLibro = () => {
  const { cierreId } = useParams();
  const navigate = useNavigate();
  const [cierre, setCierre] = useState(null);
  const [cliente, setCliente] = useState(null);
  const [resumen, setResumen] = useState(null);
  const [filtros, setFiltros] = useState({ texto: "" });
  const [sets, setSets] = useState([]);
  const [opciones, setOpciones] = useState([]);
  const [selectedSet, setSelectedSet] = useState("");
  const [selectedOpcion, setSelectedOpcion] = useState("");

  useEffect(() => {
    const fetchData = async () => {
      if (!cierreId) return;
      const cierreObj = await obtenerCierrePorId(cierreId);
      setCierre(cierreObj);
      const clienteObj = await obtenerCliente(cierreObj.cliente);
      setCliente(clienteObj);
      const setsData = await obtenerSetsClasificacion(clienteObj.id);
      setSets(setsData);
      if (setsData.length > 0) setSelectedSet(setsData[0].id.toString());
    };
    fetchData();
  }, [cierreId]);

  useEffect(() => {
    if (!selectedSet) {
      setOpciones([]);
      return;
    }
    const loadOpts = async () => {
      const opts = await obtenerOpcionesClasificacion(selectedSet);
      setOpciones(opts);
    };
    loadOpts();
  }, [selectedSet]);

  useEffect(() => {
    const fetchResumen = async () => {
      if (!cierreId) return;
      const params = {
        setId: selectedSet || undefined,
        opcionId: selectedOpcion || undefined,
      };
      const movResumen = await obtenerMovimientosResumen(cierreId, params);
      
      // Se eliminan logs de debug tras confirmación de formato correcto
      setResumen(movResumen);
    };
    fetchResumen();
  }, [cierreId, selectedSet, selectedOpcion]);

  if (!cierre || !cliente || !resumen) {
    return (
      <div className="text-white text-center mt-8">Cargando análisis de libro...</div>
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
        <div className="flex flex-col">
          <label className="text-sm text-gray-300" htmlFor="set">Set</label>
          <select
            id="set"
            className="bg-gray-700 text-white rounded px-2 py-1"
            value={selectedSet}
            onChange={(e) => {
              setSelectedSet(e.target.value);
              setSelectedOpcion("");
            }}
          >
            <option value="">Todos</option>
            {sets.map((s) => (
              <option key={s.id} value={s.id}>
                {s.nombre}
              </option>
            ))}
          </select>
        </div>
        <div className="flex flex-col">
          <label className="text-sm text-gray-300" htmlFor="opcion">Opción</label>
          <select
            id="opcion"
            className="bg-gray-700 text-white rounded px-2 py-1"
            value={selectedOpcion}
            onChange={(e) => setSelectedOpcion(e.target.value)}
            disabled={!selectedSet}
          >
            <option value="">Todas</option>
            {opciones.map((o) => (
              <option key={o.id} value={o.id}>
                {o.valor}
              </option>
            ))}
          </select>
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
              {selectedSet && (
                <th className="px-4 py-2 text-left">Clasificación</th>
              )}
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
                {selectedSet && (
                  <td className="px-4 py-2">{r.clasificacion?.opcion_valor || ""}</td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default AnalisisLibro;
