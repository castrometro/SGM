import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { obtenerDetalleNominaConsolidada, obtenerResumenNominaConsolidada } from '../../api/nomina';
import { formatearMonedaChilena } from '../../utils/formatters';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RTooltip,
  ComposedChart,
  ReferenceLine
} from 'recharts';
import {
  ArrowLeft,
  Users,
  DollarSign,
  FileText,
  Search,
  Filter,
  Download,
  Eye,
  EyeOff,
  BarChart3,
  PieChart as PieIcon,
  Sparkles
} from 'lucide-react';
import { ArrowUpDown, ChevronLeft, ChevronRight, ChevronDown, Copy } from 'lucide-react';

const LibroRemuneraciones = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  
  const [datos, setDatos] = useState(null);
  const [resumenConsolidado, setResumenConsolidado] = useState(null);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState('');
  const [filtros, setFiltros] = useState({
    busqueda: '',
    estado: 'todos',
    mostrarSoloMontos: false
  });
  const [empleadoExpandido, setEmpleadoExpandido] = useState(null);
  // Explorador de conceptos (drilldown)
  const [selectedCat, setSelectedCat] = useState(null);
  const [selectedConcept, setSelectedConcept] = useState(null);
  const [conceptQuery, setConceptQuery] = useState('');
  const [conceptSort, setConceptSort] = useState({ key: 'total', dir: 'desc' });
  const [conceptPage, setConceptPage] = useState(1);
  const [conceptPageSize, setConceptPageSize] = useState(20);
  const [conceptEmpSort, setConceptEmpSort] = useState({ key: 'monto', dir: 'desc' });
  const [conceptEmpPage, setConceptEmpPage] = useState(1);
  const [conceptEmpPageSize, setConceptEmpPageSize] = useState(20);
  const [conceptEmpQuery, setConceptEmpQuery] = useState('');
  const [conceptEmpLoading, setConceptEmpLoading] = useState(false);
  const [dense, setDense] = useState(false);
  const denseClasses = {
    rowText: dense ? 'text-xs' : 'text-sm',
    pad: dense ? 'px-3 py-2' : 'px-4 py-3',
  };
  const explorerRef = useRef(null);

  const goToExplorer = (cat) => {
    if (cat) setSelectedCat(cat);
    setSelectedConcept(null);
    // dar tiempo a actualizar estado antes de scroll
    setTimeout(() => {
      explorerRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 0);
  };

  const ESTADOS_LABEL = {
    activo: 'Activo',
    nueva_incorporacion: 'Nueva Incorporación',
    finiquito: 'Finiquito',
    ausente_total: 'Ausente Total',
    ausente_parcial: 'Ausente Parcial',
  };
  const estadoBadgeStyles = (estado) =>
    estado === 'activo'
      ? 'bg-emerald-900/50 text-emerald-300 ring-1 ring-emerald-700/40'
      : estado === 'nueva_incorporacion'
      ? 'bg-blue-900/50 text-blue-300 ring-1 ring-blue-700/40'
      : estado === 'finiquito'
      ? 'bg-rose-900/50 text-rose-300 ring-1 ring-rose-700/40'
      : estado === 'ausente_total'
      ? 'bg-amber-900/50 text-amber-300 ring-1 ring-amber-700/40'
      : 'bg-yellow-900/50 text-yellow-300 ring-1 ring-yellow-700/40';

  useEffect(() => {
    cargarDatos();
  }, [id]);

  // Reset drilldown paginación al cambiar query y selección
  useEffect(() => { setConceptPage(1); }, [conceptQuery, selectedCat]);
  useEffect(() => { setConceptEmpPage(1); setConceptEmpQuery(''); }, [selectedConcept]);
  // efecto visual de carga cuando cambian filtros/paginación del sublistado
  useEffect(() => {
    if (!selectedConcept) return;
    setConceptEmpLoading(true);
    const t = setTimeout(() => setConceptEmpLoading(false), 120);
    return () => clearTimeout(t);
  }, [selectedConcept, conceptEmpQuery, conceptEmpSort, conceptEmpPage, conceptEmpPageSize]);

  const cargarDatos = async () => {
    try {
      setCargando(true);
      const [respuesta, resumen] = await Promise.all([
        obtenerDetalleNominaConsolidada(id),
        obtenerResumenNominaConsolidada(id)
      ]);
      setDatos(respuesta);
      setResumenConsolidado(resumen);
    } catch (error) {
      console.error('Error cargando libro de remuneraciones:', error);
      setError('Error al cargar los datos del libro de remuneraciones');
    } finally {
      setCargando(false);
    }
  };

  const empleadosFiltrados = datos?.empleados?.filter(empleado => {
    const cumpleBusqueda = !filtros.busqueda || 
      empleado.nombre_empleado.toLowerCase().includes(filtros.busqueda.toLowerCase()) ||
      empleado.rut_empleado.includes(filtros.busqueda);
    
    const cumpleEstado = filtros.estado === 'todos' || empleado.estado_empleado === filtros.estado;
    
    return cumpleBusqueda && cumpleEstado;
  }) || [];

  // Índice de conceptos por categoría y totales para drilldown
  const CATEGORIAS = [
    'haber_imponible',
    'haber_no_imponible',
    'descuento_legal',
    'otro_descuento',
    'impuesto',
    'aporte_patronal'
  ];
  const CATEGORIA_META = {
    haber_imponible: { label: 'Haberes Imponibles', color: 'text-green-400', ring: 'ring-emerald-700/40', bg: 'bg-emerald-900/40' },
    haber_no_imponible: { label: 'Haberes No Imponibles', color: 'text-green-400', ring: 'ring-emerald-700/40', bg: 'bg-emerald-900/20' },
    descuento_legal: { label: 'Descuentos Legales', color: 'text-red-400', ring: 'ring-rose-700/40', bg: 'bg-rose-900/20' },
    otro_descuento: { label: 'Otros Descuentos', color: 'text-red-400', ring: 'ring-rose-700/40', bg: 'bg-rose-900/10' },
    impuesto: { label: 'Impuestos', color: 'text-red-300', ring: 'ring-yellow-700/40', bg: 'bg-yellow-900/10' },
    aporte_patronal: { label: 'Aportes Patronales', color: 'text-indigo-300', ring: 'ring-indigo-700/40', bg: 'bg-indigo-900/10' },
  };
  const normalizeCat = (s) => (s || '').toString().toLowerCase().replace(/\s+/g, '_');
  const conceptIndex = React.useMemo(() => {
    const porCategoria = {};
    const totales = {};
    for (const k of CATEGORIAS) { porCategoria[k] = {}; totales[k] = 0; }
    if (!datos?.empleados) return { porCategoria, totales };
    for (const emp of datos.empleados) {
      if (!emp.conceptos) continue;
      for (const c of emp.conceptos) {
        const cat = normalizeCat(c.clasificacion);
        if (!CATEGORIAS.includes(cat)) continue;
        const nombre = c.nombre || 'Sin nombre';
        const monto = Number(c.monto_total || 0) || 0;
        totales[cat] += monto;
        if (!porCategoria[cat][nombre]) {
          porCategoria[cat][nombre] = { total: 0, empleados: [] };
        }
        porCategoria[cat][nombre].total += monto;
        porCategoria[cat][nombre].empleados.push({
          id: emp.id,
          nombre: emp.nombre_empleado,
          rut: emp.rut_empleado,
          monto,
          cantidad: c.cantidad ?? null
        });
      }
    }
    return { porCategoria, totales };
  }, [datos]);
  const defaultCat = React.useMemo(() => {
    for (const k of CATEGORIAS) {
      if ((conceptIndex.totales?.[k] || 0) > 0) return k;
    }
    return CATEGORIAS[0];
  }, [conceptIndex]);
  useEffect(() => { if (!selectedCat) setSelectedCat(defaultCat); }, [defaultCat, selectedCat]);
  useEffect(() => { setSelectedConcept(null); }, [selectedCat]);

  const headersFiltrados = filtros.mostrarSoloMontos 
    ? datos?.headers?.filter(header => {
        // Buscar si algún empleado tiene un valor numérico para este header
        return datos.empleados.some(emp => {
          const valor = emp.valores_headers[header];
          return valor && !isNaN(parseFloat(valor.replace(/[,$]/g, '')));
        });
      }) || []
    : datos?.headers || [];

  const formatearMonto = (valor) => {
    return formatearMonedaChilena(valor);
  };

  const esMontoNumerico = (valor) => {
    if (!valor) return false;
    const numero = parseFloat(valor.toString().replace(/[,$]/g, ''));
    return !isNaN(numero) && numero !== 0;
  };
  const formatearNumero = (valor) => {
    if (valor === null || valor === undefined) return '0';
    const n = Number(valor);
    if (Number.isNaN(n)) return String(valor);
    return new Intl.NumberFormat('es-CL').format(n);
  };

  // Datos para gráficos
  const resumen = resumenConsolidado?.resumen;
  const montosChartData = resumen ? [
    { name: 'Hab. Imp.', value: Number(resumen.total_haberes_imponibles || 0) },
    { name: 'Hab. No Imp.', value: Number(resumen.total_haberes_no_imponibles || 0) },
    { name: 'Dctos. Legales', value: Number(resumen.total_dctos_legales || 0) },
    { name: 'Otros Dctos.', value: Number(resumen.total_otros_dctos || 0) },
    { name: 'Impuestos', value: Number(resumen.total_impuestos || 0) },
    { name: 'Aportes', value: Number(resumen.total_aportes_patronales || 0) },
  ] : [];
  // Estados no activos para evitar que "activo" opaque el resto
  const estadoNoActivosData = resumenConsolidado?.por_estado
    ? Object.entries(resumenConsolidado.por_estado)
        .filter(([k]) => k !== 'activo')
        .map(([k, v]) => ({ name: (ESTADOS_LABEL[k] || k.replace('_',' ')), value: Number(v) }))
        .sort((a, b) => b.value - a.value)
    : [];
  // Waterfall: Bruto a Líquido (sumas y restas)
  const waterfallData = resumen ? [
    { name: 'Haberes', add: Number(resumen.total_haberes_imponibles || 0) + Number(resumen.total_haberes_no_imponibles || 0), sub: 0, net: 0 },
    { name: 'Dctos Legales', add: 0, sub: Number(resumen.total_dctos_legales || 0), net: 0 },
    { name: 'Otros Dctos', add: 0, sub: Number(resumen.total_otros_dctos || 0), net: 0 },
    { name: 'Impuestos', add: 0, sub: Number(resumen.total_impuestos || 0), net: 0 },
    { name: 'Líquido', add: 0, sub: 0, net: Number(resumen.liquido_total || 0) },
  ] : [];
  // Top conceptos por monto total (apilado desde detalle)
  const topConceptosData = React.useMemo(() => {
    if (!datos?.empleados) return [];
    const acum = new Map();
    for (const emp of datos.empleados) {
      if (!emp.conceptos) continue;
      for (const c of emp.conceptos) {
        const key = c.nombre || 'Sin nombre';
        const monto = Number(c.monto_total || 0);
        acum.set(key, (acum.get(key) || 0) + (isNaN(monto) ? 0 : monto));
      }
    }
    return Array.from(acum.entries())
      .map(([name, value]) => ({ name, value }))
      .sort((a, b) => b.value - a.value)
      .slice(0, 8);
  }, [datos]);
  

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
            <FileText className="text-white" size={24} />
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
      {/* Header mejorado */}
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
                  <h1 className="text-2xl font-bold text-teal-400">Libro de Remuneraciones</h1>
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
          {/* Badges por estado */}
          {resumenConsolidado?.por_estado && (
            <div className="mt-4 flex flex-wrap gap-2">
              {Object.entries(resumenConsolidado.por_estado).map(([key, val]) => (
                <span key={key} className={`text-xs px-2.5 py-1 rounded-full ${estadoBadgeStyles(key)} inline-flex items-center gap-1`}>
                  <span className="h-1.5 w-1.5 rounded-full bg-current opacity-80" />
                  {ESTADOS_LABEL[key] || key.replace('_', ' ')}: {val}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Resumen */}
  <div className="w-full px-6 py-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div onClick={() => goToExplorer()} className="cursor-pointer bg-gray-900/60 rounded-xl p-6 border border-gray-800 hover:border-gray-700 transition-colors transition-transform duration-200 hover:scale-[1.02] hover:shadow-lg hover:shadow-teal-900/20">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Total Empleados</p>
                <p className="text-2xl font-bold text-white">{(resumenConsolidado?.resumen?.total_empleados ?? datos?.resumen?.total_empleados) || 0}</p>
              </div>
              <Users className="w-8 h-8 text-teal-500" />
            </div>
          </div>
          
          <div onClick={() => goToExplorer('haber_imponible')} className="cursor-pointer bg-gray-900/60 rounded-xl p-6 border border-gray-800 hover:border-gray-700 transition-colors transition-transform duration-200 hover:scale-[1.02] hover:shadow-lg hover:shadow-emerald-900/20">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Haberes Imponibles</p>
                <p className="text-2xl font-bold text-green-400">
                  {formatearMonto(resumenConsolidado?.resumen?.total_haberes_imponibles)}
                </p>
              </div>
              <BarChart3 className="w-8 h-8 text-green-500" />
            </div>
          </div>
          
          <div onClick={() => goToExplorer('haber_no_imponible')} className="cursor-pointer bg-gray-900/60 rounded-xl p-6 border border-gray-800 hover:border-gray-700 transition-colors transition-transform duration-200 hover:scale-[1.02] hover:shadow-lg hover:shadow-emerald-900/20">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Haberes No Imponibles</p>
                <p className="text-2xl font-bold text-green-400">
                  {formatearMonto(resumenConsolidado?.resumen?.total_haberes_no_imponibles)}
                </p>
              </div>
              <PieIcon className="w-8 h-8 text-green-500" />
            </div>
          </div>
          
          <div onClick={() => goToExplorer()} className="cursor-pointer bg-gray-900/60 rounded-xl p-6 border border-gray-800 hover:border-gray-700 transition-colors transition-transform duration-200 hover:scale-[1.02] hover:shadow-lg hover:shadow-teal-900/20">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Líquido Total</p>
                <p className="text-2xl font-bold text-teal-400">
                  {formatearMonto(resumenConsolidado?.resumen?.liquido_total ?? datos?.resumen?.liquido_total)}
                </p>
              </div>
              <DollarSign className="w-8 h-8 text-teal-500" />
            </div>
          </div>
        </div>

        {/* Totales por categoría (Consolidado) */}
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-6 mb-2">
          <div onClick={() => goToExplorer('descuento_legal')} className="cursor-pointer bg-gray-900/60 rounded-xl p-4 border border-gray-800 hover:border-gray-700 transition-colors transition-transform duration-200 hover:scale-[1.02]">
            <p className="text-xs text-gray-400">Descuentos Legales</p>
            <p className="text-lg font-semibold text-red-400">{formatearMonto(resumenConsolidado?.resumen?.total_dctos_legales)}</p>
          </div>
          <div onClick={() => goToExplorer('otro_descuento')} className="cursor-pointer bg-gray-900/60 rounded-xl p-4 border border-gray-800 hover:border-gray-700 transition-colors transition-transform duration-200 hover:scale-[1.02]">
            <p className="text-xs text-gray-400">Otros Descuentos</p>
            <p className="text-lg font-semibold text-red-400">{formatearMonto(resumenConsolidado?.resumen?.total_otros_dctos)}</p>
          </div>
          <div onClick={() => goToExplorer('impuesto')} className="cursor-pointer bg-gray-900/60 rounded-xl p-4 border border-gray-800 hover:border-gray-700 transition-colors transition-transform duration-200 hover:scale-[1.02]">
            <p className="text-xs text-gray-400">Impuestos</p>
            <p className="text-lg font-semibold text-red-400">{formatearMonto(resumenConsolidado?.resumen?.total_impuestos)}</p>
          </div>
          <div onClick={() => goToExplorer('aporte_patronal')} className="cursor-pointer bg-gray-900/60 rounded-xl p-4 border border-gray-800 hover:border-gray-700 transition-colors transition-transform duration-200 hover:scale-[1.02]">
            <p className="text-xs text-gray-400">Aportes Patronales</p>
            <p className="text-lg font-semibold text-green-400">{formatearMonto(resumenConsolidado?.resumen?.total_aportes_patronales)}</p>
          </div>
          <div className="bg-gray-900/60 rounded-xl p-4 border border-gray-800 transition-transform duration-200 hover:scale-[1.01]">
            <p className="text-xs text-gray-400">Horas Extras (cant.)</p>
            <p className="text-lg font-semibold text-teal-400">{formatearNumero(resumenConsolidado?.resumen?.horas_extras_cantidad_total)}</p>
          </div>
          <div className="bg-gray-900/60 rounded-xl p-4 border border-gray-800 transition-transform duration-200 hover:scale-[1.01]">
            <p className="text-xs text-gray-400">Días Ausencia</p>
            <p className="text-lg font-semibold text-yellow-400">{formatearNumero(resumenConsolidado?.resumen?.dias_ausencia_total)}</p>
          </div>
        </div>

        {/* Gráficos */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
          {/* Barras de montos por categoría */}
          <div className="bg-gray-900/60 rounded-xl p-4 border border-gray-800 transition-transform duration-200 hover:scale-[1.005] hover:border-gray-700">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <BarChart3 size={16} className="text-gray-400" />
                <h3 className="text-sm font-medium text-gray-300">Montos por categoría</h3>
              </div>
              <span className="text-xs text-gray-500">(consolidado)</span>
            </div>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={montosChartData} margin={{ top: 8, right: 16, left: 28, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                  <XAxis dataKey="name" stroke="#9ca3af" tick={{ fontSize: 12 }} />
                  <YAxis stroke="#9ca3af" width={110} tickMargin={6} tickFormatter={(v) => formatearNumero(v)} tick={{ fontSize: 12 }} />
                  <RTooltip formatter={(v) => [formatearMonedaChilena(v), '']} cursor={{ fill: 'rgba(255,255,255,0.02)' }} />
                  <Bar dataKey="value" fill="#14b8a6" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Estados no activos (conteo) */}
          <div className="bg-gray-900/60 rounded-xl p-4 border border-gray-800 transition-transform duration-200 hover:scale-[1.005] hover:border-gray-700">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <PieIcon size={16} className="text-gray-400" />
                <h3 className="text-sm font-medium text-gray-300">Estados no activos (conteo)</h3>
              </div>
              <span className="text-xs text-gray-500">(período)</span>
            </div>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={estadoNoActivosData} layout="vertical" margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                  <XAxis type="number" stroke="#9ca3af" tick={{ fontSize: 12 }} />
                  <YAxis type="category" dataKey="name" stroke="#9ca3af" width={150} tick={{ fontSize: 12 }} />
                  <RTooltip formatter={(v) => [formatearNumero(v), '']} cursor={{ fill: 'rgba(255,255,255,0.02)' }} />
                  <Bar dataKey="value" fill="#60a5fa" radius={[0, 6, 6, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* Waterfall y Top Conceptos */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
          {/* Waterfall: bruto a líquido */}
          <div className="bg-gray-900/60 rounded-xl p-4 border border-gray-800 transition-transform duration-200 hover:scale-[1.005] hover:border-gray-700">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <BarChart3 size={16} className="text-gray-400" />
                <h3 className="text-sm font-medium text-gray-300">Composición: Bruto a Líquido</h3>
              </div>
              <span className="text-xs text-gray-500">(periodo)</span>
            </div>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={waterfallData} margin={{ top: 8, right: 16, left: 32, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                  <XAxis dataKey="name" stroke="#9ca3af" tick={{ fontSize: 12 }} />
                  <YAxis stroke="#9ca3af" width={120} tickMargin={6} tickFormatter={(v) => formatearNumero(v)} tick={{ fontSize: 12 }} />
                  <ReferenceLine y={0} stroke="#6b7280" />
                  <RTooltip formatter={(v, key) => [formatearMonedaChilena(v), key]} cursor={{ fill: 'rgba(255,255,255,0.02)' }} />
                  <Bar dataKey="add" stackId="stack" fill="#10b981" radius={[6, 6, 0, 0]} />
                  <Bar dataKey="sub" stackId="stack" fill="#f87171" radius={[6, 6, 0, 0]} />
                  <Bar dataKey="net" fill="#14b8a6" radius={[6, 6, 0, 0]} />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Top conceptos por monto */}
          <div className="bg-gray-900/60 rounded-xl p-4 border border-gray-800 transition-transform duration-200 hover:scale-[1.005] hover:border-gray-700">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <BarChart3 size={16} className="text-gray-400" />
                <h3 className="text-sm font-medium text-gray-300">Top conceptos (monto total)</h3>
              </div>
              <span className="text-xs text-gray-500">(periodo)</span>
            </div>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={topConceptosData} layout="vertical" margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                  <XAxis type="number" stroke="#9ca3af" tickFormatter={(v) => formatearNumero(v)} tick={{ fontSize: 12 }} />
                  <YAxis type="category" dataKey="name" stroke="#9ca3af" width={180} tick={{ fontSize: 12 }} />
                  <RTooltip formatter={(v) => [formatearMonedaChilena(v), '']} cursor={{ fill: 'rgba(255,255,255,0.02)' }} />
                  <Bar dataKey="value" fill="#8b5cf6" radius={[0, 6, 6, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
        {/* Explorador de conceptos (drilldown) */}
  <div ref={explorerRef} className="bg-gray-900/60 rounded-xl p-5 border border-gray-800 mb-8">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-medium text-gray-300">Explorador de conceptos</h3>
            <div className="flex items-center gap-3">
              <div className="relative w-72 max-w-full">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={14} />
                <input
                  type="text"
                  placeholder="Buscar concepto..."
                  value={conceptQuery}
                  onChange={(e) => setConceptQuery(e.target.value)}
                  className="w-full pl-9 pr-3 py-2 bg-gray-800/80 border border-gray-700 rounded-lg text-white focus:ring-2 focus:ring-teal-500 focus:border-transparent placeholder-gray-500 text-sm"
                />
              </div>
              <button
                onClick={() => setDense((d) => !d)}
                className={`text-xs px-3 py-1.5 rounded-full border transition-colors ${dense ? 'bg-teal-600/20 text-teal-300 border-teal-700' : 'bg-gray-900 text-gray-300 border-gray-700 hover:border-gray-600'}`}
                title="Cambiar densidad"
              >
                {dense ? 'Modo compacto' : 'Modo cómodo'}
              </button>
            </div>
          </div>

          {/* Categorías */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-3 mb-5">
      {CATEGORIAS.map(cat => (
              <button
                key={cat}
                onClick={() => setSelectedCat(cat)}
        className={`p-3 rounded-lg border transition-colors transition-transform duration-200 hover:scale-[1.01] text-left ${selectedCat === cat ? 'border-teal-700 bg-teal-900/10 ring-1 ring-teal-700/30 shadow shadow-teal-900/10' : 'border-gray-800 hover:border-gray-700 bg-gray-900/40'}`}
              >
                <div className="text-xs text-gray-400">{CATEGORIA_META[cat]?.label || cat}</div>
                <div className={`text-lg font-semibold ${CATEGORIA_META[cat]?.color || 'text-gray-300'}`}>{formatearMonto(conceptIndex.totales?.[cat] || 0)}</div>
              </button>
            ))}
          </div>

          {/* Lista de conceptos de la categoría seleccionada */}
          <div className="bg-gray-900/60 rounded-xl border border-gray-800 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-800/80 border-b border-gray-700">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                      <button onClick={() => setConceptSort(s => ({ key: 'name', dir: s.key === 'name' && s.dir === 'asc' ? 'desc' : 'asc' }))} className="inline-flex items-center gap-1">
                        Concepto <ArrowUpDown size={12} className="text-gray-400" />
                      </button>
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-300 uppercase tracking-wider">
                      <button onClick={() => setConceptSort(s => ({ key: 'total', dir: s.key === 'total' && s.dir === 'asc' ? 'desc' : 'asc' }))} className="inline-flex items-center gap-1">
                        Total <ArrowUpDown size={12} className="text-gray-400" />
                      </button>
                    </th>
                    <th className="px-4 py-3 text-right text-xs font-medium text-gray-300 uppercase tracking-wider">
                      <button onClick={() => setConceptSort(s => ({ key: 'count', dir: s.key === 'count' && s.dir === 'asc' ? 'desc' : 'asc' }))} className="inline-flex items-center gap-1">
                        Empleados <ArrowUpDown size={12} className="text-gray-400" />
                      </button>
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-800">
                  {(() => {
                    const conceptosRaw = Object.entries(conceptIndex.porCategoria?.[selectedCat] || {}).map(([name, obj]) => ({ name, total: obj.total, count: obj.empleados.length }));
                    const q = conceptQuery.trim().toLowerCase();
                    const filtrados = q ? conceptosRaw.filter(c => c.name.toLowerCase().includes(q)) : conceptosRaw;
                    const mult = conceptSort.dir === 'asc' ? 1 : -1;
                    filtrados.sort((a, b) => {
                      if (conceptSort.key === 'name') return a.name.localeCompare(b.name) * mult;
                      if (conceptSort.key === 'count') return (a.count - b.count) * mult;
                      return (a.total - b.total) * mult;
                    });
                    const totalConceptos = filtrados.length;
                    const totalPages = Math.max(1, Math.ceil(totalConceptos / conceptPageSize));
                    const page = Math.min(conceptPage, totalPages);
                    const start = (page - 1) * conceptPageSize;
                    const end = Math.min(start + conceptPageSize, totalConceptos);
                    const pageItems = filtrados.slice(start, end);
                    return (
                      <>
                        {pageItems.map((c) => (
                          <React.Fragment key={c.name}>
                            <tr className={`group hover:bg-gray-800 cursor-pointer ${selectedConcept === c.name ? 'bg-gray-900 ring-1 ring-teal-700/40' : 'odd:bg-gray-900/20'} transition-colors`} onClick={() => setSelectedConcept(prev => prev === c.name ? null : c.name)}>
                              <td className={`${denseClasses.pad} ${denseClasses.rowText} text-white`}>
                                <span className="inline-flex items-center gap-2">
                                  <ChevronDown className={`transition-transform duration-200 ${selectedConcept === c.name ? 'rotate-180' : 'rotate-0'} text-gray-400 group-hover:text-gray-300`} size={14} />
                                  {c.name}
                                </span>
                              </td>
                              <td className={`${denseClasses.pad} text-right ${denseClasses.rowText} text-teal-400 font-medium`}>{formatearMonto(c.total)}</td>
                              <td className={`${denseClasses.pad} text-right ${denseClasses.rowText} text-gray-300`}>{c.count}</td>
                            </tr>
                            {selectedConcept === c.name && (
                              <tr>
                                <td colSpan="3" className={`${dense ? 'px-3 py-2' : 'px-4 py-3'} bg-gray-900/50`}>
                                  {/* Toolbar de empleados del concepto */}
                                  <div className="flex items-center justify-between mb-2 transition-opacity duration-200">
                                    <div className="text-xs text-gray-400">Empleados con este concepto</div>
                                    <div className="relative w-64 max-w-full">
                                      <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={14} />
                                      <input
                                        type="text"
                                        placeholder="Buscar empleado o RUT..."
                                        value={conceptEmpQuery}
                                        onChange={(e) => setConceptEmpQuery(e.target.value)}
                                        className="w-full pl-9 pr-3 py-2 bg-gray-800/80 border border-gray-700 rounded-lg text-white focus:ring-2 focus:ring-teal-500 focus:border-transparent placeholder-gray-500 text-sm"
                                      />
                                    </div>
                                  </div>
                                  <div className="overflow-y-auto h-72 rounded-lg border border-gray-800 transition-all duration-200">
                                    <table className="w-full">
                                      <thead className="bg-gray-800/80 border-b border-gray-700 sticky top-0 z-10">
                                        <tr>
                                          <th className={`${dense ? 'px-3 py-2' : 'px-4 py-3'} text-left text-xs font-medium text-gray-300 uppercase tracking-wider`}>
                                            <button onClick={() => setConceptEmpSort(s => ({ key: 'nombre', dir: s.key === 'nombre' && s.dir === 'asc' ? 'desc' : 'asc' }))} className="inline-flex items-center gap-1">Empleado <ArrowUpDown size={12} className="text-gray-400" /></button>
                                          </th>
                                          <th className={`${dense ? 'px-3 py-2' : 'px-4 py-3'} text-left text-xs font-medium text-gray-300 uppercase tracking-wider`}>RUT</th>
                                          <th className={`${dense ? 'px-3 py-2' : 'px-4 py-3'} text-right text-xs font-medium text-gray-300 uppercase tracking-wider`}>
                                            <button onClick={() => setConceptEmpSort(s => ({ key: 'monto', dir: s.key === 'monto' && s.dir === 'asc' ? 'desc' : 'asc' }))} className="inline-flex items-center gap-1">Monto <ArrowUpDown size={12} className="text-gray-400" /></button>
                                          </th>
                                        </tr>
                                      </thead>
                                      <tbody className="divide-y divide-gray-800">
                                        {conceptEmpLoading ? (
                                          [...Array(6)].map((_, i) => (
                                            <tr key={i} className="animate-pulse">
                                              <td className={`${dense ? 'px-3 py-2' : 'px-4 py-3'}`}><div className="h-3 w-40 bg-gray-800 rounded" /></td>
                                              <td className={`${dense ? 'px-3 py-2' : 'px-4 py-3'}`}><div className="h-3 w-28 bg-gray-800 rounded" /></td>
                                              <td className={`${dense ? 'px-3 py-2' : 'px-4 py-3'} text-right`}><div className="ml-auto h-3 w-20 bg-gray-800 rounded" /></td>
                                            </tr>
                                          ))
                                        ) : (() => {
                                          const lista = conceptIndex.porCategoria[selectedCat][c.name]?.empleados || [];
                                          const q = conceptEmpQuery.trim().toLowerCase();
                                          const filtradosQ = q
                                            ? lista.filter(e => e.nombre.toLowerCase().includes(q) || (e.rut || '').toLowerCase().includes(q))
                                            : lista;
                                          const multEmp = conceptEmpSort.dir === 'asc' ? 1 : -1;
                                          const ordenados = [...filtradosQ].sort((a, b) => {
                                            if (conceptEmpSort.key === 'nombre') return a.nombre.localeCompare(b.nombre) * multEmp;
                                            return (a.monto - b.monto) * multEmp;
                                          });
                                          const eTotal = ordenados.length;
                                          const eTotalPages = Math.max(1, Math.ceil(eTotal / conceptEmpPageSize));
                                          const ePage = Math.min(conceptEmpPage, eTotalPages);
                                          const eStart = (ePage - 1) * conceptEmpPageSize;
                                          const eEnd = Math.min(eStart + conceptEmpPageSize, eTotal);
                                          const pageEmps = ordenados.slice(eStart, eEnd);
                                          return (
                                            <>
                                              {pageEmps.map(emp => (
                                                <tr key={`${emp.id}-${emp.rut}`} className={`hover:bg-gray-800 ${dense ? 'odd:bg-gray-900/10' : 'odd:bg-gray-900/20'}`}>
                                                  <td className={`${denseClasses.pad} ${denseClasses.rowText} text-white`}>{emp.nombre}</td>
                                                  <td className={`${denseClasses.pad} ${denseClasses.rowText} text-gray-300`}>
                                                    {emp.rut}
                                                    <button onClick={() => navigator.clipboard?.writeText?.(emp.rut)} className="ml-2 inline-flex items-center text-gray-500 hover:text-gray-300" title="Copiar RUT"><Copy size={14} /></button>
                                                  </td>
                                                  <td className={`${denseClasses.pad} text-right ${denseClasses.rowText} text-teal-400 font-medium`}>{formatearMonto(emp.monto)}</td>
                                                </tr>
                                              ))}
                                              <tr>
                                                <td colSpan="3" className={`${dense ? 'px-3 py-2' : 'px-4 py-3'}`}>
                                                  <div className="flex items-center justify-between text-xs text-gray-400">
                                                    <div>Mostrando {eStart + 1}-{eEnd} de {eTotal}</div>
                                                    <div className="flex items-center gap-2">
                                                      <div className="flex items-center gap-2">
                                                        <span>Por página</span>
                                                        <select value={conceptEmpPageSize} onChange={(e) => { setConceptEmpPageSize(Number(e.target.value)); setConceptEmpPage(1); }} className="bg-gray-800/80 border border-gray-700 rounded px-2 py-1">
                                                          <option value={10}>10</option>
                                                          <option value={20}>20</option>
                                                          <option value={50}>50</option>
                                                        </select>
                                                      </div>
                                                      <button onClick={() => setConceptEmpPage(p => Math.max(1, p - 1))} className="px-2 py-1 rounded border border-gray-700 text-gray-300 disabled:opacity-50" disabled={ePage <= 1}><ChevronLeft size={14} /></button>
                                                      <button onClick={() => setConceptEmpPage(p => p + 1)} className="px-2 py-1 rounded border border-gray-700 text-gray-300 disabled:opacity-50" disabled={ePage >= eTotalPages}><ChevronRight size={14} /></button>
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
                        {/* Footer de paginación */}
                        <tr>
                          <td colSpan="3" className="px-4 py-3">
                            <div className="flex items-center justify-between text-xs text-gray-400">
                              <div>Mostrando {start + 1}-{end} de {totalConceptos}</div>
                              <div className="flex items-center gap-2">
                                <div className="flex items-center gap-2">
                                  <span>Por página</span>
                                  <select value={conceptPageSize} onChange={(e) => { setConceptPageSize(Number(e.target.value)); setConceptPage(1); }} className="bg-gray-800/80 border border-gray-700 rounded px-2 py-1">
                                    <option value={10}>10</option>
                                    <option value={20}>20</option>
                                    <option value={50}>50</option>
                                  </select>
                                </div>
                                <button onClick={() => setConceptPage(p => Math.max(1, p - 1))} className="px-2 py-1 rounded border border-gray-700 text-gray-300 disabled:opacity-50" disabled={page <= 1}><ChevronLeft size={14} /></button>
                                <button onClick={() => setConceptPage(p => p + 1)} className="px-2 py-1 rounded border border-gray-700 text-gray-300 disabled:opacity-50" disabled={page >= totalPages}><ChevronRight size={14} /></button>
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
          </div>
        </div>

  {/* Detalle inline ahora se despliega dentro de la tabla de conceptos al hacer clic */}
        
      </div>
    </div>
  );
};

export default LibroRemuneraciones;
