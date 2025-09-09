import React, { useState, useEffect, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { obtenerLibroResumenV2 } from '../../api/nomina';
import { formatearMonedaChilena } from '../../utils/formatters';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RTooltip, PieChart, Pie, Cell } from 'recharts';
import { ArrowLeft, Users, DollarSign, Download, BarChart3, PieChart as PieIcon, Search, ArrowUpDown, ChevronLeft, ChevronRight, Sparkles, Calendar, X, Plus } from 'lucide-react';

const CATEGORIAS = ['haber_imponible','haber_no_imponible','descuento_legal','otro_descuento','impuesto','aporte_patronal'];
const CATEGORIA_META = {
  haber_imponible: { label: 'Haberes Imponibles', color: 'text-green-400' },
  haber_no_imponible: { label: 'Haberes No Imponibles', color: 'text-green-400' },
  descuento_legal: { label: 'Descuentos Legales', color: 'text-red-400' },
  otro_descuento: { label: 'Otros Descuentos', color: 'text-red-400' },
  impuesto: { label: 'Impuestos', color: 'text-red-300' },
  aporte_patronal: { label: 'Aportes Patronales', color: 'text-indigo-300' }
};

function formatearNumero(valor) {
  if (valor === null || valor === undefined) return '0';
  const n = Number(valor);
  if (Number.isNaN(n)) return String(valor);
  return new Intl.NumberFormat('es-CL').format(n);
}

const LibroRemuneraciones = () => {
  const { id } = useParams();
  const navigate = useNavigate();

  const [resumenV2, setResumenV2] = useState(null);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState('');
  const [conceptQuery, setConceptQuery] = useState('');
  const [conceptSort, setConceptSort] = useState({ key: 'total', dir: 'desc' });
  const [conceptPage, setConceptPage] = useState(1);
  const conceptPageSize = 10; // fijo máximo 10 por página
  const [selectedCat, setSelectedCat] = useState('');
  const [dense, setDense] = useState(false);
  const [chartsEntered, setChartsEntered] = useState(false);
  const [initialChartsDone, setInitialChartsDone] = useState(false);
  // Comparador
  const [compareSelected, setCompareSelected] = useState(new Set()); // Set de nombres
  const [compareType, setCompareType] = useState('pie'); // 'pie' | 'bar'
  const [compareWarning, setCompareWarning] = useState('');
  const [compareMetric, setCompareMetric] = useState('monto'); // 'monto' | 'empleados'
  const denseClasses = { rowText: dense ? 'text-xs' : 'text-sm', pad: dense ? 'px-3 py-2' : 'px-4 py-3' };

  useEffect(() => { cargar(); }, [id]);
  useEffect(() => { setConceptPage(1); }, [conceptQuery, selectedCat]);
  // Dispara animación de gráficos cuando se completó la carga inicial
  useEffect(() => {
    if (!cargando && !initialChartsDone) {
      const t = setTimeout(()=> { setChartsEntered(true); setInitialChartsDone(true); }, 40);
      return () => clearTimeout(t);
    }
  }, [cargando, initialChartsDone]);

  async function cargar() {
    try {
      setCargando(true);
      const data = await obtenerLibroResumenV2(id);
      setResumenV2(data);
    } catch (e) {
      console.error(e);
      setError('Error al cargar los datos del libro de remuneraciones');
    } finally {
      setCargando(false);
    }
  }

  const conceptosData = useMemo(() => resumenV2?.conceptos || [], [resumenV2]);
  const conceptosFiltrados = useMemo(() => {
    if (!selectedCat) return [];
    const q = conceptQuery.trim().toLowerCase();
    return conceptosData.filter(c => c.categoria === selectedCat && (!q || c.nombre.toLowerCase().includes(q)));
  }, [conceptosData, conceptQuery, selectedCat]);
  const conceptosOrdenadosPaginados = useMemo(() => {
    const mult = conceptSort.dir === 'asc' ? 1 : -1;
    const arr = [...conceptosFiltrados].sort((a,b) => {
      if (conceptSort.key === 'name') return a.nombre.localeCompare(b.nombre) * mult;
      return (a.total - b.total) * mult; // total
    });
    const total = arr.length;
    const pages = Math.max(1, Math.ceil(total / conceptPageSize));
    const page = Math.min(conceptPage, pages);
    const start = (page - 1) * conceptPageSize;
    const end = Math.min(start + conceptPageSize, total);
    return { pageItems: arr.slice(start, end), total, page, pages, start, end };
  }, [conceptosFiltrados, conceptSort, conceptPage, conceptPageSize]);

  // Datos para nuevos gráficos basados en conceptos
  // Datos para gráficos según estado de selección de categoría
  const categoriasChartData = useMemo(() => {
    const t = resumenV2?.totales_categorias || {};
    return [
      { name: 'Haberes Imponibles', key: 'haber_imponible', value: Number(t.haber_imponible||0) },
      { name: 'Haberes No Imponibles', key: 'haber_no_imponible', value: Number(t.haber_no_imponible||0) },
      { name: 'Descuentos Legales', key: 'descuento_legal', value: Number(t.descuento_legal||0) },
      { name: 'Otros Descuentos', key: 'otro_descuento', value: Number(t.otro_descuento||0) },
      { name: 'Impuestos', key: 'impuesto', value: Number(t.impuesto||0) },
      { name: 'Aportes Patronales', key: 'aporte_patronal', value: Number(t.aporte_patronal||0) }
    ];
  }, [resumenV2]);

  const conceptosDeCategoriaData = useMemo(() => {
    if (!selectedCat) return [];
    return conceptosData
      .filter(c => c.categoria === selectedCat)
      .map(c => ({ name: c.nombre, value: Number(c.total||0) }))
      .sort((a,b) => b.value - a.value);
  }, [conceptosData, selectedCat]);

  const donutData = selectedCat ? conceptosDeCategoriaData : categoriasChartData;
  const filteredDonutData = useMemo(()=> donutData.filter(d => d.value !== 0), [donutData]);
  const [hiddenSlices, setHiddenSlices] = useState(() => new Set());
  const visibleDonutData = useMemo(()=> filteredDonutData.filter(d => !hiddenSlices.has(d.name)), [filteredDonutData, hiddenSlices]);
  const barBaseData = useMemo(()=> donutData.filter(d => d.value !== 0), [donutData]); // excluir ceros para no reservar espacio
  const totalActual = useMemo(() => visibleDonutData.reduce((acc,d)=> acc + d.value, 0), [visibleDonutData]);

  // Paleta: colores más oscuros/saturados asignados a valores grandes, tonos más claros a valores pequeños
  const donutColorMap = useMemo(() => {
    const paletteDarkToLight = [
      '#0f766e', // dark teal
      '#0d9488', // teal
      '#0891b2', // cyan
      '#0ea5e9', // sky
      '#1d4ed8', // blue
      '#6366f1', // indigo
      '#7c3aed', // violet
      '#9333ea', // purple
      '#c026d3', // fuchsia
      '#db2777', // rose
      '#f59e0b', // amber
      '#fbbf24', // light amber
      '#fde047'  // yellow (lightest)
    ];
    const sorted = [...filteredDonutData].sort((a,b)=> b.value - a.value); // base estable
    const map = {};
    sorted.forEach((d,i)=> { map[d.name] = paletteDarkToLight[i] || paletteDarkToLight[paletteDarkToLight.length-1]; });
    return map;
  }, [filteredDonutData]);

  const showDonutLabels = false; // ya no mostramos porcentajes dentro de la dona
  const legendData = useMemo(()=> [...filteredDonutData].sort((a,b)=> b.value - a.value), [filteredDonutData]);

  function toggleSlice(name){
    setHiddenSlices(prev => {
      const next = new Set(prev);
      if (next.has(name)) next.delete(name); else next.add(name);
      return next;
    });
  }
  function resetSlices(){ setHiddenSlices(new Set()); }
  // Comparador handlers
  function toggleCompare(nombre){
    setCompareSelected(prev => {
      const next = new Set(prev);
      if (next.has(nombre)) {
        next.delete(nombre);
        return next;
      }
      if (next.size >= 5) {
        setCompareWarning('Máximo 5 conceptos para comparar');
        setTimeout(()=> setCompareWarning(''), 2200);
        return prev; // no agrega
      }
      next.add(nombre);
      return next;
    });
  }
  function clearCompare(){ setCompareSelected(new Set()); }
  const compareData = useMemo(() => {
    if (!selectedCat) return [];
    const base = conceptosFiltrados.filter(c => compareSelected.has(c.nombre));
    return base.map(c => ({ name: c.nombre, value: Number(c.total||0), empleados: c.empleados }));
  }, [conceptosFiltrados, compareSelected, selectedCat]);
  const compareTotal = useMemo(()=> compareData.reduce((a,b)=> a + (compareMetric==='monto'? b.value : (b.empleados||0)), 0), [compareData, compareMetric]);

  const visibleBarData = useMemo(()=> barBaseData.filter(d => !hiddenSlices.has(d.name)), [barBaseData, hiddenSlices]);

  // Tooltips personalizados
  const BarTooltip = ({ active, payload }) => {
    if (!active || !payload || !payload.length) return null;
    const p = payload[0];
    const valor = p.value || 0;
    const pct = totalActual ? ((valor / totalActual) * 100).toFixed(2) : '0.00';
    return (
      <div className="bg-gray-900/90 backdrop-blur-sm border border-teal-700/40 rounded-md px-3 py-2 shadow-xl text-xs text-gray-200 space-y-1">
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-sm" style={{ background: p.color || '#14b8a6' }} />
          <span className="font-medium text-white max-w-[220px] truncate" title={p.payload?.name}>{p.payload?.name}</span>
        </div>
        <div className="flex justify-between gap-4">
          <span className="text-gray-400">Monto</span>
          <span className="font-semibold tabular-nums text-teal-300">{formatearMonedaChilena(valor)}</span>
        </div>
        <div className="flex justify-between gap-4">
          <span className="text-gray-400">Porcentaje</span>
          <span className="tabular-nums text-gray-300">{pct}%</span>
        </div>
      </div>
    );
  };

  const PieTooltip = ({ active, payload }) => {
    if (!active || !payload || !payload.length) return null;
    const p = payload[0];
    const valor = p.value || 0;
    const pct = totalActual ? ((valor / totalActual) * 100).toFixed(2) : '0.00';
    return (
      <div className="bg-gray-900/90 backdrop-blur-sm border border-indigo-600/40 rounded-md px-3 py-2 shadow-xl text-xs text-gray-200 space-y-1">
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-sm" style={{ background: p.color || '#6366f1' }} />
          <span className="font-medium text-white max-w-[200px] truncate" title={p.name}>{p.name}</span>
        </div>
        <div className="flex justify-between gap-4">
          <span className="text-gray-400">Monto</span>
          <span className="font-semibold tabular-nums text-indigo-300">{formatearMonedaChilena(valor)}</span>
        </div>
        <div className="flex justify-between gap-4">
          <span className="text-gray-400">Porcentaje</span>
          <span className="tabular-nums text-gray-300">{pct}%</span>
        </div>
      </div>
    );
  };

  const formatearMonto = (v) => formatearMonedaChilena(v);

  if (cargando) return <div className="p-8 text-gray-300">Cargando libro...</div>;
  if (error) return <div className="p-8 text-red-400">{error}</div>;

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <div className="bg-gradient-to-b from-teal-900/20 to-transparent border-b border-gray-800">
        <div className="w-full px-6 py-5 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button onClick={() => navigate(-1)} className="p-2 hover:bg-gray-800 rounded-lg border border-gray-800" aria-label="Volver">
              <ArrowLeft size={18} />
            </button>
            <div>
              <div className="flex items-center gap-2">
                <Sparkles className="text-teal-400" size={18} />
                <h1 className="text-2xl font-bold text-teal-400">Libro de Remuneraciones</h1>
              </div>
              <p className="text-gray-400">{resumenV2?.cierre?.cliente} · {resumenV2?.cierre?.periodo}</p>
            </div>
          </div>
          <button onClick={() => window.print()} className="bg-teal-600/90 hover:bg-teal-600 text-white px-4 py-2 rounded-lg flex items-center gap-2">
            <Download size={16} /> Exportar
          </button>
        </div>
      </div>

      <div className="w-full px-6 py-6 space-y-8">
        {/* Cards resumen principales */}
        {/* Tarjetas totales unificadas */}
        <div className="flex flex-wrap gap-4">
          <div className="group flex-1 bg-gray-900/60 rounded-lg px-5 py-4 border border-gray-800 hover:border-teal-700/60 transition-colors flex flex-col gap-1">
            <div className="flex items-center justify-between mb-1">
              <p className="text-[11px] font-medium tracking-wide text-gray-400 group-hover:text-teal-300/90 uppercase">Total Empleados</p>
              <Users className="w-5 h-5 text-teal-500" />
            </div>
            <p className="text-2xl font-semibold text-white leading-snug tabular-nums whitespace-nowrap">{resumenV2?.cierre?.total_empleados || 0}</p>
          </div>
          <div className="group flex-1 bg-gray-900/60 rounded-lg px-5 py-4 border border-gray-800 hover:border-teal-700/60 transition-colors flex flex-col gap-1">
            <div className="flex items-center justify-between mb-1">
              <p className="text-[11px] font-medium tracking-wide text-gray-400 group-hover:text-teal-300/90 uppercase">Mes Cierre</p>
              <Calendar className="w-5 h-5 text-teal-500" />
            </div>
            <p className="text-2xl font-semibold text-white leading-snug tabular-nums whitespace-nowrap">
              {(resumenV2?.cierre?.periodo || '').toString().slice(0,7) || '-'}
            </p>
          </div>
          <div onClick={()=>setSelectedCat(prev=> prev==='haber_imponible' ? '' : 'haber_imponible')} className={`group flex-1 cursor-pointer bg-gray-900/60 rounded-lg px-5 py-4 border transition-colors flex flex-col gap-1 ${selectedCat==='haber_imponible' ? 'border-teal-600 ring-1 ring-teal-600/30' : 'border-gray-800 hover:border-teal-700/60'}`}>
            <p className="text-[11px] font-medium tracking-wide text-gray-400 group-hover:text-teal-300/90 uppercase">Haberes Imponibles</p>
            <p className="text-2xl font-semibold text-green-400 leading-snug tabular-nums whitespace-nowrap">{formatearMonto(resumenV2?.totales_categorias?.haber_imponible)}</p>
          </div>
          <div onClick={()=>setSelectedCat(prev=> prev==='haber_no_imponible' ? '' : 'haber_no_imponible')} className={`group flex-1 cursor-pointer bg-gray-900/60 rounded-lg px-5 py-4 border transition-colors flex flex-col gap-1 ${selectedCat==='haber_no_imponible' ? 'border-teal-600 ring-1 ring-teal-600/30' : 'border-gray-800 hover:border-teal-700/60'}`}>
            <p className="text-[11px] font-medium tracking-wide text-gray-400 group-hover:text-teal-300/90 uppercase">Haberes No Imponibles</p>
            <p className="text-2xl font-semibold text-green-400 leading-snug tabular-nums whitespace-nowrap">{formatearMonto(resumenV2?.totales_categorias?.haber_no_imponible)}</p>
          </div>
          <div onClick={()=>setSelectedCat(prev=> prev==='descuento_legal' ? '' : 'descuento_legal')} className={`group flex-1 cursor-pointer bg-gray-900/60 rounded-lg px-5 py-4 border transition-colors flex flex-col gap-1 ${selectedCat==='descuento_legal' ? 'border-teal-600 ring-1 ring-teal-600/30' : 'border-gray-800 hover:border-teal-700/60'}`}>
            <p className="text-[11px] font-medium tracking-wide text-gray-400 group-hover:text-teal-300/90 uppercase">Descuentos Legales</p>
            <p className="text-2xl font-semibold text-red-400 leading-snug tabular-nums whitespace-nowrap">{formatearMonto(resumenV2?.totales_categorias?.descuento_legal)}</p>
          </div>
          <div onClick={()=>setSelectedCat(prev=> prev==='otro_descuento' ? '' : 'otro_descuento')} className={`group flex-1 cursor-pointer bg-gray-900/60 rounded-lg px-5 py-4 border transition-colors flex flex-col gap-1 ${selectedCat==='otro_descuento' ? 'border-teal-600 ring-1 ring-teal-600/30' : 'border-gray-800 hover:border-teal-700/60'}`}>
            <p className="text-[11px] font-medium tracking-wide text-gray-400 group-hover:text-teal-300/90 uppercase">Otros Descuentos</p>
            <p className="text-2xl font-semibold text-red-400 leading-snug tabular-nums whitespace-nowrap">{formatearMonto(resumenV2?.totales_categorias?.otro_descuento)}</p>
          </div>
          <div onClick={()=>setSelectedCat(prev=> prev==='impuesto' ? '' : 'impuesto')} className={`group flex-1 cursor-pointer bg-gray-900/60 rounded-lg px-5 py-4 border transition-colors flex flex-col gap-1 ${selectedCat==='impuesto' ? 'border-teal-600 ring-1 ring-teal-600/30' : 'border-gray-800 hover:border-teal-700/60'}`}>
            <p className="text-[11px] font-medium tracking-wide text-gray-400 group-hover:text-teal-300/90 uppercase">Impuestos</p>
            <p className="text-2xl font-semibold text-red-300 leading-snug tabular-nums whitespace-nowrap">{formatearMonto(resumenV2?.totales_categorias?.impuesto)}</p>
          </div>
          <div onClick={()=>setSelectedCat(prev=> prev==='aporte_patronal' ? '' : 'aporte_patronal')} className={`group flex-1 cursor-pointer bg-gray-900/60 rounded-lg px-5 py-4 border transition-colors flex flex-col gap-1 ${selectedCat==='aporte_patronal' ? 'border-teal-600 ring-1 ring-teal-600/30' : 'border-gray-800 hover:border-teal-700/60'}`}>
            <p className="text-[11px] font-medium tracking-wide text-gray-400 group-hover:text-teal-300/90 uppercase">Aportes Patronales</p>
            <p className="text-2xl font-semibold text-indigo-300 leading-snug tabular-nums whitespace-nowrap">{formatearMonto(resumenV2?.totales_categorias?.aporte_patronal)}</p>
          </div>
        </div>

  {/* (Se unificaron las tarjetas de totales arriba) */}

        {/* Gráficos: categorías vs items de categoría seleccionada */}
  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6"> 
          {/* Barras */}
          <div className={`bg-gray-900/60 rounded-xl p-4 border border-gray-800 flex flex-col transform transition-all duration-700 ease-out ${chartsEntered ? 'opacity-100 scale-100 translate-y-0' : 'opacity-0 scale-[0.97] translate-y-2'}`}> 
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <BarChart3 size={16} className="text-gray-400" />
                <h3 className="text-sm font-medium text-gray-300">
                  {selectedCat ? `Items de ${CATEGORIA_META[selectedCat]?.label}` : 'Totales por categoría'}
                </h3>
              </div>
              {/* Botón de volver removido: ahora toggle directo en tarjetas */}
            </div>
            <div className="flex-1 h-80">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={visibleBarData} layout="vertical" margin={{ top: 8, right: 16, left: 0, bottom: 8 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                  <XAxis type="number" stroke="#9ca3af" tickFormatter={formatearNumero} tick={{ fontSize: 11 }} />
                  <YAxis type="category" dataKey="name" stroke="#9ca3af" width={selectedCat ? 230 : 170} tick={{ fontSize: 11 }} />
                  <RTooltip content={<BarTooltip />} cursor={{ fill: 'rgba(255,255,255,0.04)' }} wrapperStyle={{ outline: 'none' }} />
                  <Bar dataKey="value" radius={[0,6,6,0]} isAnimationActive animationDuration={600} animationEasing="ease-out">
                    {visibleBarData.map((entry,i) => {
                      const palette = ['#0d9488','#14b8a6','#2dd4bf','#0ea5e9','#6366f1','#8b5cf6','#d946ef','#f59e0b','#f97316','#f43f5e'];
                      return <Cell key={`bar-${i}`} fill={palette[i % palette.length]} className="cursor-pointer" onClick={() => toggleSlice(entry.name)} />;
                    })}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
            {visibleBarData.length === 0 && (
              <div className="text-center text-xs text-gray-500 py-4">No hay elementos visibles. Usa "Mostrar todo" para resetear.</div>
            )}
            <div className="pt-2 text-xs text-gray-400">Total mostrado: {formatearMonedaChilena(totalActual)}</div>
          </div>
          {/* Donut */}
          <div className={`bg-gray-900/60 rounded-xl p-4 border border-gray-800 flex flex-col transform transition-all duration-700 ease-out delay-75 ${chartsEntered ? 'opacity-100 scale-100 translate-y-0' : 'opacity-0 scale-[0.97] translate-y-2'}`}> 
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <PieIcon size={16} className="text-gray-400" />
                <h3 className="text-sm font-medium text-gray-300">
                  {selectedCat ? 'Distribución items' : 'Distribución categorías'}
                </h3>
              </div>
              {selectedCat && (<span className="text-xs text-gray-500">{CATEGORIA_META[selectedCat]?.label}</span>)}
            </div>
            <div className="flex-1 flex items-center justify-center">
              <ResponsiveContainer width="100%" height={selectedCat ? 320 : 300}>
                <PieChart>
                  <Pie
                    data={visibleDonutData}
                    dataKey="value"
                    nameKey="name"
                    innerRadius={70}
                    outerRadius={110}
                    paddingAngle={2}
                    labelLine={false}
                    label={false}
                    isAnimationActive
                    animationDuration={600}
                    animationEasing="ease-out"
                  >
                    {visibleDonutData.map((entry,i) => (
                      <Cell key={`slice-${i}`} fill={donutColorMap[entry.name]} stroke="#0f172a" strokeWidth={1} />
                    ))}
                  </Pie>
                  <RTooltip content={<PieTooltip />} wrapperStyle={{ outline: 'none' }} />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="mt-2 text-center text-xs text-gray-400 flex items-center justify-center gap-4">
              <span>Total visible: {formatearMonedaChilena(totalActual)}</span>
              {hiddenSlices.size>0 && (
                <button onClick={resetSlices} className="text-teal-400 hover:underline">Mostrar todo</button>
              )}
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

  {/* Lista detalle + Comparador */}
  <div className="flex flex-col lg:flex-row gap-6">
  <div className="bg-gray-900/60 rounded-xl p-5 border border-gray-800 max-w-4xl flex-shrink-0 w-full lg:w-[840px]">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-gray-300">Detalle de conceptos</h3>
            <div className="flex items-center gap-3">
              <div className="relative w-64 max-w-full">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={14} />
                <input value={conceptQuery} onChange={e=>setConceptQuery(e.target.value)} placeholder="Buscar concepto..." className="w-full pl-9 pr-3 py-2 bg-gray-800/80 border border-gray-700 rounded-lg text-white focus:ring-2 focus:ring-teal-500 text-sm placeholder-gray-500" />
              </div>
              <button onClick={()=>setDense(d=>!d)} className={`text-xs px-3 py-1.5 rounded-full border ${dense? 'bg-teal-600/20 text-teal-300 border-teal-700':'bg-gray-900 text-gray-300 border-gray-700 hover:border-gray-600'}`}>{dense? 'Modo compacto':'Modo cómodo'}</button>
            </div>
          </div>
          {/* Se removieron las tarjetas de filtros por categoría en esta sección */}
          <div className="bg-gray-900/60 rounded-xl border border-gray-800 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-800/80 border-b border-gray-700">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider w-1/2">
                      <button onClick={()=>setConceptSort(s=>({ key:'name', dir: s.key==='name' && s.dir==='asc'?'desc':'asc'}))} className="inline-flex items-center gap-1">Concepto <ArrowUpDown size={12} className="text-gray-400" /></button>
                    </th>
                    <th className="px-2 py-3 text-center text-xs font-medium text-gray-300 uppercase tracking-wider w-1/6">Empleados</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-300 uppercase tracking-wider w-1/3">
                      <button onClick={()=>setConceptSort(s=>({ key:'total', dir: s.key==='total' && s.dir==='asc'?'desc':'asc'}))} className="inline-flex items-center gap-1">Total <ArrowUpDown size={12} className="text-gray-400" /></button>
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-800">
                  {conceptosOrdenadosPaginados.total === 0 ? (
                    <tr>
                      <td colSpan="3" className="px-6 py-8 text-center text-sm text-gray-500">
                        {!selectedCat ? 'Seleccione una categoría en la parte superior para ver sus conceptos.' : 'No hay conceptos que coincidan con el filtro.'}
                      </td>
                    </tr>
                  ) : (
                    <>
                      {conceptosOrdenadosPaginados.pageItems.map(c => {
                        const selected = compareSelected.has(c.nombre);
                        return (
                        <tr key={c.nombre} onClick={()=>toggleCompare(c.nombre)} className={`cursor-pointer ${selected? 'bg-teal-900/30 hover:bg-teal-900/40':'hover:bg-gray-800'} ${dense? 'odd:bg-gray-900/10':'odd:bg-gray-900/20'}`} title={c.empleados>0 ? `${c.empleados} empleados con este concepto` : 'Sin empleados con este concepto'}>
                          <td className={`${denseClasses.pad} ${denseClasses.rowText} text-white flex items-center gap-2`}>{selected && <span className="inline-block w-2 h-2 rounded-full bg-teal-400" />}{c.nombre}</td>
                          <td className={`px-2 ${dense? 'py-2':'py-3'} text-center ${denseClasses.rowText} text-gray-300 tabular-nums`}>{c.empleados>0 ? c.empleados : '-'}</td>
                          <td className={`${denseClasses.pad} text-right ${denseClasses.rowText} text-teal-400 font-medium`}>{formatearMonto(c.total)}</td>
                        </tr>
                      );})}
                      {/* Filas de relleno para mantener altura constante (10) */}
                      {Array.from({ length: Math.max(0, conceptPageSize - conceptosOrdenadosPaginados.pageItems.length) }).map((_,i)=>(
                        <tr key={`filler-${i}`} className={`${dense? 'odd:bg-gray-900/10':'odd:bg-gray-900/20'} invisible`}>
                          <td className={`${denseClasses.pad}`}> </td>
                          <td className={`px-2 ${dense? 'py-2':'py-3'}`}> </td>
                          <td className={`${denseClasses.pad}`}> </td>
                        </tr>
                      ))}
                      <tr>
        <td colSpan="3" className="px-4 py-3">
                          <div className="flex items-center justify-between text-xs text-gray-400">
                            <div>Mostrando {conceptosOrdenadosPaginados.start + 1}-{conceptosOrdenadosPaginados.end} de {conceptosOrdenadosPaginados.total}</div>
                            <div className="flex items-center gap-2">
          <div className="text-gray-500">10 por página</div>
                              <button onClick={()=>setConceptPage(p=>Math.max(1,p-1))} className="px-2 py-1 rounded border border-gray-700 text-gray-300 disabled:opacity-50" disabled={conceptosOrdenadosPaginados.page <= 1}><ChevronLeft size={14} /></button>
                              <button onClick={()=>setConceptPage(p=>p+1)} className="px-2 py-1 rounded border border-gray-700 text-gray-300 disabled:opacity-50" disabled={conceptosOrdenadosPaginados.page >= conceptosOrdenadosPaginados.pages}><ChevronRight size={14} /></button>
                            </div>
                          </div>
                        </td>
                      </tr>
                    </>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
        {/* Comparador */}
        <div className="bg-gray-900/60 rounded-xl p-5 border border-gray-800 flex-1 min-h-[400px] flex flex-col">
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
          {compareWarning && <div className="mb-2 text-[11px] text-amber-400">{compareWarning}</div>}
          {!selectedCat && (
            <div className="text-gray-500 text-xs">Seleccione una categoría para comparar conceptos.</div>
          )}
          {selectedCat && compareSelected.size===0 && (
            <div className="text-gray-500 text-xs">Haz clic en filas de la tabla izquierda para agregarlas al comparador.</div>
          )}
          {selectedCat && compareSelected.size>0 && compareData.length===0 && (
            <div className="text-gray-500 text-xs">Todos los seleccionados tienen valor 0.</div>
          )}
          {compareData.length>0 && (
            <div className="flex-1 flex flex-col">
              <div className="flex-1">
                <ResponsiveContainer width="100%" height={compareType==='pie'? 300: 340}>
                  {compareType==='pie'? (
                    <PieChart>
                      <Pie data={compareData} dataKey={compareMetric==='monto' ? 'value':'empleados'} nameKey="name" innerRadius={60} outerRadius={110} paddingAngle={2}>
                        {compareData.map((entry,i)=>(<Cell key={entry.name} fill={donutColorMap[entry.name] || '#14b8a6'} stroke="#0f172a" strokeWidth={1}/>))}
                      </Pie>
                      <RTooltip wrapperStyle={{ outline:'none' }} content={({active,payload})=>{
                        if(!active||!payload||!payload.length) return null; const p=payload[0];
                        const raw = p.payload; const val = compareMetric==='monto'? raw.value : (raw.empleados||0);
                        const pct = compareTotal? ((val/compareTotal)*100).toFixed(2):'0.00';
                        return (<div className="bg-gray-900/90 backdrop-blur-sm border border-indigo-600/40 rounded-md px-3 py-2 shadow-xl text-xs text-gray-200 space-y-1">
                          <div className="flex items-center gap-2"><span className="w-2.5 h-2.5 rounded-sm" style={{ background:p.color || '#6366f1' }}/><span className="font-medium text-white max-w-[200px] truncate" title={raw.name}>{raw.name}</span></div>
                          <div className="flex justify-between gap-4"><span className="text-gray-400">{compareMetric==='monto'?'Monto':'Empleados'}</span><span className="font-semibold tabular-nums text-indigo-300">{compareMetric==='monto'? formatearMonedaChilena(val): val}</span></div>
                          <div className="flex justify-between gap-4"><span className="text-gray-400">Porcentaje</span><span className="tabular-nums text-gray-300">{pct}%</span></div>
                        </div>);
                      }} />
                    </PieChart>
                  ) : (
                    <BarChart data={compareData} layout="vertical" margin={{ top:4, right: 12, left:0, bottom:4 }}>
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
                  )}
                </ResponsiveContainer>
              </div>
              <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px] max-h-40 overflow-auto pr-1">
                {compareData.sort((a,b)=> (compareMetric==='monto'? b.value - a.value : (b.empleados||0) - (a.empleados||0))).map(d=>{
                  const metricVal = compareMetric==='monto'? d.value : (d.empleados||0);
                  const pct = compareTotal ? ((metricVal/compareTotal)*100).toFixed(1):'0.0';
                  return (
                    <div key={d.name} className="flex items-center gap-2 bg-gray-800/40 rounded px-2 py-1">
                      <span className="w-3 h-3 rounded-sm" style={{ background: donutColorMap[d.name] || '#14b8a6' }} />
          <span className="truncate" title={d.name}>{d.name}</span>
                      {compareMetric==='empleados' && d.empleados>0 && <span className="text-gray-400 text-[10px]">{d.empleados}</span>}
                      {compareMetric==='monto' && <span className="text-gray-400 text-[10px] tabular-nums">{formatearNumero(d.value)}</span>}
                      <span className="ml-auto tabular-nums text-teal-300">{pct}%</span>
                      <button onClick={()=>toggleCompare(d.name)} className="text-gray-500 hover:text-red-400 p-0.5"><X size={12} /></button>
                    </div>
                  );
                })}
              </div>
              <div className="pt-2 text-xs text-gray-400">Total comparación: {compareMetric==='monto'? formatearMonedaChilena(compareTotal): compareTotal + ' empleados'}</div>
            </div>
          )}
        </div>
        </div>
      </div>
    </div>
  );
};

export default LibroRemuneraciones;
