import React, { useEffect, useMemo, useState } from 'react';
import TarjetasLibro from '../../DashboardNomina/LibroRemuneraciones/TarjetasLibro';
import TarjetasLibroComparativo from '../../DashboardNomina/LibroRemuneraciones/TarjetasLibroComparativo';
import ChartsLibro from '../../DashboardNomina/LibroRemuneraciones/ChartsLibro';
import TablaConceptosLibro from '../../DashboardNomina/LibroRemuneraciones/TablaConceptosLibro';
import ComparadorLibro from '../../DashboardNomina/LibroRemuneraciones/ComparadorLibro';
import { buildOrderedColorMap, BASE_PALETTE } from '../../../utils/dashboard/colors';

const formatearMoneda = (v) => new Intl.NumberFormat('es-CL').format(Number(v || 0));

// Embed completo del Libro, recibe bloque libro_resumen_v2 ya cargado
const LibroEmbed = ({ resumenV2, resumenAnterior }) => {
  const [selectedCat, setSelectedCat] = useState('');
  const [conceptQuery, setConceptQuery] = useState('');
  const [conceptSort, setConceptSort] = useState({ key: 'total', dir: 'desc' });
  const [conceptPage, setConceptPage] = useState(1);
  const conceptPageSize = 10;
  const [dense, setDense] = useState(false);

  const [chartsEntered, setChartsEntered] = useState(false);
  const [initialChartsDone, setInitialChartsDone] = useState(false);
  useEffect(()=>{
    if (!initialChartsDone) {
      const t = setTimeout(()=> { setChartsEntered(true); setInitialChartsDone(true); }, 40);
      return () => clearTimeout(t);
    }
  }, [initialChartsDone]);

  const [compareSelected, setCompareSelected] = useState(new Set());
  const [compareType, setCompareType] = useState('pie');
  const [compareWarning, setCompareWarning] = useState('');
  const [compareMetric, setCompareMetric] = useState('monto');

  useEffect(()=>{ setConceptPage(1); }, [conceptQuery, selectedCat]);

  if (!resumenV2) return null;

  // Derivados conceptos
  const conceptosData = useMemo(()=> resumenV2?.conceptos || [], [resumenV2]);
  const conceptosFiltrados = useMemo(()=> {
    if (!selectedCat) return [];
    const q = conceptQuery.trim().toLowerCase();
    return conceptosData.filter(c => c.categoria === selectedCat && (!q || c.nombre.toLowerCase().includes(q)));
  }, [conceptosData, conceptQuery, selectedCat]);
  const conceptosOrdenadosPaginados = useMemo(()=> {
    const mult = conceptSort.dir === 'asc' ? 1 : -1;
    const arr = [...conceptosFiltrados].sort((a,b)=> {
      if (conceptSort.key === 'name') return a.nombre.localeCompare(b.nombre)*mult;
      return (a.total - b.total)*mult;
    });
    const total = arr.length;
    const pages = Math.max(1, Math.ceil(total / conceptPageSize));
    const page = Math.min(conceptPage, pages);
    const start = (page - 1) * conceptPageSize;
    const end = Math.min(start + conceptPageSize, total);
    return { pageItems: arr.slice(start,end), total, page, pages, start, end };
  }, [conceptosFiltrados, conceptSort, conceptPage, conceptPageSize]);

  // Datos gráficos
  const categoriasChartData = useMemo(()=> {
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
  const categoriasChartDataAnterior = useMemo(()=> {
    if (!resumenAnterior) return null;
    const t = resumenAnterior?.totales_categorias || {};
    return [
      { name: 'Haberes Imponibles', key: 'haber_imponible', value: Number(t.haber_imponible||0) },
      { name: 'Haberes No Imponibles', key: 'haber_no_imponible', value: Number(t.haber_no_imponible||0) },
      { name: 'Descuentos Legales', key: 'descuento_legal', value: Number(t.descuento_legal||0) },
      { name: 'Otros Descuentos', key: 'otro_descuento', value: Number(t.otro_descuento||0) },
      { name: 'Impuestos', key: 'impuesto', value: Number(t.impuesto||0) },
      { name: 'Aportes Patronales', key: 'aporte_patronal', value: Number(t.aporte_patronal||0) }
    ];
  }, [resumenAnterior]);
  const conceptosDeCategoriaData = useMemo(()=> {
    if (!selectedCat) return [];
    return conceptosData
      .filter(c=> c.categoria === selectedCat)
      .map(c=> ({ name: c.nombre, value: Number(c.total||0) }))
      .sort((a,b)=> b.value - a.value);
  }, [conceptosData, selectedCat]);
  const conceptosDeCategoriaDataAnterior = useMemo(()=> {
    if (!selectedCat || !resumenAnterior) return [];
    const prevConceptos = resumenAnterior?.conceptos || [];
    return prevConceptos
      .filter(c=> c.categoria === selectedCat)
      .map(c=> ({ name: c.nombre, value: Number(c.total||0) }))
      .sort((a,b)=> b.value - a.value);
  }, [resumenAnterior, selectedCat]);
  const donutData = selectedCat ? conceptosDeCategoriaData : categoriasChartData;
  const filteredDonutData = useMemo(()=> donutData.filter(d=> d.value !== 0), [donutData]);
  const [hiddenSlices, setHiddenSlices] = useState(()=> new Set());
  const visibleDonutData = useMemo(()=> filteredDonutData.filter(d=> !hiddenSlices.has(d.name)), [filteredDonutData, hiddenSlices]);
  const barBaseData = useMemo(()=> donutData.filter(d=> d.value !==0), [donutData]);
  const visibleBarData = useMemo(()=> barBaseData.filter(d=> !hiddenSlices.has(d.name)), [barBaseData, hiddenSlices]);
  const totalActual = useMemo(()=> visibleDonutData.reduce((acc,d)=> acc + d.value, 0), [visibleDonutData]);
  const legendData = useMemo(()=> [...filteredDonutData].sort((a,b)=> b.value - a.value), [filteredDonutData]);
  const donutColorMap = useMemo(()=> buildOrderedColorMap(filteredDonutData, 'name', 'value', BASE_PALETTE), [filteredDonutData]);

  function toggleSlice(name){
    setHiddenSlices(prev => { const next=new Set(prev); if (next.has(name)) next.delete(name); else next.add(name); return next; });
  }
  function resetSlices(){ setHiddenSlices(new Set()); }

  function toggleCompare(nombre){
    setCompareSelected(prev => {
      const next = new Set(prev);
      if (next.has(nombre)) { next.delete(nombre); return next; }
      if (next.size >= 5) { setCompareWarning('Máximo 5 conceptos para comparar'); setTimeout(()=> setCompareWarning(''), 2200); return prev; }
      next.add(nombre); return next;
    });
  }
  function clearCompare(){ setCompareSelected(new Set()); }
  const compareData = useMemo(()=> {
    if (!selectedCat) return [];
    const base = conceptosFiltrados.filter(c=> compareSelected.has(c.nombre));
    return base.map(c=> ({ name: c.nombre, value: Number(c.total||0), empleados: c.empleados }));
  }, [conceptosFiltrados, compareSelected, selectedCat]);
  const compareTotal = useMemo(()=> compareData.reduce((a,b)=> a + (compareMetric==='monto' ? b.value : (b.empleados||0)),0), [compareData, compareMetric]);

  return (
    <div className="w-full space-y-6">
      {resumenAnterior ? (
        <TarjetasLibroComparativo actual={resumenV2} anterior={resumenAnterior} selectedCat={selectedCat} setSelectedCat={setSelectedCat} />
      ) : (
        <TarjetasLibro resumen={resumenV2} selectedCat={selectedCat} setSelectedCat={setSelectedCat} formatearMonto={formatearMoneda} />
      )}
      <ChartsLibro
        chartsEntered={chartsEntered}
        selectedCat={selectedCat}
        visibleBarData={visibleBarData}
        toggleSlice={toggleSlice}
        totalActual={totalActual}
        visibleDonutData={visibleDonutData}
        donutColorMap={donutColorMap}
        hiddenSlices={hiddenSlices}
        resetSlices={resetSlices}
        legendData={legendData}
        formatearNumero={(v)=>new Intl.NumberFormat('es-CL').format(Number(v||0))}
        categoriasChartData={categoriasChartData}
        categoriasChartDataAnterior={categoriasChartDataAnterior}
        conceptosDeCategoriaDataActual={conceptosDeCategoriaData}
        conceptosDeCategoriaDataAnterior={conceptosDeCategoriaDataAnterior}
        tieneAnterior={!!resumenAnterior}
      />
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 lg:gap-8 xl:gap-10">
        <TablaConceptosLibro
          conceptosOrdenadosPaginados={conceptosOrdenadosPaginados}
          conceptQuery={conceptQuery}
          setConceptQuery={setConceptQuery}
          dense={dense}
          setDense={setDense}
          conceptSort={conceptSort}
          setConceptSort={setConceptSort}
          conceptPageSize={conceptPageSize}
          setConceptPage={setConceptPage}
          compareSelected={compareSelected}
          toggleCompare={toggleCompare}
          selectedCat={selectedCat}
          resumenAnterior={resumenAnterior}
          resumenActual={resumenV2}
          allowReclasificar={false}
        />
        <ComparadorLibro
          selectedCat={selectedCat}
          compareSelected={compareSelected}
          compareType={compareType}
          setCompareType={setCompareType}
          compareMetric={compareMetric}
          setCompareMetric={setCompareMetric}
          clearCompare={clearCompare}
          compareWarning={compareWarning}
          compareData={compareData}
          compareTotal={compareTotal}
          toggleCompare={toggleCompare}
          donutColorMap={donutColorMap}
          formatearNumero={(v)=>new Intl.NumberFormat('es-CL').format(Number(v||0))}
        />
      </div>
    </div>
  );
};

export default LibroEmbed;
