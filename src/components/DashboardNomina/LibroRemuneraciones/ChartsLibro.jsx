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
  formatearNumero,
  categoriasChartData,
  categoriasChartDataAnterior,
  conceptosDeCategoriaDataActual,
  conceptosDeCategoriaDataAnterior,
  tieneAnterior
}) => {
  // Estado para énfasis de barras (cuando no hay categoría seleccionada)
  const [barEmphasis, setBarEmphasis] = React.useState('actual'); // 'actual' | 'anterior'
  // Estado dataset donut (selector de cierre)
  const [donutDataset, setDonutDataset] = React.useState('actual');

  // Data comparativa para barras de categorías (solo cuando no hay categoría seleccionada)
  const categoriasComparacion = React.useMemo(() => {
    if (selectedCat || !categoriasChartData) return [];
    if (!tieneAnterior || !categoriasChartDataAnterior) {
      return categoriasChartData.map(d => ({ name: d.name, value_actual: d.value, value_anterior: null }));
    }
    const mapPrev = new Map(categoriasChartDataAnterior.map(d => [d.key, d]));
    return categoriasChartData.map(d => {
      const prev = mapPrev.get(d.key);
      return { name: d.name, key: d.key, value_actual: d.value, value_anterior: prev ? prev.value : 0 };
    });
  }, [selectedCat, categoriasChartData, categoriasChartDataAnterior, tieneAnterior]);

  const activeConceptosBarData = React.useMemo(() => {
    if (!selectedCat) return visibleBarData; // reutiliza actual existente
    if (!tieneAnterior || donutDataset === 'actual') return conceptosDeCategoriaDataActual;
    return conceptosDeCategoriaDataAnterior;
  }, [selectedCat, visibleBarData, tieneAnterior, donutDataset, conceptosDeCategoriaDataActual, conceptosDeCategoriaDataAnterior]);

  const activeDonutData = React.useMemo(() => {
    if (!tieneAnterior) return visibleDonutData; // original
    if (selectedCat) {
      return donutDataset === 'actual' ? conceptosDeCategoriaDataActual : conceptosDeCategoriaDataAnterior;
    }
    // Distribución por categorías
    return donutDataset === 'actual' ? categoriasChartData : categoriasChartDataAnterior;
  }, [tieneAnterior, visibleDonutData, donutDataset, selectedCat, conceptosDeCategoriaDataActual, conceptosDeCategoriaDataAnterior, categoriasChartData, categoriasChartDataAnterior]);

  // Recalcular total para el donut a partir del dataset activo
  const donutTotal = React.useMemo(() => (activeDonutData || []).reduce((a,b)=> a + (b.value||0), 0), [activeDonutData]);

  // Color map se recalcula para dataset activo (evita colores residuales cuando cambia cierre)
  const donutColorMapActive = React.useMemo(() => buildColorMap(activeDonutData), [activeDonutData]);

  function buildColorMap(data){
    const palette = ['#0d9488','#14b8a6','#2dd4bf','#0ea5e9','#6366f1','#8b5cf6','#d946ef','#f59e0b','#f97316','#f43f5e'];
    const map = {};
    data?.forEach((d,i)=> { map[d.name] = palette[i % palette.length]; });
    return map;
  }
  // Tooltips reutilizando fábrica compartida
  const BarTooltipComp = React.useMemo(() => createBarTooltip({
    getTotal: () => totalActual,
    labelValor: 'Monto',
    valueFormatter: v => formatearMonedaChilena(v)
  }), [totalActual]);
  const PieTooltipComp = React.useMemo(() => createPieTooltip({
    getTotal: () => donutTotal,
    labelValor: 'Monto',
    valueFormatter: v => formatearMonedaChilena(v)
  }), [donutTotal]);

  // Tooltip custom para barras comparativas categorías
  const TooltipCategoriasComp = ({ active, payload }) => {
    if (!active || !payload || !payload.length) return null;
    const p = payload[0];
    const data = p.payload;
    const actual = data.value_actual;
    const anterior = data.value_anterior;
    const delta = (anterior ?? null) !== null ? (actual - anterior) : null;
    const pct = anterior && anterior !== 0 ? (delta / anterior) * 100 : null;
    return (
      <div className="bg-gray-900/90 backdrop-blur-sm border border-teal-600/40 rounded-md px-3 py-2 shadow-xl text-xs text-gray-200 space-y-1">
        <div className="font-medium text-white truncate" title={data.name}>{data.name}</div>
        <div className="flex justify-between gap-4"><span className="text-gray-400">Actual</span><span className="tabular-nums font-semibold text-teal-300">{formatearMonedaChilena(actual)}</span></div>
        {anterior !== null && (
          <div className="flex justify-between gap-4"><span className="text-gray-400">Anterior</span><span className="tabular-nums text-gray-300">{formatearMonedaChilena(anterior)}</span></div>
        )}
        {delta !== null && (
          <div className="flex justify-between gap-4 border-t border-gray-700 pt-1">
            <span className="text-gray-400">Δ / Δ%</span>
            <span className={`tabular-nums font-medium ${delta>0?'text-emerald-400':(delta<0?'text-rose-400':'text-gray-400')}`}>{formatearMonedaChilena(delta)}{pct!==null? ` (${pct.toFixed(1)}%)`:''}</span>
          </div>
        )}
      </div>
    );
  };
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* BARRAS */}
      <div className={`bg-gray-900/60 rounded-xl p-4 border border-gray-800 flex flex-col transform transition-all duration-700 ease-out ${chartsEntered ? 'opacity-100 scale-100 translate-y-0' : 'opacity-0 scale-[0.97] translate-y-2'}`}>
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <BarChart3 size={16} className="text-gray-400" />
            <h3 className="text-sm font-medium text-gray-300">{selectedCat ? 'Items de categoría' : 'Totales por categoría'}</h3>
          </div>
          {!selectedCat && tieneAnterior && (
            <div className="flex items-center gap-1 bg-gray-800/60 rounded-md p-1 text-[11px]">
              {['actual','anterior'].map(k => (
                <button key={k} onClick={()=>setBarEmphasis(k)} className={`px-2 py-0.5 rounded ${barEmphasis===k? 'bg-teal-600 text-white':'text-gray-400 hover:text-gray-200'}`}>{k==='actual'?'Actual':'Anterior'}</button>
              ))}
            </div>
          )}
        </div>
        <div className="flex-1 h-80">
          <ResponsiveContainer width="100%" height="100%">
            {(!selectedCat && categoriasComparacion.length) ? (
              <BarChart data={categoriasComparacion} layout="vertical" margin={{ top:8,right:16,left:0,bottom:8 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                <XAxis type="number" stroke="#9ca3af" tickFormatter={formatearNumero} tick={{ fontSize: 11 }} />
                <YAxis type="category" dataKey="name" stroke="#9ca3af" width={170} tick={{ fontSize: 11 }} />
                <RTooltip content={<TooltipCategoriasComp />} cursor={{ fill: 'rgba(255,255,255,0.04)' }} wrapperStyle={{ outline: 'none' }} />
                {barEmphasis==='anterior' && (
                  <Bar dataKey="value_actual" radius={[0,6,6,0]} fill="#14b8a6" fillOpacity={0.25} isAnimationActive animationDuration={600} />
                )}
                <Bar dataKey={barEmphasis==='actual'? 'value_actual':'value_anterior'} radius={[0,6,6,0]} fill={barEmphasis==='actual'? '#14b8a6':'#6366f1'} isAnimationActive animationDuration={600} />
                {barEmphasis==='actual' && tieneAnterior && (
                  <Bar dataKey="value_anterior" radius={[0,6,6,0]} fill="#6366f1" fillOpacity={0.3} isAnimationActive animationDuration={600} />
                )}
              </BarChart>
            ) : (
              <BarChart data={activeConceptosBarData} layout="vertical" margin={{ top:8,right:16,left:0,bottom:8 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                <XAxis type="number" stroke="#9ca3af" tickFormatter={formatearNumero} tick={{ fontSize: 11 }} />
                <YAxis type="category" dataKey="name" stroke="#9ca3af" width={230} tick={{ fontSize: 11 }} />
                <RTooltip content={<BarTooltipComp />} cursor={{ fill: 'rgba(255,255,255,0.04)' }} wrapperStyle={{ outline: 'none' }} />
                <Bar dataKey="value" radius={[0,6,6,0]} isAnimationActive animationDuration={600} animationEasing="ease-out">
                  {activeConceptosBarData.map((entry,i) => {
                    const palette = ['#0d9488','#14b8a6','#2dd4bf','#0ea5e9','#6366f1','#8b5cf6','#d946ef','#f59e0b','#f97316','#f43f5e'];
                    return <Cell key={`bar-${i}`} fill={palette[i % palette.length]} className="cursor-pointer" onClick={() => toggleSlice(entry.name)} />;
                  })}
                </Bar>
              </BarChart>
            )}
          </ResponsiveContainer>
        </div>
        {!selectedCat && categoriasComparacion.length===0 && <div className="text-center text-xs text-gray-500 py-4">Sin datos</div>}
        {selectedCat && activeConceptosBarData.length === 0 && <div className="text-center text-xs text-gray-500 py-4">No hay elementos visibles.</div>}
      </div>
      {/* DONUT */}
      <div className={`bg-gray-900/60 rounded-xl p-4 border border-gray-800 flex flex-col transform transition-all duration-700 ease-out delay-75 ${chartsEntered ? 'opacity-100 scale-100 translate-y-0' : 'opacity-0 scale-[0.97] translate-y-2'}`}>
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <PieIcon size={16} className="text-gray-400" />
            <h3 className="text-sm font-medium text-gray-300">{selectedCat ? 'Distribución items' : 'Distribución categorías'}</h3>
          </div>
          {tieneAnterior && (
            <div className="flex items-center gap-1 bg-gray-800/60 rounded-md p-1 text-[11px]">
              {['actual','anterior'].map(k => (
                <button key={k} onClick={()=>{ setDonutDataset(k); resetSlices(); }} className={`px-2 py-0.5 rounded ${donutDataset===k? 'bg-teal-600 text-white':'text-gray-400 hover:text-gray-200'}`}>{k==='actual'?'Actual':'Anterior'}</button>
              ))}
            </div>
          )}
        </div>
        <div className="flex-1 flex items-center justify-center">
          <ResponsiveContainer width="100%" height={selectedCat ? 320 : 300}>
            <PieChart>
              <Pie data={activeDonutData} dataKey="value" nameKey="name" innerRadius={70} outerRadius={110} paddingAngle={2} labelLine={false} label={false} isAnimationActive animationDuration={600} animationEasing="ease-out">
                {activeDonutData.map((entry,i) => (
                  <Cell key={`slice-${i}`} fill={donutColorMapActive[entry.name]} stroke="#0f172a" strokeWidth={1} />
                ))}
              </Pie>
              <RTooltip content={<PieTooltipComp />} wrapperStyle={{ outline: 'none' }} />
            </PieChart>
          </ResponsiveContainer>
        </div>
        <div className="mt-2 text-center text-xs text-gray-400 flex items-center justify-center gap-4">
          <span>Total visible: {formatearMonedaChilena(donutTotal)}</span>
          {hiddenSlices.size>0 && (<button onClick={resetSlices} className="text-teal-400 hover:underline">Mostrar todo</button>)}
        </div>
        <div className="mt-3 grid grid-cols-2 gap-2 max-h-48 overflow-auto pr-1 border-t border-gray-800 pt-2">
          {activeDonutData.map(d => {
            const hidden = hiddenSlices.has(d.name);
            const pct = !hidden && donutTotal ? ((d.value/donutTotal)*100).toFixed(1) : (hidden ? '--' : '0.0');
            return (
              <button type="button" onClick={()=>toggleSlice(d.name)} key={d.name} className={`flex items-center gap-2 text-[11px] w-full text-left rounded px-1 py-0.5 transition-colors border border-transparent ${hidden? 'opacity-40 hover:opacity-70 line-through':'hover:bg-gray-800/60'}`}>
                <span className="w-3 h-3 rounded-sm shrink-0 ring-1 ring-gray-900" style={{ background: donutColorMapActive[d.name] }} />
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
