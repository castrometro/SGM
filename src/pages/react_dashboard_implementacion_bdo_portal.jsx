import React, { useMemo, useState } from "react";
import * as XLSX from "xlsx";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
  PieChart,
  Pie,
  Cell,
} from "recharts";

/**
 * Implementación BDO Portal – Dashboard (React + Tailwind + Recharts)
 *
 * Instrucciones rápidas:
 * 1) npm i xlsx recharts
 * 2) Asegúrate de tener Tailwind configurado (https://tailwindcss.com/docs/guides/vite)
 * 3) Importa y usa <ImplementacionBDODashboard /> en tu App.
 * 4) Sube el Excel (botón "Cargar Excel"), elige "Todos" o un país específico.
 */

// === Paleta de colores consistente para series ===
const COLORS = {
  activos: "#0ea5e9", // sky
  propia: "#10b981", // emerald
  aImplementar: "#22c55e", // green
  creados: "#6366f1", // indigo
  activa: "#f59e0b", // amber
  tareasInternas: "#06b6d4", // cyan
  tareasExternas: "#ef4444", // red
  pctInicial: "#84cc16", // lime
  pctCompleta: "#a855f7", // purple
  revision: "#14b8a6", // teal
  actualizacion: "#e11d48", // rose
  axis: "#cbd5e1",
  grid: "#334155",
};

const PALETTE = [
  "#6366f1", // Indigo
  "#22c55e", // Green
  "#f59e0b", // Amber
  "#06b6d4", // Cyan
  "#ef4444", // Red
  "#84cc16", // Lime
  "#a855f7", // Purple
  "#10b981", // Emerald
  "#f472b6", // Pink
];

// === Seed (agregado por país) basado en tu Excel ===
const SEED_BY_COUNTRY = [
  { "PAIS": "Brasil", " CLIENTES BSO ACTIVOS": 280.0, "CLIENTES CON HERRAMIENTA PROPIA": 15.0, "PORTALES A IMPLEMENTAR": 265, "PORTALES CREADOS": 1.0, "PORTALES CON INTERACCIÓN ACTIVA": 1.0, "PORTALES EN LOS QUE UTILIZAN TAREAS INTERNAS BDO": 1.0, "PORTALES EN LOS QUE UTILIZAN TAREAS/TEMPLATE CON CLIENTES EXTERNOS": 1.0, "% DE IMPLEMENTACIÓN INICIAL": 0.0037735849056603, "% DE IMPLEMENTACIÓN COMPLETA": 0.0037735849056603 },
  { "PAIS": "Chile", " CLIENTES BSO ACTIVOS": 132.0, "CLIENTES CON HERRAMIENTA PROPIA": 1.0, "PORTALES A IMPLEMENTAR": 131, "PORTALES CREADOS": 125.0, "PORTALES CON INTERACCIÓN ACTIVA": 125.0, "PORTALES EN LOS QUE UTILIZAN TAREAS INTERNAS BDO": 0.0, "PORTALES EN LOS QUE UTILIZAN TAREAS/TEMPLATE CON CLIENTES EXTERNOS": 0.0, "% DE IMPLEMENTACIÓN INICIAL": 0.9541984732824428, "% DE IMPLEMENTACIÓN COMPLETA": 0.0 },
  { "PAIS": "Costa Rica", " CLIENTES BSO ACTIVOS": 57.0, "CLIENTES CON HERRAMIENTA PROPIA": 4.0, "PORTALES A IMPLEMENTAR": 53, "PORTALES CREADOS": 30.0, "PORTALES CON INTERACCIÓN ACTIVA": 30.0, "PORTALES EN LOS QUE UTILIZAN TAREAS INTERNAS BDO": 0.0, "PORTALES EN LOS QUE UTILIZAN TAREAS/TEMPLATE CON CLIENTES EXTERNOS": 0.0, "% DE IMPLEMENTACIÓN INICIAL": 0.5660377358490566, "% DE IMPLEMENTACIÓN COMPLETA": 0.0 },
  { "PAIS": "Ecuador", " CLIENTES BSO ACTIVOS": 49.0, "CLIENTES CON HERRAMIENTA PROPIA": 1.0, "PORTALES A IMPLEMENTAR": 48, "PORTALES CREADOS": 3.0, "PORTALES CON INTERACCIÓN ACTIVA": 2.0, "PORTALES EN LOS QUE UTILIZAN TAREAS INTERNAS BDO": 2.0, "PORTALES EN LOS QUE UTILIZAN TAREAS/TEMPLATE CON CLIENTES EXTERNOS": 2.0, "% DE IMPLEMENTACIÓN INICIAL": 0.0625, "% DE IMPLEMENTACIÓN COMPLETA": 0.041666666666666664 },
  { "PAIS": "El Salvador", " CLIENTES BSO ACTIVOS": 19.0, "CLIENTES CON HERRAMIENTA PROPIA": 1.0, "PORTALES A IMPLEMENTAR": 18, "PORTALES CREADOS": 15.0, "PORTALES CON INTERACCIÓN ACTIVA": 15.0, "PORTALES EN LOS QUE UTILIZAN TAREAS INTERNAS BDO": 0.0, "PORTALES EN LOS QUE UTILIZAN TAREAS/TEMPLATE CON CLIENTES EXTERNOS": 0.0, "% DE IMPLEMENTACIÓN INICIAL": 0.8333333333333334, "% DE IMPLEMENTACIÓN COMPLETA": 0.0 },
  { "PAIS": "Guatemala", " CLIENTES BSO ACTIVOS": 20.0, "CLIENTES CON HERRAMIENTA PROPIA": 0.0, "PORTALES A IMPLEMENTAR": 20, "PORTALES CREADOS": 12.0, "PORTALES CON INTERACCIÓN ACTIVA": 12.0, "PORTALES EN LOS QUE UTILIZAN TAREAS INTERNAS BDO": 0.0, "PORTALES EN LOS QUE UTILIZAN TAREAS/TEMPLATE CON CLIENTES EXTERNOS": 0.0, "% DE IMPLEMENTACIÓN INICIAL": 0.6, "% DE IMPLEMENTACIÓN COMPLETA": 0.0 },
  { "PAIS": "Honduras", " CLIENTES BSO ACTIVOS": 20.0, "CLIENTES CON HERRAMIENTA PROPIA": 0.0, "PORTALES A IMPLEMENTAR": 20, "PORTALES CREADOS": 2.0, "PORTALES CON INTERACCIÓN ACTIVA": 2.0, "PORTALES EN LOS QUE UTILIZAN TAREAS INTERNAS BDO": 0.0, "PORTALES EN LOS QUE UTILIZAN TAREAS/TEMPLATE CON CLIENTES EXTERNOS": 0.0, "% DE IMPLEMENTACIÓN INICIAL": 0.1, "% DE IMPLEMENTACIÓN COMPLETA": 0.0 },
  { "PAIS": "México", " CLIENTES BSO ACTIVOS": 377.0, "CLIENTES CON HERRAMIENTA PROPIA": 15.0, "PORTALES A IMPLEMENTAR": 362, "PORTALES CREADOS": 227.0, "PORTALES CON INTERACCIÓN ACTIVA": 227.0, "PORTALES EN LOS QUE UTILIZAN TAREAS INTERNAS BDO": 57.0, "PORTALES EN LOS QUE UTILIZAN TAREAS/TEMPLATE CON CLIENTES EXTERNOS": 291.0, "% DE IMPLEMENTACIÓN INICIAL": 0.6270718232044199, "% DE IMPLEMENTACIÓN COMPLETA": 0.8066298342541437 },
  { "PAIS": "Nicaragua", " CLIENTES BSO ACTIVOS": 32.0, "CLIENTES CON HERRAMIENTA PROPIA": 1.0, "PORTALES A IMPLEMENTAR": 31, "PORTALES CREADOS": 16.0, "PORTALES CON INTERACCIÓN ACTIVA": 1.0, "PORTALES EN LOS QUE UTILIZAN TAREAS INTERNAS BDO": 0.0, "PORTALES EN LOS QUE UTILIZAN TAREAS/TEMPLATE CON CLIENTES EXTERNOS": 0.0, "% DE IMPLEMENTACIÓN INICIAL": 0.5161290322580645, "% DE IMPLEMENTACIÓN COMPLETA": 0.03225806451612903 },
  { "PAIS": "Panamá", " CLIENTES BSO ACTIVOS": 38.0, "CLIENTES CON HERRAMIENTA PROPIA": 0.0, "PORTALES A IMPLEMENTAR": 38, "PORTALES CREADOS": 14.0, "PORTALES CON INTERACCIÓN ACTIVA": 13.0, "PORTALES EN LOS QUE UTILIZAN TAREAS INTERNAS BDO": 0.0, "PORTALES EN LOS QUE UTILIZAN TAREAS/TEMPLATE CON CLIENTES EXTERNOS": 0.0, "% DE IMPLEMENTACIÓN INICIAL": 0.34210526315789475, "% DE IMPLEMENTACIÓN COMPLETA": 0.3157894736842105 },
  { "PAIS": "Paraguay", " CLIENTES BSO ACTIVOS": 20.0, "CLIENTES CON HERRAMIENTA PROPIA": 0.0, "PORTALES A IMPLEMENTAR": 20, "PORTALES CREADOS": 14.0, "PORTALES CON INTERACCIÓN ACTIVA": 14.0, "PORTALES EN LOS QUE UTILIZAN TAREAS INTERNAS BDO": 0.0, "PORTALES EN LOS QUE UTILIZAN TAREAS/TEMPLATE CON CLIENTES EXTERNOS": 0.0, "% DE IMPLEMENTACIÓN INICIAL": 0.7, "% DE IMPLEMENTACIÓN COMPLETA": 0.7 },
  { "PAIS": "Perú", " CLIENTES BSO ACTIVOS": 226.0, "CLIENTES CON HERRAMIENTA PROPIA": 7.0, "PORTALES A IMPLEMENTAR": 219, "PORTALES CREADOS": 207.0, "PORTALES CON INTERACCIÓN ACTIVA": 203.0, "PORTALES EN LOS QUE UTILIZAN TAREAS INTERNAS BDO": 2.0, "PORTALES EN LOS QUE UTILIZAN TAREAS/TEMPLATE CON CLIENTES EXTERNOS": 55.0, "% DE IMPLEMENTACIÓN INICIAL": 0.9452054794520548, "% DE IMPLEMENTACIÓN COMPLETA": 0.9269406392694064 },
  { "PAIS": "República Dominicana", " CLIENTES BSO ACTIVOS": 35.0, "CLIENTES CON HERRAMIENTA PROPIA": 1.0, "PORTALES A IMPLEMENTAR": 34, "PORTALES CREADOS": 12.0, "PORTALES CON INTERACCIÓN ACTIVA": 12.0, "PORTALES EN LOS QUE UTILIZAN TAREAS INTERNAS BDO": 0.0, "PORTALES EN LOS QUE UTILIZAN TAREAS/TEMPLATE CON CLIENTES EXTERNOS": 0.0, "% DE IMPLEMENTACIÓN INICIAL": 0.35294117647058826, "% DE IMPLEMENTACIÓN COMPLETA": 0.35294117647058826 },
  { "PAIS": "Uruguay", " CLIENTES BSO ACTIVOS": 45.0, "CLIENTES CON HERRAMIENTA PROPIA": 3.0, "PORTALES A IMPLEMENTAR": 42, "PORTALES CREADOS": 2.0, "PORTALES CON INTERACCIÓN ACTIVA": 2.0, "PORTALES EN LOS QUE UTILIZAN TAREAS INTERNAS BDO": 5.0, "PORTALES EN LOS QUE UTILIZAN TAREAS/TEMPLATE CON CLIENTES EXTERNOS": 19.0, "% DE IMPLEMENTACIÓN INICIAL": 0.047619047619047616, "% DE IMPLEMENTACIÓN COMPLETA": 0.047619047619047616 },
];

const SEED_TOTALS = {
  " CLIENTES BSO ACTIVOS": 1350.0,
  "CLIENTES CON HERRAMIENTA PROPIA": 48.0,
  "PORTALES A IMPLEMENTAR": 1302.0,
  "PORTALES CREADOS": 834.0,
  "PORTALES CON INTERACCIÓN ACTIVA": 705.0,
  "PORTALES EN LOS QUE UTILIZAN TAREAS INTERNAS BDO": 67.0,
  "PORTALES EN LOS QUE UTILIZAN TAREAS/TEMPLATE CON CLIENTES EXTERNOS": 368.0,
  "% DE IMPLEMENTACIÓN INICIAL": 0.5479659842913014,
  "% DE IMPLEMENTACIÓN COMPLETA": 0.24141145143681664,
  // Si el Excel trae estas dos columnas como %/Sí/No, las promediamos al cargar
  "REVISIÓN DE ALERTAS Y CORREOS": 0,
  "ACTUALIZACIÓN DE ESTADOS DE TAREAS": 0,
};

// Column keys as they appear in Excel
const COLS = {
  pais: "PAIS",
  activos: " CLIENTES BSO ACTIVOS",
  propia: "CLIENTES CON HERRAMIENTA PROPIA",
  aImplementar: "PORTALES A IMPLEMENTAR",
  creados: "PORTALES CREADOS",
  activa: "PORTALES CON INTERACCIÓN ACTIVA",
  tareasInternas: "PORTALES EN LOS QUE UTILIZAN TAREAS INTERNAS BDO",
  tareasExternas: "PORTALES EN LOS QUE UTILIZAN TAREAS/TEMPLATE CON CLIENTES EXTERNOS",
  pctInicial: "% DE IMPLEMENTACIÓN INICIAL",
  pctCompleta: "% DE IMPLEMENTACIÓN COMPLETA",
  revisionAlertas: "REVISIÓN DE ALERTAS Y CORREOS",
  actualizacionEstados: "ACTUALIZACIÓN DE ESTADOS DE TAREAS",
};

function toNumber(value) {
  if (value == null) return 0;
  if (typeof value === "number" && !Number.isNaN(value)) return value;
  const s = String(value).replace("%", "").replace(/\./g, "").replace(",", ".");
  const n = Number(s);
  return Number.isFinite(n) ? n : 0;
}

function asPercent01(v) {
  const n = Number(v);
  if (!Number.isFinite(n)) return 0;
  if (n > 1) return n / 100;
  if (n < 0) return 0;
  return n;
}

function boolish01(v) {
  if (v == null) return null;
  if (typeof v === "number") {
    // Si dan 0-1 o 0-100
    if (v <= 1) return Math.max(0, Math.min(1, v));
    if (v <= 100) return v / 100;
    return 1; // cualquier número grande lo tomamos como true
  }
  const s = String(v).trim().toLowerCase();
  if (!s) return null;
  if (["si", "sí", "ok", "true", "x", "1", "hecho", "listo", "activo", "activa"].includes(s)) return 1;
  if (["no", "false", "0"].includes(s)) return 0;
  // Si viene como porcentaje "45%"
  if (s.endsWith("%")) return asPercent01(toNumber(s));
  // Si es cualquier otro texto no lo contamos
  return null;
}

function avg01(arr) {
  const clean = arr.filter((x) => x != null && Number.isFinite(Number(x)));
  if (!clean.length) return 0;
  const sum = clean.reduce((a, b) => a + Number(b), 0);
  return sum / clean.length;
}

function downloadJSON(filename, data) {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

function StatCard({ title, value, subtitle, children }) {
  return (
    <div className="rounded-2xl bg-slate-900/60 border border-slate-700 p-4 shadow">
      <div className="text-slate-300 text-sm">{title}</div>
      <div className="text-3xl font-semibold text-white mt-1">{value}</div>
      {subtitle && <div className="text-slate-400 text-xs mt-1">{subtitle}</div>}
      {children}
    </div>
  );
}

function Progress({ value, color = COLORS.creados }) {
  return (
    <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden mt-3">
      <div className="h-full" style={{ width: `${Math.min(Math.max(value, 0), 100)}%`, background: color }} />
    </div>
  );
}

export default function ImplementacionBDODashboard() {
  const [byCountry, setByCountry] = useState(SEED_BY_COUNTRY);
  const [totals, setTotals] = useState(SEED_TOTALS);
  const [query, setQuery] = useState("");
  const [selectedCountry, setSelectedCountry] = useState("ALL");

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    const arr = q
      ? byCountry.filter((r) => String(r[COLS.pais]).toLowerCase().includes(q))
      : byCountry;
    return [...arr].sort((a, b) => toNumber(b[COLS.aImplementar]) - toNumber(a[COLS.aImplementar]));
  }, [byCountry, query]);

  const selectedRow = useMemo(() => {
    if (selectedCountry === "ALL") return null;
    return byCountry.find((r) => String(r[COLS.pais]) === selectedCountry) || null;
  }, [selectedCountry, byCountry]);

  const kpis = useMemo(() => {
    const src = selectedRow || totals || {};
    const activos = toNumber(src[COLS.activos]);
    const propia = toNumber(src[COLS.propia]);
    const aImpl = toNumber(src[COLS.aImplementar]);
    const cread = toNumber(src[COLS.creados]);
    const activa = toNumber(src[COLS.activa]);

    const promInicial = asPercent01(toNumber(src[COLS.pctInicial])) * 100;
    const promCompleta = asPercent01(toNumber(src[COLS.pctCompleta])) * 100;

    const rev = asPercent01(src[COLS.revisionAlertas]) * 100;
    const act = asPercent01(src[COLS.actualizacionEstados]) * 100;

    const tasaActivacionSobreCreados = cread > 0 ? (activa / cread) * 100 : 0;
    const avanceCreadosSobrePlan = aImpl > 0 ? (cread / aImpl) * 100 : 0;
    const ratioPropia = activos > 0 ? (propia / activos) * 100 : 0;

    return {
      activos,
      propia,
      aImpl,
      cread,
      activa,
      promInicial,
      promCompleta,
      tasaActivacionSobreCreados,
      avanceCreadosSobrePlan,
      ratioPropia,
      rev,
      act,
    };
  }, [totals, selectedRow]);

  function handleExcel(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (evt) => {
      const data = new Uint8Array(evt.target.result);
      const wb = XLSX.read(data, { type: "array" });
      const ws = wb.Sheets[wb.SheetNames[0]];
      const rows = XLSX.utils.sheet_to_json(ws, { defval: null });

      // Group by PAIS and aggregate sums
      const groups = new Map();
      for (const row of rows) {
        const pais = row[COLS.pais] ?? "(Sin país)";
        if (!groups.has(pais)) {
          groups.set(pais, {
            [COLS.pais]: pais,
            [COLS.activos]: 0,
            [COLS.propia]: 0,
            [COLS.aImplementar]: 0,
            [COLS.creados]: 0,
            [COLS.activa]: 0,
            [COLS.tareasInternas]: 0,
            [COLS.tareasExternas]: 0,
            _pctIniArr: [],
            _pctCompArr: [],
            _revArr: [],
            _actArr: [],
          });
        }
        const acc = groups.get(pais);
        acc[COLS.activos] += toNumber(row[COLS.activos]);
        acc[COLS.propia] += toNumber(row[COLS.propia]);
        acc[COLS.aImplementar] += toNumber(row[COLS.aImplementar]);
        acc[COLS.creados] += toNumber(row[COLS.creados]);
        acc[COLS.activa] += toNumber(row[COLS.activa]);
        acc[COLS.tareasInternas] += toNumber(row[COLS.tareasInternas]);
        acc[COLS.tareasExternas] += toNumber(row[COLS.tareasExternas]);

        if (row[COLS.pctInicial] != null) acc._pctIniArr.push(asPercent01(toNumber(row[COLS.pctInicial])));
        if (row[COLS.pctCompleta] != null) acc._pctCompArr.push(asPercent01(toNumber(row[COLS.pctCompleta])));

        const bRev = boolish01(row[COLS.revisionAlertas]);
        if (bRev != null) acc._revArr.push(bRev);
        const bAct = boolish01(row[COLS.actualizacionEstados]);
        if (bAct != null) acc._actArr.push(bAct);
      }

      const aggregated = Array.from(groups.values()).map((g) => ({
        ...g,
        [COLS.pctInicial]: avg01(g._pctIniArr),
        [COLS.pctCompleta]: avg01(g._pctCompArr),
        [COLS.revisionAlertas]: avg01(g._revArr),
        [COLS.actualizacionEstados]: avg01(g._actArr),
      }));

      // Totales globales/Promedios
      const t = rows.reduce(
        (acc, r) => {
          acc[COLS.activos] += toNumber(r[COLS.activos]);
          acc[COLS.propia] += toNumber(r[COLS.propia]);
          acc[COLS.aImplementar] += toNumber(r[COLS.aImplementar]);
          acc[COLS.creados] += toNumber(r[COLS.creados]);
          acc[COLS.activa] += toNumber(r[COLS.activa]);
          acc[COLS.tareasInternas] += toNumber(r[COLS.tareasInternas]);
          acc[COLS.tareasExternas] += toNumber(r[COLS.tareasExternas]);

          const p1 = asPercent01(toNumber(r[COLS.pctInicial]));
          if (Number.isFinite(p1)) acc._pctIniArr.push(p1);
          const p2 = asPercent01(toNumber(r[COLS.pctCompleta]));
          if (Number.isFinite(p2)) acc._pctCompArr.push(p2);

          const bRev = boolish01(r[COLS.revisionAlertas]);
          if (bRev != null) acc._revArr.push(bRev);
          const bAct = boolish01(r[COLS.actualizacionEstados]);
          if (bAct != null) acc._actArr.push(bAct);
          return acc;
        },
        {
          [COLS.activos]: 0,
          [COLS.propia]: 0,
          [COLS.aImplementar]: 0,
          [COLS.creados]: 0,
          [COLS.activa]: 0,
          [COLS.tareasInternas]: 0,
          [COLS.tareasExternas]: 0,
          _pctIniArr: [],
          _pctCompArr: [],
          _revArr: [],
          _actArr: [],
        }
      );

      const totalsNew = {
        [COLS.activos]: t[COLS.activos],
        [COLS.propia]: t[COLS.propia],
        [COLS.aImplementar]: t[COLS.aImplementar],
        [COLS.creados]: t[COLS.creados],
        [COLS.activa]: t[COLS.activa],
        [COLS.tareasInternas]: t[COLS.tareasInternas],
        [COLS.tareasExternas]: t[COLS.tareasExternas],
        [COLS.pctInicial]: avg01(t._pctIniArr),
        [COLS.pctCompleta]: avg01(t._pctCompArr),
        [COLS.revisionAlertas]: avg01(t._revArr),
        [COLS.actualizacionEstados]: avg01(t._actArr),
      };

      setByCountry(aggregated);
      setTotals(totalsNew);
      setSelectedCountry("ALL");
    };
    reader.readAsArrayBuffer(file);
  }

  // === Datos para gráficos ===
  const chartAllCountries_main = useMemo(() => {
    return byCountry.map((r) => ({
      pais: r[COLS.pais],
      aImplementar: toNumber(r[COLS.aImplementar]),
      creados: toNumber(r[COLS.creados]),
      activa: toNumber(r[COLS.activa]),
    }));
  }, [byCountry]);

  const chartAllCountries_tasks = useMemo(() => {
    return byCountry.map((r) => ({
      pais: r[COLS.pais],
      tareasInternas: toNumber(r[COLS.tareasInternas]),
      tareasExternas: toNumber(r[COLS.tareasExternas]),
    }));
  }, [byCountry]);

  const chartAllCountries_clients = useMemo(() => {
    return byCountry.map((r) => ({
      pais: r[COLS.pais],
      activos: toNumber(r[COLS.activos]),
      propia: toNumber(r[COLS.propia]),
    }));
  }, [byCountry]);

  const chartCountryBars = useMemo(() => {
    const src = selectedRow;
    if (!src) return [];
    return [
      { name: "A implementar", key: "aImplementar", value: toNumber(src[COLS.aImplementar]) },
      { name: "Creados", key: "creados", value: toNumber(src[COLS.creados]) },
      { name: "Interacción activa", key: "activa", value: toNumber(src[COLS.activa]) },
      { name: "Con herramienta propia", key: "propia", value: toNumber(src[COLS.propia]) },
    ];
  }, [selectedRow]);

  const chartCountryPie = useMemo(() => {
    const src = selectedRow;
    if (!src) return [];
    return [
      { name: "Tareas internas", key: "tareasInternas", value: toNumber(src[COLS.tareasInternas]) },
      { name: "Tareas externas", key: "tareasExternas", value: toNumber(src[COLS.tareasExternas]) },
    ];
  }, [selectedRow]);

  function colorForSeries(keyOrName) {
    if (keyOrName === "activos") return COLORS.activos;
    if (keyOrName === "propia" || keyOrName === "Con herramienta propia") return COLORS.propia;
    if (keyOrName === "aImplementar" || keyOrName === "A implementar") return COLORS.aImplementar;
    if (keyOrName === "creados" || keyOrName === "Creados") return COLORS.creados;
    if (keyOrName === "activa" || keyOrName === "Interacción activa") return COLORS.activa;
    if (keyOrName === "tareasInternas" || keyOrName === "Tareas internas") return COLORS.tareasInternas;
    if (keyOrName === "tareasExternas" || keyOrName === "Tareas externas") return COLORS.tareasExternas;
    return PALETTE[Math.floor(Math.random() * PALETTE.length)];
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        <header className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold">Implementación BDO Portal – Dashboard</h1>
            <p className="text-slate-400 text-sm mt-1">Vista general y detalle por país. El dashboard expone todas las columnas del Excel.</p>
          </div>
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
            <input
              type="file"
              accept=".xlsx,.xls"
              onChange={handleExcel}
              className="block text-sm file:mr-4 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-sm file:font-semibold file:bg-indigo-600 file:text-white hover:file:bg-indigo-500"
            />
            <select
              value={selectedCountry}
              onChange={(e) => setSelectedCountry(e.target.value)}
              className="px-3 py-2 rounded-xl bg-slate-800 border border-slate-700 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="ALL">Todos los países</option>
              {byCountry.map((r) => (
                <option key={String(r[COLS.pais])} value={String(r[COLS.pais])}>
                  {String(r[COLS.pais])}
                </option>
              ))}
            </select>
          </div>
        </header>

        {/* KPIs (cambian con la selección) */}
        <section className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard title="Clientes BSO activos" value={kpis.activos} />
          <StatCard title="Con herramienta propia" value={`${kpis.propia} (${kpis.ratioPropia.toFixed(1)}%)`} />
          <StatCard title="Portales creados" value={kpis.cread} subtitle={`${kpis.avanceCreadosSobrePlan.toFixed(1)}% del plan`}>
            <Progress value={kpis.avanceCreadosSobrePlan} color={COLORS.creados} />
          </StatCard>
          <StatCard title="Interacción activa" value={kpis.activa} subtitle={`${kpis.tasaActivacionSobreCreados.toFixed(1)}% de los creados`}>
            <Progress value={kpis.tasaActivacionSobreCreados} color={COLORS.activa} />
          </StatCard>
        </section>

        <section className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard title="% Impl. inicial (promedio)" value={`${kpis.promInicial.toFixed(1)}%`}>
            <Progress value={kpis.promInicial} color={COLORS.pctInicial} />
          </StatCard>
          <StatCard title="% Impl. completa (promedio)" value={`${kpis.promCompleta.toFixed(1)}%`}>
            <Progress value={kpis.promCompleta} color={COLORS.pctCompleta} />
          </StatCard>
          <StatCard title="Revisión de alertas/correos" value={`${kpis.rev.toFixed(1)}%`}>
            <Progress value={kpis.rev} color={COLORS.revision} />
          </StatCard>
          <StatCard title="Actualización de estados" value={`${kpis.act.toFixed(1)}%`}>
            <Progress value={kpis.act} color={COLORS.actualizacion} />
          </StatCard>
        </section>

        {/* === Vista GENERAL (Todos los países) === */}
        {selectedCountry === "ALL" && (
          <>
            <section className="rounded-2xl bg-slate-900/60 border border-slate-700 p-4 shadow">
              <div className="flex items-center justify-between pb-3">
                <h2 className="text-lg font-semibold">Portales por país</h2>
                <span className="text-xs text-slate-400">Vista general</span>
              </div>
              <div className="w-full h-96">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartAllCountries_main} margin={{ top: 10, right: 20, bottom: 0, left: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke={COLORS.grid} />
                    <XAxis dataKey="pais" tick={{ fontSize: 12, fill: COLORS.axis }} />
                    <YAxis tick={{ fontSize: 12, fill: COLORS.axis }} />
                    <Tooltip contentStyle={{ background: "#0f172a", border: `1px solid ${COLORS.grid}`, color: "#e2e8f0" }} />
                    <Legend wrapperStyle={{ color: "#e2e8f0" }} />
                    <Bar dataKey="aImplementar" name="A implementar" fill={COLORS.aImplementar} />
                    <Bar dataKey="creados" name="Creados" fill={COLORS.creados} />
                    <Bar dataKey="activa" name="Interacción activa" fill={COLORS.activa} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </section>

            <section className="rounded-2xl bg-slate-900/60 border border-slate-700 p-4 shadow">
              <div className="flex items-center justify-between pb-3">
                <h2 className="text-lg font-semibold">Tareas internas vs externas por país</h2>
                <span className="text-xs text-slate-400">Vista general</span>
              </div>
              <div className="w-full h-96">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartAllCountries_tasks} margin={{ top: 10, right: 20, bottom: 0, left: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke={COLORS.grid} />
                    <XAxis dataKey="pais" tick={{ fontSize: 12, fill: COLORS.axis }} />
                    <YAxis tick={{ fontSize: 12, fill: COLORS.axis }} />
                    <Tooltip contentStyle={{ background: "#0f172a", border: `1px solid ${COLORS.grid}`, color: "#e2e8f0" }} />
                    <Legend wrapperStyle={{ color: "#e2e8f0" }} />
                    <Bar dataKey="tareasInternas" name="Tareas internas" fill={COLORS.tareasInternas} stackId="tareas" />
                    <Bar dataKey="tareasExternas" name="Tareas externas" fill={COLORS.tareasExternas} stackId="tareas" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </section>

            <section className="rounded-2xl bg-slate-900/60 border border-slate-700 p-4 shadow">
              <div className="flex items-center justify-between pb-3">
                <h2 className="text-lg font-semibold">Clientes activos vs con herramienta propia</h2>
                <span className="text-xs text-slate-400">Vista general</span>
              </div>
              <div className="w-full h-96">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartAllCountries_clients} margin={{ top: 10, right: 20, bottom: 0, left: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke={COLORS.grid} />
                    <XAxis dataKey="pais" tick={{ fontSize: 12, fill: COLORS.axis }} />
                    <YAxis tick={{ fontSize: 12, fill: COLORS.axis }} />
                    <Tooltip contentStyle={{ background: "#0f172a", border: `1px solid ${COLORS.grid}`, color: "#e2e8f0" }} />
                    <Legend wrapperStyle={{ color: "#e2e8f0" }} />
                    <Bar dataKey="activos" name="Activos" fill={COLORS.activos} />
                    <Bar dataKey="propia" name="Con herramienta propia" fill={COLORS.propia} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </section>
          </>
        )}

        {/* === Vista DETALLE (País seleccionado) === */}
        {selectedCountry !== "ALL" && selectedRow && (
          <>
            <section className="rounded-2xl bg-slate-900/60 border border-slate-700 p-4 shadow">
              <div className="flex items-center justify-between pb-3">
                <h2 className="text-lg font-semibold">Detalle: {selectedCountry}</h2>
                <span className="text-xs text-slate-400">Vista específica</span>
              </div>
              <div className="grid lg:grid-cols-3 gap-6">
                {/* Barras por categoría */}
                <div className="w-full h-80">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={chartCountryBars} margin={{ top: 10, right: 20, bottom: 0, left: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke={COLORS.grid} />
                      <XAxis dataKey="name" tick={{ fontSize: 12, fill: COLORS.axis }} />
                      <YAxis tick={{ fontSize: 12, fill: COLORS.axis }} />
                      <Tooltip contentStyle={{ background: "#0f172a", border: `1px solid ${COLORS.grid}`, color: "#e2e8f0" }} />
                      <Legend wrapperStyle={{ color: "#e2e8f0" }} />
                      <Bar dataKey="value" name="Cantidad">
                        {chartCountryBars.map((item) => (
                          <Cell key={item.key} fill={colorForSeries(item.key)} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>

                {/* Donut Tareas */}
                <div className="w-full h-80">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Tooltip contentStyle={{ background: "#0f172a", border: `1px solid ${COLORS.grid}`, color: "#e2e8f0" }} />
                      <Legend wrapperStyle={{ color: "#e2e8f0" }} />
                      <Pie data={chartCountryPie} dataKey="value" nameKey="name" innerRadius={60} outerRadius={100}>
                        {chartCountryPie.map((entry) => (
                          <Cell key={entry.key} fill={colorForSeries(entry.key)} />
                        ))}
                      </Pie>
                    </PieChart>
                  </ResponsiveContainer>
                </div>

                {/* Resumen textual + % de revisión/actualización */}
                <div className="rounded-xl bg-slate-900 border border-slate-700 p-4 space-y-2">
                  <h3 className="font-semibold">Resumen</h3>
                  <ul className="mt-3 space-y-2 text-sm text-slate-300">
                    <li><span className="text-slate-400">Clientes activos:</span> {toNumber(selectedRow[COLS.activos])}</li>
                    <li><span className="text-slate-400">Con herramienta propia:</span> {toNumber(selectedRow[COLS.propia])}</li>
                    <li><span className="text-slate-400">Portales a implementar:</span> {toNumber(selectedRow[COLS.aImplementar])}</li>
                    <li><span className="text-slate-400">Portales creados:</span> {toNumber(selectedRow[COLS.creados])}</li>
                    <li><span className="text-slate-400">Interacción activa:</span> {toNumber(selectedRow[COLS.activa])}</li>
                    <li><span className="text-slate-400">Tareas internas:</span> {toNumber(selectedRow[COLS.tareasInternas])}</li>
                    <li><span className="text-slate-400">Tareas externas:</span> {toNumber(selectedRow[COLS.tareasExternas])}</li>
                    <li><span className="text-slate-400">% Impl. inicial:</span> {(asPercent01(toNumber(selectedRow[COLS.pctInicial])) * 100).toFixed(1)}%</li>
                    <li><span className="text-slate-400">% Impl. completa:</span> {(asPercent01(toNumber(selectedRow[COLS.pctCompleta])) * 100).toFixed(1)}%</li>
                  </ul>
                  <div className="pt-2">
                    <div className="text-slate-300 text-sm">Revisión de alertas/correos: { (asPercent01(selectedRow[COLS.revisionAlertas]) * 100).toFixed(1)}%</div>
                    <Progress value={asPercent01(selectedRow[COLS.revisionAlertas]) * 100} color={COLORS.revision} />
                    <div className="text-slate-300 text-sm mt-2">Actualización de estados: { (asPercent01(selectedRow[COLS.actualizacionEstados]) * 100).toFixed(1)}%</div>
                    <Progress value={asPercent01(selectedRow[COLS.actualizacionEstados]) * 100} color={COLORS.actualizacion} />
                  </div>
                </div>
              </div>
            </section>
          </>
        )}

        {/* Búsqueda y Tabla detalle (con TODAS las columnas) */}
        <section className="rounded-2xl bg-slate-900/60 border border-slate-700 p-4 shadow">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3 pb-3">
            <h2 className="text-lg font-semibold">Detalle por país</h2>
            <div className="flex items-center gap-3">
              <input
                type="text"
                placeholder="Filtrar por país..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="px-3 py-2 rounded-xl bg-slate-800 border border-slate-700 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              />
              <button
                onClick={() => downloadJSON("implementacion_por_pais.json", byCountry)}
                className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-sm"
              >
                Descargar JSON agregado
              </button>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="text-left text-slate-300 border-b border-slate-700">
                  <th className="py-2 pr-4">País</th>
                  <th className="py-2 pr-4">Clientes activos</th>
                  <th className="py-2 pr-4">Con herramienta propia</th>
                  <th className="py-2 pr-4">A implementar</th>
                  <th className="py-2 pr-4">Creados</th>
                  <th className="py-2 pr-4">Interacción activa</th>
                  <th className="py-2 pr-4">Tareas internas</th>
                  <th className="py-2 pr-4">Tareas externas</th>
                  <th className="py-2 pr-4">% Inicial</th>
                  <th className="py-2 pr-4">% Completa</th>
                  <th className="py-2 pr-4">Revisión alertas/correos</th>
                  <th className="py-2 pr-4">Actualización de estados</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((r) => (
                  <tr key={String(r[COLS.pais])} className="border-b border-slate-800 hover:bg-slate-800/50">
                    <td className="py-2 pr-4">{r[COLS.pais]}</td>
                    <td className="py-2 pr-4">{toNumber(r[COLS.activos])}</td>
                    <td className="py-2 pr-4">{toNumber(r[COLS.propia])}</td>
                    <td className="py-2 pr-4">{toNumber(r[COLS.aImplementar])}</td>
                    <td className="py-2 pr-4">{toNumber(r[COLS.creados])}</td>
                    <td className="py-2 pr-4">{toNumber(r[COLS.activa])}</td>
                    <td className="py-2 pr-4">{toNumber(r[COLS.tareasInternas])}</td>
                    <td className="py-2 pr-4">{toNumber(r[COLS.tareasExternas])}</td>
                    <td className="py-2 pr-4">{(asPercent01(toNumber(r[COLS.pctInicial])) * 100).toFixed(1)}%</td>
                    <td className="py-2 pr-4">{(asPercent01(toNumber(r[COLS.pctCompleta])) * 100).toFixed(1)}%</td>
                    <td className="py-2 pr-4">{(asPercent01(r[COLS.revisionAlertas]) * 100).toFixed(1)}%</td>
                    <td className="py-2 pr-4">{(asPercent01(r[COLS.actualizacionEstados]) * 100).toFixed(1)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <footer className="text-xs text-slate-500 pt-2 pb-4">
          <p>
            * Encabezados requeridos (tal cual en Excel): "PAIS", " CLIENTES BSO ACTIVOS", "CLIENTES CON HERRAMIENTA PROPIA",
            "PORTALES A IMPLEMENTAR", "PORTALES CREADOS", "PORTALES CON INTERACCIÓN ACTIVA",
            "PORTALES EN LOS QUE UTILIZAN TAREAS INTERNAS BDO", "PORTALES EN LOS QUE UTILIZAN TAREAS/TEMPLATE CON CLIENTES EXTERNOS",
            "% DE IMPLEMENTACIÓN INICIAL", "% DE IMPLEMENTACIÓN COMPLETA", "REVISIÓN DE ALERTAS Y CORREOS", "ACTUALIZACIÓN DE ESTADOS DE TAREAS".
          </p>
          <p className="mt-1">* Para "Revisión" y "Actualización" se aceptan porcentajes (ej. "75%"), valores de 0 a 1, o respuestas tipo Sí/No (se calculan como cumplimiento promedio).</p>
        </footer>
      </div>
    </div>
  );
}
