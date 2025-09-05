import React, { useEffect, useMemo, useRef, useState } from "react";
import { Upload, CalendarDays, FileSpreadsheet, Info, RefreshCw, Users, Sparkles, DollarSign, ChevronLeft, ChevronRight } from "lucide-react";
import * as XLSX from "xlsx";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";

// Utilidad: convertir serial de Excel a Date
function excelSerialToDate(serial) {
  if (typeof serial !== "number") return null;
  const utcDays = Math.floor(serial - 25569);
  const utcValue = utcDays * 86400; // segundos
  return new Date(utcValue * 1000);
}

// Normalizar fecha desde diferentes formatos
function normalizeDate(value) {
  if (!value) return null;
  if (value instanceof Date && !isNaN(value)) return value;
  if (typeof value === "number") {
    const d = excelSerialToDate(value);
    return d && !isNaN(d) ? d : null;
  }
  // Intentar parsear strings comunes
  const d = new Date(value);
  return isNaN(d) ? null : d;
}

// Formatear clave año-mes
function ymKey(date) {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  return `${y}-${m}`;
}

// Nombre legible de mes
function ymLabel(key) {
  const [y, m] = key.split("-");
  const d = new Date(Number(y), Number(m) - 1, 1);
  return new Intl.DateTimeFormat("es-CL", { month: "long", year: "numeric" }).format(d);
}

// Heurística de mapeo de columnas por encabezado
function detectColumns(headers) {
  const lower = headers.map((h) => (h ? String(h).toLowerCase().trim() : ""));
  const findCol = (cands) => lower.findIndex((h) => cands.some((c) => h.includes(c)));
  const dateIdx = findCol(["emision", "emisión", "fecha", "date", "vencimiento"]);
  const amountIdx = findCol(["monto", "importe", "total", "valor", "neto", "bruto"]);
  const statusIdx = findCol(["estado", "status", "situacion", "situación"]);
  return { dateIdx, amountIdx, statusIdx };
}

// Simulación de clientes (sin API)
const CLIENTES_SIMULADOS = [
  { id: "ebanx", nombre: "Ebanx", rut: "76.123.456-7" },
  { id: "fraser", nombre: "Fraser", rut: "77.987.654-3" },
];

// Generar facturas de ejemplo para los últimos meses
function generarFacturasDemo() {
  const months = lastNMonths(12);
  const mk = (y, m, d) => new Date(y, m, d);
  const data = { ebanx: [], fraser: [] };
  // Ebanx: más volumen, mezcla de emitidas y pendientes (con mora)
  months.forEach((m, i) => {
    const d = m.date;
    const base = 600000 + i * 45000;
    data.ebanx.push(
      { fecha: mk(d.getFullYear(), d.getMonth(), 8), monto: base, estado: i % 3 === 0 ? "Pendiente" : "Emitida" },
      { fecha: mk(d.getFullYear(), d.getMonth(), 20), monto: Math.round(base * 0.6), estado: i % 4 === 0 ? "Pendiente" : "Emitida" }
    );
  });
  // Forzar mora (pendientes con fecha pasada)
  const hoy = new Date();
  data.ebanx.push({ fecha: new Date(hoy.getFullYear(), hoy.getMonth() - 2, 5), monto: 920000, estado: "Pendiente" });

  // Fraser: menor volumen, más al día, algunos pendientes recientes
  months.forEach((m, i) => {
    const d = m.date;
    const base = 320000 + i * 30000;
    data.fraser.push(
      { fecha: mk(d.getFullYear(), d.getMonth(), 10), monto: base, estado: i % 5 === 0 ? "Pendiente" : "Emitida" }
    );
  });
  data.fraser.push({ fecha: new Date(hoy.getFullYear(), hoy.getMonth() - 1, 15), monto: 380000, estado: "Pendiente" });
  return data;
}

// Lista de últimos N meses (rolling), desde el mes actual hacia atrás
function lastNMonths(n = 12) {
  const out = [];
  const today = new Date();
  const start = new Date(today.getFullYear(), today.getMonth(), 1);
  for (let i = 0; i < n; i++) {
    const d = new Date(start.getFullYear(), start.getMonth() - i, 1);
    const key = ymKey(d);
    out.push({ key, label: ymLabel(key), date: d });
  }
  return out.reverse(); // cronológico ascendente
}

// Ventana deslizante de N meses, con offset relativo al presente
function monthsWindow(count = 8, offset = 0) {
  const out = [];
  const today = new Date();
  // ventana por defecto: últimos (count-1) meses + mes actual
  const start = new Date(today.getFullYear(), today.getMonth() - (count - 1) + offset, 1);
  for (let i = 0; i < count; i++) {
    const d = new Date(start.getFullYear(), start.getMonth() + i, 1);
    const key = ymKey(d);
    out.push({ key, label: ymLabel(key), date: d });
  }
  return out;
}

const GestionCobranza = () => {
  const [clientes, setClientes] = useState([]);
  const [clienteId, setClienteId] = useState("all");
  const [archivo, setArchivo] = useState(null);
  const [procesando, setProcesando] = useState(false);
  const [mensaje, setMensaje] = useState("");
  const [tipo, setTipo] = useState("pendientes"); // 'emitidas' | 'pendientes' | 'todas'
  const [monthOffset, setMonthOffset] = useState(0); // navegación del calendario
  // Estructura en memoria: { [clienteId]: [{fecha: Date, monto: number, estado: string}] }
  const [facturasByCliente, setFacturasByCliente] = useState(() => {
    const s = localStorage.getItem("cobranza_facturas");
    if (s) {
      try {
        const parsed = JSON.parse(s);
        // deserializar fechas
        Object.keys(parsed || {}).forEach((cid) => {
          parsed[cid] = (parsed[cid] || []).map((f) => ({
            ...f,
            fecha: f.fecha ? new Date(f.fecha) : null,
          }));
        });
        return parsed;
      } catch (e) {}
    }
    // Si no hay nada en storage, sembrar demo
    return generarFacturasDemo();
  });

  // Auto-seed en primer render si no hay datos
  const seededRef = useRef(false);
  useEffect(() => {
    if (seededRef.current) return;
    const hasAny = Object.values(facturasByCliente || {}).some((arr) => (arr?.length || 0) > 0);
    if (!hasAny) {
      setFacturasByCliente(generarFacturasDemo());
    }
    seededRef.current = true;
  }, []);

  useEffect(() => {
    // Cargar clientes simulados
    setClientes(CLIENTES_SIMULADOS);
  }, []);

  // Persistir facturas en localStorage
  useEffect(() => {
    const serializable = {};
    Object.keys(facturasByCliente).forEach((cid) => {
      serializable[cid] = facturasByCliente[cid].map((f) => ({
        ...f,
        fecha: f.fecha ? f.fecha.toISOString() : null,
      }));
    });
    localStorage.setItem("cobranza_facturas", JSON.stringify(serializable));
  }, [facturasByCliente]);

  // Helper para saber si considerar factura por 'tipo'
  const matchTipo = (estado) => {
    if (tipo === "todas") return true;
    const st = String(estado || "").toLowerCase();
    return tipo === "emitidas" ? st.includes("emit") : st.includes("pend");
  };

  // Agregación por mes (ventana de 8 meses deslizante)
  const agregadosPorMes = useMemo(() => {
    const months = monthsWindow(8, monthOffset);
    const acc = Object.fromEntries(months.map((m) => [m.key, 0]));
    const clientesConsiderados = clienteId === "all" ? Object.keys(facturasByCliente) : [clienteId];
    for (const cid of clientesConsiderados) {
      const datos = facturasByCliente[cid] || [];
      for (const f of datos) {
        if (!f.fecha || isNaN(f.fecha)) continue;
        if (!matchTipo(f.estado)) continue;
        const key = ymKey(f.fecha);
        if (key in acc) acc[key] += Number(f.monto) || 0;
      }
    }
    return months.map((m) => ({ key: m.key, label: m.label, monto: acc[m.key] || 0 }));
  }, [facturasByCliente, clienteId, tipo, monthOffset]);

  // Totales por cliente (para panel y para gráfico de mora)
  const totalesPorCliente = useMemo(() => {
    const out = [];
    const ids = Object.keys(facturasByCliente);
    for (const cid of ids) {
      const datos = facturasByCliente[cid] || [];
      let total = 0;
      for (const f of datos) {
        if (!matchTipo(f.estado)) continue;
        total += Number(f.monto) || 0;
      }
      out.push({ clienteId: cid, total });
    }
    // Mapear nombre cliente
    return out
      .map((r) => ({ ...r, nombre: clientes.find((c) => String(c.id) === String(r.clienteId))?.nombre || r.clienteId }))
      .sort((a, b) => b.total - a.total);
  }, [facturasByCliente, clientes, tipo]);

  // Clientes en mora: pendientes con fecha < hoy
  const clientesEnMora = useMemo(() => {
    const hoy = new Date();
    const out = [];
    const ids = clienteId === "all" ? Object.keys(facturasByCliente) : [clienteId];
    for (const cid of ids) {
      const datos = facturasByCliente[cid] || [];
      let mora = 0;
      for (const f of datos) {
        const st = String(f.estado || "").toLowerCase();
        if (!f.fecha || isNaN(f.fecha)) continue;
        if (!st.includes("pend")) continue; // mora definida solo para pendientes
        if (f.fecha < hoy) mora += Number(f.monto) || 0;
      }
      if (mora > 0) out.push({ clienteId: cid, mora });
    }
    return out
      .map((r) => ({ ...r, nombre: clientes.find((c) => String(c.id) === String(r.clienteId))?.nombre || r.clienteId }))
      .sort((a, b) => b.mora - a.mora)
      .slice(0, 8); // top 8
  }, [facturasByCliente, clientes]);

  // Resumen (cards)
  const resumenCards = useMemo(() => {
    const ids = clienteId === "all" ? Object.keys(facturasByCliente) : [clienteId];
    let totalPend = 0, totalEmit = 0, countFact = 0, moraCount = 0;
    const hoy = new Date();
    for (const cid of ids) {
      const datos = facturasByCliente[cid] || [];
      let moraCliente = 0;
      for (const f of datos) {
        if (!f.fecha || isNaN(f.fecha)) continue;
        countFact++;
        const st = String(f.estado || "").toLowerCase();
        if (st.includes("pend")) {
          totalPend += Number(f.monto) || 0;
          if (f.fecha < hoy) moraCliente += Number(f.monto) || 0;
        } else if (st.includes("emit")) {
          totalEmit += Number(f.monto) || 0;
        }
      }
      if (moraCliente > 0) moraCount++;
    }
    return { totalPend, totalEmit, countFact, moraCount };
  }, [facturasByCliente, clienteId]);

  const onFileChange = (e) => {
    const file = e.target.files?.[0];
    setArchivo(file || null);
  };

  const cargarDatosDemo = () => {
    setFacturasByCliente(generarFacturasDemo());
    setMensaje("Datos de ejemplo cargados.");
  };

  const vaciarDatos = () => {
    setFacturasByCliente({});
    setMensaje("Datos vaciados. Puedes cargar un Excel o usar 'Cargar demo'.");
  };

  const procesarArchivo = async (e) => {
    e?.preventDefault?.();
    setMensaje("");
    if (!clienteId) {
      setMensaje("Seleccione un cliente antes de subir el archivo.");
      return;
    }
    if (!archivo) {
      setMensaje("Adjunte un archivo Excel (.xlsx o .xls).");
      return;
    }
    setProcesando(true);
    try {
      const data = await archivo.arrayBuffer();
      const wb = XLSX.read(data, { type: "array", cellDates: true });
      const wsName = wb.SheetNames[0];
      const ws = wb.Sheets[wsName];
      const rows = XLSX.utils.sheet_to_json(ws, { header: 1, defval: "" });
      if (!rows.length) throw new Error("El archivo está vacío.");
      const headers = rows[0];
      const { dateIdx, amountIdx, statusIdx } = detectColumns(headers);
      if (dateIdx === -1 || amountIdx === -1) {
        throw new Error(
          "No pude detectar las columnas de Fecha y Monto. Asegúrese de incluir encabezados como 'Fecha' y 'Monto'."
        );
      }
      const nuevas = [];
      for (let i = 1; i < rows.length; i++) {
        const row = rows[i];
        const fecha = normalizeDate(row[dateIdx]);
        const monto = Number(String(row[amountIdx]).replace(/[^0-9.-]/g, ""));
        const estadoRaw = statusIdx !== -1 ? String(row[statusIdx]) : "Emitida";
        if (!fecha || isNaN(monto)) continue;
        nuevas.push({ fecha, monto, estado: estadoRaw });
      }
      setFacturasByCliente((prev) => ({
        ...prev,
        [clienteId]: [...(prev[clienteId] || []), ...nuevas],
      }));
      setMensaje(`Se procesaron ${nuevas.length} facturas.`);
      setArchivo(null);
      // limpiar input file si existe
      const input = document.getElementById("archivo-excel-cobranza");
      if (input) input.value = "";
    } catch (err) {
      console.error(err);
      setMensaje(err.message || "No se pudo procesar el archivo.");
    } finally {
      setProcesando(false);
    }
  };

  const limpiarDatosCliente = () => {
    if (!clienteId) return;
    setFacturasByCliente((prev) => ({ ...prev, [clienteId]: [] }));
  };

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* Header */}
      <div className="bg-gradient-to-b from-teal-900/20 to-transparent border-b border-gray-800">
        <div className="w-full px-6 py-5">
          <div className="flex items-center justify-between gap-3">
            <div className="h-9 w-9 rounded-lg bg-gray-800/70 flex items-center justify-center border border-gray-700"><CalendarDays className="text-teal-400" size={18} /></div>
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <Sparkles className="text-teal-400" size={16} />
                <h1 className="text-2xl font-bold text-teal-400">Gestión de Cobranza</h1>
              </div>
              <p className="text-gray-400 text-sm">Calendario mensual, clientes en mora y totales. Datos simulados (Ebanx, Fraser).</p>
            </div>
            <div className="flex items-center gap-2">
              <button onClick={cargarDatosDemo} className="px-3 py-1.5 rounded-lg border border-teal-700/40 bg-teal-900/20 text-teal-300 text-sm hover:bg-teal-900/30">Cargar demo</button>
              <button onClick={vaciarDatos} className="px-3 py-1.5 rounded-lg border border-gray-700 bg-gray-900 text-gray-300 text-sm hover:border-gray-600">Vaciar</button>
            </div>
          </div>
        </div>
      </div>

      <div className="w-full px-6 py-6">
      {/* Resumen cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
        <div className="bg-gray-900/60 rounded-xl p-6 border border-gray-800 hover:border-gray-700 transition-colors">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400">Total pendiente</p>
              <p className="text-2xl font-bold text-rose-300">{resumenCards.totalPend.toLocaleString("es-CL", { style: "currency", currency: "CLP", maximumFractionDigits: 0 })}</p>
            </div>
            <DollarSign className="w-8 h-8 text-rose-400" />
          </div>
        </div>
        <div className="bg-gray-900/60 rounded-xl p-6 border border-gray-800 hover:border-gray-700 transition-colors">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400">Total emitido</p>
              <p className="text-2xl font-bold text-emerald-300">{resumenCards.totalEmit.toLocaleString("es-CL", { style: "currency", currency: "CLP", maximumFractionDigits: 0 })}</p>
            </div>
            <FileSpreadsheet className="w-8 h-8 text-emerald-400" />
          </div>
        </div>
        <div className="bg-gray-900/60 rounded-xl p-6 border border-gray-800 hover:border-gray-700 transition-colors">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400">Clientes en mora</p>
              <p className="text-2xl font-bold text-blue-300">{resumenCards.moraCount}</p>
            </div>
            <Users className="w-8 h-8 text-blue-400" />
          </div>
        </div>
        <div className="bg-gray-900/60 rounded-xl p-6 border border-gray-800 hover:border-gray-700 transition-colors">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400">Facturas cargadas</p>
              <p className="text-2xl font-bold text-gray-200">{resumenCards.countFact}</p>
            </div>
            <CalendarDays className="w-8 h-8 text-gray-400" />
          </div>
        </div>
      </div>

      {/* Formulario de carga */}
      <form
        onSubmit={procesarArchivo}
        className="bg-white/5 border border-white/10 rounded-xl p-4 mb-6 backdrop-blur-sm"
      >
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
          <div className="flex flex-col">
            <label className="text-sm text-gray-300 mb-1">Seleccione cliente</label>
            <select
              value={clienteId}
              onChange={(e) => setClienteId(e.target.value)}
              className="bg-white/10 text-white rounded-lg px-3 py-2 outline-none border border-white/10 focus:border-blue-500"
            >
              <option value="all">Todos los clientes</option>
              {clientes.map((c) => (
                <option key={c.id} value={c.id} className="bg-slate-900">
                  {c.nombre}
                </option>
              ))}
            </select>
          </div>

          <div className="flex flex-col">
            <label className="text-sm text-gray-300 mb-1">Archivo Excel</label>
            <input
              id="archivo-excel-cobranza"
              type="file"
              accept=".xlsx,.xls"
              onChange={onFileChange}
              className="file:mr-3 file:py-2 file:px-3 file:rounded-lg file:border-0 file:bg-blue-600 file:text-white file:cursor-pointer bg-white/10 text-white rounded-lg px-3 py-2 outline-none border border-white/10 focus:border-blue-500"
            />
          </div>

      <div className="flex gap-2">
            <button
              type="submit"
              disabled={procesando}
              className="inline-flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50"
            >
              <Upload className="w-4 h-4" /> Procesar
            </button>
            <button
              type="button"
              onClick={limpiarDatosCliente}
        disabled={clienteId === "all"}
              className="inline-flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-slate-700 hover:bg-slate-600 disabled:opacity-50"
              title="Limpiar datos cargados para este cliente"
            >
              <RefreshCw className="w-4 h-4" /> Limpiar
            </button>
          </div>
        </div>

        {mensaje && (
          <div className="mt-3 text-sm text-blue-300">{mensaje}</div>
        )}

        <div className="mt-4 flex items-center gap-3 text-sm text-gray-300">
          <Info className="w-4 h-4 text-yellow-400" />
          <p>
            El archivo debe incluir encabezados como "Fecha" y "Monto". Opcionalmente "Estado" (por ejemplo: Emitida o Pendiente).
          </p>
        </div>
      </form>

      {/* Filtros rápidos */}
      <div className="flex items-center gap-2 mb-4">
        <span className="text-sm text-gray-300">Tipo</span>
        <div className="inline-flex bg-white/10 rounded-lg p-1">
          {[
            { v: "todas", label: "Todas" },
            { v: "emitidas", label: "Emitidas" },
            { v: "pendientes", label: "Pendientes" },
          ].map((opt) => (
            <button
              key={opt.v}
              onClick={() => setTipo(opt.v)}
              className={`px-3 py-1 rounded-md text-sm ${
                tipo === opt.v ? "bg-blue-600" : "hover:bg-white/10"
              }`}
              type="button"
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

  {/* Dashboard principal: calendario + panel lateral */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Calendario (resumen por mes) */}
        <div className="xl:col-span-2 bg-white/5 border border-white/10 rounded-xl p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <FileSpreadsheet className="w-5 h-5 text-emerald-400" />
              <h2 className="text-xl font-semibold">Calendario (8 meses)</h2>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setMonthOffset((o) => o - 1)}
                className="p-2 rounded-lg border border-gray-700 bg-gray-900 hover:bg-gray-800"
                title="Mes anterior"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <button
                onClick={() => setMonthOffset(0)}
                className="px-3 py-1.5 rounded-lg border border-teal-700/40 bg-teal-900/20 text-teal-300 text-sm hover:bg-teal-900/30"
                title="Ir a hoy"
              >
                Hoy
              </button>
              <button
                onClick={() => setMonthOffset((o) => o + 1)}
                className="p-2 rounded-lg border border-gray-700 bg-gray-900 hover:bg-gray-800"
                title="Mes siguiente"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
          {/* Grid 8 meses */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {agregadosPorMes.map(({ key, label, monto }) => (
              <div key={key} className="rounded-xl p-3 bg-gray-900/60 border border-gray-800 hover:border-gray-700 transition-colors">
                <div className="text-xs text-gray-400 mb-1">{label}</div>
                <div className="text-lg font-semibold">
                  {monto.toLocaleString("es-CL", { style: "currency", currency: "CLP", maximumFractionDigits: 0 })}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Panel lateral: clientes en mora + totales por cliente */}
        <div className="space-y-6">
          <div className="bg-white/5 border border-white/10 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-3">
              <Users className="w-5 h-5 text-pink-400" />
              <h3 className="text-lg font-semibold">Clientes en mora</h3>
            </div>
            {clientesEnMora.length === 0 ? (
              <div className="text-gray-400 text-sm">No hay clientes en mora.</div>
            ) : (
              <div className="h-56">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={clientesEnMora} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                    <XAxis dataKey="nombre" tick={{ fill: "#cbd5e1", fontSize: 12 }} interval={0} angle={-20} textAnchor="end" height={60} />
                    <YAxis tick={{ fill: "#cbd5e1" }} />
                    <Tooltip formatter={(v) => v.toLocaleString("es-CL", { style: "currency", currency: "CLP", maximumFractionDigits: 0 })} contentStyle={{ backgroundColor: "#0f172a", border: "1px solid #334155", color: "#e2e8f0" }} />
                    <Bar dataKey="mora" fill="#f43f5e" radius={[6, 6, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>

          <div className="bg-white/5 border border-white/10 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-3">
              <CalendarDays className="w-5 h-5 text-blue-400" />
              <h3 className="text-lg font-semibold">Totales por cliente</h3>
            </div>
            {totalesPorCliente.length === 0 ? (
              <div className="text-gray-400 text-sm">Sin datos cargados.</div>
            ) : (
              <ul className="divide-y divide-white/10">
                {(clienteId === "all" ? totalesPorCliente : totalesPorCliente.filter((r) => String(r.clienteId) === String(clienteId)))
                  .slice(0, clienteId === "all" ? 6 : 1)
                  .map((r) => (
                    <li key={r.clienteId} className="flex items-center justify-between py-2">
                      <span className="text-sm text-gray-300">{r.nombre}</span>
                      <span className="text-sm font-semibold">
                        {r.total.toLocaleString("es-CL", { style: "currency", currency: "CLP", maximumFractionDigits: 0 })}
                      </span>
                    </li>
                  ))}
              </ul>
            )}
          </div>
        </div>
      </div>
  </div>
    </div>
  );
};

export default GestionCobranza;
