import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { obtenerMovimientosPersonalV3 } from '../../api/nomina';
import { 
  ArrowLeft, 
  Users, 
  UserPlus, 
  UserMinus,
  Calendar,
  Download,
  AlertCircle,
  CheckCircle,
  Clock,
  Sparkles,
  BarChart3,
  ChevronDown
} from 'lucide-react';
import { ArrowUpDown, ChevronLeft, ChevronRight } from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RTooltip,
  PieChart,
  Pie,
  Cell
} from 'recharts';
import { Legend } from 'recharts';
// Comparador inline (eliminamos componente externo)

const MovimientosMes = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  
  const [datos, setDatos] = useState(null);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState('');
  const [sort, setSort] = useState({ key: 'fecha_deteccion', dir: 'desc' });
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [selectedTipo, setSelectedTipo] = useState(null);
  const [tipoEmpSort, setTipoEmpSort] = useState({ key: 'nombre', dir: 'asc' });
  const [tipoEmpPage, setTipoEmpPage] = useState(1);
  const [tipoEmpPageSize, setTipoEmpPageSize] = useState(20);
  const [chartBasis, setChartBasis] = useState('deteccion'); // 'deteccion' | 'movimiento'
  const [ausMotivoMetric, setAusMotivoMetric] = useState('dias'); // 'dias' | 'eventos'
  const [selectedCard, setSelectedCard] = useState(''); // clave de la métrica seleccionada
  const [hiddenSlices, setHiddenSlices] = useState(() => new Set());
  // Estados comparador (similar a LibroRemuneraciones)
  const [compareSelected, setCompareSelected] = useState(new Set()); // Set de keys seleccionadas
  const [compareType, setCompareType] = useState('pie'); // 'pie' | 'bar'
  const [compareMetric, setCompareMetric] = useState('valor'); // 'valor' | 'empleados'
  const tablaRef = useRef(null);

  const scrollToTabla = (tipo = null) => {
    setSelectedTipo(tipo);
    setTipoEmpPage(1);
    if (tablaRef.current) {
      tablaRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  useEffect(() => {
    cargarDatos();
  }, [id]);

  const cargarDatos = async () => {
    try {
      setCargando(true);
  const respuesta = await obtenerMovimientosPersonalV3(id);
      setDatos(respuesta);
    } catch (error) {
      console.error('Error cargando movimientos del mes:', error);
      setError('Error al cargar los movimientos del mes');
    } finally {
      setCargando(false);
    }
  };

  // Sin filtros: usamos todos los movimientos directamente
  const movimientosFiltrados = datos?.movimientos || [];

  // Reset de página al cambiar filtros o sort
  useEffect(() => { setPage(1); }, [sort]);

  // Ordenamiento
  const sortedMovimientos = React.useMemo(() => {
    const arr = [...movimientosFiltrados];
    const mult = sort.dir === 'asc' ? 1 : -1;
    arr.sort((a, b) => {
      switch (sort.key) {
        case 'fecha_movimiento': { // ahora fecha_inicio
          const da = a.fecha_inicio ? new Date(a.fecha_inicio).getTime() : 0;
          const db = b.fecha_inicio ? new Date(b.fecha_inicio).getTime() : 0;
          return (da - db) * mult;
        }
        case 'tipo':
          return (a.categoria || '').localeCompare(b.categoria || '') * mult;
        case 'nombre':
          return (a.empleado?.nombre || '').localeCompare(b.empleado?.nombre || '') * mult;
        case 'fecha_deteccion':
        default: {
          const da = a.fecha_deteccion ? new Date(a.fecha_deteccion).getTime() : 0;
          const db = b.fecha_deteccion ? new Date(b.fecha_deteccion).getTime() : 0;
          return (da - db) * mult;
        }
      }
    });
    return arr;
  }, [movimientosFiltrados, sort]);

  // Paginación
  const total = sortedMovimientos.length;
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const safePage = Math.min(page, totalPages);
  const start = (safePage - 1) * pageSize;
  const end = Math.min(start + pageSize, total);
  const pageItems = sortedMovimientos.slice(start, end);

  // Datos para gráficos
  const tiposChartData = React.useMemo(() => {
    const porCat = datos?.resumen?.por_categoria || datos?.resumen?.por_tipo || {};
    return Object.entries(porCat).map(([key, info]) => ({ name: key, value: Number((info.count) || 0) }));
  }, [datos]);
  const porDiaTipoChartData = React.useMemo(() => {
    const m = new Map();
    const useMovimiento = chartBasis === 'movimiento';
  const tipos = ['ingreso','finiquito','ausencia','cambio_datos'];
    for (const mv of datos?.movimientos || []) {
  const fechaStr = useMovimiento ? (mv.fecha_inicio || mv.fecha_deteccion) : (mv.fecha_deteccion || mv.fecha_inicio);
      const d = fechaStr ? new Date(fechaStr) : null;
      if (!d) continue;
      const k = d.toISOString().slice(0, 10);
      if (!m.has(k)) {
        const base = { date: k };
        for (const t of tipos) base[t] = 0;
        m.set(k, base);
      }
      const obj = m.get(k);
  const t = mv.categoria;
      if (obj[t] === undefined) obj[t] = 0;
      obj[t] += 1;
    }
    return Array.from(m.values())
      .sort((a, b) => a.date.localeCompare(b.date))
      .map((o) => ({ name: new Date(o.date + 'T00:00:00').toLocaleDateString('es-CL'), ...o }));
  }, [datos, chartBasis]);
  const porDiaChartData = React.useMemo(() => {
    const m = new Map();
    const useMovimiento = chartBasis === 'movimiento';
    for (const mv of datos?.movimientos || []) {
      const fechaStr = useMovimiento ? (mv.fecha_movimiento || mv.fecha_deteccion) : (mv.fecha_deteccion || mv.fecha_movimiento);
      const d = fechaStr ? new Date(fechaStr) : null;
      if (!d) continue;
      const k = d.toISOString().slice(0, 10); // YYYY-MM-DD
      m.set(k, (m.get(k) || 0) + 1);
    }
    return Array.from(m.entries())
      .sort((a, b) => a[0].localeCompare(b[0]))
      .map(([k, v]) => ({ name: new Date(k + 'T00:00:00').toLocaleDateString('es-CL'), value: v }));
  }, [datos, chartBasis]);
  const ausentismoKPIs = React.useMemo(() => {
  const lista = (datos?.movimientos || []).filter((m) => m.categoria === 'ausencia');
    let totalDias = 0;
    let eventos = 0;
    for (const m of lista) {
  const dias = Number(m.dias_en_periodo ?? m.dias_evento ?? 0);
      totalDias += isNaN(dias) ? 0 : dias;
      eventos += 1;
    }
    const promedio = eventos > 0 ? Math.round((totalDias / eventos) * 10) / 10 : 0;
    return { totalDias, eventos, promedio };
  }, [datos]);

  // Métricas tarjetas (con días justificados en lugar de conteo de eventos)
  const tarjetasMetrics = React.useMemo(() => {
    const movs = datos?.movimientos || [];
    let ingresos = 0;
    let finiquitos = 0;
    let diasAusJustificados = 0; // suma días ausencias justificadas (excluye vacaciones y sin_justificar)
    let vacacionesDias = 0;      // suma días vacaciones
    let ausSinJustificar = 0;    // conteo eventos sin_justificar
    // Sets para empleados distintos por métrica
    const ingresosSet = new Set();
    const finiquitosSet = new Set();
    const diasAusJustSet = new Set();
    const vacacionesSet = new Set();
    const ausSinJustSet = new Set();
    for (const mv of movs) {
      const cat = mv.categoria;
      const empKey = mv?.empleado ? (mv.empleado.id || mv.empleado.rut || mv.empleado.uuid || mv.empleado.run || null) : null;
      if (cat === 'ingreso') ingresos += 1;
      else if (cat === 'finiquito') finiquitos += 1;
      else if (cat === 'ausencia') {
        const st = (mv.subtipo || '').trim() || 'sin_justificar';
        const dias = Number(mv.dias_en_periodo ?? mv.dias_evento ?? 0) || 0;
        if (st === 'vacaciones') vacacionesDias += dias;
        else if (st === 'sin_justificar') ausSinJustificar += 1;
        else diasAusJustificados += dias;
      }
      // Registrar empleados según corresponda
      if (empKey) {
        if (cat === 'ingreso') ingresosSet.add(empKey);
        else if (cat === 'finiquito') finiquitosSet.add(empKey);
        else if (cat === 'ausencia') {
          const st = (mv.subtipo || '').trim() || 'sin_justificar';
            if (st === 'vacaciones') vacacionesSet.add(empKey);
            else if (st === 'sin_justificar') ausSinJustSet.add(empKey);
            else diasAusJustSet.add(empKey);
        }
      }
    }
    return {
      ingresos,
      finiquitos,
      diasAusJustificados,
      vacacionesDias,
      ausSinJustificar,
      // Conteos de empleados distintos
      ingresosEmp: ingresosSet.size,
      finiquitosEmp: finiquitosSet.size,
      diasAusJustEmp: diasAusJustSet.size,
      vacacionesEmp: vacacionesSet.size,
      ausSinJustEmp: ausSinJustSet.size,
      total: movs.length
    };
  }, [datos]);

  // Dataset base para gráficos (normaliza métricas a un mismo eje "valor")
  const chartBaseData = React.useMemo(() => {
    return [
      { key: 'ingreso', name: 'Ingresos', value: tarjetasMetrics.ingresos, tipo: 'count' },
      { key: 'finiquito', name: 'Finiquitos', value: tarjetasMetrics.finiquitos, tipo: 'count' },
      { key: 'dias_ausencia_justificados', name: 'Días ausencia justificados', value: tarjetasMetrics.diasAusJustificados, tipo: 'dias' },
      { key: 'vacaciones', name: 'Días de vacaciones', value: tarjetasMetrics.vacacionesDias, tipo: 'dias' },
      { key: 'ausencias_sin_justificar', name: 'Ausencias sin justificar', value: tarjetasMetrics.ausSinJustificar, tipo: 'count' },
    ].filter(d => d.value > 0);
  }, [tarjetasMetrics]);

  // Helper para formatear etiquetas (debe estar antes de usar en selectedBreakdown)
  const prettifyEtiqueta = React.useCallback((raw) => {
    if (!raw) return '-';
    const lower = raw.toLowerCase();
    const mapa = {
      'licencia_medica': 'Licencia médica',
      'sin_justificar': 'Sin justificar',
      'vacaciones': 'Vacaciones',
      'cambio_datos': 'Cambio de datos',
      'cambio_contrato': 'Cambio de contrato',
      'cambio_sueldo': 'Cambio de sueldo',
      'reincorporacion': 'Reincorporación',
      'ingreso': 'Ingreso',
      'finiquito': 'Finiquito',
      'ausencia': 'Ausencia',
      'sin_subtipo': 'Sin subtipo'
    };
    if (mapa[lower]) return mapa[lower];
    return lower.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
  }, []);

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

  // Tooltips personalizados (alineados con LibroRemuneraciones)
  const BarTooltipMain = ({ active, payload }) => {
    if (!active || !payload || !payload.length) return null;
    const p = payload[0];
    const valor = p.value || 0;
    const pct = totalChartVisible ? ((valor / totalChartVisible) * 100).toFixed(1) : '0.0';
    return (
      <div className="bg-gray-900/90 backdrop-blur-sm border border-teal-600/40 rounded-md px-3 py-2 shadow-xl text-xs text-gray-200 space-y-1">
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-sm" style={{ background: p.color || '#14b8a6' }} />
          <span className="font-medium text-white max-w-[220px] truncate" title={p.payload?.name}>{p.payload?.name}</span>
        </div>
        <div className="flex justify-between gap-4">
          <span className="text-gray-400">Valor</span>
          <span className="font-semibold tabular-nums text-teal-300">{valor}</span>
        </div>
        <div className="flex justify-between gap-4">
          <span className="text-gray-400">Porcentaje</span>
          <span className="tabular-nums text-gray-300">{pct}%</span>
        </div>
      </div>
    );
  };
  const PieTooltipMain = ({ active, payload }) => {
    if (!active || !payload || !payload.length) return null;
    const p = payload[0];
    const valor = p.value || 0;
    const pct = totalChartVisible ? ((valor / totalChartVisible) * 100).toFixed(1) : '0.0';
    return (
      <div className="bg-gray-900/90 backdrop-blur-sm border border-indigo-600/40 rounded-md px-3 py-2 shadow-xl text-xs text-gray-200 space-y-1">
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-sm" style={{ background: p.color || '#6366f1' }} />
          <span className="font-medium text-white max-w-[200px] truncate" title={p.name}>{p.name}</span>
        </div>
        <div className="flex justify-between gap-4">
          <span className="text-gray-400">Valor</span>
          <span className="font-semibold tabular-nums text-indigo-300">{valor}</span>
        </div>
        <div className="flex justify-between gap-4">
          <span className="text-gray-400">Porcentaje</span>
          <span className="tabular-nums text-gray-300">{pct}%</span>
        </div>
      </div>
    );
  };
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
  const basePalette = React.useMemo(()=>[
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
    '#fde047'  // yellow
  ], []);
  const colorMapOrdenado = React.useMemo(()=>{
    const sorted = [...activeChartData].sort((a,b)=> b.value - a.value);
    const map = {};
    sorted.forEach((d,i)=> { map[d.key || d.name] = basePalette[i] || basePalette[basePalette.length-1]; });
    return map;
  }, [activeChartData, basePalette]);
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

  const toggleSlice = (name) => {
    setHiddenSlices(prev => {
      const next = new Set(prev);
      if (next.has(name)) next.delete(name); else next.add(name);
      return next;
    });
  };
  const resetSlices = () => setHiddenSlices(new Set());

  // Al hacer click en una tarjeta togglear selección y reiniciar slices
  const handleSelectCard = (key) => {
    setCompareSelected(new Set()); // limpiar comparador al cambiar métrica base
    setHiddenSlices(new Set());
    setSelectedCard(prev => prev === key ? '' : key);
    setSelectedTipo(prev => prev === key ? null : key);
  };

  // Paleta y función hash para asignar color por empleado (solo en ausencias/vacaciones)
  const EMP_COLOR_CLASSES = React.useMemo(() => [
    'border-l-teal-500',
    'border-l-emerald-500',
    'border-l-sky-500',
    'border-l-indigo-500',
    'border-l-fuchsia-500',
    'border-l-rose-500',
    'border-l-amber-500',
    'border-l-lime-500',
    'border-l-cyan-500',
    'border-l-orange-500',
  ], []);

  const obtenerClaseColorEmpleado = React.useCallback((empleado) => {
    if (!empleado) return 'border-l-4 border-l-gray-700';
    const key = String(empleado.id || empleado.rut || empleado.uuid || '');
    if (!key) return 'border-l-4 border-l-gray-700';
    let hash = 0;
    for (let i = 0; i < key.length; i++) {
      hash = (hash * 31 + key.charCodeAt(i)) & 0xffffffff;
    }
    const idx = Math.abs(hash) % EMP_COLOR_CLASSES.length;
    return 'border-l-4 ' + EMP_COLOR_CLASSES[idx];
  }, [EMP_COLOR_CLASSES]);

  const obtenerIndiceColorEmpleado = React.useCallback((empleado) => {
    if (!empleado) return -1;
    const key = String(empleado.id || empleado.rut || empleado.uuid || '');
    if (!key) return -1;
    let hash = 0;
    for (let i = 0; i < key.length; i++) {
      hash = (hash * 31 + key.charCodeAt(i)) & 0xffffffff;
    }
    return Math.abs(hash) % EMP_COLOR_CLASSES.length;
  }, [EMP_COLOR_CLASSES]);

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

  if (cargando) {
    return (
      <div className="min-h-screen bg-gray-950 text-white">
        <div className="bg-gradient-to-b from-teal-900/20 to-transparent border-b border-gray-800">
          <div className="max-w-7xl mx-auto px-6 py-6">
            <div className="flex items-center gap-3">
              <div className="h-9 w-9 rounded-lg bg-gray-800 animate-pulse" />
              <div className="space-y-2">
                <div className="h-4 w-56 bg-gray-800 rounded animate-pulse" />
                <div className="h-3 w-40 bg-gray-800 rounded animate-pulse" />
              </div>
            </div>
          </div>
        </div>
        <div className="max-w-7xl mx-auto px-6 py-6 space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="bg-gray-900/60 rounded-xl p-6 border border-gray-800">
                <div className="h-5 w-24 bg-gray-800 rounded animate-pulse mb-4" />
                <div className="h-7 w-32 bg-gray-800 rounded animate-pulse" />
              </div>
            ))}
          </div>
          <div className="bg-gray-900/60 rounded-xl border border-gray-800 overflow-hidden">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="grid grid-cols-6 gap-4 p-4 border-b border-gray-800">
                {[...Array(6)].map((__, j) => (
                  <div key={j} className="h-4 bg-gray-800 rounded animate-pulse" />
                ))}
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="bg-red-600 w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-4">
            <AlertCircle className="text-white" size={24} />
          </div>
          <h3 className="text-xl font-semibold text-white mb-2">Error al cargar</h3>
          <p className="text-gray-400 mb-4">{error}</p>
          <button
            onClick={() => navigate(-1)}
            className="bg-teal-600 hover:bg-teal-700 text-white px-4 py-2 rounded-lg transition-colors"
          >
            Regresar
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* Header con estilo de Libro */}
      <div className="bg-gradient-to-b from-teal-900/20 to-transparent border-b border-gray-800">
        <div className="w-full px-6 py-5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={() => navigate(-1)}
                className="p-2 hover:bg-gray-800 rounded-lg transition-colors border border-gray-800"
                aria-label="Volver"
              >
                <ArrowLeft size={18} />
              </button>
              <div>
                <div className="flex items-center gap-2">
                  <Sparkles className="text-teal-400" size={18} />
                  <h1 className="text-2xl font-bold text-teal-400">Movimientos de Personal</h1>
                </div>
                <p className="text-gray-400">
                  {datos?.cierre?.cliente} · {datos?.cierre?.periodo}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={() => window.print()}
                className="bg-teal-600/90 hover:bg-teal-600 text-white px-4 py-2 rounded-lg font-medium transition-colors transition-transform duration-200 hover:scale-[1.02] flex items-center gap-2 shadow shadow-teal-900/30"
              >
                <Download size={16} />
                Exportar
              </button>
            </div>
          </div>
          {/* Badges removidos junto con buscador/filtros */}
        </div>
      </div>

      {/* Contenido principal */}
      <div className="w-full px-6 py-6">
        {/* Tarjetas métricas normalizadas solicitadas */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
          {/* Ingresos */}
          <div onClick={()=>handleSelectCard('ingreso')} className={`bg-gray-900/60 rounded-xl p-4 border transition-colors duration-200 cursor-pointer ${selectedCard==='ingreso' ? 'border-teal-600 ring-1 ring-teal-600/40' : 'border-gray-800 hover:border-gray-700'}`}>            
            <div className="flex items-center justify-between mb-1">
              {obtenerIconoTipo('ingreso')}
              <span className="text-2xl font-bold text-white">{tarjetasMetrics.ingresos}</span>
            </div>
            <p className="text-sm text-gray-300">Ingresos</p>
          </div>
          {/* Finiquitos */}
          <div onClick={()=>handleSelectCard('finiquito')} className={`bg-gray-900/60 rounded-xl p-4 border transition-colors duration-200 cursor-pointer ${selectedCard==='finiquito' ? 'border-teal-600 ring-1 ring-teal-600/40' : 'border-gray-800 hover:border-gray-700'}`}>            
            <div className="flex items-center justify-between mb-1">
              {obtenerIconoTipo('finiquito')}
              <span className="text-2xl font-bold text-white">{tarjetasMetrics.finiquitos}</span>
            </div>
            <p className="text-sm text-gray-300">Finiquitos</p>
          </div>
          {/* Días de ausencia justificados */}
          <div onClick={()=>handleSelectCard('dias_ausencia_justificados')} className={`bg-gray-900/60 rounded-xl p-4 border transition-colors duration-200 cursor-pointer ${selectedCard==='dias_ausencia_justificados' ? 'border-teal-600 ring-1 ring-teal-600/40' : 'border-gray-800 hover:border-gray-700'}`}>            
            <div className="flex items-center justify-between mb-1">
              <Calendar className="w-5 h-5 text-emerald-400" />
              <span className="text-2xl font-bold text-white">{tarjetasMetrics.diasAusJustificados}</span>
            </div>
            <p className="text-sm text-gray-300">Días ausencia justificados</p>
          </div>
          {/* Vacaciones (días) */}
          <div onClick={()=>handleSelectCard('vacaciones')} className={`bg-gray-900/60 rounded-xl p-4 border transition-colors duration-200 cursor-pointer ${selectedCard==='vacaciones' ? 'border-teal-600 ring-1 ring-teal-600/40' : 'border-gray-800 hover:border-gray-700'}`}>            
            <div className="flex items-center justify-between mb-1">
              <Calendar className="w-5 h-5 text-yellow-400" />
              <span className="text-2xl font-bold text-white">{tarjetasMetrics.vacacionesDias}</span>
            </div>
            <p className="text-sm text-gray-300">Días de vacaciones</p>
          </div>
          {/* Ausencias sin justificar (eventos) */}
          <div onClick={()=>handleSelectCard('ausencias_sin_justificar')} className={`bg-gray-900/60 rounded-xl p-4 border transition-colors duration-200 cursor-pointer ${selectedCard==='ausencias_sin_justificar' ? 'border-teal-600 ring-1 ring-teal-600/40' : 'border-gray-800 hover:border-gray-700'}`}>            
            <div className="flex items-center justify-between mb-1">
              <Calendar className="w-5 h-5 text-red-400" />
              <span className="text-2xl font-bold text-white">{tarjetasMetrics.ausSinJustificar}</span>
            </div>
            <p className="text-sm text-gray-300">Ausencias sin justificar</p>
          </div>
        </div>
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
          {/* Tabla agregada (sin datos de empleado) - ancho reducido similar al libro */}
          <div ref={tablaRef} className="bg-gray-900/60 rounded-xl p-5 border border-gray-800 max-w-4xl flex-shrink-0 w-full lg:w-[840px]">
            <div className="bg-gray-900/60 rounded-xl border border-gray-800 overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-800/80 border-b border-gray-700">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Tipo / Métrica</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-300 uppercase tracking-wider">Valor</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-300 uppercase tracking-wider">Empleados</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-300 uppercase tracking-wider">Comparar</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-800">
                    {(() => {
                      let rows = [
                        { key: 'ingreso', name: 'Ingresos', value: tarjetasMetrics.ingresos, empleados: tarjetasMetrics.ingresosEmp, tipo: 'count' },
                        { key: 'finiquito', name: 'Finiquitos', value: tarjetasMetrics.finiquitos, empleados: tarjetasMetrics.finiquitosEmp, tipo: 'count' },
                        { key: 'dias_ausencia_justificados', name: 'Días ausencia justificados', value: tarjetasMetrics.diasAusJustificados, empleados: tarjetasMetrics.diasAusJustEmp, tipo: 'dias' },
                        { key: 'vacaciones', name: 'Días de vacaciones', value: tarjetasMetrics.vacacionesDias, empleados: tarjetasMetrics.vacacionesEmp, tipo: 'dias' },
                        { key: 'ausencias_sin_justificar', name: 'Ausencias sin justificar', value: tarjetasMetrics.ausSinJustificar, empleados: tarjetasMetrics.ausSinJustEmp, tipo: 'count' },
                      ];
                      if (selectedCard) rows = rows.filter(r=> r.key === selectedCard);
                      if (rows.length === 0) {
                        return (
                          <tr>
                            <td colSpan="4" className="px-4 py-8 text-center text-gray-500">Sin datos</td>
                          </tr>
                        );
                      }
                      return rows.map((r) => (
                        <React.Fragment key={r.key}>
                          <tr
                            className={`group hover:bg-gray-800 cursor-pointer ${selectedTipo === r.key ? 'bg-gray-900 ring-1 ring-teal-700/40' : 'odd:bg-gray-900/20'} transition-colors`}
                            onClick={() => setSelectedTipo(prev => prev === r.key ? null : r.key)}
                          >
                            <td className="px-4 py-3 text-white">
                              <span className="inline-flex items-center gap-2">
                                {obtenerIconoTipo(r.key.includes('ausencia') || r.key==='vacaciones' ? 'ausencia' : (r.key==='ausencias_sin_justificar' ? 'ausencia' : r.key))} {prettifyEtiqueta(r.name.toLowerCase().replace(/\s+/g,'_'))}
                              </span>
                            </td>
                            <td className="px-4 py-3 text-right text-gray-300">{r.value}</td>
                            <td className="px-4 py-3 text-right text-gray-300">{r.empleados ?? '-'}</td>
                            <td className="px-4 py-3 text-right text-gray-300">
                              <button
                                type="button"
                                onClick={(e)=> { e.stopPropagation(); toggleCompare(r.key); }}
                                className={`text-[10px] px-2 py-1 rounded-md border ${compareSelected.has(r.key) ? 'bg-teal-600/30 border-teal-500 text-teal-200' : 'bg-gray-800/50 border-gray-700 text-gray-400 hover:border-gray-600'}`}
                              >{compareSelected.has(r.key) ? 'Quitar' : 'Comparar'}</button>
                            </td>
                          </tr>
                          {selectedTipo === r.key && (
                            <tr>
                              <td colSpan="4" className="px-4 py-3 bg-gray-900/50">
                                <div className="overflow-y-auto max-h-96 rounded-lg border border-gray-800">
                                  <table className="w-full">
                                    <thead className="bg-gray-800/80 border-b border-gray-700 sticky top-0 z-10">
                                      {(() => {
                                        const isIF = r.key === 'ingreso' || r.key === 'finiquito';
                                        if (isIF) return (<tr><th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase">Fecha</th></tr>);
                                        return (
                                          <tr>
                                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase">Categoría/Subtipo</th>
                                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase">Fecha Inicio</th>
                                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase">Fecha Fin</th>
                                            <th className="px-4 py-3 text-right text-xs font-medium text-gray-300 uppercase">Días</th>
                                          </tr>
                                        );
                                      })()}
                                    </thead>
                                    <tbody className="divide-y divide-gray-800">
                                      {(() => {
                                        const base = datos?.movimientos || [];
                                        let eventos = [];
                                        if (r.key === 'ingreso') eventos = base.filter(m => m.categoria === 'ingreso');
                                        else if (r.key === 'finiquito') eventos = base.filter(m => m.categoria === 'finiquito');
                                        else if (r.key === 'vacaciones') eventos = base.filter(m => m.categoria === 'ausencia' && (m.subtipo || '').trim() === 'vacaciones');
                                        else if (r.key === 'ausencias_sin_justificar') eventos = base.filter(m => m.categoria === 'ausencia' && ((m.subtipo || '').trim() === 'sin_justificar' || !(m.subtipo)));
                                        else if (r.key === 'dias_ausencia_justificados') eventos = base.filter(m => m.categoria === 'ausencia' && !['sin_justificar','vacaciones',''].includes((m.subtipo || '').trim()));
                                        const rowsDet = eventos.map(ev => {
                                          const dias = Number(ev.dias_en_periodo ?? ev.dias_evento ?? 0) || 0;
                                          return {
                                            cat: ev.categoria === 'ausencia' ? (ev.subtipo || 'sin_subtipo') : ev.categoria,
                                            fi: ev.fecha_inicio || '-',
                                            ff: ev.fecha_fin || ev.fecha_inicio || '-',
                                            dias,
                                            id: ev.id,
                                            color: (ev.categoria === 'ausencia') ? obtenerClaseColorEmpleado(ev.empleado) : '',
                                            colorIdx: (ev.categoria === 'ausencia') ? obtenerIndiceColorEmpleado(ev.empleado) : 999
                                          };
                                        });
                                        if (rowsDet.length === 0) return (<tr><td colSpan={r.key === 'ingreso' || r.key === 'finiquito' ? 1 : 4} className="px-4 py-6 text-center text-gray-500">Sin eventos</td></tr>);
                                        const isIF = r.key === 'ingreso' || r.key === 'finiquito';
                                        return rowsDet
                                          .sort((a,b)=> a.colorIdx - b.colorIdx || (new Date(a.fi||'1970-01-01') - new Date(b.fi||'1970-01-01')))
                                          .map(rw => {
                                            if (isIF) {
                                              const fecha = rw.fi && rw.fi !== '-' ? new Date(rw.fi).toLocaleDateString('es-CL') : (rw.ff && rw.ff !== '-' ? new Date(rw.ff).toLocaleDateString('es-CL') : '-');
                                              return (<tr key={rw.id} className="hover:bg-gray-800/60"><td className="px-4 py-3 text-white text-sm">{fecha}</td></tr>);
                                            }
                                            return (
                                              <tr key={rw.id} className={`hover:bg-gray-800/60 ${rw.color}`}>
                                                <td className="px-4 py-3 text-white text-sm">{prettifyEtiqueta(rw.cat)}</td>
                                                <td className="px-4 py-3 text-gray-300 text-sm">{rw.fi ? new Date(rw.fi).toLocaleDateString('es-CL') : '-'}</td>
                                                <td className="px-4 py-3 text-gray-300 text-sm">{rw.ff ? new Date(rw.ff).toLocaleDateString('es-CL') : '-'}</td>
                                                <td className="px-4 py-3 text-gray-200 text-sm text-right">{rw.dias}</td>
                                              </tr>
                                            );
                                          });
                                      })()}
                                    </tbody>
                                  </table>
                                </div>
                              </td>
                            </tr>
                          )}
                        </React.Fragment>
                      ));
                    })()}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
          {/* Comparador */}
          {/* Comparador inline estilo Libro - ancho expandido */}
          <div className="bg-gray-900/60 rounded-xl p-5 border border-gray-800 flex-1 min-h-[400px] flex flex-col">
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
                          {compareData.map((entry,i)=> (
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
                          {compareData.map((entry,i)=>(
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
        </div>

        

        
      </div>
    </div>
  );
};

export default MovimientosMes;
