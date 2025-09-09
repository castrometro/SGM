import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { obtenerMovimientosMes } from '../../api/nomina';
import { 
  ArrowLeft, 
  Users, 
  UserPlus, 
  UserMinus,
  Calendar,
  Search,
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
  Tooltip as RTooltip
} from 'recharts';
import { Legend } from 'recharts';

const MovimientosMes = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  
  const [datos, setDatos] = useState(null);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState('');
  const [filtros, setFiltros] = useState({
    busqueda: '',
    tipo: 'todos',
    fechaDesde: '',
    fechaHasta: ''
  });
  const [sort, setSort] = useState({ key: 'fecha_deteccion', dir: 'desc' });
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [selectedTipo, setSelectedTipo] = useState(null);
  const [tipoQuery, setTipoQuery] = useState('');
  const [tipoEmpSort, setTipoEmpSort] = useState({ key: 'nombre', dir: 'asc' });
  const [tipoEmpPage, setTipoEmpPage] = useState(1);
  const [tipoEmpPageSize, setTipoEmpPageSize] = useState(20);
  const [chartBasis, setChartBasis] = useState('deteccion'); // 'deteccion' | 'movimiento'
  const [ausMotivoMetric, setAusMotivoMetric] = useState('dias'); // 'dias' | 'eventos'
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
      const respuesta = await obtenerMovimientosMes(id);
      setDatos(respuesta);
    } catch (error) {
      console.error('Error cargando movimientos del mes:', error);
      setError('Error al cargar los movimientos del mes');
    } finally {
      setCargando(false);
    }
  };

  const movimientosFiltrados = datos?.movimientos?.filter(movimiento => {
    const cumpleBusqueda = !filtros.busqueda || 
      movimiento.empleado.nombre.toLowerCase().includes(filtros.busqueda.toLowerCase()) ||
      movimiento.empleado.rut.includes(filtros.busqueda);
    
    const cumpleTipo = filtros.tipo === 'todos' || movimiento.tipo_movimiento === filtros.tipo;
    
    let cumpleFecha = true;
    if (filtros.fechaDesde && movimiento.fecha_movimiento) {
      cumpleFecha = cumpleFecha && new Date(movimiento.fecha_movimiento) >= new Date(filtros.fechaDesde);
    }
    if (filtros.fechaHasta && movimiento.fecha_movimiento) {
      cumpleFecha = cumpleFecha && new Date(movimiento.fecha_movimiento) <= new Date(filtros.fechaHasta);
    }
    
    return cumpleBusqueda && cumpleTipo && cumpleFecha;
  }) || [];

  // Reset de página al cambiar filtros o sort
  useEffect(() => { setPage(1); }, [filtros, sort]);

  // Ordenamiento
  const sortedMovimientos = React.useMemo(() => {
    const arr = [...movimientosFiltrados];
    const mult = sort.dir === 'asc' ? 1 : -1;
    arr.sort((a, b) => {
      switch (sort.key) {
        case 'fecha_movimiento': {
          const da = a.fecha_movimiento ? new Date(a.fecha_movimiento).getTime() : 0;
          const db = b.fecha_movimiento ? new Date(b.fecha_movimiento).getTime() : 0;
          return (da - db) * mult;
        }
        case 'tipo':
          return (a.tipo_display || '').localeCompare(b.tipo_display || '') * mult;
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
    const porTipo = datos?.resumen?.por_tipo || {};
    return Object.entries(porTipo).map(([key, info]) => ({ name: info.display || key, value: Number(info.count || 0) }));
  }, [datos]);
  const porDiaTipoChartData = React.useMemo(() => {
    const m = new Map();
    const useMovimiento = chartBasis === 'movimiento';
    const tipos = ['ingreso','finiquito','ausentismo','reincorporacion','cambio_datos'];
    for (const mv of datos?.movimientos || []) {
      const fechaStr = useMovimiento ? (mv.fecha_movimiento || mv.fecha_deteccion) : (mv.fecha_deteccion || mv.fecha_movimiento);
      const d = fechaStr ? new Date(fechaStr) : null;
      if (!d) continue;
      const k = d.toISOString().slice(0, 10);
      if (!m.has(k)) {
        const base = { date: k };
        for (const t of tipos) base[t] = 0;
        m.set(k, base);
      }
      const obj = m.get(k);
      const t = mv.tipo_movimiento;
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
    const lista = (datos?.movimientos || []).filter((m) => m.tipo_movimiento === 'ausentismo');
    let totalDias = 0;
    let eventos = 0;
    for (const m of lista) {
      const dias = Number(m.dias_ausencia || 0);
      totalDias += isNaN(dias) ? 0 : dias;
      eventos += 1;
    }
    const promedio = eventos > 0 ? Math.round((totalDias / eventos) * 10) / 10 : 0;
    return { totalDias, eventos, promedio };
  }, [datos]);
  const topAusenciasData = React.useMemo(() => {
    const acc = new Map();
    for (const m of datos?.movimientos || []) {
      if (m.tipo_movimiento !== 'ausentismo') continue;
      const rut = m.empleado?.rut || '';
      const name = m.empleado?.nombre || rut || 'Empleado';
      const dias = Number(m.dias_ausencia || 0);
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
      if (m.tipo_movimiento !== 'ausentismo') continue;
      const rawMotivo = (m.motivo || '').trim();
      const key = rawMotivo ? rawMotivo : 'Sin motivo';
      const dias = Number(m.dias_ausencia || 0);
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

  // Inasistencias por tipo (agregado backend V2: ausentismo_metricas.por_tipo)
  const inasistenciasPorTipoData = React.useMemo(() => {
    const tipos = datos?.resumen?.ausentismo_metricas?.por_tipo;
    if (Array.isArray(tipos) && tipos.length) {
      return tipos.map(t => ({ name: t.tipo, eventos: t.eventos, dias: t.dias }));
    }
    // Fallback: derivar del motivo (segmento antes de ' - ' o Vacaciones)
    const acc = new Map();
    for (const m of datos?.movimientos || []) {
      if (m.tipo_movimiento !== 'ausentismo') continue;
      const rawMotivo = (m.motivo || '').trim() || 'Sin motivo';
      let tipoBase;
      if (rawMotivo === 'Vacaciones') tipoBase = 'Vacaciones';
      else {
        const parts = rawMotivo.split(' - ', 1);
        tipoBase = parts[0] ? parts[0].trim() : rawMotivo;
      }
      if (!tipoBase) tipoBase = 'Sin tipo';
      const dias = Number(m.dias_ausencia || 0) || 0;
      const obj = acc.get(tipoBase) || { name: tipoBase, eventos: 0, dias: 0 };
      obj.eventos += 1;
      obj.dias += dias;
      acc.set(tipoBase, obj);
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
      case 'ausentismo':
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
      case 'ausentismo':
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
          {/* Badges por tipo de movimiento */}
          {datos?.resumen?.por_tipo && (
            <div className="mt-4 flex flex-wrap gap-2">
              {Object.entries(datos.resumen.por_tipo).map(([tipo, info]) => (
                <button
                  key={tipo}
                  onClick={() => setFiltros((f) => ({ ...f, tipo }))}
                  className={`text-xs px-2.5 py-1 rounded-full inline-flex items-center gap-1 ${tipoBadgeStyles(tipo)} hover:opacity-90`}
                  title={`Filtrar por ${info.display || tipo}`}
                >
                  <span className="h-1.5 w-1.5 rounded-full bg-current opacity-80" />
                  {(info.display || tipo)}: {info.count}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Contenido principal */}
      <div className="w-full px-6 py-6">
        {/* Resumen por tipo (solo tarjetas solicitadas) */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          {['ingreso','finiquito','ausentismo'].map((tipo) => {
            const info = datos?.resumen?.por_tipo?.[tipo] || { count: 0 };
            const emp = info.empleados_unicos ?? null;
            const label = tipo === 'ingreso' ? 'Ingresos' : tipo === 'finiquito' ? 'Finiquitos' : 'Ausencias';
            return (
              <div
                key={tipo}
                onClick={() => scrollToTabla(tipo)}
                className="bg-gray-900/60 rounded-xl p-4 border border-gray-800 hover:border-gray-700 transition-colors transition-transform duration-200 hover:scale-[1.02] cursor-pointer"
              >
                <div className="flex items-center justify-between mb-1">
                  {obtenerIconoTipo(tipo)}
                  <span className="text-2xl font-bold text-white">{info.count}</span>
                </div>
                <p className="text-sm text-gray-300 mb-0.5">{label}</p>
                {emp !== null && <p className="text-[11px] text-gray-400"><span className="text-teal-300 font-medium">{emp}</span> empleado{emp===1?'':'s'}</p>}
              </div>
            );
          })}
          <div
            onClick={() => scrollToTabla(null)}
            className="bg-gray-900/60 rounded-xl p-4 border border-gray-800 hover:border-gray-700 transition-colors transition-transform duration-200 hover:scale-[1.02] cursor-pointer"
          >
            <div className="flex items-center justify-between mb-2">
              <Users className="w-5 h-5 text-gray-400" />
              <span className="text-2xl font-bold text-white">{datos?.resumen?.total_movimientos || 0}</span>
            </div>
            <p className="text-sm text-gray-300">Total de Movimientos</p>
          </div>
        </div>

    {/* Gráficos */}
  <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-5 gap-6 mt-2 mb-10">
          <div className="bg-gray-900/60 rounded-xl p-4 border border-gray-800 transition-transform duration-200 hover:scale-[1.005] hover:border-gray-700">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <BarChart3 size={16} className="text-gray-400" />
                <h3 className="text-sm font-medium text-gray-300">Movimientos por tipo</h3>
              </div>
              <span className="text-xs text-gray-500">(conteo)</span>
            </div>
      <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
        <BarChart data={tiposChartData} margin={{ top: 12, right: 24, left: 32, bottom: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                  <XAxis dataKey="name" stroke="#9ca3af" tick={{ fontSize: 12 }} />
                  <YAxis stroke="#9ca3af" width={50} tickMargin={6} tick={{ fontSize: 12 }} />
                  <RTooltip formatter={(v) => [v, '']} cursor={{ fill: 'rgba(255,255,255,0.02)' }} />
                  <Bar dataKey="value" fill="#14b8a6" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
          <div className="bg-gray-900/60 rounded-xl p-4 border border-gray-800 transition-transform duration-200 hover:scale-[1.005] hover:border-gray-700">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <BarChart3 size={16} className="text-gray-400" />
                <h3 className="text-sm font-medium text-gray-300">Eventos por día (stacked por tipo)</h3>
              </div>
              <div className="flex items-center gap-1 text-xs bg-gray-800/60 border border-gray-700 rounded-lg p-0.5">
                <button
                  onClick={() => setChartBasis('deteccion')}
                  className={`px-2 py-1 rounded ${chartBasis === 'deteccion' ? 'bg-teal-600 text-white' : 'text-gray-300 hover:text-white'}`}
                >
                  Detección
                </button>
                <button
                  onClick={() => setChartBasis('movimiento')}
                  className={`px-2 py-1 rounded ${chartBasis === 'movimiento' ? 'bg-teal-600 text-white' : 'text-gray-300 hover:text-white'}`}
                >
                  Movimiento
                </button>
              </div>
            </div>
      <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
        <BarChart data={porDiaTipoChartData} margin={{ top: 12, right: 24, left: 32, bottom: 28 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                  <XAxis dataKey="name" stroke="#9ca3af" tick={{ fontSize: 12 }} />
                  <YAxis stroke="#9ca3af" width={50} tickMargin={6} tick={{ fontSize: 12 }} />
                  <RTooltip formatter={(v) => [v, '']} cursor={{ fill: 'rgba(255,255,255,0.02)' }} />
          <Legend verticalAlign="bottom" height={32} wrapperStyle={{ color: '#9ca3af' }} />
                  <Bar dataKey="ingreso" stackId="a" fill="#34d399" radius={[6, 6, 0, 0]} name="Ingreso" />
                  <Bar dataKey="finiquito" stackId="a" fill="#f87171" radius={[6, 6, 0, 0]} name="Finiquito" />
                  <Bar dataKey="reincorporacion" stackId="a" fill="#60a5fa" radius={[6, 6, 0, 0]} name="Reincorporación" />
                  <Bar dataKey="cambio_datos" stackId="a" fill="#a78bfa" radius={[6, 6, 0, 0]} name="Cambio de datos" />
                  <Bar dataKey="ausentismo" stackId="a" fill="#fbbf24" radius={[6, 6, 0, 0]} name="Ausentismo" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
          <div className="bg-gray-900/60 rounded-xl p-4 border border-gray-800 transition-transform duration-200 hover:scale-[1.005] hover:border-gray-700">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <BarChart3 size={16} className="text-gray-400" />
                <h3 className="text-sm font-medium text-gray-300">Ausentismo: Top por días</h3>
              </div>
              <div className="flex items-center gap-3 text-xs text-gray-400">
                <span>Total días: <span className="text-gray-200 font-medium">{ausentismoKPIs.totalDias}</span></span>
                <span>Promedio/evt: <span className="text-gray-200 font-medium">{ausentismoKPIs.promedio}</span></span>
              </div>
            </div>
      <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
        <BarChart data={topAusenciasData} layout="vertical" margin={{ top: 12, right: 24, left: 48, bottom: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                  <XAxis type="number" stroke="#9ca3af" tick={{ fontSize: 12 }} />
          <YAxis type="category" dataKey="name" stroke="#9ca3af" width={160} tick={{ fontSize: 12 }} />
                  <RTooltip formatter={(v) => [v, 'días']} cursor={{ fill: 'rgba(255,255,255,0.02)' }} />
                  <Bar dataKey="dias" fill="#fbbf24" radius={[0, 6, 6, 0]} name="Días" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
          {/* Ausentismo por motivo */}
          <div className="bg-gray-900/60 rounded-xl p-4 border border-gray-800 transition-transform duration-200 hover:scale-[1.005] hover:border-gray-700">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <BarChart3 size={16} className="text-gray-400" />
                <h3 className="text-sm font-medium text-gray-300">Ausentismo por motivo</h3>
              </div>
              <div className="flex items-center gap-1 text-xs bg-gray-800/60 border border-gray-700 rounded-lg p-0.5">
                <button onClick={()=>setAusMotivoMetric('dias')} className={`px-2 py-1 rounded ${ausMotivoMetric==='dias' ? 'bg-teal-600 text-white':'text-gray-300 hover:text-white'}`}>Días</button>
                <button onClick={()=>setAusMotivoMetric('eventos')} className={`px-2 py-1 rounded ${ausMotivoMetric==='eventos' ? 'bg-teal-600 text-white':'text-gray-300 hover:text-white'}`}>Eventos</button>
              </div>
            </div>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={ausentismoPorMotivoData} margin={{ top: 12, right: 24, left: 32, bottom: 60 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                  <XAxis dataKey="name" stroke="#9ca3af" tick={{ fontSize: 11 }} interval={0} angle={-35} textAnchor="end" height={70} />
                  <YAxis stroke="#9ca3af" width={50} tick={{ fontSize: 12 }} />
                  <RTooltip cursor={{ fill: 'rgba(255,255,255,0.02)' }} formatter={(v)=> [v, ausMotivoMetric==='dias'? 'días':'eventos']} />
                  <Bar dataKey={ausMotivoMetric} fill={ausMotivoMetric==='dias'? '#facc15':'#60a5fa'} radius={[6,6,0,0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
          {/* Inasistencias por tipo (eventos) */}
          <div className="bg-gray-900/60 rounded-xl p-4 border border-gray-800 transition-transform duration-200 hover:scale-[1.005] hover:border-gray-700">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <BarChart3 size={16} className="text-gray-400" />
                <h3 className="text-sm font-medium text-gray-300">Inasistencias por tipo</h3>
              </div>
              <span className="text-xs text-gray-500">(eventos)</span>
            </div>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={inasistenciasPorTipoData} margin={{ top: 12, right: 24, left: 32, bottom: 60 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                  <XAxis dataKey="name" stroke="#9ca3af" tick={{ fontSize: 11 }} interval={0} angle={-35} textAnchor="end" height={70} />
                  <YAxis stroke="#9ca3af" width={50} tick={{ fontSize: 12 }} />
                  <RTooltip cursor={{ fill: 'rgba(255,255,255,0.02)' }} formatter={(v)=> [v, 'eventos']} />
                  <Bar dataKey="eventos" fill="#14b8a6" radius={[6,6,0,0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* Filtros */}
        <div className="bg-gray-900/60 rounded-xl p-6 border border-gray-800 mb-8">
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Buscar Empleado
              </label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
                <input
                  type="text"
                  placeholder="Nombre o RUT..."
                  value={filtros.busqueda}
                  onChange={(e) => setFiltros(prev => ({ ...prev, busqueda: e.target.value }))}
                  className="w-full pl-10 pr-4 py-2 bg-gray-800/80 border border-gray-700 rounded-lg text-white focus:ring-2 focus:ring-teal-500 focus:border-transparent placeholder-gray-500"
                />
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Tipo de Movimiento
              </label>
              <select
                value={filtros.tipo}
                onChange={(e) => setFiltros(prev => ({ ...prev, tipo: e.target.value }))}
                className="w-full px-3 py-2 bg-gray-800/80 border border-gray-700 rounded-lg text-white focus:ring-2 focus:ring-teal-500 focus:border-transparent"
              >
                <option value="todos">Todos</option>
                <option value="ingreso">Ingreso</option>
                <option value="finiquito">Finiquito</option>
                <option value="ausentismo">Ausentismo</option>
                <option value="reincorporacion">Reincorporación</option>
                <option value="cambio_datos">Cambio de Datos</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Fecha Desde
              </label>
              <input
                type="date"
                value={filtros.fechaDesde}
                onChange={(e) => setFiltros(prev => ({ ...prev, fechaDesde: e.target.value }))}
                className="w-full px-3 py-2 bg-gray-800/80 border border-gray-700 rounded-lg text-white focus:ring-2 focus:ring-teal-500 focus:border-transparent"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Fecha Hasta
              </label>
              <input
                type="date"
                value={filtros.fechaHasta}
                onChange={(e) => setFiltros(prev => ({ ...prev, fechaHasta: e.target.value }))}
                className="w-full px-3 py-2 bg-gray-800/80 border border-gray-700 rounded-lg text-white focus:ring-2 focus:ring-teal-500 focus:border-transparent"
              />
            </div>
            
            <div className="flex items-end justify-end gap-3">
              <button
                onClick={() => setFiltros({ busqueda: '', tipo: 'todos', fechaDesde: '', fechaHasta: '' })}
                className="px-3 py-2 rounded-lg border border-gray-700 text-gray-300 hover:border-gray-600 text-sm"
              >
                Limpiar filtros
              </button>
              <p className="text-sm text-gray-400">
                {movimientosFiltrados.length} de {datos?.movimientos?.length || 0} movimientos
              </p>
            </div>
          </div>
        </div>

        

        {/* Tabla agrupada por tipo (concepto) */}
  <div ref={tablaRef} className="bg-gray-900/60 rounded-xl p-5 border border-gray-800 mb-4">
          <div className="bg-gray-900/60 rounded-xl border border-gray-800 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-800/80 border-b border-gray-700">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Tipo</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-300 uppercase tracking-wider">Cantidad</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-800">
                  {(() => {
                    const rows = Object.entries(datos?.resumen?.por_tipo || {})
                      .map(([key, info]) => ({ key, name: info.display || key, count: Number(info.count || 0) }))
                      .sort((a, b) => b.count - a.count);
                    if (rows.length === 0) {
                      return (
                        <tr>
                          <td colSpan="2" className="px-4 py-8 text-center text-gray-500">Sin datos</td>
                        </tr>
                      );
                    }
                    return (
                      <>
                        {rows.map((r) => (
                          <React.Fragment key={r.key}>
                            <tr
                              className={`group hover:bg-gray-800 cursor-pointer ${selectedTipo === r.key ? 'bg-gray-900 ring-1 ring-teal-700/40' : 'odd:bg-gray-900/20'} transition-colors`}
                              onClick={() => setSelectedTipo(prev => prev === r.key ? null : r.key)}
                            >
                              <td className="px-4 py-3 text-white">
                                <span className="inline-flex items-center gap-2">
                                  {obtenerIconoTipo(r.key)} {r.name}
                                </span>
                              </td>
                              <td className="px-4 py-3 text-right text-gray-300">{r.count}</td>
                            </tr>
                            {selectedTipo === r.key && (
                              <tr>
                                <td colSpan="2" className="px-4 py-3 bg-gray-900/50">
                                  <div className="flex items-center justify-between mb-2">
                                    <div className="text-xs text-gray-400">Movimientos: {r.name}</div>
                                    <div className="relative w-64 max-w-full">
                                      <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={14} />
                                      <input
                                        type="text"
                                        placeholder="Buscar empleado o RUT..."
                                        value={tipoQuery}
                                        onChange={(e) => { setTipoQuery(e.target.value); setTipoEmpPage(1); }}
                                        className="w-full pl-9 pr-3 py-2 bg-gray-800/80 border border-gray-700 rounded-lg text-white focus:ring-2 focus:ring-teal-500 focus:border-transparent placeholder-gray-500 text-sm"
                                      />
                                    </div>
                                  </div>
                                  <div className="overflow-y-auto max-h-96 rounded-lg border border-gray-800">
                                    <table className="w-full">
                                      <thead className="bg-gray-800/80 border-b border-gray-700 sticky top-0 z-10">
                                        <tr>
                                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                                            <button onClick={() => setTipoEmpSort(s => ({ key: 'nombre', dir: s.key === 'nombre' && s.dir === 'asc' ? 'desc' : 'asc' }))} className="inline-flex items-center gap-1">Empleado <ArrowUpDown size={12} className="text-gray-400" /></button>
                                          </th>
                                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">RUT</th>
                                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Cargo</th>
                                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Centro Costo</th>
                                          <th className="px-4 py-3 text-right text-xs font-medium text-gray-300 uppercase tracking-wider">
                                            <button onClick={() => setTipoEmpSort(s => ({ key: 'fecha', dir: s.key === 'fecha' && s.dir === 'asc' ? 'desc' : 'asc' }))} className="inline-flex items-center gap-1">Fecha <ArrowUpDown size={12} className="text-gray-400" /></button>
                                          </th>
                                        </tr>
                                      </thead>
                                      <tbody className="divide-y divide-gray-800">
                                        {(() => {
                                          const lista = (datos?.movimientos || []).filter(m => m.tipo_movimiento === r.key).map(m => ({
                                            nombre: m.empleado?.nombre || '',
                                            rut: m.empleado?.rut || '',
                                            cargo: m.empleado?.cargo || '-',
                                            centro: m.empleado?.centro_costo || '-',
                                            fecha: m.fecha_movimiento || m.fecha_deteccion,
                                          }));
                                          const q = tipoQuery.trim().toLowerCase();
                                          const filtrados = q ? lista.filter(e => e.nombre.toLowerCase().includes(q) || e.rut.toLowerCase().includes(q)) : lista;
                                          const mult = tipoEmpSort.dir === 'asc' ? 1 : -1;
                                          filtrados.sort((a, b) => {
                                            if (tipoEmpSort.key === 'nombre') return a.nombre.localeCompare(b.nombre) * mult;
                                            const da = a.fecha ? new Date(a.fecha).getTime() : 0;
                                            const db = b.fecha ? new Date(b.fecha).getTime() : 0;
                                            return (da - db) * mult;
                                          });
                                          const eTotal = filtrados.length;
                                          const eTotalPages = Math.max(1, Math.ceil(eTotal / tipoEmpPageSize));
                                          const ePage = Math.min(tipoEmpPage, eTotalPages);
                                          const eStart = (ePage - 1) * tipoEmpPageSize;
                                          const eEnd = Math.min(eStart + tipoEmpPageSize, eTotal);
                                          const pageRows = filtrados.slice(eStart, eEnd);
                                          return (
                                            <>
                                              {pageRows.map((emp, idx) => (
                                                <tr key={`${emp.rut}-${idx}`} className="hover:bg-gray-800 odd:bg-gray-900/20">
                                                  <td className="px-4 py-3 text-white">{emp.nombre}</td>
                                                  <td className="px-4 py-3 text-gray-300">{emp.rut}</td>
                                                  <td className="px-4 py-3 text-gray-300">{emp.cargo}</td>
                                                  <td className="px-4 py-3 text-gray-300">{emp.centro}</td>
                                                  <td className="px-4 py-3 text-right text-gray-300">{emp.fecha ? new Date(emp.fecha).toLocaleDateString('es-CL') : '-'}</td>
                                                </tr>
                                              ))}
                                              <tr>
                                                <td colSpan="5" className="px-4 py-3">
                                                  <div className="flex items-center justify-between text-xs text-gray-400">
                                                    <div>Mostrando {eTotal === 0 ? 0 : eStart + 1}-{eEnd} de {eTotal}</div>
                                                    <div className="flex items-center gap-2">
                                                      <div className="flex items-center gap-2">
                                                        <span>Por página</span>
                                                        <select value={tipoEmpPageSize} onChange={(e) => { setTipoEmpPageSize(Number(e.target.value)); setTipoEmpPage(1); }} className="bg-gray-800/80 border border-gray-700 rounded px-2 py-1">
                                                          <option value={10}>10</option>
                                                          <option value={20}>20</option>
                                                          <option value={50}>50</option>
                                                        </select>
                                                      </div>
                                                      <button onClick={() => setTipoEmpPage(p => Math.max(1, p - 1))} className="px-2 py-1 rounded border border-gray-700 text-gray-300 disabled:opacity-50" disabled={ePage <= 1}><ChevronLeft size={14} /></button>
                                                      <button onClick={() => setTipoEmpPage(p => p + 1)} className="px-2 py-1 rounded border border-gray-700 text-gray-300 disabled:opacity-50" disabled={ePage >= eTotalPages}><ChevronRight size={14} /></button>
                                                    </div>
                                                  </div>
                                                </td>
                                              </tr>
                                            </>
                                          );
                                        })()}
                                      </tbody>
                                    </table>
                                  </div>
                                </td>
                              </tr>
                            )}
                          </React.Fragment>
                        ))}
                      </>
                    );
                  })()}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        

        
      </div>
    </div>
  );
};

export default MovimientosMes;
