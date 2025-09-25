import React, { useMemo } from 'react';
import { ArrowDownRight, ArrowUpRight } from 'lucide-react';

/*
  Componente ComparativoMovimientos
  Props:
    actual: bloque movimientos_v3 actual
    anterior: bloque movimientos_v3 anterior
    periodoAnterior: string
  Deriva las mismas métricas que TarjetasMetricasMovimientos y muestra delta.
*/
const calcularMetrics = (bloque) => {
  if (!bloque) return null;
  const arr = bloque.movimientos || [];
  const countBy = (f) => arr.filter(f).length;
  const diasAus = arr.reduce((acc,m)=> acc + (m.categoria==='ausencia' ? Number(m.dias_en_periodo ?? m.dias_evento ?? 0) : 0), 0);
  return {
    ingresos: countBy(m=>m.categoria==='ingreso'),
    finiquitos: countBy(m=>m.categoria==='finiquito'),
    dias_ausencia_justificados: diasAus,
    vacaciones: countBy(m=>m.categoria==='ausencia' && m.subtipo==='vacaciones'),
    ausencias_sin_justificar: countBy(m=>m.categoria==='ausencia' && (m.subtipo==='sin_justificar' || m.motivo==='sin_justificar')),
  };
};

const etiquetas = {
  ingresos: 'Ingresos',
  finiquitos: 'Finiquitos',
  dias_ausencia_justificados: 'Días ausencia justificados',
  vacaciones: 'Días de vacaciones',
  ausencias_sin_justificar: 'Ausencias sin justificar'
};

const ComparativoMovimientos = ({ actual, anterior, periodoAnterior }) => {
  const a = useMemo(()=> calcularMetrics(actual), [actual]);
  const b = useMemo(()=> calcularMetrics(anterior), [anterior]);
  const rows = useMemo(()=> {
    if (!a) return [];
    return Object.keys(etiquetas).map(k => {
      const cur = a[k] || 0;
      const prev = b ? (b[k] || 0) : null;
      const delta = prev === null ? null : cur - prev;
      const pct = prev && prev !== 0 ? (delta / prev) * 100 : (prev === 0 && cur !==0 ? 100 : null);
      return { key: k, label: etiquetas[k], cur, prev, delta, pct };
    });
  }, [a, b]);

  if (!a) return null;
  if (!b) return <div className="text-xs text-gray-400">No hay cierre anterior finalizado para comparar.</div>;

  return (
    <div className="space-y-4">
      <div className="overflow-auto rounded-lg border border-gray-800">
        <table className="min-w-full text-xs">
          <thead className="bg-gray-900/70 text-[10px] uppercase tracking-wide text-gray-400">
            <tr>
              <th className="px-3 py-2 text-left">Métrica</th>
              <th className="px-3 py-2 text-right">Actual</th>
              <th className="px-3 py-2 text-right">Anterior</th>
              <th className="px-3 py-2 text-right">Δ</th>
              <th className="px-3 py-2 text-right">Δ%</th>
            </tr>
          </thead>
          <tbody>
            {rows.map(r => {
              const pos = r.delta > 0;
              const Icon = pos ? ArrowUpRight : ArrowDownRight;
              const cls = r.delta === 0 || r.delta === null ? 'text-gray-400' : (pos ? 'text-emerald-400' : 'text-rose-400');
              const pct = r.pct === null ? '--' : `${r.pct.toFixed(1)}%`;
              return (
                <tr key={r.key} className="border-t border-gray-800 hover:bg-gray-900/60">
                  <td className="px-3 py-1.5 text-gray-200 whitespace-nowrap">{r.label}</td>
                  <td className="px-3 py-1.5 text-right font-medium text-gray-300 tabular-nums">{r.cur}</td>
                  <td className="px-3 py-1.5 text-right text-gray-500 tabular-nums">{r.prev !== null ? r.prev : '--'}</td>
                  <td className={`px-3 py-1.5 text-right tabular-nums font-medium ${cls}`}>{r.delta === null ? '--' : (<span className="inline-flex items-center gap-0.5"><Icon size={14} /> {r.delta}</span>)}</td>
                  <td className={`px-3 py-1.5 text-right tabular-nums ${cls}`}>{pct}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <div className="text-[10px] text-gray-500">Comparando contra {periodoAnterior}</div>
    </div>
  );
};

export default ComparativoMovimientos;
