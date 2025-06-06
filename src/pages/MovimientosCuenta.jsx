import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import CierreInfoBar from "../components/InfoCards/CierreInfoBar";
import {
  obtenerCierrePorId,
  obtenerMovimientosCuenta,
} from "../api/contabilidad";
import { obtenerCliente } from "../api/clientes";
import { formatMoney } from "../utils/format";

const MovimientosCuenta = () => {
  const { cierreId, cuentaId } = useParams();
  const [cierre, setCierre] = useState(null);
  const [cliente, setCliente] = useState(null);
  const [detalle, setDetalle] = useState(null);
  const [filtros, setFiltros] = useState({ desde: "", hasta: "", texto: "" });
  const [sortField, setSortField] = useState("fecha");
  const [sortOrder, setSortOrder] = useState("asc");

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
    return (
      <div className="text-white text-center mt-8">Cargando movimientos...</div>
    );
  }

  const { desde, hasta, texto } = filtros;
  const movimientosFiltrados = detalle.movimientos.filter((m) => {
    if (desde && new Date(m.fecha) < new Date(desde)) return false;
    if (hasta && new Date(m.fecha) > new Date(hasta)) return false;
    if (
      texto &&
      !m.descripcion.toLowerCase().includes(texto.toLowerCase())
    )
      return false;
    return true;
  });

  const handleSort = (field) => {
    if (sortField === field) {
      setSortOrder((o) => (o === "asc" ? "desc" : "asc"));
    } else {
      setSortField(field);
      setSortOrder("asc");
    }
  };

  const movimientosOrdenados = [...movimientosFiltrados].sort((a, b) => {
    let valA = a[sortField];
    let valB = b[sortField];
    if (sortField === "fecha") {
      valA = new Date(valA);
      valB = new Date(valB);
    }
    if (valA < valB) return sortOrder === "asc" ? -1 : 1;
    if (valA > valB) return sortOrder === "asc" ? 1 : -1;
    return 0;
  });

  return (
    <div className="space-y-6">
      <CierreInfoBar cierre={cierre} cliente={cliente} />
      <Link to={`/menu/cierres/${cierreId}/analisis`} className="text-blue-400">
        ← Volver
      </Link>
      <h2 className="text-xl font-semibold text-white">
        {detalle.codigo} - {detalle.nombre}
      </h2>

      <div className="bg-gray-800 p-4 rounded-md flex flex-col gap-4 md:flex-row md:items-end">
        <div className="flex flex-col">
          <label className="text-sm text-gray-300" htmlFor="desde">Desde</label>
          <input
            id="desde"
            type="date"
            className="bg-gray-700 text-white rounded px-2 py-1"
            value={desde}
            onChange={(e) =>
              setFiltros((f) => ({ ...f, desde: e.target.value }))
            }
          />
        </div>
        <div className="flex flex-col">
          <label className="text-sm text-gray-300" htmlFor="hasta">Hasta</label>
          <input
            id="hasta"
            type="date"
            className="bg-gray-700 text-white rounded px-2 py-1"
            value={hasta}
            onChange={(e) =>
              setFiltros((f) => ({ ...f, hasta: e.target.value }))
            }
          />
        </div>
        <div className="flex flex-col flex-grow">
          <label className="text-sm text-gray-300" htmlFor="texto">Buscar</label>
          <input
            id="texto"
            type="text"
            placeholder="Descripción..."
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
              <th
                className="px-4 py-2 cursor-pointer"
                onClick={() => handleSort("fecha")}
              >
                Fecha {sortField === "fecha" && (sortOrder === "asc" ? "▲" : "▼")}
              </th>
              <th
                className="px-4 py-2 cursor-pointer"
                onClick={() => handleSort("tipo_documento")}
              >
                Tipo doc.{" "}
                {sortField === "tipo_documento" &&
                  (sortOrder === "asc" ? "▲" : "▼")}
              </th>
              <th
                className="px-4 py-2 cursor-pointer"
                onClick={() => handleSort("numero_comprobante")}
              >
                N° comprobante {sortField === "numero_comprobante" && (sortOrder === "asc" ? "▲" : "▼")}
              </th>
              <th
                className="px-4 py-2 cursor-pointer"
                onClick={() => handleSort("descripcion")}
              >
                Descripción {sortField === "descripcion" && (sortOrder === "asc" ? "▲" : "▼")}
              </th>
              <th
                className="px-4 py-2 text-right cursor-pointer"
                onClick={() => handleSort("debe")}
              >
                Debe {sortField === "debe" && (sortOrder === "asc" ? "▲" : "▼")}
              </th>
              <th
                className="px-4 py-2 text-right cursor-pointer"
                onClick={() => handleSort("haber")}
              >
                Haber {sortField === "haber" && (sortOrder === "asc" ? "▲" : "▼")}
              </th>
              <th
                className="px-4 py-2 text-right cursor-pointer"
                onClick={() => handleSort("saldo")}
              >
                Saldo {sortField === "saldo" && (sortOrder === "asc" ? "▲" : "▼")}
              </th>
            </tr>
          </thead>
          <tbody>
            <tr className="bg-gray-800 font-semibold">
              <td colSpan={6} className="px-4 py-2 text-right">Saldo inicial</td>
              <td className="px-4 py-2 text-right">{formatMoney(detalle.saldo_inicial)}</td>
            </tr>
            {movimientosOrdenados.map((m) => (
              <tr key={m.id} className="bg-gray-800">
                <td className="px-4 py-2">{m.fecha}</td>
                <td className="px-4 py-2">{m.tipo_documento || ""}</td>
                <td className="px-4 py-2">{m.numero_comprobante}</td>
                <td className="px-4 py-2">{m.descripcion}</td>
                <td className="px-4 py-2 text-right">{formatMoney(m.debe)}</td>
                <td className="px-4 py-2 text-right">{formatMoney(m.haber)}</td>
                <td className="px-4 py-2 text-right">{formatMoney(m.saldo)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default MovimientosCuenta;
