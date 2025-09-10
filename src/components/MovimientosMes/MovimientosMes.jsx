import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { obtenerMovimientosPersonalV3 } from '../../api/nomina';
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
  const respuesta = await obtenerMovimientosPersonalV3(id);
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
    
    const cumpleTipo = filtros.tipo === 'todos' || movimiento.categoria === filtros.tipo || movimiento.subtipo === filtros.tipo;
    
    let cumpleFecha = true;
    const fechaRef = movimiento.fecha_inicio || movimiento.fecha_fin || movimiento.fecha_deteccion;
    if (filtros.fechaDesde && fechaRef) {
      cumpleFecha = cumpleFecha && new Date(fechaRef) >= new Date(filtros.fechaDesde);
    }
    if (filtros.fechaHasta && fechaRef) {
      cumpleFecha = cumpleFecha && new Date(fechaRef) <= new Date(filtros.fechaHasta);
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
    for (const mv of movs) {
      const cat = mv.categoria;
      if (cat === 'ingreso') ingresos += 1;
      else if (cat === 'finiquito') finiquitos += 1;
      else if (cat === 'ausencia') {
        const st = (mv.subtipo || '').trim() || 'sin_justificar';
        const dias = Number(mv.dias_en_periodo ?? mv.dias_evento ?? 0) || 0;
        if (st === 'vacaciones') vacacionesDias += dias;
        else if (st === 'sin_justificar') ausSinJustificar += 1;
        else diasAusJustificados += dias;
      }
    }
    return { ingresos, finiquitos, diasAusJustificados, vacacionesDias, ausSinJustificar, total: movs.length };
  }, [datos]);
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
        {/* Tarjetas métricas normalizadas solicitadas */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
          {/* Ingresos */}
          <div className="bg-gray-900/60 rounded-xl p-4 border border-gray-800 hover:border-gray-700 transition-colors duration-200">
            <div className="flex items-center justify-between mb-1">
              {obtenerIconoTipo('ingreso')}
              <span className="text-2xl font-bold text-white">{tarjetasMetrics.ingresos}</span>
            </div>
            <p className="text-sm text-gray-300">Ingresos</p>
          </div>
          {/* Finiquitos */}
          <div className="bg-gray-900/60 rounded-xl p-4 border border-gray-800 hover:border-gray-700 transition-colors duration-200">
            <div className="flex items-center justify-between mb-1">
              {obtenerIconoTipo('finiquito')}
              <span className="text-2xl font-bold text-white">{tarjetasMetrics.finiquitos}</span>
            </div>
            <p className="text-sm text-gray-300">Finiquitos</p>
          </div>
          {/* Días de ausencia justificados */}
          <div className="bg-gray-900/60 rounded-xl p-4 border border-gray-800 hover:border-gray-700 transition-colors duration-200">
            <div className="flex items-center justify-between mb-1">
              <Calendar className="w-5 h-5 text-emerald-400" />
              <span className="text-2xl font-bold text-white">{tarjetasMetrics.diasAusJustificados}</span>
            </div>
            <p className="text-sm text-gray-300">Días ausencia justificados</p>
          </div>
          {/* Vacaciones (días) */}
          <div className="bg-gray-900/60 rounded-xl p-4 border border-gray-800 hover:border-gray-700 transition-colors duration-200">
            <div className="flex items-center justify-between mb-1">
              <Calendar className="w-5 h-5 text-yellow-400" />
              <span className="text-2xl font-bold text-white">{tarjetasMetrics.vacacionesDias}</span>
            </div>
            <p className="text-sm text-gray-300">Días de vacaciones</p>
          </div>
          {/* Ausencias sin justificar (eventos) */}
          <div className="bg-gray-900/60 rounded-xl p-4 border border-gray-800 hover:border-gray-700 transition-colors duration-200">
            <div className="flex items-center justify-between mb-1">
              <Calendar className="w-5 h-5 text-red-400" />
              <span className="text-2xl font-bold text-white">{tarjetasMetrics.ausSinJustificar}</span>
            </div>
            <p className="text-sm text-gray-300">Ausencias sin justificar</p>
          </div>
        </div>
        {/* Gráficos en standby (se removió render) */}

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
                <option value="cambio_contrato">Cambio de Contrato</option>
                <option value="cambio_sueldo">Cambio de Sueldo</option>
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

        

        {/* Tabla agregada (sin datos de empleado) */}
        <div ref={tablaRef} className="bg-gray-900/60 rounded-xl p-5 border border-gray-800 mb-4">
          <div className="bg-gray-900/60 rounded-xl border border-gray-800 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-800/80 border-b border-gray-700">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Tipo / Métrica</th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-300 uppercase tracking-wider">Valor</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-800">
                  {(() => {
                    const rows = [
                      { key: 'ingreso', name: 'Ingresos', value: tarjetasMetrics.ingresos, tipo: 'count' },
                      { key: 'finiquito', name: 'Finiquitos', value: tarjetasMetrics.finiquitos, tipo: 'count' },
                      { key: 'dias_ausencia_justificados', name: 'Días ausencia justificados', value: tarjetasMetrics.diasAusJustificados, tipo: 'dias' },
                      { key: 'vacaciones', name: 'Días de vacaciones', value: tarjetasMetrics.vacacionesDias, tipo: 'dias' },
                      { key: 'ausencias_sin_justificar', name: 'Ausencias sin justificar', value: tarjetasMetrics.ausSinJustificar, tipo: 'count' },
                    ];
                    // Mantener orden listado
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
                                  {obtenerIconoTipo(r.key.includes('ausencia') || r.key==='vacaciones' ? 'ausencia' : (r.key==='ausencias_sin_justificar' ? 'ausencia' : r.key))} {r.name}
                                </span>
                              </td>
                              <td className="px-4 py-3 text-right text-gray-300">{r.value}</td>
                            </tr>
                            {selectedTipo === r.key && (
                              <tr>
                                <td colSpan="2" className="px-4 py-3 bg-gray-900/50">
                                  {/* Detalle por tipo sin datos personales */}
                                  <div className="overflow-y-auto max-h-96 rounded-lg border border-gray-800">
                                    <table className="w-full">
                                      <thead className="bg-gray-800/80 border-b border-gray-700 sticky top-0 z-10">
                                        <tr>
                                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase">Categoría/Subtipo</th>
                                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase">Fecha Inicio</th>
                                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase">Fecha Fin</th>
                                          <th className="px-4 py-3 text-right text-xs font-medium text-gray-300 uppercase">Días</th>
                                        </tr>
                                      </thead>
                                      <tbody className="divide-y divide-gray-800">
                                        {(() => {
                                          const base = datos?.movimientos || [];
                                          let eventos = [];
                                          if (r.key === 'ingreso') {
                                            eventos = base.filter(m => m.categoria === 'ingreso');
                                          } else if (r.key === 'finiquito') {
                                            eventos = base.filter(m => m.categoria === 'finiquito');
                                          } else if (r.key === 'vacaciones') {
                                            eventos = base.filter(m => m.categoria === 'ausencia' && (m.subtipo || '').trim() === 'vacaciones');
                                          } else if (r.key === 'ausencias_sin_justificar') {
                                            eventos = base.filter(m => m.categoria === 'ausencia' && ((m.subtipo || '').trim() === 'sin_justificar' || !(m.subtipo)));
                                          } else if (r.key === 'dias_ausencia_justificados') {
                                            eventos = base.filter(m => m.categoria === 'ausencia' && !['sin_justificar','vacaciones',''].includes((m.subtipo || '').trim()));
                                          }
                                          const rowsDet = eventos.map(ev => {
                                            const dias = Number(ev.dias_en_periodo ?? ev.dias_evento ?? 0) || 0;
                                            return {
                                              cat: ev.categoria === 'ausencia' ? (ev.subtipo || 'sin_subtipo') : ev.categoria,
                                              fi: ev.fecha_inicio || '-',
                                              ff: ev.fecha_fin || ev.fecha_inicio || '-',
                                              dias,
                                              id: ev.id
                                            };
                                          });
                                          if (rowsDet.length === 0) {
                                            return (
                                              <tr>
                                                <td colSpan={4} className="px-4 py-6 text-center text-gray-500">Sin eventos</td>
                                              </tr>
                                            );
                                          }
                                          return rowsDet.sort((a,b)=> (new Date(a.fi||'1970-01-01') - new Date(b.fi||'1970-01-01'))).map(rw => (
                                            <tr key={rw.id} className="hover:bg-gray-800/60">
                                              <td className="px-4 py-3 text-white text-sm">{rw.cat}</td>
                                              <td className="px-4 py-3 text-gray-300 text-sm">{rw.fi ? new Date(rw.fi).toLocaleDateString('es-CL') : '-'}</td>
                                              <td className="px-4 py-3 text-gray-300 text-sm">{rw.ff ? new Date(rw.ff).toLocaleDateString('es-CL') : '-'}</td>
                                              <td className="px-4 py-3 text-gray-200 text-sm text-right">{rw.dias}</td>
                                            </tr>
                                          ));
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
