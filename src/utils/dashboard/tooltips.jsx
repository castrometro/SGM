import React from 'react';

// Tooltips reutilizables para gráficos (Bar/Pie) en dashboards Nómina
// Se evita insertar \n literales dentro de JSX; se construye estructura directamente.

export function createBarTooltip({ getTotal, labelValor='Valor', accentColor='#14b8a6', borderColor='border-teal-600/40', valueFormatter = v => v }) {
  return function ReusableBarTooltip({ active, payload }) {
    if (!active || !payload || !payload.length) return null;
    const p = payload[0];
    const valor = p.value || 0;
    const total = getTotal();
    const pct = total ? ((valor / total) * 100).toFixed(1) : '0.0';
    return (
      <div className={`bg-gray-900/90 backdrop-blur-sm border ${borderColor} rounded-md px-3 py-2 shadow-xl text-xs text-gray-200 space-y-1`}>
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-sm" style={{ background: p.color || accentColor }} />
          <span className="font-medium text-white max-w-[220px] truncate" title={p.payload?.name}>{p.payload?.name}</span>
        </div>
        <div className="flex justify-between gap-4">
          <span className="text-gray-400">{labelValor}</span>
          <span className="font-semibold tabular-nums text-teal-300">{valueFormatter(valor)}</span>
        </div>
        <div className="flex justify-between gap-4">
          <span className="text-gray-400">Porcentaje</span>
          <span className="tabular-nums text-gray-300">{pct}%</span>
        </div>
      </div>
    );
  };
}

export function createPieTooltip({ getTotal, labelValor='Valor', accentColor='#6366f1', borderColor='border-indigo-600/40', valueFormatter = v => v }) {
  return function ReusablePieTooltip({ active, payload }) {
    if (!active || !payload || !payload.length) return null;
    const p = payload[0];
    const valor = p.value || 0;
    const total = getTotal();
    const pct = total ? ((valor / total) * 100).toFixed(1) : '0.0';
    return (
      <div className={`bg-gray-900/90 backdrop-blur-sm border ${borderColor} rounded-md px-3 py-2 shadow-xl text-xs text-gray-200 space-y-1`}>
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-sm" style={{ background: p.color || accentColor }} />
          <span className="font-medium text-white max-w-[200px] truncate" title={p.name}>{p.name}</span>
        </div>
        <div className="flex justify-between gap-4">
          <span className="text-gray-400">{labelValor}</span>
          <span className="font-semibold tabular-nums text-indigo-300">{valueFormatter(valor)}</span>
        </div>
        <div className="flex justify-between gap-4">
          <span className="text-gray-400">Porcentaje</span>
          <span className="tabular-nums text-gray-300">{pct}%</span>
        </div>
      </div>
    );
  };
}

// Tooltip reutilizable para LineChart (multi serie), estilo consistente con Pie
export function createLineTooltip({
  labelValor = 'Valor',
  borderColor = 'border-slate-600/40',
  valueFormatter = v => v,
  titleFormatter = (label) => label,
  accentColor = '#14b8a6'
}) {
  return function ReusableLineTooltip({ active, payload, label }) {
    if (!active || !payload || !payload.length) return null;
    return (
      <div className={`bg-gray-900/90 backdrop-blur-sm border ${borderColor} rounded-md px-3 py-2 shadow-xl text-xs text-gray-200 space-y-1`}> 
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-sm" style={{ background: payload[0]?.color || accentColor }} />
          <span className="font-medium text-white max-w-[220px] truncate" title={String(label)}>{titleFormatter(label)}</span>
        </div>
        {payload.map((p) => (
          <div key={p.dataKey} className="flex justify-between gap-4 items-center">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-sm" style={{ background: p.color || accentColor }} />
              <span className="text-gray-300">{p.name || p.dataKey}</span>
            </div>
            <span className="font-semibold tabular-nums text-teal-300">{valueFormatter(p.value || 0)}</span>
          </div>
        ))}
      </div>
    );
  };
}
