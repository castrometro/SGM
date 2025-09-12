import React, { useEffect, useMemo, useRef, useState } from "react";
import { Users, DollarSign, FileSpreadsheet, AlertTriangle } from "lucide-react";
import { useNavigate } from 'react-router-dom';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, LineChart, Line, PieChart, Pie, Cell } from "recharts";
import { buildOrderedColorMap, BASE_PALETTE } from "../utils/dashboard/colors";
import { createBarTooltip, createPieTooltip, createLineTooltip } from "../utils/dashboard/tooltips.jsx";

// Clientes de ejemplo
const CLIENTES = [
  { id: "ebanx", nombre: "Ebanx" },
  { id: "frontier", nombre: "Frontier" },
  { id: "fraiser", nombre: "Fraiser" },
];

// Asignación demo de analistas por cliente (basado en ejemplos)
const CLIENTE_ANALISTA = {
  ebanx: "Pablo Isla",
  frontier: "Rodrigo Garcia",
  fraiser: "Eduardo Cortes",
};

// Genera facturas demo simples: { fecha: Date, monto: number, estado: "Pendiente"|"Emitida"|"Pagada" }
function generarFacturasDemo() {
  const mk = (y, m, d) => new Date(y, m, d);
  const hoy = new Date();
  const data = { ebanx: [], frontier: [], fraiser: [] };

  // Últimos 12 meses con variación
  for (let i = 0; i < 12; i++) {
    const d = new Date(hoy.getFullYear(), hoy.getMonth() - i, 1);
    const baseE = 550_000 + i * 35_000;
    const baseN = 420_000 + i * 28_000; // Frontier
    const baseF = 320_000 + i * 22_000; // Fraiser

    // Ebanx: más mezcla y algunos pendientes
    data.ebanx.push(
      { fecha: mk(d.getFullYear(), d.getMonth(), 8), monto: baseE, estado: i % 3 === 0 ? "Pendiente" : i % 4 === 0 ? "Pagada" : "Emitida" },
      { fecha: mk(d.getFullYear(), d.getMonth(), 20), monto: Math.round(baseE * 0.6), estado: i % 5 === 0 ? "Pendiente" : "Emitida" }
    );

    // Frontier: intermedio
    data.frontier.push(
      { fecha: mk(d.getFullYear(), d.getMonth(), 12), monto: baseN, estado: i % 4 === 0 ? "Pendiente" : i % 3 === 0 ? "Pagada" : "Emitida" }
    );

    // Fraiser: menor volumen, más al día
    data.fraiser.push(
      { fecha: mk(d.getFullYear(), d.getMonth(), 10), monto: baseF, estado: i % 4 === 0 ? "Pendiente" : i % 3 === 0 ? "Pagada" : "Emitida" }
    );
  }

  // Forzar mora (pendientes atrasadas)
  data.ebanx.push({ fecha: new Date(hoy.getFullYear(), hoy.getMonth() - 2, 5), monto: 920_000, estado: "Pendiente" });
  data.frontier.push({ fecha: new Date(hoy.getFullYear(), hoy.getMonth() - 3, 18), monto: 610_000, estado: "Pendiente" });
  data.fraiser.push({ fecha: new Date(hoy.getFullYear(), hoy.getMonth() - 1, 15), monto: 380_000, estado: "Pendiente" });

  return data;
}

const GestionCobranzav2 = () => {
  const navigate = useNavigate();
  const [clienteId, setClienteId] = useState("all");
  const [facturasByCliente] = useState(() => generarFacturasDemo());
  const [isKiosk, setIsKiosk] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(() => !!document.fullscreenElement);
  const [periodoCliente, setPeriodoCliente] = useState('all'); // usado por vista anterior (bar simple)
  const [rangoConteo, setRangoConteo] = useState('12m'); // '12m' | '6m' para serie temporal

  // IDs a considerar según filtro
  const idsSeleccionados = useMemo(() => (clienteId === "all" ? Object.keys(facturasByCliente) : [clienteId]), [clienteId, facturasByCliente]);

  // Métricas requeridas
  const { montoPendiente, countPendiente, clientesEnMora, montoEnMora } = useMemo(() => {
    const hoy = new Date();
    let montoPend = 0;
    let countPend = 0;
    let montoMora = 0;
    let clientesMoraCount = 0;

    for (const cid of idsSeleccionados) {
      const arr = facturasByCliente[cid] || [];
      let moraCliente = 0;
      for (const f of arr) {
        const st = String(f.estado || "").toLowerCase();
        if (st.includes("pend")) {
          const monto = Number(f.monto) || 0;
          montoPend += monto;
          countPend += 1;
          if (f.fecha instanceof Date && !isNaN(f.fecha) && f.fecha < hoy) {
            moraCliente += monto; // solo facturas pendientes vencidas
          }
        }
      }
      if (moraCliente > 0) {
        clientesMoraCount += 1;
        montoMora += moraCliente;
      }
    }

    return { montoPendiente: montoPend, countPendiente: countPend, clientesEnMora: clientesMoraCount, montoEnMora: montoMora };
  }, [idsSeleccionados, facturasByCliente]);

  // Leaderboard de analistas: porcentaje de facturas pagadas y monto cobrado
  const leaderboardAnalistas = useMemo(() => {
    const map = new Map(); // analista -> { pagadas, total, monto }
    for (const cid of idsSeleccionados) {
      const analista = CLIENTE_ANALISTA[cid] || "N/D";
      const arr = facturasByCliente[cid] || [];
      let entry = map.get(analista);
      if (!entry) { entry = { analista, pagadas: 0, total: 0, monto: 0 }; map.set(analista, entry); }
      for (const f of arr) {
        const st = String(f.estado || "").toLowerCase();
        if (st.includes("pag")) { entry.pagadas += 1; entry.monto += Number(f.monto) || 0; }
        entry.total += 1;
      }
    }
    const rows = Array.from(map.values()).map(r => ({
      analista: r.analista,
      porcentaje: r.total ? Math.round((r.pagadas / r.total) * 100) : 0,
      montoCobrado: r.monto,
    }));
    return rows.sort((a,b)=> b.porcentaje - a.porcentaje || b.montoCobrado - a.montoCobrado).slice(0,8);
  }, [idsSeleccionados, facturasByCliente]);

  // Delta de ranking del leaderboard
  const prevRanksRef = useRef(new Map());
  const leaderboardConDelta = useMemo(() => {
    const prev = prevRanksRef.current;
    return leaderboardAnalistas.map((r, idx) => {
      const rank = idx + 1;
      const prevRank = prev.get(r.analista);
      const delta = prevRank ? prevRank - rank : 0; // positivo = sube
      return { ...r, rank, delta };
    });
  }, [leaderboardAnalistas]);
  useEffect(() => {
    const map = new Map();
    leaderboardAnalistas.forEach((r, idx) => map.set(r.analista, idx + 1));
    prevRanksRef.current = map;
  }, [leaderboardAnalistas]);

  // Top clientes con deuda en mora
  const topClientesMora = useMemo(() => {
    const hoy = new Date();
    const rows = [];
    for (const cid of idsSeleccionados) {
      const arr = facturasByCliente[cid] || [];
      let mora = 0;
      for (const f of arr) {
        const st = String(f.estado || "").toLowerCase();
        if (!st.includes("pend")) continue;
        if (f.fecha instanceof Date && !isNaN(f.fecha) && f.fecha < hoy) {
          mora += Number(f.monto) || 0;
        }
      }
      rows.push({ cliente: CLIENTES.find(c=>c.id===cid)?.nombre || cid, mora });
    }
    return rows.filter(r=> r.mora>0).sort((a,b)=> b.mora - a.mora).slice(0,8);
  }, [idsSeleccionados, facturasByCliente]);

  // Map de colores por barra (top mora)
  const colorMapTopMora = useMemo(() => buildOrderedColorMap(topClientesMora, 'cliente', 'mora', BASE_PALETTE), [topClientesMora]);

  // Serie CxC por mes (Emitidas + Pendientes)
  const serieCXC = useMemo(() => {
    const hoy = new Date();
    const months = [];
    for (let i = 11; i >= 0; i--) {
      const d = new Date(hoy.getFullYear(), hoy.getMonth() - i, 1);
      const key = `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}`;
      const label = new Intl.DateTimeFormat('es-CL', { month: 'short' }).format(d);
      months.push({ key, label });
    }
    const sumByKey = new Map();
    for (const cid of idsSeleccionados) {
      const arr = facturasByCliente[cid] || [];
      for (const f of arr) {
        if (!(f.fecha instanceof Date) || isNaN(f.fecha)) continue;
        const st = String(f.estado || "").toLowerCase();
        if (!(st.includes("emit") || st.includes("pend"))) continue; // CxC
        const k = `${f.fecha.getFullYear()}-${String(f.fecha.getMonth()+1).padStart(2,'0')}`;
        sumByKey.set(k, (sumByKey.get(k) || 0) + (Number(f.monto)||0));
      }
    }
    return months.map(m => ({ mes: m.label, monto: sumByKey.get(m.key) || 0 }));
  }, [idsSeleccionados, facturasByCliente]);

  // Serie temporal por cliente: conteo de facturas cobradas vs por cobrar por mes (últimos 12 meses)
  const serieConteosCliente = useMemo(() => {
    if (clienteId === 'all') return [];
    const arr = facturasByCliente[clienteId] || [];
    const hoy = new Date();
    const months = [];
    for (let i = 11; i >= 0; i--) {
      const d = new Date(hoy.getFullYear(), hoy.getMonth() - i, 1);
      const key = `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}`;
      const label = new Intl.DateTimeFormat('es-CL', { month: 'short' }).format(d);
      months.push({ key, label });
    }
    const cntByKey = new Map(); // key -> { cobradas, porCobrar }
    for (const f of arr) {
      if (!(f.fecha instanceof Date) || isNaN(f.fecha)) continue;
      const k = `${f.fecha.getFullYear()}-${String(f.fecha.getMonth()+1).padStart(2,'0')}`;
      const st = String(f.estado || '').toLowerCase();
      const entry = cntByKey.get(k) || { cobradas: 0, porCobrar: 0 };
      if (st.includes('pag')) entry.cobradas += 1;
      else if (st.includes('pend')) entry.porCobrar += 1;
      cntByKey.set(k, entry);
    }
    return months.map(m => ({ mes: m.label, cobradas: cntByKey.get(m.key)?.cobradas || 0, porCobrar: cntByKey.get(m.key)?.porCobrar || 0 }));
  }, [clienteId, facturasByCliente]);

  const nombreClienteActual = clienteId === "all" ? "Todos los clientes" : (CLIENTES.find(c => c.id === clienteId)?.nombre || clienteId);

  const fmtMonto = (v) => v.toLocaleString("es-CL", { style: "currency", currency: "CLP", maximumFractionDigits: 0 });

  // Detectar modo kiosko por query param
  useEffect(() => {
    try {
      const params = new URLSearchParams(window.location.search);
      const k = params.get('kiosk');
      setIsKiosk(k === '1' || k === 'true');
    } catch {}
  }, []);

  // Escuchar cambios de pantalla completa
  useEffect(() => {
    const handler = () => setIsFullscreen(!!document.fullscreenElement);
    document.addEventListener('fullscreenchange', handler);
    return () => document.removeEventListener('fullscreenchange', handler);
  }, []);

  const enterFullscreen = () => {
    try { document.documentElement.requestFullscreen?.(); } catch {}
  };
  const exitFullscreen = () => {
    try { document.exitFullscreen?.(); } catch {}
  };

  const goToKiosk = () => {
    try {
      const url = new URL(window.location.href);
      url.searchParams.set('kiosk', '1');
      window.location.assign(url.toString());
    } catch {
      // Fallback simple
      window.location.search = '?kiosk=1';
    }
  };

  // Auto-rotación de cliente en kiosko
  useEffect(() => {
    if (!isKiosk) return;
    const seq = ['all', ...CLIENTES.map(c => c.id)];
    let idx = Math.max(0, seq.indexOf(clienteId));
    const t = setInterval(() => {
      idx = (idx + 1) % seq.length;
      setClienteId(seq[idx]);
    }, 3000);
    return () => clearInterval(t);
  }, [isKiosk, clienteId]);

  const chartH = isKiosk ? 'h-80' : 'h-64';
  const tableH = isKiosk ? 'max-h-80' : 'max-h-64';

  // Resumen por cliente (monto cobrado vs pendiente) para pie chart
  const resumenClienteMontos = useMemo(() => {
    if (clienteId === 'all') return { cobrado: 0, pendiente: 0 };
    const arr = facturasByCliente[clienteId] || [];
    let cobrado = 0, pendiente = 0;
    for (const f of arr) {
      const st = String(f.estado || '').toLowerCase();
      const monto = Number(f.monto) || 0;
      if (st.includes('pag')) cobrado += monto;
      else if (st.includes('pend')) pendiente += monto;
    }
    return { cobrado, pendiente };
  }, [clienteId, facturasByCliente]);

  // Resumen por cliente (conteo cobradas vs por cobrar) con periodo
  const resumenClienteConteos = useMemo(() => {
    if (clienteId === 'all') return { cobradas: 0, porCobrar: 0 };
    const arr = facturasByCliente[clienteId] || [];
    const now = new Date();
    const y = now.getFullYear();
    const m = now.getMonth();
    let cobradas = 0, porCobrar = 0;
    for (const f of arr) {
      if (!(f.fecha instanceof Date) || isNaN(f.fecha)) continue;
      if (periodoCliente === 'lastMonth' && !(f.fecha.getFullYear() === y && f.fecha.getMonth() === m)) continue;
      const st = String(f.estado || '').toLowerCase();
      if (st.includes('pag')) cobradas += 1;
      else if (st.includes('pend')) porCobrar += 1;
    }
    return { cobradas, porCobrar };
  }, [clienteId, facturasByCliente, periodoCliente]);

  // Tooltips reutilizables
  const MoraTooltip = useMemo(() => createBarTooltip({ getTotal: () => topClientesMora.reduce((a,b)=>a+(b.mora||0),0), labelValor: 'Mora', accentColor: '#f59e0b', borderColor: 'border-amber-600/40', valueFormatter: fmtMonto }), [topClientesMora]);
  const ConteosTooltip = useMemo(() => createBarTooltip({ getTotal: () => (resumenClienteConteos.cobradas + resumenClienteConteos.porCobrar), labelValor: 'Cantidad', accentColor: '#60a5fa', borderColor: 'border-blue-600/40', valueFormatter: (v)=> new Intl.NumberFormat('es-CL').format(v) }), [resumenClienteConteos]);
  const PieMontosTooltip = useMemo(() => createPieTooltip({ getTotal: () => (resumenClienteMontos.cobrado + resumenClienteMontos.pendiente), labelValor: 'Monto', accentColor: '#34d399', borderColor: 'border-emerald-600/40', valueFormatter: fmtMonto }), [resumenClienteMontos]);
  const LineValoresTooltip = useMemo(() => createLineTooltip({ labelValor: 'Monto', borderColor: 'border-emerald-600/40', valueFormatter: fmtMonto, titleFormatter: (l)=>`Mes: ${l}` }), []);

  return (
    <div className={`min-h-screen bg-gray-950 text-white ${isKiosk ? 'h-screen overflow-hidden' : ''}`}>
      {/* Controles de kiosko */}
      {isKiosk && !isFullscreen && (
        <div className="fixed top-2 right-2 z-50">
          <button onClick={enterFullscreen} className="px-3 py-1.5 text-xs rounded-md bg-teal-600 hover:bg-teal-500">Pantalla completa</button>
        </div>
      )}

      {/* Header simple (oculto en kiosko) */}
      {!isKiosk && (
        <div className="w-full px-6 pt-6">
          <div className="flex items-start justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold text-teal-400">Gestión de Cobranza (v2)</h1>
              <p className="text-gray-400 text-sm">Vista mínima: selector de cliente y totales clave.</p>
            </div>
            <div className="flex items-center gap-2">
              <button onClick={goToKiosk} className="px-3 py-1.5 text-xs rounded-md bg-indigo-600 hover:bg-indigo-500">Modo kiosko</button>
              <button onClick={enterFullscreen} className="px-3 py-1.5 text-xs rounded-md bg-teal-600 hover:bg-teal-500">Pantalla completa</button>
              {clienteId !== 'all' && (
                <button onClick={()=>navigate(`/menu/gestion-cobranza-v2/${clienteId}/facturas`)} className="px-3 py-1.5 text-xs rounded-md bg-amber-600 hover:bg-amber-500">Ver facturas</button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Contenido */}
      <div className="w-full px-6 py-6 space-y-6">
        {/* Selector de cliente (oculto en kiosko) */}
        {!isKiosk && (
          <div className="mb-2 bg-white/5 border border-white/10 rounded-xl p-3 flex flex-col md:flex-row md:items-center md:justify-between gap-3">
            <div className="flex items-center gap-3">
              <span className="text-sm text-gray-300">Cliente</span>
              <select
                value={clienteId}
                onChange={(e) => setClienteId(e.target.value)}
                className="bg-white/10 text-white rounded-lg px-3 py-2 outline-none border border-white/10 focus:border-blue-500 min-w-[220px]"
              >
                <option value="all">Todos los clientes</option>
                {CLIENTES.map((c) => (
                  <option key={c.id} value={c.id} className="bg-slate-900">
                    {c.nombre}
                  </option>
                ))}
              </select>
            </div>
            <div className="text-xs text-gray-400">Mostrando: {nombreClienteActual}</div>
          </div>
        )}
        {isKiosk && (
          <div className="text-xl text-white-400 -mt-2">Mostrando: {nombreClienteActual}</div>
        )}

        {/* Tarjetas de totales */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {/* Monto Total Pendiente por cobrar */}
          <div className="bg-gray-900/60 rounded-xl p-6 border border-gray-800 hover:border-gray-700 transition-colors">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Monto total pendiente por cobrar</p>
                <p className="text-2xl font-bold text-rose-300">{fmtMonto(montoPendiente)}</p>
                <p className="text-xs text-gray-500 mt-1">{nombreClienteActual}</p>
              </div>
              <DollarSign className="w-8 h-8 text-rose-400" />
            </div>
          </div>

          {/* Total de Facturas por cobrar (conteo pendientes) */}
          <div className="bg-gray-900/60 rounded-xl p-6 border border-gray-800 hover:border-gray-700 transition-colors">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Total de facturas por cobrar</p>
                <p className="text-2xl font-bold text-emerald-300">{countPendiente}</p>
                <p className="text-xs text-gray-500 mt-1">Solo facturas pendientes</p>
              </div>
              <FileSpreadsheet className="w-8 h-8 text-emerald-400" />
            </div>
          </div>

          {/* Cantidad de clientes en mora */}
          <div className="bg-gray-900/60 rounded-xl p-6 border border-gray-800 hover:border-gray-700 transition-colors">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Clientes en mora</p>
                <p className="text-2xl font-bold text-blue-300">{clientesEnMora}</p>
                <p className="text-xs text-gray-500 mt-1">Al menos una factura pendiente vencida</p>
              </div>
              <Users className="w-8 h-8 text-blue-400" />
            </div>
          </div>

          {/* Monto total en mora (pendientes vencidas) */}
          <div className="bg-gray-900/60 rounded-xl p-6 border border-gray-800 hover:border-gray-700 transition-colors">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Monto en mora</p>
                <p className="text-2xl font-bold text-amber-300">{fmtMonto(montoEnMora)}</p>
                <p className="text-xs text-gray-500 mt-1">Suma de facturas pendientes vencidas</p>
              </div>
              <AlertTriangle className="w-8 h-8 text-amber-400" />
            </div>
          </div>
        </div>

        {/* Gráficos */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Panel izquierdo: Global = leaderboard | Cliente = pie cobrado vs pendiente */}
          {clienteId === 'all' ? (
            <div className="bg-white/5 border border-white/10 rounded-xl p-4">
              <div className="flex items-center gap-2 mb-3">
                <Users className="w-5 h-5 text-sky-400" />
                <h3 className="text-lg font-semibold">Leaderboard</h3>
              </div>
              <div className="max-h-64 overflow-auto rounded-lg border border-white/5">
                <table className="w-full text-sm">
                  <thead className="bg-white/5 text-gray-300">
                    <tr>
                      <th className="px-3 py-2 text-left">Pos</th>
                      <th className="px-3 py-2 text-left">Vendedor(a)</th>
                      <th className="px-3 py-2 text-right">Monto cobrado</th>
                      <th className="px-3 py-2 text-right">% cobradas</th>
                      <th className="px-3 py-2 text-right">Δ puesto</th>
                    </tr>
                  </thead>
                  <tbody>
                    {leaderboardConDelta.map((r) => (
                      <tr key={r.analista} className="odd:bg-white/0 even:bg-white/5">
                        <td className="px-3 py-2">{r.rank}</td>
                        <td className="px-3 py-2">{r.analista}</td>
                        <td className="px-3 py-2 text-right">{fmtMonto(r.montoCobrado)}</td>
                        <td className="px-3 py-2 text-right">{r.porcentaje}%</td>
                        <td className="px-3 py-2 text-right">
                          {r.delta === 0 ? (
                            <span className="text-gray-400">–</span>
                          ) : r.delta > 0 ? (
                            <span className="text-emerald-400">▲ {r.delta}</span>
                          ) : (
                            <span className="text-rose-400">▼ {Math.abs(r.delta)}</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="mt-2 text-xs text-gray-400">El Δ compara con el ranking anterior durante esta sesión.</div>
            </div>
          ) : (
            <div className="bg-white/5 border border-white/10 rounded-xl p-4">
              <div className="flex items-center gap-2 mb-3">
                <FileSpreadsheet className="w-5 h-5 text-emerald-400" />
                <h3 className="text-lg font-semibold">Recaudado vs pendiente</h3>
              </div>
              <div className={`${chartH} select-none cursor-default relative`}>
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Tooltip wrapperStyle={{ zIndex: 50 }} content={<PieMontosTooltip />} />
                    <Pie
                      dataKey="value"
                      nameKey="name"
                      data={[
                        { name: 'Recaudado', value: resumenClienteMontos.cobrado },
                        { name: 'Pendiente', value: resumenClienteMontos.pendiente },
                      ]}
                      innerRadius="62%"
                      outerRadius="84%"
                      startAngle={90}
                      endAngle={450}
                      paddingAngle={2}
                      labelLine={false}
                    >
                      <Cell fill="#34d399" stroke="#0f172a" strokeWidth={2} />
                      <Cell fill="#f43f5e" stroke="#0f172a" strokeWidth={2} />
                    </Pie>
                  </PieChart>
                </ResponsiveContainer>
                {/* Etiqueta central por encima del donut, pero bajo el tooltip */}
                {(() => {
                  const total = (resumenClienteMontos.cobrado || 0) + (resumenClienteMontos.pendiente || 0);
                  const pct = total > 0 ? Math.round((resumenClienteMontos.cobrado / total) * 100) : 0;
                  return (
                    <div className="absolute inset-0 z-10 flex flex-col items-center justify-center pointer-events-none">
                      <div className={`font-bold ${isKiosk ? 'text-4xl' : 'text-3xl'} text-slate-100 tabular-nums drop-shadow-md`}>{pct}%</div>
                      <div className={`mt-1 ${isKiosk ? 'text-sm' : 'text-xs'} text-slate-300`}>Total {fmtMonto(total)}</div>
                    </div>
                  );
                })()}
              </div>
            </div>
          )}

          {/* Panel derecho: Global = top mora | Cliente = cobradas vs por cobrar con toggle */}
          {clienteId === 'all' ? (
            <div className="bg-white/5 border border-white/10 rounded-xl p-4">
              <div className="flex items-center gap-2 mb-3">
                <AlertTriangle className="w-5 h-5 text-amber-400" />
                <h3 className="text-lg font-semibold">Top clientes con mora</h3>
              </div>
              <div className={`${chartH} select-none cursor-default`}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={topClientesMora} layout="vertical" margin={{ top: 5, right: 10, left: 20, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                    <XAxis type="number" tick={{ fill: "#cbd5e1" }} />
                    <YAxis dataKey="cliente" type="category" tick={{ fill: "#cbd5e1" }} width={100} />
                    <Tooltip content={<MoraTooltip />} />
                    <Bar dataKey="mora" radius={[0,6,6,0]}>
                      {topClientesMora.map((entry) => (
                        <Cell key={entry.cliente} fill={colorMapTopMora[entry.cliente]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          ) : (
            <div className="bg-white/5 border border-white/10 rounded-xl p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <Users className="w-5 h-5 text-sky-400" />
                  <h3 className="text-lg font-semibold">Cobradas vs por cobrar en el tiempo</h3>
                </div>
                <div className="inline-flex bg-white/10 rounded-lg p-1 text-xs">
                  {[
                    { v: '12m', label: '12 meses' },
                    { v: '6m', label: '6 meses' },
                  ].map(opt => (
                    <button key={opt.v} onClick={() => setRangoConteo(opt.v)} className={`px-2 py-0.5 rounded-md ${rangoConteo === opt.v ? 'bg-blue-600' : 'hover:bg-white/10'}`}>
                      {opt.label}
                    </button>
                  ))}
                </div>
              </div>
              <div className={`${chartH} select-none cursor-default`}>
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={rangoConteo === '6m' ? serieConteosCliente.slice(-6) : serieConteosCliente} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                    <XAxis dataKey="mes" tick={{ fill: "#cbd5e1" }} />
                    <YAxis tick={{ fill: "#cbd5e1" }} allowDecimals={false} />
                    <Tooltip content={<LineValoresTooltip />} wrapperStyle={{ zIndex: 50 }} />
                    <Line type="monotone" dataKey="cobradas" name="Cobradas" stroke="#34d399" strokeWidth={2} dot={{ r: 3 }} />
                    <Line type="monotone" dataKey="porCobrar" name="Por cobrar" stroke="#60a5fa" strokeWidth={2} dot={{ r: 3 }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {/* CxC por meses (línea) */}
          <div className="bg-white/5 border border-white/10 rounded-xl p-4 lg:col-span-2">
            <div className="flex items-center gap-2 mb-3">
              <FileSpreadsheet className="w-5 h-5 text-emerald-400" />
              <h3 className="text-lg font-semibold">CxC por meses</h3>
            </div>
            <div className={`${chartH} select-none cursor-default`}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={serieCXC} margin={{ top: 5, right: 10, left: 8, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="mes" tick={{ fill: "#cbd5e1" }} />
                  <YAxis tick={{ fill: "#cbd5e1" }} tickFormatter={fmtMonto} width={110} />
                  <Tooltip content={<LineValoresTooltip />} wrapperStyle={{ zIndex: 50 }} />
                  <Line type="monotone" dataKey="monto" stroke="#34d399" strokeWidth={2} dot={{ r: 3 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GestionCobranzav2;
