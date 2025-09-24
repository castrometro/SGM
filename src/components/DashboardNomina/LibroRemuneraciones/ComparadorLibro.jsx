import React from 'react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RTooltip, PieChart, Pie, Cell } from 'recharts';
import { X } from 'lucide-react';
import { formatearMonedaChilena } from '../../../utils/formatters';

const ComparadorLibro = ({
  selectedCat,
  compareSelected,
  compareType,
  setCompareType,
  compareMetric,
  setCompareMetric,
  clearCompare,
  compareWarning,
  compareData,
  compareTotal,
  toggleCompare,
  donutColorMap,
  formatearNumero
}) => {
  return (
    <div className="bg-gray-900/60 rounded-xl p-6 border border-gray-800 flex-1 min-h-[420px] min-w-[320px] flex flex-col">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-medium text-gray-300">Comparador</h3>
        <div className="flex items-center gap-2">
          <div className="inline-flex rounded-md overflow-hidden border border-gray-700">
            <button onClick={()=>setCompareType('pie')} className={`px-3 py-1.5 text-xs font-medium ${compareType==='pie'?'bg-teal-600/80 text-white':'bg-gray-800 text-gray-300 hover:bg-gray-700'}`}>Torta</button>
            <button onClick={()=>setCompareType('bar')} className={`px-3 py-1.5 text-xs font-medium ${compareType==='bar'?'bg-teal-600/80 text-white':'bg-gray-800 text-gray-300 hover:bg-gray-700'}`}>Barras</button>
          </div>
          <div className="inline-flex rounded-md overflow-hidden border border-gray-700 ml-1">
            <button onClick={()=>setCompareMetric('monto')} className={`px-2.5 py-1.5 text-[10px] font-medium ${compareMetric==='monto'?'bg-indigo-600/80 text-white':'bg-gray-800 text-gray-300 hover:bg-gray-700'}`}>Monto</button>
            <button onClick={()=>setCompareMetric('empleados')} className={`px-2.5 py-1.5 text-[10px] font-medium ${compareMetric==='empleados'?'bg-indigo-600/80 text-white':'bg-gray-800 text-gray-300 hover:bg-gray-700'}`}>Empl.</button>
          </div>
          {compareSelected.size>0 && <button onClick={clearCompare} className="text-xs text-gray-400 hover:text-teal-300 underline">Limpiar</button>}
        </div>
      </div>
  {compareWarning && <div className="mb-3 text-[11px] text-amber-400">{compareWarning}</div>}
      {!selectedCat && <div className="text-gray-500 text-xs">Seleccione una categoría para comparar conceptos.</div>}
      {selectedCat && compareSelected.size===0 && <div className="text-gray-500 text-xs">Haz clic en filas de la tabla izquierda para agregarlas al comparador.</div>}
      {selectedCat && compareSelected.size>0 && compareData.length===0 && <div className="text-gray-500 text-xs">Todos los seleccionados tienen valor 0.</div>}
      {compareData.length>0 && (
        <div className="flex-1 flex flex-col">
          <div className="flex-1 flex items-center justify-center">
            {compareType==='pie' ? (
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie data={compareData} dataKey={compareMetric==='monto' ? 'value':'empleados'} nameKey="name" innerRadius={60} outerRadius={110} paddingAngle={2}>
                    {compareData.map((entry,i)=>(<Cell key={entry.name} fill={donutColorMap[entry.name] || '#14b8a6'} stroke="#0f172a" strokeWidth={1}/>))}
                  </Pie>
                  <RTooltip wrapperStyle={{ outline:'none' }} content={({active,payload})=>{
                    if(!active||!payload||!payload.length) return null; const p=payload[0]; const raw=p.payload; const val=compareMetric==='monto'? raw.value : (raw.empleados||0); const pct=compareTotal?((val/compareTotal)*100).toFixed(2):'0.00';
                    return (<div className="bg-gray-900/90 backdrop-blur-sm border border-indigo-600/40 rounded-md px-3 py-2 shadow-xl text-xs text-gray-200 space-y-1">
                      <div className="flex items-center gap-2"><span className="w-2.5 h-2.5 rounded-sm" style={{ background:p.color || '#6366f1' }}/><span className="font-medium text-white max-w-[200px] truncate" title={raw.name}>{raw.name}</span></div>
                      <div className="flex justify-between gap-4"><span className="text-gray-400">{compareMetric==='monto'?'Monto':'Empleados'}</span><span className="font-semibold tabular-nums text-indigo-300">{compareMetric==='monto'? formatearMonedaChilena(val): val}</span></div>
                      <div className="flex justify-between gap-4"><span className="text-gray-400">Porcentaje</span><span className="tabular-nums text-gray-300">{pct}%</span></div>
                    </div>);
                  }} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="w-full max-w-[900px] px-2 sm:px-4">
                <ResponsiveContainer width="100%" height={340}>
                  <BarChart data={compareData} layout="vertical" margin={{ top:8, right: 24, left:24, bottom:8 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                    <XAxis type="number" stroke="#9ca3af" tickFormatter={formatearNumero} tick={{ fontSize: 11 }} />
                    <YAxis type="category" dataKey="name" stroke="#9ca3af" width={180} tick={{ fontSize: 11 }} />
                    <RTooltip wrapperStyle={{ outline:'none' }} cursor={{ fill:'rgba(255,255,255,0.04)'}} content={({active,payload})=>{
                      if(!active||!payload||!payload.length) return null; const p=payload[0]; const raw=p.payload; const val=compareMetric==='monto'? raw.value : (raw.empleados||0); const pct=compareTotal?((val/compareTotal)*100).toFixed(2):'0.00';
                      return (<div className="bg-gray-900/90 backdrop-blur-sm border border-teal-700/40 rounded-md px-3 py-2 shadow-xl text-xs text-gray-200 space-y-1">
                        <div className="flex items-center gap-2"><span className="w-2.5 h-2.5 rounded-sm" style={{ background:p.color || '#14b8a6' }} /><span className="font-medium text-white max-w-[220px] truncate" title={raw.name}>{raw.name}</span></div>
                        <div className="flex justify-between gap-4"><span className="text-gray-400">{compareMetric==='monto'?'Monto':'Empleados'}</span><span className="font-semibold tabular-nums text-teal-300">{compareMetric==='monto'? formatearMonedaChilena(val): val}</span></div>
                        <div className="flex justify-between gap-4"><span className="text-gray-400">Porcentaje</span><span className="tabular-nums text-gray-300">{pct}%</span></div>
                      </div>);
                    }} />
                    <Bar dataKey={compareMetric==='monto' ? 'value':'empleados'} radius={[0,6,6,0]} isAnimationActive animationDuration={500}>
                      {compareData.map((entry,i)=>(<Cell key={entry.name} fill={donutColorMap[entry.name] || '#14b8a6'} />))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>
          <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-2.5 text-[11px] max-h-44 overflow-auto pr-1">
            {compareData.sort((a,b)=> (compareMetric==='monto'? b.value - a.value : (b.empleados||0) - (a.empleados||0))).map(d=>{
              const metricVal = compareMetric==='monto'? d.value : (d.empleados||0);
              const pct = compareTotal ? ((metricVal/compareTotal)*100).toFixed(1):'0.0';
              return (
                <div key={d.name} className="flex items-center gap-2 bg-gray-800/40 rounded px-2 py-1">
                  <span className="w-3 h-3 rounded-sm" style={{ background: donutColorMap[d.name] || '#14b8a6' }} />
                  <span className="truncate" title={d.name}>{d.name}</span>
                  {compareMetric==='empleados' && d.empleados>0 && <span className="text-gray-400 text-[10px]">{d.empleados}</span>}
                  {compareMetric==='monto' && <span className="text-gray-400 text-[10px] tabular-nums">{new Intl.NumberFormat('es-CL').format(d.value)}</span>}
                  <span className="ml-auto tabular-nums text-teal-300">{pct}%</span>
                  <button onClick={()=>toggleCompare(d.name)} className="text-gray-500 hover:text-red-400 p-0.5"><X size={12} /></button>
                </div>
              );
            })}
          </div>
          <div className="pt-3 text-xs text-gray-400">Total comparación: {compareMetric==='monto'? formatearMonedaChilena(compareTotal): compareTotal + ' empleados'}</div>
        </div>
      )}
    </div>
  );
};

export default ComparadorLibro;
