import React from 'react';
import { ResponsiveContainer, PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RTooltip } from 'recharts';

const ComparadorMovimientos = ({
  compareSelected,
  compareData,
  compareType,
  setCompareType,
  compareMetric,
  setCompareMetric,
  clearCompare,
  toggleCompare,
  compareColorMap,
  compareTotal,
  CompareTooltip
}) => {
  return (
  <div className="bg-gray-900/60 rounded-xl p-6 border border-gray-800 flex-1 min-h-[420px] min-w-[320px] flex flex-col">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-medium text-gray-300">Comparador</h3>
        <div className="flex items-center gap-2">
          <div className="inline-flex rounded-md overflow-hidden border border-gray-700">
            <button onClick={()=>setCompareType('pie')} className={`px-2.5 py-1.5 text-[11px] font-medium ${compareType==='pie'?'bg-teal-600/80 text-white':'bg-gray-800 text-gray-300 hover:bg-gray-700'}`}>Torta</button>
            <button onClick={()=>setCompareType('bar')} className={`px-2.5 py-1.5 text-[11px] font-medium ${compareType==='bar'?'bg-teal-600/80 text-white':'bg-gray-800 text-gray-300 hover:bg-gray-700'}`}>Barras</button>
          </div>
          <div className="inline-flex rounded-md overflow-hidden border border-gray-700">
            <button onClick={()=>setCompareMetric('valor')} className={`px-2.5 py-1.5 text-[11px] font-medium ${compareMetric==='valor'?'bg-indigo-600/80 text-white':'bg-gray-800 text-gray-300 hover:bg-gray-700'}`}>Valor</button>
            <button onClick={()=>setCompareMetric('empleados')} className={`px-2.5 py-1.5 text-[11px] font-medium ${compareMetric==='empleados'?'bg-indigo-600/80 text-white':'bg-gray-800 text-gray-300 hover:bg-gray-700'}`}>Empl.</button>
          </div>
          {compareSelected.size>0 && (
            <button onClick={clearCompare} className="text-xs text-gray-400 hover:text-teal-300 underline">Limpiar</button>
          )}
        </div>
      </div>
      {compareSelected.size===0 && (
        <div className="text-[11px] text-gray-500 mb-2">Usa el botón "Comparar" de la tabla para añadir métricas.</div>
      )}
      {compareSelected.size>0 && compareData.length===0 && (
        <div className="text-[11px] text-gray-500 mb-2">Sin valores.</div>
      )}
      {compareData.length>0 && (
        <div className="flex-1 flex flex-col">
          <div className="flex-1">
            <ResponsiveContainer width="100%" height={compareType==='pie'? 300: 340}>
              {compareType==='pie' ? (
                <PieChart>
                  <Pie data={compareData} dataKey={compareMetric==='valor' ? 'value':'empleados'} nameKey="name" innerRadius={55} outerRadius={100} paddingAngle={2}>
                    {compareData.map((entry)=> (
                      <Cell key={entry.key||entry.name} fill={compareColorMap[entry.key||entry.name]} stroke="#0f172a" strokeWidth={1} onClick={()=> toggleCompare(entry.key||entry.name)} className="cursor-pointer" />
                    ))}
                  </Pie>
                  <RTooltip content={<CompareTooltip />} wrapperStyle={{ outline:'none' }} />
                </PieChart>
              ) : (
                <BarChart data={compareData} layout="vertical" margin={{ top:4, right: 12, left:0, bottom:4 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                  <XAxis type="number" stroke="#9ca3af" tick={{ fontSize: 11 }} />
                  <YAxis type="category" dataKey="name" stroke="#9ca3af" width={150} tick={{ fontSize: 11 }} />
                  <RTooltip content={<CompareTooltip />} cursor={{ fill:'rgba(255,255,255,0.04)'}} wrapperStyle={{ outline:'none' }} />
                  <Bar dataKey={compareMetric==='valor' ? 'value':'empleados'} radius={[0,6,6,0]} isAnimationActive animationDuration={500}>
                    {compareData.map((entry)=> (
                      <Cell key={entry.key||entry.name} fill={compareColorMap[entry.key||entry.name]} onClick={()=> toggleCompare(entry.key||entry.name)} className="cursor-pointer" />
                    ))}
                  </Bar>
                </BarChart>
              )}
            </ResponsiveContainer>
          </div>
          <div className="mt-3 grid grid-cols-1 gap-2 text-[11px] max-h-40 overflow-auto pr-1 border-t border-gray-800 pt-2">
            {compareData.slice().sort((a,b)=> (compareMetric==='valor'? b.value - a.value : (b.empleados||0) - (a.empleados||0))).map(d => {
              const baseVal = compareMetric==='valor'? d.value : (d.empleados||0);
              const pct = compareTotal ? ((baseVal/compareTotal)*100).toFixed(1) : '0.0';
              return (
                <div key={d.key||d.name} className="flex items-center gap-2">
                  <span className="w-3 h-3 rounded-sm ring-1 ring-gray-900 shrink-0" style={{ background: compareColorMap[d.key||d.name] }} />
                  <span className="truncate" title={d.name}>{d.name}</span>
                  <span className="ml-auto tabular-nums text-gray-300">{baseVal}</span>
                  <span className="text-gray-500 w-12 text-right">{pct}%</span>
                </div>
              );
            })}
          </div>
          <div className="pt-2 text-xs text-gray-400">Total comparación: {compareTotal}{compareMetric==='empleados' ? ' empleados' : ''}</div>
        </div>
      )}
    </div>
  );
};

export default ComparadorMovimientos;
