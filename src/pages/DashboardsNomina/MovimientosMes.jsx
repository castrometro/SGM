import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { obtenerMovimientosPersonalV3 } from '../../api/nomina';
import { 
  Users, 
  UserPlus, 
  UserMinus,
  Calendar,
  AlertCircle,
  CheckCircle,
  Clock,
  BarChart3,
  ChevronDown
} from 'lucide-react';
import HeaderMovimientos from '../../components/DashboardNomina/Movimientos/HeaderMovimientos';
import TarjetasMetricasMovimientos from '../../components/DashboardNomina/Movimientos/TarjetasMetricasMovimientos';
import DistribucionMovimientosCharts from '../../components/DashboardNomina/Movimientos/DistribucionMovimientosCharts';
import ComparadorMovimientos from '../../components/DashboardNomina/Movimientos/ComparadorMovimientos';
import TablaResumenMovimientos from '../../components/DashboardNomina/Movimientos/TablaResumenMovimientos';
import LoadingSkeleton from '../../components/DashboardNomina/common/LoadingSkeleton';
import ErrorState from '../../components/DashboardNomina/common/ErrorState';
import { ArrowUpDown, ChevronLeft, ChevronRight } from 'lucide-react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RTooltip, PieChart, Pie, Cell } from 'recharts';
import { buildOrderedColorMap, BASE_PALETTE } from '../../utils/dashboard/colors';
import { createBarTooltip, createPieTooltip } from '../../utils/dashboard/tooltips.jsx';
import { prettifyEtiqueta as prettifyEtiquetaUtil } from '../../utils/dashboard/labels';
import { colorClassForEmpleado, colorIndexForEmpleado } from '../../utils/dashboard/colorHash';
import { useMovimientosMetrics } from '../../hooks/dashboard/useMovimientosMetrics';
import { useHiddenSlices } from '../../hooks/dashboard/useHiddenSlices';
// Componente principal
const MovimientosMes = () => {
  // Navegación y params (por ahora no usados directamente, se pueden reutilizar si se restaura fetch real)
  const navigate = useNavigate();
  const { id } = useParams();

  // Estados base de datos / carga
  const [datos, setDatos] = useState(null);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState(null);

  // Estados UI métricas / selección
  const [selectedCard, setSelectedCard] = useState('');
  const [selectedTipo, setSelectedTipo] = useState(null);
  const { hiddenSlices, toggleSlice, resetSlices } = useHiddenSlices();

  // Estados comparador
  const [compareSelected, setCompareSelected] = useState(new Set());
  const [compareType, setCompareType] = useState('pie'); // 'pie' | 'bar'
  const [compareMetric, setCompareMetric] = useState('valor'); // 'valor' | 'empleados'

  // Ref tabla
  const tablaRef = useRef(null);

  // Carga real desde API V3 (con fallback si faltan campos esperados)
  useEffect(() => {
    let cancel = false;
    async function cargar() {
      if (!id) { setCargando(false); return; }
      setCargando(true);
      setError(null);
      try {
        const data = await obtenerMovimientosPersonalV3(id);
        if (cancel) return;
        console.log('🔍 [MovimientosMes] Datos recibidos:', data);
        console.log('🎯 [MovimientosMes] Metadata:', data?._metadata);
        // Intentamos normalizar a la estructura esperada por el componente
        const movimientos = data?.movimientos || data?.detalle || data?.items || [];
        const cierre = data?.cierre || {
          cliente: data?.cliente || null,
          periodo: data?.periodo || null
        };
        // Algunos endpoints podrían entregar métricas pre-calculadas (resumen / ausentismo_metricas / etc.)
        // Si no hay, dejamos objeto vacío; la UI hace fallback a cálculos locales.
        const resumen = data?.resumen || data?.metricas || {};
        setDatos({ movimientos, cierre, resumen, raw: data });
      } catch (e) {
        if (!cancel) setError('No fue posible cargar movimientos');
        console.error('[MovimientosMes] Error fetching movimientos V3:', e);
      } finally {
        if (!cancel) setCargando(false);
      }
    }
    cargar();
    return () => { cancel = true; };
  }, [id]);

  // Movimientos filtrados (filtros eliminados -> todos)
  const movimientosFiltrados = React.useMemo(() => datos?.movimientos || [], [datos]);

            // Métricas tarjetas
            const tarjetasMetrics = useMovimientosMetrics(datos);

  // Helper para formatear etiquetas
  const prettifyEtiqueta = React.useCallback(prettifyEtiquetaUtil, []);

  // Dataset base para gráficos
  const chartBaseData = React.useMemo(() => {
    return [
      { key: 'ingreso', name: 'Ingresos', value: tarjetasMetrics.ingresos, tipo: 'count' },
      { key: 'finiquito', name: 'Finiquitos', value: tarjetasMetrics.finiquitos, tipo: 'count' },
      { key: 'dias_ausencia_justificados', name: 'Días ausencia justificados', value: tarjetasMetrics.diasAusJustificados, tipo: 'dias' },
      { key: 'vacaciones', name: 'Días de vacaciones', value: tarjetasMetrics.vacacionesDias, tipo: 'dias' },
      { key: 'ausencias_sin_justificar', name: 'Ausencias sin justificar', value: tarjetasMetrics.ausSinJustificar, tipo: 'count' },
    ].filter(d => d.value > 0);
  }, [tarjetasMetrics]);

  // Breakdown cuando se selecciona una tarjeta específica
  const selectedBreakdown = React.useMemo(() => {
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
        return Array.from(acc.entries()).map(([k,v]) => ({ key: k, name: prettifyEtiqueta(k), value: v })).sort((a,b)=> b.value - a.value);
      }
      case 'vacaciones': {
        const dias = chartBaseData.find(d=>d.key==='vacaciones')?.value || 0;
        return dias ? [{ key: 'vacaciones', name: 'Vacaciones', value: dias }] : [];
      }
      case 'ausencias_sin_justificar': {
        // Podemos mostrar cada evento como 1 o agrupar por día; aquí se deja un único slice (conteo total)
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
  }, [selectedCard, datos, chartBaseData, prettifyEtiqueta]);

  // Datos efectivos para gráficos (si hay selección usar breakdown; sino dataset base)
  const activeChartData = selectedCard && selectedBreakdown.length ? selectedBreakdown : chartBaseData;
  const visibleChartData = React.useMemo(() => activeChartData.filter(d => !hiddenSlices.has(d.name)), [activeChartData, hiddenSlices]);
  const totalChartVisible = React.useMemo(() => visibleChartData.reduce((a,b)=> a + (b.value||0), 0), [visibleChartData]);

  // Tooltips reutilizando utilidades compartidas
  const BarTooltipMain = React.useMemo(() => createBarTooltip({ getTotal: () => totalChartVisible, labelValor: 'Valor' }), [totalChartVisible]);
  const PieTooltipMain = React.useMemo(() => createPieTooltip({ getTotal: () => totalChartVisible, labelValor: 'Valor' }), [totalChartVisible]);
  // Tooltip para comparador
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

  // Lógica comparador (nivel superior, no dentro de handlers)
  // Paleta jerárquica (oscuro->claro) similar a LibroRemuneraciones
  const colorMapOrdenado = React.useMemo(()=> buildOrderedColorMap(activeChartData, 'key', 'value', BASE_PALETTE), [activeChartData]);
  const compareColorMap = colorMapOrdenado;

  const toggleCompare = (rowKey) => {
    setCompareSelected(prev => {
      const next = new Set(prev);
      if (next.has(rowKey)) next.delete(rowKey); else next.add(rowKey);
      return next;
    });
  };
  const clearCompare = () => setCompareSelected(new Set());
  const compareData = React.useMemo(() => {
    if (!compareSelected.size) return [];
    // Enriquecer filas con conteo de empleados si existe en tarjetasMetrics
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
  const compareTotal = React.useMemo(() => compareData.reduce((acc,d)=> acc + (compareMetric==='valor' ? (d.value||0) : (d.empleados||0)), 0), [compareData, compareMetric]);

  // toggleSlice y resetSlices provienen del hook useHiddenSlices

  // Al hacer click en una tarjeta togglear selección y reiniciar slices
  const handleSelectCard = (key) => {
    setCompareSelected(new Set()); // limpiar comparador al cambiar métrica base
    resetSlices();
    setSelectedCard(prev => prev === key ? '' : key);
    setSelectedTipo(prev => prev === key ? null : key);
  };

  // Paleta y función hash para asignar color por empleado (solo en ausencias/vacaciones)
  const obtenerClaseColorEmpleado = React.useCallback(colorClassForEmpleado, []);
  const obtenerIndiceColorEmpleado = React.useCallback(colorIndexForEmpleado, []);

  const topAusenciasData = React.useMemo(() => {
    const acc = new Map();
    for (const m of datos?.movimientos || []) {
  if (m.categoria !== 'ausencia') continue;
      const rut = m.empleado?.rut || '';
      const name = m.empleado?.nombre || rut || 'Empleado';
  const dias = Number(m.dias_en_periodo ?? m.dias_evento ?? 0);
      const prev = acc.get(rut) || { name, dias: 0 };
      prev.dias += isNaN(dias) ? 0 : dias;
      prev.name = name;
      acc.set(rut, prev);
    }
    return Array.from(acc.values())
      .sort((a, b) => b.dias - a.dias)
      .slice(0, 8)
      .map((o) => ({ name: o.name, dias: o.dias }));
  }, [datos]);

  // Ausentismo por motivo (tipo específico de ausencia)
  const ausentismoPorMotivoData = React.useMemo(() => {
    // Si backend V2 entregó motivos en resumen (ausentismo_metricas.motivos) los usamos directamente
    const motivosBackend = datos?.resumen?.ausentismo_metricas?.motivos;
    if (Array.isArray(motivosBackend) && motivosBackend.length) {
      // Normalizamos claves a name para gráfico
      return motivosBackend.map(m => ({ name: m.motivo, eventos: m.eventos, dias: m.dias }));
    }
    // Fallback cálculo local (V1)
    const acc = new Map();
    for (const m of datos?.movimientos || []) {
      if (m.categoria !== 'ausencia') continue;
      const rawMotivo = (m.motivo || '').trim();
      const key = rawMotivo ? rawMotivo : 'Sin motivo';
      const dias = Number(m.dias_en_periodo ?? m.dias_evento ?? 0);
      const item = acc.get(key) || { name: key, eventos: 0, dias: 0 };
      item.eventos += 1;
      item.dias += isNaN(dias) ? 0 : dias;
      acc.set(key, item);
    }
    const arr = Array.from(acc.values());
    arr.sort((a,b)=> (b.dias - a.dias) || (b.eventos - a.eventos));
    if (arr.length > 12) {
      const top = arr.slice(0,11);
      const rest = arr.slice(11);
      const otros = rest.reduce((o,c)=> { o.eventos += c.eventos; o.dias += c.dias; return o; }, { name: 'Otros', eventos:0, dias:0 });
      top.push(otros);
      return top;
    }
    return arr;
  }, [datos]);

  // Inasistencias por subtipo normalizado (si backend provee 'subtipos'), fallback a por_tipo legacy
  const inasistenciasPorTipoData = React.useMemo(() => {
    const subtipos = datos?.resumen?.ausentismo_metricas?.subtipos;
    if (Array.isArray(subtipos) && subtipos.length) {
      return subtipos.map(s => ({ name: s.subtipo, eventos: s.eventos, dias: s.dias }));
    }
    const tipos = datos?.resumen?.ausentismo_metricas?.por_tipo;
    if (Array.isArray(tipos) && tipos.length) {
      return tipos.map(t => ({ name: t.tipo, eventos: t.eventos, dias: t.dias }));
    }
    // Fallback final: derivar de motivo crudo
    const acc = new Map();
    for (const m of datos?.movimientos || []) {
      if (m.categoria !== 'ausencia') continue;
      const base = (m.subtipo || '').trim() || 'sin_justificar';
      const dias = Number(m.dias_en_periodo ?? m.dias_evento ?? 0) || 0;
      const obj = acc.get(base) || { name: base, eventos: 0, dias: 0 };
      obj.eventos += 1;
      obj.dias += dias;
      acc.set(base, obj);
    }
    return Array.from(acc.values()).sort((a,b)=> b.eventos - a.eventos || b.dias - a.dias);
  }, [datos]);

  const formatearFecha = (fecha) => {
    if (!fecha) return '-';
    return new Date(fecha).toLocaleDateString('es-CL');
  };

  const obtenerIconoTipo = (tipo) => {
    switch (tipo) {
      case 'ingreso':
        return <UserPlus className="w-5 h-5 text-green-500" />;
      case 'finiquito':
        return <UserMinus className="w-5 h-5 text-red-500" />;
  case 'ausencia':
        return <Calendar className="w-5 h-5 text-yellow-500" />;
      case 'reincorporacion':
        return <CheckCircle className="w-5 h-5 text-blue-500" />;
      case 'cambio_datos':
        return <AlertCircle className="w-5 h-5 text-purple-500" />;
      default:
        return <Clock className="w-5 h-5 text-gray-500" />;
    }
  };

  const obtenerColorFondo = (tipo) => {
    switch (tipo) {
      case 'ingreso':
        return 'bg-green-900 border-green-700';
      case 'finiquito':
        return 'bg-red-900 border-red-700';
  case 'ausencia':
        return 'bg-yellow-900 border-yellow-700';
      case 'reincorporacion':
        return 'bg-blue-900 border-blue-700';
      case 'cambio_datos':
        return 'bg-purple-900 border-purple-700';
      default:
        return 'bg-gray-800 border-gray-700';
    }
  };

  // Estilos de badge por tipo (header)
  const tipoBadgeStyles = (tipo) =>
    tipo === 'ingreso'
      ? 'bg-emerald-900/50 text-emerald-300 ring-1 ring-emerald-700/40'
      : tipo === 'finiquito'
      ? 'bg-rose-900/50 text-rose-300 ring-1 ring-rose-700/40'
      : tipo === 'ausentismo'
      ? 'bg-amber-900/50 text-amber-300 ring-1 ring-amber-700/40'
      : tipo === 'reincorporacion'
      ? 'bg-blue-900/50 text-blue-300 ring-1 ring-blue-700/40'
      : 'bg-purple-900/50 text-purple-300 ring-1 ring-purple-700/40';

  if (cargando) return <LoadingSkeleton variant="movimientos" />;
  if (error) return <ErrorState message={error} onBack={()=>navigate(-1)} />;

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <HeaderMovimientos 
        cliente={datos?.cierre?.cliente} 
        periodo={datos?.cierre?.periodo} 
        onBack={()=>navigate(-1)}
        metadata={datos?.raw?._metadata}
      />

      {/* Contenido principal */}
      <div className="w-full px-6 py-6">
  <TarjetasMetricasMovimientos tarjetasMetrics={tarjetasMetrics} selectedCard={selectedCard} handleSelectCard={handleSelectCard} obtenerIconoTipo={obtenerIconoTipo} />
        {/* Gráficos (barras + torta) */}
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
              {hiddenSlices.size>0 && (
                <button onClick={resetSlices} className="text-xs text-teal-400 hover:underline">Mostrar todo</button>
              )}
            </div>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
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
                    <span className="text-gray-500 ml-auto tabular-nums">{pct}%</span>
                  </button>
                );
              })}
            </div>
          </div>
        </div>

  {/* Indicador simple de cantidad (filtros eliminados) */}
  <div className="mb-6 text-sm text-gray-400">Total movimientos: {movimientosFiltrados.length}</div>

        

        {/* Layout tabla + comparador */}
        <div className="flex flex-col lg:flex-row gap-6 mb-8">
          <TablaResumenMovimientos
            tablaRef={tablaRef}
            tarjetasMetrics={tarjetasMetrics}
            selectedCard={selectedCard}
            selectedTipo={selectedTipo}
            setSelectedTipo={setSelectedTipo}
            compareSelected={compareSelected}
            toggleCompare={toggleCompare}
            obtenerIconoTipo={obtenerIconoTipo}
            prettifyEtiqueta={prettifyEtiqueta}
            datos={datos}
            obtenerClaseColorEmpleado={obtenerClaseColorEmpleado}
            obtenerIndiceColorEmpleado={obtenerIndiceColorEmpleado}
          />
          {/* Comparador */}
          <ComparadorMovimientos
            compareSelected={compareSelected}
            compareData={compareData}
            compareType={compareType}
            setCompareType={setCompareType}
            compareMetric={compareMetric}
            setCompareMetric={setCompareMetric}
            clearCompare={clearCompare}
            toggleCompare={toggleCompare}
            compareColorMap={compareColorMap}
            compareTotal={compareTotal}
            CompareTooltip={CompareTooltip}
          />
        </div>

        

        
      </div>
    </div>
  );
};

export default MovimientosMes;
