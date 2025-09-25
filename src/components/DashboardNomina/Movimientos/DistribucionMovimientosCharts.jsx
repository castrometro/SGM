import React from 'react';
import { BarChart3 } from 'lucide-react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RTooltip, PieChart, Pie, Cell } from 'recharts';

const DistribucionMovimientosCharts = ({
  selectedCard,
  hiddenSlices,
  resetSlices,
  visibleChartData,
  colorMapOrdenado,
  toggleSlice,
  totalChartVisible,
  activeChartData,
  BarTooltipMain,
  PieTooltipMain,
  comparacionBarras,
  barEmphasis,
  setBarEmphasis,
  tieneAnterior,
  pieDataset,
  setPieDataset
}) => {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-10">
      {/* Barras */}
      <div className="bg-gray-900/60 rounded-xl p-4 border border-gray-800 flex flex-col">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <BarChart3 size={16} className="text-gray-400" />
            <h3 className="text-sm font-medium text-gray-300">
              {selectedCard ? 'Detalle seleccionado' : 'Distribución general'}
            </h3>
          </div>
          {!selectedCard && tieneAnterior && comparacionBarras && (
            <div className="flex items-center gap-1 bg-gray-800/60 rounded-md p-1 text-[11px]">
              {['actual','anterior'].map(k => (
                <button key={k} onClick={()=>setBarEmphasis(k)} className={`px-2 py-0.5 rounded ${barEmphasis===k? 'bg-teal-600 text-white':'text-gray-400 hover:text-gray-200'}`}>{k==='actual' ? 'Actual':'Anterior'}</button>
              ))}
            </div>
          )}
          {hiddenSlices.size>0 && (
            <button onClick={resetSlices} className="text-xs text-teal-400 hover:underline">Mostrar todo</button>
          )}
        </div>
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            {(!selectedCard && comparacionBarras) ? (
              <BarChart data={comparacionBarras} layout="vertical" margin={{ top: 8, right: 16, left: 0, bottom: 8 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                <XAxis type="number" stroke="#9ca3af" tick={{ fontSize: 11 }} />
                <YAxis type="category" dataKey="name" stroke="#9ca3af" width={210} tick={{ fontSize: 11 }} />
                <RTooltip content={<BarTooltipMain />} cursor={{ fill: 'rgba(255,255,255,0.04)' }} wrapperStyle={{ outline:'none' }} />
                {barEmphasis==='anterior' && (
                  <Bar dataKey="value_actual" radius={[0,6,6,0]} fill="#14b8a6" fillOpacity={0.25} />
                )}
                <Bar dataKey={barEmphasis==='actual'? 'value_actual':'value_anterior'} radius={[0,6,6,0]} fill={barEmphasis==='actual'? '#14b8a6':'#6366f1'} />
                {barEmphasis==='actual' && (
                  <Bar dataKey="value_anterior" radius={[0,6,6,0]} fill="#6366f1" fillOpacity={0.3} />
                )}
              </BarChart>
            ) : (
              <BarChart data={visibleChartData} layout="vertical" margin={{ top: 8, right: 16, left: 0, bottom: 8 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                <XAxis type="number" stroke="#9ca3af" tick={{ fontSize: 11 }} />
                <YAxis type="category" dataKey="name" stroke="#9ca3af" width={210} tick={{ fontSize: 11 }} />
                <RTooltip content={<BarTooltipMain />} cursor={{ fill: 'rgba(255,255,255,0.04)' }} wrapperStyle={{ outline:'none' }} />
                <Bar dataKey="value" radius={[0,6,6,0]}>
                  {visibleChartData
                    .sort((a,b)=> b.value - a.value)
                    .map((entry,i) => (
                      <Cell key={`bar-${entry.key||i}`} fill={colorMapOrdenado[entry.key||entry.name]} className="cursor-pointer" onClick={() => toggleSlice(entry.name)} />
                    ))}
                </Bar>
              </BarChart>
            )}
          </ResponsiveContainer>
        </div>
        <div className="pt-2 text-xs text-gray-400">Total visible: {totalChartVisible}</div>
      </div>
      {/* Torta */}
      <div className="bg-gray-900/60 rounded-xl p-4 border border-gray-800 flex flex-col">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <BarChart3 size={16} className="text-gray-400" />
            <h3 className="text-sm font-medium text-gray-300">{selectedCard ? 'Porción seleccionada' : 'Distribución porcentual'}</h3>
          </div>
          {tieneAnterior && (
            <div className="flex items-center gap-1 bg-gray-800/60 rounded-md p-1 text-[11px]">
              {['actual','anterior'].map(k => (
                <button key={k} onClick={() => { setPieDataset(k); resetSlices(); }} className={`px-2 py-0.5 rounded ${pieDataset===k? 'bg-teal-600 text-white':'text-gray-400 hover:text-gray-200'}`}>{k==='actual'? 'Actual':'Anterior'}</button>
              ))}
            </div>
          )}
        </div>
        <div className="flex-1 flex items-center justify-center">
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie data={visibleChartData} dataKey="value" nameKey="name" innerRadius={70} outerRadius={110} paddingAngle={2} labelLine={false} label={false}>
                {visibleChartData
                  .sort((a,b)=> b.value - a.value)
                  .map((entry,i) => (
                    <Cell key={`slice-${entry.key||i}`} fill={colorMapOrdenado[entry.key||entry.name]} stroke="#0f172a" strokeWidth={1} onClick={()=>toggleSlice(entry.name)} className="cursor-pointer" />
                  ))}
              </Pie>
              <RTooltip content={<PieTooltipMain />} wrapperStyle={{ outline:'none' }} />
            </PieChart>
          </ResponsiveContainer>
        </div>
        <div className="mt-2 text-center text-xs text-gray-400 flex items-center justify-center gap-4">
          <span>Total visible: {totalChartVisible}</span>
          {hiddenSlices.size>0 && (
            <button onClick={resetSlices} className="text-teal-400 hover:underline">Mostrar todo</button>
          )}
        </div>
        <div className="mt-3 grid grid-cols-2 gap-2 max-h-44 overflow-auto pr-1 border-t border-gray-800 pt-2">
          {activeChartData.slice().sort((a,b)=> b.value - a.value).map(d => {
            const hidden = hiddenSlices.has(d.name);
            const pct = !hidden && totalChartVisible ? ((d.value/totalChartVisible)*100).toFixed(1) : (hidden ? '--' : '0.0');
            return (
              <button type="button" onClick={()=>toggleSlice(d.name)} key={d.name} className={`flex items-center gap-2 text-[11px] w-full text-left rounded px-1 py-0.5 transition-colors border border-transparent ${hidden? 'opacity-40 hover:opacity-70 line-through':'hover:bg-gray-800/60'}`}>
                <span className="w-3 h-3 rounded-sm shrink-0 ring-1 ring-gray-900" style={{ background: colorMapOrdenado[d.key||d.name] }} />
                <span className="truncate" title={d.name}>{d.name}</span>
                <span className="ml-auto tabular-nums text-gray-300">{pct}%</span>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default DistribucionMovimientosCharts;
