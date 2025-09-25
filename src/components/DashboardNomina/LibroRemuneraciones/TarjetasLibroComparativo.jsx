import React, { useMemo } from 'react';
import { ArrowUpRight, ArrowDownRight, ArrowRight } from 'lucide-react';
import { formatearMonedaChilena } from '../../../utils/formatters';

/*
  TarjetasLibroComparativo
  Muestra una tarjeta por categoría con: valor actual, anterior, delta absoluto y %.
  Props:
    actual: bloque libro_resumen_v2 actual
    anterior: bloque libro_resumen_v2 anterior (asegura deltas)
*/

const categoryMeta = {
  haber_imponible: { label: 'Haberes Imponibles', cls: 'text-emerald-400', sentido: 'positivo' },
  haber_no_imponible: { label: 'Haberes No Imponibles', cls: 'text-emerald-300', sentido: 'positivo' },
  descuento_legal: { label: 'Descuentos Legales', cls: 'text-rose-400', sentido: 'negativo' },
  otro_descuento: { label: 'Otros Descuentos', cls: 'text-rose-300', sentido: 'negativo' },
  impuesto: { label: 'Impuestos', cls: 'text-red-300', sentido: 'negativo' },
  aporte_patronal: { label: 'Aportes Patronales', cls: 'text-indigo-300', sentido: 'neutro' },
};

const TarjetasLibroComparativo = ({ actual, anterior, selectedCat, setSelectedCat }) => {
  const categorias = actual?.totales_categorias || {};
  const categoriasPrev = anterior?.totales_categorias || {};

  const rows = useMemo(() => Object.keys(categoryMeta).map(key => {
    const cur = Number(categorias[key] || 0);
    const prev = Number(categoriasPrev[key] || 0);
    const delta = cur - prev;
    const pct = prev !== 0 ? (delta / prev) * 100 : (prev === 0 && cur !== 0 ? 100 : 0);
    return { key, cur, prev, delta, pct, ...categoryMeta[key] };
  }), [categorias, categoriasPrev]);

  function deltaBadge(delta, sentido){
    if (delta === 0) return <span className="text-xs text-gray-400 flex items-center gap-0.5">0</span>;
    const pos = delta > 0;
    let color = pos ? 'text-emerald-400' : 'text-rose-400';
    if (sentido === 'negativo') color = pos ? 'text-rose-400' : 'text-emerald-400';
    const Icon = pos ? ArrowUpRight : ArrowDownRight;
    return <span className={`text-xs font-medium flex items-center gap-0.5 ${color}`}><Icon size={14} /> {formatearMonedaChilena(delta)}</span>;
  }
  function pctText(pct, sentido){
    if (pct === 0) return <span className="text-[10px] text-gray-400">0%</span>;
    const pos = pct > 0;
    let color = pos ? 'text-emerald-400' : 'text-rose-400';
    if (sentido === 'negativo') color = pos ? 'text-rose-400' : 'text-emerald-400';
    if (Math.abs(pct) < 0.05) color = 'text-gray-400';
    return <span className={`text-[10px] font-medium tabular-nums ${color}`}>{pct.toFixed(1)}%</span>;
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
      {rows.map(r => {
        const active = selectedCat === r.key;
        return (
        <button type="button" onClick={()=> setSelectedCat(prev => prev === r.key ? '' : r.key)} key={r.key} className={`text-left bg-gray-900/70 rounded-lg border p-3 flex flex-col gap-1 transition-colors ${active? 'border-teal-600 ring-1 ring-teal-600/40':'border-gray-800 hover:border-teal-700/50'}`}>        
          <div className="flex items-center justify-between">
            <p className="text-[11px] uppercase tracking-wide text-gray-400">{r.label}</p>
            <ArrowRight size={14} className="text-gray-600" />
          </div>
          <div className="flex items-end justify-between gap-2">
            <div className="flex flex-col">
              <span className={`text-sm font-medium ${r.cls} tabular-nums`}>{formatearMonedaChilena(r.cur)}</span>
              <span className="text-[10px] text-gray-500 tabular-nums">Prev: {formatearMonedaChilena(r.prev)}</span>
            </div>
            <div className="flex flex-col items-end">
              {deltaBadge(r.delta, r.sentido)}
              {pctText(r.pct, r.sentido)}
            </div>
          </div>
        </button>
      );})}
    </div>
  );
};

export default TarjetasLibroComparativo;
