import React, { useState, useEffect, useMemo } from 'react';
// Sin cabecera de acordeón en esta tarjeta
import { obtenerLibroResumenV2 } from '../../api/nomina';
import { formatearMonedaChilena } from '../../utils/formatters';
import { buildOrderedColorMap, BASE_PALETTE } from '../../utils/dashboard/colors';

// Reutilizamos los mismos componentes del dashboard original
import TarjetasLibro from '../DashboardNomina/LibroRemuneraciones/TarjetasLibro';
import ChartsLibro from '../DashboardNomina/LibroRemuneraciones/ChartsLibro';
import TablaConceptosLibro from '../DashboardNomina/LibroRemuneraciones/TablaConceptosLibro';
import ComparadorLibro from '../DashboardNomina/LibroRemuneraciones/ComparadorLibro';
import LoadingSkeleton from '../DashboardNomina/common/LoadingSkeleton';
import ErrorState from '../DashboardNomina/common/ErrorState';

function formatearNumero(valor) {
  if (valor === null || valor === undefined) return '0';
  const n = Number(valor);
  if (Number.isNaN(n)) return String(valor);
  return new Intl.NumberFormat('es-CL').format(n);
}

// Contenedor mínimo que renderiza el dashboard del Libro de Remuneraciones
// dentro de la tarjeta de Incidencias, para "ver cómo queda".
const IncidenciasDashboard = ({ cierre, expandido = true, onToggleExpansion }) => {
  const id = cierre?.id;

  // Estado base del dashboard (idéntico al del libro)
  const [resumenV2, setResumenV2] = useState(null);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState('');

  // Tabla conceptos
  const [conceptQuery, setConceptQuery] = useState('');
  const [conceptSort, setConceptSort] = useState({ key: 'total', dir: 'desc' });
  const [conceptPage, setConceptPage] = useState(1);
  const conceptPageSize = 10;

  // Selección categoría / vista
  const [selectedCat, setSelectedCat] = useState('');
  const [dense, setDense] = useState(false);

  // Animación charts
  const [chartsEntered, setChartsEntered] = useState(false);
  const [initialChartsDone, setInitialChartsDone] = useState(false);

  // Comparador
  const [compareSelected, setCompareSelected] = useState(new Set());
  const [compareType, setCompareType] = useState('pie');
  const [compareWarning, setCompareWarning] = useState('');
  const [compareMetric, setCompareMetric] = useState('monto');

  useEffect(() => { cargar(); }, [id]);
  useEffect(() => { setConceptPage(1); }, [conceptQuery, selectedCat]);
  useEffect(() => {
    if (!cargando && !initialChartsDone) {
      const t = setTimeout(() => { setChartsEntered(true); setInitialChartsDone(true); }, 40);
      return () => clearTimeout(t);
    }
  }, [cargando, initialChartsDone]);

  async function cargar() {
    if (!id) {
      setError('Falta id de cierre para cargar el libro.');
      setCargando(false);
      return;
    }
    try {
      setCargando(true);
      const data = await obtenerLibroResumenV2(id);
      setResumenV2(data);
      setError('');
    } catch (e) {
      console.error(e);
      setError('Error al cargar los datos del libro de remuneraciones');
    } finally {
      setCargando(false);
    }
  }

  // Derivados conceptos (idénticos al libro)
  const conceptosData = useMemo(() => resumenV2?.conceptos || [], [resumenV2]);
  const conceptosFiltrados = useMemo(() => {
    if (!selectedCat) return [];
    const q = conceptQuery.trim().toLowerCase();
    return conceptosData.filter(c => c.categoria === selectedCat && (!q || c.nombre.toLowerCase().includes(q)));
  }, [conceptosData, conceptQuery, selectedCat]);
  const conceptosOrdenadosPaginados = useMemo(() => {
    const mult = conceptSort.dir === 'asc' ? 1 : -1;
    const arr = [...conceptosFiltrados].sort((a, b) => {
      if (conceptSort.key === 'name') return a.nombre.localeCompare(b.nombre) * mult;
      return (a.total - b.total) * mult;
    });
    const total = arr.length;
    const pages = Math.max(1, Math.ceil(total / conceptPageSize));
    const page = Math.min(conceptPage, pages);
    const start = (page - 1) * conceptPageSize;
    const end = Math.min(start + conceptPageSize, total);
    return { pageItems: arr.slice(start, end), total, page, pages, start, end };
  }, [conceptosFiltrados, conceptSort, conceptPage, conceptPageSize]);

  // Datos gráficos (idénticos al libro)
  const categoriasChartData = useMemo(() => {
    const t = resumenV2?.totales_categorias || {};
    return [
      { name: 'Haberes Imponibles', key: 'haber_imponible', value: Number(t.haber_imponible || 0) },
      { name: 'Haberes No Imponibles', key: 'haber_no_imponible', value: Number(t.haber_no_imponible || 0) },
      { name: 'Descuentos Legales', key: 'descuento_legal', value: Number(t.descuento_legal || 0) },
      { name: 'Otros Descuentos', key: 'otro_descuento', value: Number(t.otro_descuento || 0) },
      { name: 'Impuestos', key: 'impuesto', value: Number(t.impuesto || 0) },
      { name: 'Aportes Patronales', key: 'aporte_patronal', value: Number(t.aporte_patronal || 0) }
    ];
  }, [resumenV2]);
  const conceptosDeCategoriaData = useMemo(() => {
    if (!selectedCat) return [];
    return conceptosData
      .filter(c => c.categoria === selectedCat)
      .map(c => ({ name: c.nombre, value: Number(c.total || 0) }))
      .sort((a, b) => b.value - a.value);
  }, [conceptosData, selectedCat]);
  const donutData = selectedCat ? conceptosDeCategoriaData : categoriasChartData;
  const filteredDonutData = useMemo(() => donutData.filter(d => d.value !== 0), [donutData]);
  const [hiddenSlices, setHiddenSlices] = useState(() => new Set());
  const visibleDonutData = useMemo(() => filteredDonutData.filter(d => !hiddenSlices.has(d.name)), [filteredDonutData, hiddenSlices]);
  const barBaseData = useMemo(() => donutData.filter(d => d.value !== 0), [donutData]);
  const visibleBarData = useMemo(() => barBaseData.filter(d => !hiddenSlices.has(d.name)), [barBaseData, hiddenSlices]);
  const totalActual = useMemo(() => visibleDonutData.reduce((acc, d) => acc + d.value, 0), [visibleDonutData]);
  const legendData = useMemo(() => [...filteredDonutData].sort((a, b) => b.value - a.value), [filteredDonutData]);
  const donutColorMap = useMemo(() => buildOrderedColorMap(filteredDonutData, 'name', 'value', BASE_PALETTE), [filteredDonutData]);

  function toggleSlice(name) {
    setHiddenSlices(prev => { const next = new Set(prev); if (next.has(name)) next.delete(name); else next.add(name); return next; });
  }
  function resetSlices() { setHiddenSlices(new Set()); }

  // Comparador handlers (idénticos al libro)
  function toggleCompare(nombre) {
    setCompareSelected(prev => {
      const next = new Set(prev);
      if (next.has(nombre)) { next.delete(nombre); return next; }
      if (next.size >= 5) { setCompareWarning('Máximo 5 conceptos para comparar'); setTimeout(() => setCompareWarning(''), 2200); return prev; }
      next.add(nombre); return next;
    });
  }
  function clearCompare() { setCompareSelected(new Set()); }
  const compareData = useMemo(() => {
    if (!selectedCat) return [];
    const base = conceptosFiltrados.filter(c => compareSelected.has(c.nombre));
    return base.map(c => ({ name: c.nombre, value: Number(c.total || 0), empleados: c.empleados }));
  }, [conceptosFiltrados, compareSelected, selectedCat]);
  const compareTotal = useMemo(() => compareData.reduce((a, b) => a + (compareMetric === 'monto' ? b.value : (b.empleados || 0)), 0), [compareData, compareMetric]);

  const formatearMonto = (v) => formatearMonedaChilena(v);

  if (cargando) return <LoadingSkeleton variant="libro" />;
  if (error) return <ErrorState message={error} onBack={() => setError('')} />;

  return (
    <section className="w-full max-w-none px-0 py-0 space-y-8">
      <TarjetasLibro resumen={resumenV2} selectedCat={selectedCat} setSelectedCat={setSelectedCat} formatearMonto={formatearMonto} />
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
        formatearNumero={formatearNumero}
      />
      <div className="flex flex-col lg:flex-row gap-6">
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
          formatearNumero={formatearNumero}
        />
      </div>
    </section>
  );
};

export default IncidenciasDashboard;