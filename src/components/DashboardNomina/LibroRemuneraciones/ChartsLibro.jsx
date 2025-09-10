import React from 'react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RTooltip, PieChart, Pie, Cell } from 'recharts';
import { BarChart3, PieChart as PieIcon } from 'lucide-react';
import { formatearMonedaChilena } from '../../../utils/formatters';
import { createBarTooltip, createPieTooltip } from '../../../utils/dashboard/tooltips.jsx';

const ChartsLibro = ({
  chartsEntered,
  selectedCat,
  visibleBarData,
  toggleSlice,
  totalActual,
  visibleDonutData,
  donutColorMap,
  hiddenSlices,
  resetSlices,
  legendData,
  formatearNumero
}) => {
  // Tooltips reutilizando fábrica compartida
  const BarTooltipComp = React.useMemo(() => createBarTooltip({
    getTotal: () => totalActual,
    labelValor: 'Monto',
    valueFormatter: v => formatearMonedaChilena(v)
  }), [totalActual]);
  const PieTooltipComp = React.useMemo(() => createPieTooltip({
    getTotal: () => totalActual,
    labelValor: 'Monto',
    valueFormatter: v => formatearMonedaChilena(v)
  }), [totalActual]);
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div className={`bg-gray-900/60 rounded-xl p-4 border border-gray-800 flex flex-col transform transition-all duration-700 ease-out ${chartsEntered ? 'opacity-100 scale-100 translate-y-0' : 'opacity-0 scale-[0.97] translate-y-2'}`}>
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <BarChart3 size={16} className="text-gray-400" />
            <h3 className="text-sm font-medium text-gray-300">{selectedCat ? 'Items de categoría' : 'Totales por categoría'}</h3>
          </div>
        </div>
        <div className="flex-1 h-80">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={visibleBarData} layout="vertical" margin={{ top: 8, right: 16, left: 0, bottom: 8 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
              <XAxis type="number" stroke="#9ca3af" tickFormatter={formatearNumero} tick={{ fontSize: 11 }} />
              <YAxis type="category" dataKey="name" stroke="#9ca3af" width={selectedCat ? 230 : 170} tick={{ fontSize: 11 }} />
              <RTooltip content={<BarTooltipComp />} cursor={{ fill: 'rgba(255,255,255,0.04)' }} wrapperStyle={{ outline: 'none' }} />
              <Bar dataKey="value" radius={[0,6,6,0]} isAnimationActive animationDuration={600} animationEasing="ease-out">
                {visibleBarData.map((entry,i) => {
                  const palette = ['#0d9488','#14b8a6','#2dd4bf','#0ea5e9','#6366f1','#8b5cf6','#d946ef','#f59e0b','#f97316','#f43f5e'];
                  return <Cell key={`bar-${i}`} fill={palette[i % palette.length]} className="cursor-pointer" onClick={() => toggleSlice(entry.name)} />;
                })}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
        {visibleBarData.length === 0 && <div className="text-center text-xs text-gray-500 py-4">No hay elementos visibles. Usa "Mostrar todo".</div>}
        <div className="pt-2 text-xs text-gray-400">Total mostrado: {formatearMonedaChilena(totalActual)}</div>
      </div>
      <div className={`bg-gray-900/60 rounded-xl p-4 border border-gray-800 flex flex-col transform transition-all duration-700 ease-out delay-75 ${chartsEntered ? 'opacity-100 scale-100 translate-y-0' : 'opacity-0 scale-[0.97] translate-y-2'}`}>
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <PieIcon size={16} className="text-gray-400" />
            <h3 className="text-sm font-medium text-gray-300">{selectedCat ? 'Distribución items' : 'Distribución categorías'}</h3>
          </div>
        </div>
        <div className="flex-1 flex items-center justify-center">
          <ResponsiveContainer width="100%" height={selectedCat ? 320 : 300}>
            <PieChart>
              <Pie data={visibleDonutData} dataKey="value" nameKey="name" innerRadius={70} outerRadius={110} paddingAngle={2} labelLine={false} label={false} isAnimationActive animationDuration={600} animationEasing="ease-out">
                {visibleDonutData.map((entry,i) => (
                  <Cell key={`slice-${i}`} fill={donutColorMap[entry.name]} stroke="#0f172a" strokeWidth={1} />
                ))}
              </Pie>
              <RTooltip content={<PieTooltipComp />} wrapperStyle={{ outline: 'none' }} />
            </PieChart>
          </ResponsiveContainer>
        </div>
        <div className="mt-2 text-center text-xs text-gray-400 flex items-center justify-center gap-4">
          <span>Total visible: {formatearMonedaChilena(totalActual)}</span>
          {hiddenSlices.size>0 && (<button onClick={resetSlices} className="text-teal-400 hover:underline">Mostrar todo</button>)}
        </div>
        <div className="mt-3 grid grid-cols-2 gap-2 max-h-48 overflow-auto pr-1 border-t border-gray-800 pt-2">
          {legendData.map(d => {
            const hidden = hiddenSlices.has(d.name);
            const pct = !hidden && totalActual ? ((d.value/totalActual)*100).toFixed(1) : (hidden ? '--' : '0.0');
            return (
              <button type="button" onClick={()=>toggleSlice(d.name)} key={d.name} className={`flex items-center gap-2 text-[11px] w-full text-left rounded px-1 py-0.5 transition-colors border border-transparent ${hidden? 'opacity-40 hover:opacity-70 line-through':'hover:bg-gray-800/60'}`}>
                <span className="w-3 h-3 rounded-sm shrink-0 ring-1 ring-gray-900" style={{ background: donutColorMap[d.name] }} />
                <span className="truncate" title={d.name}>{d.name}</span>
                <span className="text-gray-500 ml-auto tabular-nums">{pct}%</span>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default ChartsLibro;
