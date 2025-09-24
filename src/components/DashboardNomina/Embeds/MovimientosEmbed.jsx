import React, { useMemo, useRef, useState } from 'react';
import TarjetasMetricasMovimientos from '../../DashboardNomina/Movimientos/TarjetasMetricasMovimientos';
import DistribucionMovimientosCharts from '../../DashboardNomina/Movimientos/DistribucionMovimientosCharts';
import ComparadorMovimientos from '../../DashboardNomina/Movimientos/ComparadorMovimientos';
import TablaResumenMovimientos from '../../DashboardNomina/Movimientos/TablaResumenMovimientos';
import { buildOrderedColorMap, BASE_PALETTE } from '../../../utils/dashboard/colors';
import { createBarTooltip, createPieTooltip } from '../../../utils/dashboard/tooltips.jsx';
import { prettifyEtiqueta as prettifyEtiquetaUtil } from '../../../utils/dashboard/labels';
import { colorClassForEmpleado, colorIndexForEmpleado } from '../../../utils/dashboard/colorHash';

const MovimientosEmbed = ({ bloque }) => {
  if (!bloque) return null;
  const [selectedCard, setSelectedCard] = useState('');
  const [selectedTipo, setSelectedTipo] = useState(null);
  const [compareSelected, setCompareSelected] = useState(new Set());
  const [compareType, setCompareType] = useState('pie');
  const [compareMetric, setCompareMetric] = useState('valor');

  const datos = useMemo(() => ({
    cierre: bloque.cierre,
    resumen: bloque.resumen || {},
    movimientos: bloque.movimientos || [],
  }), [bloque]);

  // Métricas tarjetas (reuso simplificado)
  const tarjetasMetrics = useMemo(() => {
    const res = datos.resumen || {};
    const porTipo = res.por_tipo || {};
    const arr = datos.movimientos || [];
    const countBy = (f) => arr.filter(f).length;
    const diasAus = arr.reduce((acc,m)=> acc + (m.categoria==='ausencia' ? Number(m.dias_en_periodo ?? m.dias_evento ?? 0) : 0), 0);
    return {
      ingresos: porTipo.ingreso?.count ?? countBy(m=>m.categoria==='ingreso'),
      finiquitos: porTipo.finiquito?.count ?? countBy(m=>m.categoria==='finiquito'),
      diasAusJustificados: res.ausentismo_metricas?.total_dias ?? diasAus,
      ausSinJustificar: countBy(m=>m.categoria==='ausencia' && (m.subtipo==='sin_justificar' || m.motivo==='sin_justificar')),
      vacacionesDias: countBy(m=>m.categoria==='ausencia' && m.subtipo==='vacaciones'),
      ingresosEmp: porTipo.ingreso?.empleados_unicos ?? 0,
      finiquitosEmp: porTipo.finiquito?.empleados_unicos ?? 0,
      diasAusJustEmp: 0,
      ausSinJustEmp: 0,
      vacacionesEmp: 0,
    };
  }, [datos]);

  // Dataset base para gráficos
  const chartBaseData = useMemo(() => {
    return [
      { key: 'ingreso', name: 'Ingresos', value: tarjetasMetrics.ingresos, tipo: 'count' },
      { key: 'finiquito', name: 'Finiquitos', value: tarjetasMetrics.finiquitos, tipo: 'count' },
      { key: 'dias_ausencia_justificados', name: 'Días ausencia justificados', value: tarjetasMetrics.diasAusJustificados, tipo: 'dias' },
      { key: 'vacaciones', name: 'Días de vacaciones', value: tarjetasMetrics.vacacionesDias, tipo: 'dias' },
      { key: 'ausencias_sin_justificar', name: 'Ausencias sin justificar', value: tarjetasMetrics.ausSinJustificar, tipo: 'count' },
    ].filter(d => d.value > 0);
  }, [tarjetasMetrics]);

  const hiddenSlicesState = useState(()=> new Set());
  const [hiddenSlices, setHiddenSlices] = hiddenSlicesState;
  const toggleSlice = (name) => setHiddenSlices(prev => { const next=new Set(prev); if (next.has(name)) next.delete(name); else next.add(name); return next; });
  const resetSlices = () => setHiddenSlices(new Set());

  const selectedBreakdown = useMemo(() => {
    if (!selectedCard) return [];
    const movs = datos?.movimientos || [];
    switch (selectedCard) {
      case 'dias_ausencia_justificados': {
        const acc = new Map();
        for (const m of movs) {
          if (m.categoria !== 'ausencia') continue;
          const st = (m.subtipo || '').trim();
          if (!st || st === 'vacaciones' || st === 'sin_justificar') continue;
          const dias = Number(m.dias_en_periodo ?? m.dias_evento ?? 0) || 0;
          acc.set(st, (acc.get(st) || 0) + dias);
        }
        return Array.from(acc.entries()).map(([k,v]) => ({ key: k, name: k, value: v })).sort((a,b)=> b.value - a.value);
      }
      case 'vacaciones': {
        const dias = chartBaseData.find(d=>d.key==='vacaciones')?.value || 0;
        return dias ? [{ key: 'vacaciones', name: 'Vacaciones', value: dias }] : [];
      }
      case 'ausencias_sin_justificar': {
        const v = chartBaseData.find(d=>d.key==='ausencias_sin_justificar')?.value || 0;
        return v ? [{ key: 'ausencias_sin_justificar', name: 'Ausencias sin justificar', value: v }] : [];
      }
      case 'ingreso': {
        const v = chartBaseData.find(d=>d.key==='ingreso')?.value || 0;
        return v ? [{ key: 'ingreso', name: 'Ingresos', value: v }] : [];
      }
      case 'finiquito': {
        const v = chartBaseData.find(d=>d.key==='finiquito')?.value || 0;
        return v ? [{ key: 'finiquito', name: 'Finiquitos', value: v }] : [];
      }
      default:
        return [];
    }
  }, [selectedCard, datos, chartBaseData]);

  const activeChartData = selectedCard && selectedBreakdown.length ? selectedBreakdown : chartBaseData;
  const visibleChartData = useMemo(() => activeChartData.filter(d => !hiddenSlices.has(d.name)), [activeChartData, hiddenSlices]);
  const totalChartVisible = useMemo(() => visibleChartData.reduce((a,b)=> a + (b.value||0), 0), [visibleChartData]);

  const BarTooltipMain = useMemo(() => createBarTooltip({ getTotal: () => totalChartVisible, labelValor: 'Valor' }), [totalChartVisible]);
  const PieTooltipMain = useMemo(() => createPieTooltip({ getTotal: () => totalChartVisible, labelValor: 'Valor' }), [totalChartVisible]);
  const colorMapOrdenado = useMemo(()=> buildOrderedColorMap(activeChartData, 'key', 'value', BASE_PALETTE), [activeChartData]);

  const toggleCompare = (rowKey) => setCompareSelected(prev => { const next=new Set(prev); if (next.has(rowKey)) next.delete(rowKey); else next.add(rowKey); return next; });
  const clearCompare = () => setCompareSelected(new Set());
  const compareData = useMemo(() => {
    if (!compareSelected.size) return [];
    const raw = activeChartData.filter(d => compareSelected.has(d.key || d.name));
    return raw.map(item => {
      let empleados = 0;
      switch (item.key) {
        case 'ingreso': empleados = tarjetasMetrics.ingresosEmp || 0; break;
        case 'finiquito': empleados = tarjetasMetrics.finiquitosEmp || 0; break;
        case 'dias_ausencia_justificados': empleados = tarjetasMetrics.diasAusJustEmp || 0; break;
        case 'vacaciones': empleados = tarjetasMetrics.vacacionesEmp || 0; break;
        case 'ausencias_sin_justificar': empleados = tarjetasMetrics.ausSinJustEmp || 0; break;
        default: break;
      }
      return { ...item, empleados };
    });
  }, [activeChartData, compareSelected, tarjetasMetrics]);
  const compareTotal = useMemo(() => compareData.reduce((acc,d)=> acc + (compareMetric==='valor' ? (d.value||0) : (d.empleados||0)), 0), [compareData, compareMetric]);
  const CompareTooltip = ({ active, payload }) => {
    if (!active || !payload || !payload.length) return null;
    const p = payload[0];
    const raw = p.payload;
    const valor = compareMetric==='valor'? (raw.value||0) : (raw.empleados||0);
    const pct = compareTotal ? ((valor / compareTotal) * 100).toFixed(1) : '0.0';
    return (
      <div className="bg-gray-900/90 backdrop-blur-sm border border-teal-600/40 rounded-md px-3 py-2 shadow-xl text-xs text-gray-200 space-y-1">
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-sm" style={{ background: p.color || '#14b8a6' }} />
          <span className="font-medium text-white max-w-[200px] truncate" title={raw.name}>{raw.name}</span>
        </div>
        <div className="flex justify-between gap-4">
          <span className="text-gray-400">{compareMetric==='valor'? (raw.tipo==='dias'? 'Días':'Eventos') : 'Empleados'}</span>
          <span className="font-semibold tabular-nums text-teal-300">{valor}</span>
        </div>
        <div className="flex justify-between gap-4">
          <span className="text-gray-400">Porcentaje</span>
          <span className="tabular-nums text-gray-300">{pct}%</span>
        </div>
      </div>
    );
  };

  const tablaRef = useRef(null);
  const prettifyEtiqueta = prettifyEtiquetaUtil;
  const obtenerClaseColorEmpleado = colorClassForEmpleado;
  const obtenerIndiceColorEmpleado = colorIndexForEmpleado;

  return (
    <div className="w-full space-y-6">
      <TarjetasMetricasMovimientos tarjetasMetrics={tarjetasMetrics} selectedCard={selectedCard} handleSelectCard={(k)=>{ setCompareSelected(new Set()); resetSlices(); setSelectedCard(prev => prev===k?'':k); setSelectedTipo(prev=> prev===k? null : k); }} obtenerIconoTipo={()=>null} />
      <DistribucionMovimientosCharts
        selectedCard={selectedCard}
        hiddenSlices={hiddenSlices}
        resetSlices={resetSlices}
        visibleChartData={visibleChartData}
        colorMapOrdenado={colorMapOrdenado}
        toggleSlice={toggleSlice}
        totalChartVisible={totalChartVisible}
        activeChartData={activeChartData}
        BarTooltipMain={BarTooltipMain}
        PieTooltipMain={PieTooltipMain}
      />
      <div className="flex flex-col lg:flex-row gap-6 mb-8">
        <TablaResumenMovimientos
          tablaRef={tablaRef}
          tarjetasMetrics={tarjetasMetrics}
          selectedCard={selectedCard}
          selectedTipo={selectedTipo}
          setSelectedTipo={setSelectedTipo}
          compareSelected={compareSelected}
          toggleCompare={toggleCompare}
          obtenerIconoTipo={()=>null}
          prettifyEtiqueta={prettifyEtiqueta}
          datos={datos}
          obtenerClaseColorEmpleado={obtenerClaseColorEmpleado}
          obtenerIndiceColorEmpleado={obtenerIndiceColorEmpleado}
        />
        <ComparadorMovimientos
          compareSelected={compareSelected}
          compareData={compareData}
          compareType={compareType}
          setCompareType={setCompareType}
          compareMetric={compareMetric}
          setCompareMetric={setCompareMetric}
          clearCompare={clearCompare}
          toggleCompare={toggleCompare}
          compareColorMap={buildOrderedColorMap(compareData, 'key', 'value', BASE_PALETTE)}
          compareTotal={compareTotal}
          CompareTooltip={CompareTooltip}
        />
      </div>
    </div>
  );
};

export default MovimientosEmbed;
