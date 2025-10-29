import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import {
  obtenerCierresCliente,
  obtenerCierreMensual,
  obtenerEstadoCacheCierre,
  obtenerInformeCierre,
} from '../../api/nomina';
import { ArrowLeft, Calendar, BookOpen, Users2 } from 'lucide-react';
import LibroEmbed from '../../components/DashboardNomina/Embeds/LibroEmbed';
import MovimientosEmbed from '../../components/DashboardNomina/Embeds/MovimientosEmbed';
import DataSourceBadge from '../../components/DashboardNomina/common/DataSourceBadge';

// Util: calcula periodo anterior YYYY-MM
function periodoAnterior(periodo) {
  if (!periodo || !/^\d{4}-\d{2}$/.test(periodo)) return null;
  const [yStr, mStr] = periodo.split('-');
  let y = parseInt(yStr, 10);
  let m = parseInt(mStr, 10) - 1;
  if (m === 0) { m = 12; y -= 1; }
  return `${y}-${String(m).padStart(2, '0')}`;
}

const TABS = [
  { key: 'libro', label: 'Libro' },
  { key: 'movimientos', label: 'Movimientos' },
];

const NominaDashboard = () => {
  const { clienteId } = useParams();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  // URL state
  const tab = searchParams.get('tab') || 'libro';
  const periodo = searchParams.get('periodo') || '';

  // Estados
  const [initLoading, setInitLoading] = useState(true);
  const [cierreActual, setCierreActual] = useState(null);
  const [cierreAnterior, setCierreAnterior] = useState(null);
  const [resumenLibroActual, setResumenLibroActual] = useState(null);
  const [resumenLibroAnterior, setResumenLibroAnterior] = useState(null);
  const [movsActual, setMovsActual] = useState(null);
  const [movsAnterior, setMovsAnterior] = useState(null);
  const [cierresFinalizados, setCierresFinalizados] = useState([]);
  const [mensaje, setMensaje] = useState('');
  const [cargandoDatos, setCargandoDatos] = useState(false);
  const [informeMetaActual, setInformeMetaActual] = useState(null); // { source, fecha_generacion }
  const [informeMetaAnterior, setInformeMetaAnterior] = useState(null);

  // Cargar periodo por defecto: último cierre finalizado
  useEffect(() => {
    async function boot() {
      try {
        const cierres = await obtenerCierresCliente(clienteId);
        const finalizados = Array.isArray(cierres) ? cierres.filter(c => c.estado === 'finalizado') : [];
        finalizados.sort((a,b)=> (a.periodo < b.periodo ? 1 : -1));
        setCierresFinalizados(finalizados);
        if (!periodo) {
          const ultimo = finalizados[0];
          if (ultimo) {
            const next = new URLSearchParams(searchParams);
            next.set('periodo', ultimo.periodo);
            if (!next.get('tab')) next.set('tab', 'libro');
            setSearchParams(next, { replace: true });
            return; // Esperar a que cambie el periodo para continuar
          } else {
            setMensaje('No hay cierres finalizados para este cliente.');
          }
        }
      } finally {
        setInitLoading(false);
      }
    }
    boot();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [clienteId]);

  // Cargar cierres actual/anterior y validar estado finalizado
  useEffect(() => {
    async function cargarCierresYDatos() {
      if (!periodo) return;
      setCargandoDatos(true);
      setMensaje('');
      try {
        const actual = await obtenerCierreMensual(clienteId, periodo);
        if (!actual) {
          setMensaje('No existe un cierre para el período seleccionado.');
          setCierreActual(null);
          setResumenLibroActual(null);
          setMovsActual(null);
          return;
        }
        if (actual.estado !== 'finalizado') {
          setMensaje('Este período no está finalizado. Finaliza el cierre para ver el dashboard.');
          setCierreActual(actual);
          setResumenLibroActual(null);
          setMovsActual(null);
          // Igual mostramos meta del cierre sin datos
        } else {
          setCierreActual(actual);
          // Cargar informe completo y extraer bloques
          try {
            const informe = await obtenerInformeCierre(actual.id);
            console.log('🔍 Respuesta completa del informe:', informe);
            console.log('🎯 [Source Check] Extracción desde:', informe?.source, '| En cache:', informe?.en_cache);
            const libroAct = informe?.datos_cierre?.libro_resumen_v2 || null;
            const movAct = informe?.datos_cierre?.movimientos_v3 || null;
            setResumenLibroActual(libroAct);
            setMovsActual(movAct);
            setInformeMetaActual({ source: informe?.source || null, fecha_generacion: informe?.fecha_generacion || null });
            if (!libroAct && !movAct) setMensaje('Este cierre finalizado no tiene datos de informe.');
          } catch (err) {
            const status = err?.response?.status;
            if (status === 404) {
              setMensaje('Este cierre finalizado aún no tiene informe generado.');
            } else if (status === 400) {
              setMensaje('El cierre debe estar finalizado para consultar el informe.');
            } else {
              throw err;
            }
          }
        }

        // Cierre anterior (si finalizado)
        const perv = periodoAnterior(periodo);
        if (perv) {
          const ant = await obtenerCierreMensual(clienteId, perv);
          if (ant && ant.estado === 'finalizado') {
            setCierreAnterior(ant);
            const informeAnt = await obtenerInformeCierre(ant.id).catch(()=>null);
            const libroAnt = informeAnt?.datos_cierre?.libro_resumen_v2 || null;
            const movAnt = informeAnt?.datos_cierre?.movimientos_v3 || null;
            setResumenLibroAnterior(libroAnt);
            setMovsAnterior(movAnt);
            if (informeAnt) setInformeMetaAnterior({ source: informeAnt?.source || null, fecha_generacion: informeAnt?.fecha_generacion || null });
          } else {
            setCierreAnterior(null);
            setResumenLibroAnterior(null);
            setMovsAnterior(null);
            setInformeMetaAnterior(null);
          }
        } else {
          setCierreAnterior(null);
          setResumenLibroAnterior(null);
          setMovsAnterior(null);
          setInformeMetaAnterior(null);
        }
      } catch (e) {
        console.error(e);
        setMensaje('Error cargando datos del dashboard.');
      } finally {
        setCargandoDatos(false);
      }
    }
    cargarCierresYDatos();
  }, [clienteId, periodo]);

  // KPIs básicos desde libro_resumen_v2
  const kpis = useMemo(() => {
    const t = resumenLibroActual?.totales_categorias || {};
    const tPrev = resumenLibroAnterior?.totales_categorias || null;
    function delta(key){
      if (!tPrev) return null;
      const a = Number(t[key] || 0);
      const b = Number(tPrev[key] || 0);
      const d = a - b;
      const pct = b !== 0 ? (d / b) * 100 : null;
      return { d, pct };
    }
    return [
      { key: 'haber_imponible', label: 'Haberes Imponibles', value: Number(t.haber_imponible||0), delta: delta('haber_imponible') },
      { key: 'haber_no_imponible', label: 'Haberes No Imponibles', value: Number(t.haber_no_imponible||0), delta: delta('haber_no_imponible') },
      { key: 'descuento_legal', label: 'Descuentos Legales', value: Number(t.descuento_legal||0), delta: delta('descuento_legal') },
      { key: 'otro_descuento', label: 'Otros Descuentos', value: Number(t.otro_descuento||0), delta: delta('otro_descuento') },
      { key: 'aporte_patronal', label: 'Aportes Patronales', value: Number(t.aporte_patronal||0), delta: delta('aporte_patronal') },
    ];
  }, [resumenLibroActual, resumenLibroAnterior]);

  const onChangePeriodo = (e) => {
    const val = e.target.value; // YYYY-MM
    const next = new URLSearchParams(searchParams);
    next.set('periodo', val);
    setSearchParams(next);
  };

  const SelectorCierre = (
    <div className="flex items-center gap-2">
      <Calendar className="w-5 h-5 text-gray-400" />
      <select
        className="bg-gray-900 border border-gray-700 rounded-md px-3 py-2 text-sm text-gray-200 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        value={periodo || ''}
        onChange={(e)=>{
          const next = new URLSearchParams(searchParams);
          next.set('periodo', e.target.value);
          setSearchParams(next);
        }}
      >
        {cierresFinalizados.map(c => (
          <option key={c.id} value={c.periodo}>{c.periodo}</option>
        ))}
      </select>
    </div>
  );

  const onChangeTab = (nextTab) => {
    const next = new URLSearchParams(searchParams);
    next.set('tab', nextTab);
    setSearchParams(next);
  };

  const PeriodoSelector = (
    <div className="flex items-center gap-3">
      <Calendar className="w-5 h-5 text-gray-400" />
      <input
        type="month"
        value={periodo || ''}
        onChange={onChangePeriodo}
        className="bg-gray-900 border border-gray-700 rounded-md px-3 py-2 text-sm text-gray-200 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
      />
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* Header */}
      <div className="w-full px-6 py-4 border-b border-gray-800 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button onClick={() => navigate(-1)} className="p-2 rounded-md hover:bg-gray-800">
            <ArrowLeft className="w-5 h-5 text-gray-300" />
          </button>
          <h1 className="text-xl font-semibold">Dashboard Nómina</h1>
          {cierreActual && (
            <span className="text-sm text-gray-400 ml-2">Cliente #{cierreActual.cliente} • {periodo || cierreActual.periodo}</span>
          )}
          {informeMetaActual && (
            <div className="ml-3">
              <DataSourceBadge metadata={informeMetaActual} size="sm" />
            </div>
          )}
        </div>
        {SelectorCierre}
      </div>

      {/* Body */}
      <div className="w-full px-6 py-6 space-y-6">
        {/* Mensajes de estado */}
        {initLoading && (
          <div className="text-gray-400">Cargando...</div>
        )}
        {!initLoading && mensaje && (
          <div className="p-3 bg-yellow-900/20 border border-yellow-600/30 rounded-md text-yellow-300 text-sm">{mensaje}</div>
        )}

        {/* KPIs iniciales removidos; dejamos solo pestañas con dashboards completos */}

        {/* Tabs */}
        <div className="flex items-center gap-2 border-b border-gray-800">
          {TABS.map(t => (
            <button
              key={t.key}
              onClick={() => onChangeTab(t.key)}
              className={`px-4 py-2 -mb-px border-b-2 ${tab === t.key ? 'border-blue-500 text-white' : 'border-transparent text-gray-400 hover:text-gray-200'}`}
            >
              {t.label}
            </button>
          ))}
        </div>

        {/* Contenido de pestañas */}
        <div>
          {tab === 'libro' && (
            <div className="space-y-4">
              {cargandoDatos && <div className="text-gray-400">Cargando libro...</div>}
              {!cargandoDatos && cierreActual?.estado === 'finalizado' && resumenLibroActual ? (
                <div className="bg-gray-900/60 border border-gray-800 rounded-lg p-4">
                  <LibroEmbed resumenV2={resumenLibroActual} resumenAnterior={resumenLibroAnterior} />
                  {/* Se eliminó tabla comparativa explícita vs cierre anterior para Libro */}
                </div>
              ) : (
                <div className="text-gray-500 text-sm">Selecciona un período finalizado para ver el libro.</div>
              )}
            </div>
          )}

          {tab === 'movimientos' && (
            <div className="space-y-4">
              {cargandoDatos && <div className="text-gray-400">Cargando movimientos...</div>}
              {!cargandoDatos && cierreActual?.estado === 'finalizado' && movsActual ? (
                <div className="bg-gray-900/60 border border-gray-800 rounded-lg p-4">
                  <MovimientosEmbed bloque={movsActual} bloqueAnterior={movsAnterior} />
                  {/* Se eliminó tabla comparativa explícita vs cierre anterior para Movimientos */}
                </div>
              ) : (
                <div className="text-gray-500 text-sm">Selecciona un período finalizado para ver movimientos.</div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default NominaDashboard;
