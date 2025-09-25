import React, { useMemo, useState } from 'react';
import { ArrowUpRight, ArrowDownRight, ArrowRight } from 'lucide-react';
import { formatearMonedaChilena } from '../../../utils/formatters';

/*
  Componente ComparativoLibro
  Props:
    actual: bloque libro_resumen_v2 del período seleccionado
    anterior: bloque libro_resumen_v2 del período anterior (o null)
    periodoAnterior: string YYYY-MM del cierre anterior
*/
const categoryMeta = {
  haber_imponible: { label: 'Haberes Imponibles', cls: 'text-emerald-400', sentido: 'positivo' },
  haber_no_imponible: { label: 'Haberes No Imponibles', cls: 'text-emerald-300', sentido: 'positivo' },
  descuento_legal: { label: 'Descuentos Legales', cls: 'text-rose-400', sentido: 'negativo' },
  otro_descuento: { label: 'Otros Descuentos', cls: 'text-rose-300', sentido: 'negativo' },
  impuesto: { label: 'Impuestos', cls: 'text-red-300', sentido: 'negativo' },
  aporte_patronal: { label: 'Aportes Patronales', cls: 'text-indigo-300', sentido: 'neutro' },
};

const ComparativoLibro = ({ actual, anterior, periodoAnterior, showCategorias = true }) => {
  const [topN, setTopN] = useState(10);
  const categorias = useMemo(()=> actual?.totales_categorias || {}, [actual]);
  const categoriasPrev = useMemo(()=> anterior?.totales_categorias || {}, [anterior]);

  const catRows = useMemo(()=> Object.keys(categoryMeta).map(key => {
    const cur = Number(categorias[key] || 0);
    const prev = anterior ? Number(categoriasPrev[key] || 0) : null;
    const delta = prev === null ? null : cur - prev;
    const pct = (prev && prev !== 0) ? (delta / prev) * 100 : (prev === 0 && cur !== 0 ? 100 : null);
    return { key, cur, prev, delta, pct, ...categoryMeta[key] };
  }), [categorias, categoriasPrev, anterior]);

  // Construir mapa de conceptos previos por nombre
  const conceptoRows = useMemo(()=> {
    if (!actual?.conceptos) return [];
    const prevMap = new Map();
    if (anterior?.conceptos) {
      for (const c of anterior.conceptos) prevMap.set(c.nombre, c);
    }
    const rows = [];
    for (const c of actual.conceptos) {
      const prev = prevMap.get(c.nombre);
      const curTotal = Number(c.total || 0);
      const prevTotal = prev ? Number(prev.total || 0) : 0;
      const delta = curTotal - prevTotal;
      const pct = prevTotal !== 0 ? (delta / prevTotal) * 100 : null;
      rows.push({ nombre: c.nombre, categoria: c.categoria, cur: curTotal, prev: prev ? prevTotal : null, delta, pct });
      if (prev) prevMap.delete(c.nombre);
    }
    // Conceptos que existían antes y desaparecen
    for (const [nombre, prev] of prevMap.entries()) {
      const prevTotal = Number(prev.total || 0);
      rows.push({ nombre, categoria: prev.categoria, cur: 0, prev: prevTotal, delta: -prevTotal, pct: -100 });
    }
    rows.sort((a,b)=> Math.abs(b.delta) - Math.abs(a.delta));
    return rows;
  }, [actual, anterior]);

  const topConceptos = useMemo(()=> conceptoRows.slice(0, topN), [conceptoRows, topN]);

  function deltaBadge(delta, sentido) {
    if (delta === null || delta === 0) return <span className="text-xs text-gray-400 flex items-center gap-1">0</span>;
    const pos = delta > 0;
    let color = pos ? 'text-emerald-400' : 'text-rose-400';
    // Ajustar color según sentido lógico
    if (sentido === 'negativo') color = pos ? 'text-rose-400' : 'text-emerald-400';
    const Icon = pos ? ArrowUpRight : ArrowDownRight;
    return (
      <span className={`text-xs font-medium flex items-center gap-0.5 ${color}`}>
        <Icon size={14} /> {formatearMonedaChilena(delta)}
      </span>
    );
  }

  function pctText(pct, sentido) {
    if (pct === null) return <span className="text-[10px] text-gray-500">--</span>;
    const pos = pct > 0;
    let color = pos ? 'text-emerald-400' : 'text-rose-400';
    if (sentido === 'negativo') color = pos ? 'text-rose-400' : 'text-emerald-400';
    if (Math.abs(pct) < 0.05) color = 'text-gray-400';
    return <span className={`text-[10px] font-medium tabular-nums ${color}`}>{pct.toFixed(1)}%</span>;
  }

  if (!actual) return null;
  if (!anterior) return (
    <div className="text-xs text-gray-400">No hay cierre anterior finalizado para comparar.</div>
  );

  return (
    <div className="space-y-6">
      {showCategorias && (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {catRows.map(r => (
            <div key={r.key} className="bg-gray-900/70 rounded-lg border border-gray-800 p-3 flex flex-col gap-1">
              <div className="flex items-center justify-between">
                <p className="text-[11px] uppercase tracking-wide text-gray-400">{r.label}</p>
                <ArrowRight size={14} className="text-gray-600" />
              </div>
              <div className="flex items-end justify-between gap-2">
                <div className="flex flex-col">
                  <span className={`text-sm font-medium ${r.cls} tabular-nums`}>{formatearMonedaChilena(r.cur)}</span>
                  <span className="text-[10px] text-gray-500 tabular-nums">Prev: {r.prev !== null ? formatearMonedaChilena(r.prev) : '--'}</span>
                </div>
                <div className="flex flex-col items-end">
                  {deltaBadge(r.delta, r.sentido)}
                  {pctText(r.pct, r.sentido)}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="flex items-center justify-between">
        <h4 className="text-sm font-semibold text-gray-200">Top variaciones de conceptos</h4>
        <div className="flex items-center gap-2 text-[11px] text-gray-400">
          <span>Mostrar</span>
            {[5,10,20,50].map(n => (
              <button key={n} onClick={()=>setTopN(n)} className={`px-2 py-0.5 rounded border text-xs ${topN===n ? 'border-teal-600 text-teal-300' : 'border-gray-700 text-gray-400 hover:border-teal-600/50'}`}>{n}</button>
            ))}
        </div>
      </div>
      <div className="overflow-auto rounded-lg border border-gray-800 max-h-[480px]">
        <table className="min-w-full text-xs">
          <thead className="bg-gray-900/70 sticky top-0 z-10">
            <tr className="text-[10px] text-gray-400 uppercase tracking-wide">
              <th className="px-3 py-2 text-left font-medium">Concepto</th>
              <th className="px-3 py-2 text-right font-medium">Actual</th>
              <th className="px-3 py-2 text-right font-medium">Anterior</th>
              <th className="px-3 py-2 text-right font-medium">Δ</th>
              <th className="px-3 py-2 text-right font-medium">Δ%</th>
            </tr>
          </thead>
          <tbody>
            {topConceptos.map(r => {
              const sentido = categoryMeta[r.categoria]?.sentido || 'neutro';
              const clsBase = sentido==='negativo'
                ? (r.delta>0 ? 'text-rose-400' : 'text-emerald-400')
                : (r.delta>0 ? 'text-emerald-400' : 'text-rose-400');
              const pct = r.pct === null ? '--' : `${r.pct.toFixed(1)}%`;
              return (
                <tr key={r.nombre} className="border-t border-gray-800 hover:bg-gray-900/60">
                  <td className="px-3 py-1.5 text-gray-200 whitespace-nowrap max-w-[260px] truncate" title={r.nombre}>{r.nombre}</td>
                  <td className="px-3 py-1.5 text-right tabular-nums text-gray-300">{formatearMonedaChilena(r.cur)}</td>
                  <td className="px-3 py-1.5 text-right tabular-nums text-gray-500">{r.prev !== null ? formatearMonedaChilena(r.prev) : '--'}</td>
                  <td className={`px-3 py-1.5 text-right tabular-nums font-medium ${r.delta===0? 'text-gray-400': clsBase}`}>{formatearMonedaChilena(r.delta)}</td>
                  <td className={`px-3 py-1.5 text-right tabular-nums ${r.delta===0? 'text-gray-400': clsBase}`}>{pct}</td>
                </tr>
              );
            })}
            {!topConceptos.length && (
              <tr>
                <td colSpan={5} className="px-3 py-4 text-center text-gray-500">No hay variaciones</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      <div className="text-[10px] text-gray-500">Comparando contra {periodoAnterior}</div>
    </div>
  );
};

export default ComparativoLibro;
