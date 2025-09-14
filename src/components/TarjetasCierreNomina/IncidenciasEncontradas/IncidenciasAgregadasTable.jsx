import React, { useMemo, useState } from "react";
import { ArrowUpDown } from "lucide-react";
import { formatearMonedaChilena } from "../../../utils/formatters";

const headers = [
  { key: "tipo_concepto", label: "Concepto" },
  { key: "concepto", label: "Ítem" },
  { key: "suma_anterior", label: "Σ Anterior" },
  { key: "suma_actual", label: "Σ Actual" },
  { key: "variacion_porcentual", label: "Variación %" },
  { key: "variacion_absoluta", label: "Δ Absoluta" },
  { key: "prioridad", label: "Prioridad" },
];

export default function IncidenciasAgregadasTable({ incidencias = [] }) {
  const [sortKey, setSortKey] = useState("variacion_porcentual");
  const [sortDir, setSortDir] = useState("desc");
  const [filtroConcepto, setFiltroConcepto] = useState("");

  const rows = useMemo(() => {
    const agregadas = incidencias.filter(i => i?.tipo_comparacion === 'suma_total');
    const mapRows = agregadas.map(i => {
      const da = i.datos_adicionales || {};
      return {
        id: i.id,
        tipo_concepto: da.tipo_concepto || da.categoria || i.tipo_concepto,
        concepto: da.concepto || i.concepto_afectado,
        suma_actual: Number(da.suma_actual ?? 0),
        suma_anterior: Number(da.suma_anterior ?? 0),
        variacion_porcentual: Number(da.variacion_porcentual ?? 0),
        variacion_absoluta: Number(da.variacion_absoluta ?? Math.abs((da.suma_actual ?? 0) - (da.suma_anterior ?? 0))),
        prioridad: i.prioridad || 'baja',
      };
    });

    const filtrados = filtroConcepto
      ? mapRows.filter(r => (r.tipo_concepto || '').includes(filtroConcepto))
      : mapRows;

    const sorted = [...filtrados].sort((a, b) => {
      const va = a[sortKey];
      const vb = b[sortKey];
      if (va === vb) return 0;
      return (va > vb ? 1 : -1) * (sortDir === 'asc' ? 1 : -1);
    });

    return sorted;
  }, [incidencias, sortKey, sortDir, filtroConcepto]);

  const onSort = (key) => {
    if (sortKey === key) {
      setSortDir(sortDir === 'asc' ? 'desc' : 'asc');
    } else {
      setSortKey(key);
      setSortDir('desc');
    }
  };

  const headerCell = (h) => (
    <th
      key={h.key}
      className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider cursor-pointer select-none"
      onClick={() => onSort(h.key)}
    >
      <span className="inline-flex items-center gap-1">
        {h.label}
        <ArrowUpDown size={14} className="opacity-60" />
      </span>
    </th>
  );

  const badgeConcepto = (tipo) => {
    const map = {
      haber_imponible: '💰 Haberes Imponibles',
      haber_no_imponible: '🎁 Haberes No Imponibles',
      otro_descuento: '📋 Otros Descuentos',
    };
    return map[tipo] || tipo;
  };

  const badgePrioridad = (p) => {
    const cls = p === 'critica'
      ? 'bg-rose-900/50 text-rose-300 ring-1 ring-rose-700/40'
      : p === 'alta'
        ? 'bg-orange-900/50 text-orange-300 ring-1 ring-orange-700/40'
        : p === 'media'
          ? 'bg-amber-900/50 text-amber-300 ring-1 ring-amber-700/40'
          : 'bg-emerald-900/50 text-emerald-300 ring-1 ring-emerald-700/40';
    return <span className={`px-2 py-0.5 rounded text-xs ${cls}`}>{p}</span>;
  };

  if (!incidencias?.length) {
    return (
      <div className="text-center py-6 text-gray-400">No hay incidencias agregadas por ítem</div>
    );
  }

  return (
    <div className="bg-gray-900/60 rounded-xl p-4 border border-gray-800">
      <div className="flex items-center justify-between mb-3">
        <h4 className="text-sm font-medium text-gray-300">Ítems con variación (agregado por mes)</h4>
        <select
          value={filtroConcepto}
          onChange={(e) => setFiltroConcepto(e.target.value)}
          className="bg-gray-700 border border-gray-600 rounded px-2 py-1 text-xs text-white"
        >
          <option value="">Todos los conceptos</option>
          <option value="haber_imponible">Haberes Imponibles</option>
          <option value="haber_no_imponible">Haberes No Imponibles</option>
          <option value="otro_descuento">Otros Descuentos</option>
        </select>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full bg-gray-800 rounded-lg">
          <thead className="bg-gray-800/80 border-b border-gray-700">
            <tr>
              {headers.map(headerCell)}
            </tr>
          </thead>
          <tbody>
            {rows.map((r, idx) => (
              <tr key={`${r.tipo_concepto}-${r.concepto}-${idx}`} className="border-b border-gray-700/50">
                <td className="px-4 py-2 text-gray-300 whitespace-nowrap">{badgeConcepto(r.tipo_concepto)}</td>
                <td className="px-4 py-2 text-gray-100">{r.concepto}</td>
                <td className="px-4 py-2 text-gray-300">{formatearMonedaChilena(r.suma_anterior)}</td>
                <td className="px-4 py-2 text-gray-300">{formatearMonedaChilena(r.suma_actual)}</td>
                <td className={`px-4 py-2 font-medium ${r.variacion_porcentual >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                  {r.variacion_porcentual.toFixed(2)}%
                </td>
                <td className="px-4 py-2 text-gray-300">{formatearMonedaChilena(r.variacion_absoluta)}</td>
                <td className="px-4 py-2">{badgePrioridad(r.prioridad)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
