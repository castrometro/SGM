import React, { useEffect, useMemo, useRef, useState } from "react";
import { Upload, CalendarDays, FileSpreadsheet, Info, RefreshCw, Users, Sparkles, DollarSign } from "lucide-react";
import * as XLSX from "xlsx";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, LineChart, Line, Legend, ComposedChart } from "recharts";

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

// Parse explícito dd/mm/yyyy (day-first) si aplica
function parseDateDayFirst(value) {
  if (!value) return null;
  if (value instanceof Date && !isNaN(value)) return value;
  if (typeof value === "number") return normalizeDate(value);
  const s = String(value).trim();
  const m = s.match(/^([0-3]?\d)\/(0?\d|1[0-2])\/(\d{4})$/);
  if (m) {
    const dd = parseInt(m[1], 10);
    const mm = parseInt(m[2], 10) - 1;
    const yy = parseInt(m[3], 10);
    const d = new Date(yy, mm, dd);
    return isNaN(d) ? null : d;
  }
  return normalizeDate(value);
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

// Heurística de mapeo de columnas por encabezado (flexible)
function detectColumns(headers) {
  const lower = headers.map((h) => (h ? String(h).toLowerCase().trim() : ""));
  const findCol = (cands) => lower.findIndex((h) => cands.some((c) => h.includes(c)));
  // Emisión / Fecha documento
  const dateIdx = findCol([
    "fecha emisión",
    "fecha emision",
    "f. emisión",
    "f. emision",
    "emision",
    "emisión",
    "fecha",
    "date",
    "fec doc",
  ]);
  // Vencimiento
  const dueIdx = findCol([
  "vencimiento",
  "vcto",
  "vto",
  "fecha vto",
  "fec vto",
  "f. venc",
  "fecha venc",
  ]);
  // Monto total
  const totalIdx = findCol(["total", "monto", "importe", "valor total", "total c/iva", "total con iva"]);
  // Desgloses (fallback si no hay total)
  const netoIdx = findCol(["neto", "subtotal", "afecto", "valor neto"]);
  const ivaIdx = findCol(["iva", "impuesto", "iva 19", "iva%", "iva monto"]);
  const exentoIdx = findCol(["exento", "no afecto"]);
  // Estado explícito o inferible por saldo
  const statusIdx = findCol(["estado", "status", "situacion", "situación"]);
  const saldoIdx = findCol(["saldo", "por cobrar", "pendiente", "restante"]);
  // Contabilidades comunes
  const debeIdx = findCol(["debe"]);
  const haberIdx = findCol(["haber"]);
  // Identificadores
  const numberIdx = findCol(["n° factura", "nº factura", "nro factura", "folio", "n° doc", "n° documento", "numero", "número", "documento"]);
  const currencyIdx = findCol(["moneda", "divisa", "currency"]);
  const clienteIdx = findCol(["cliente", "razón social", "razon social", "nombre cliente"]);
  const rutIdx = findCol(["rut", "r.u.t", "ruc", "tax id"]);
  const descripcionIdx = findCol(["descripción", "descripcion", "glosa", "detalle"]);
  return { dateIdx, dueIdx, totalIdx, netoIdx, ivaIdx, exentoIdx, statusIdx, saldoIdx, debeIdx, haberIdx, numberIdx, currencyIdx, clienteIdx, rutIdx, descripcionIdx };
}

// Encontrar fila de encabezados: escanea varias filas y elige la de mayor puntaje de keywords
function findHeaderRow(rows) {
  const base = [
    "fecha", "emision", "emisión", "venc", "vencimiento", "monto", "total", "neto", "iva", "estado", "saldo", "factura", "folio"
  ];
  const strong = [
    "emision", "emisión", "vcto", "vto", "emisión", "debe", "haber", "saldo", "tipo", "nº", "n°", "documento", "referencia", "correlativo", "descripción", "descripcion"
  ];
  const maxScan = Math.min(rows.length, 80);
  let bestIdx = -1;
  let bestScore = -1;
  for (let i = 0; i < maxScan; i++) {
    const row = rows[i] || [];
    const cells = row.map((c) => (c ? String(c).toLowerCase() : ""));
    const baseHits = cells.filter((txt) => base.some((k) => txt.includes(k))).length;
    const strongHits = cells.filter((txt) => strong.some((k) => txt.includes(k))).length;
    const score = baseHits + strongHits * 2; // dar más peso a columnas típicas de tabla
    if (score > bestScore && cells.filter(Boolean).length >= 3) {
      bestScore = score;
      bestIdx = i;
    }
  }
  // Si no encontramos nada convincente, volver a 0
  return bestIdx === -1 ? 0 : bestIdx;
}

// Parse robusto de montos (CLP/US, con puntos/commas y símbolos)
function parseAmount(v) {
  if (typeof v === "number") return v;
  if (!v) return NaN;
  const s = String(v).replace(/[^0-9,.-]/g, "");
  // Si hay coma y punto, decidir separador decimal por última ocurrencia
  const lastComma = s.lastIndexOf(",");
  const lastDot = s.lastIndexOf(".");
  let normalized = s;
  if (lastComma > lastDot) {
    // Formato europeo: 1.234.567,89 -> 1234567.89
    normalized = s.replace(/\./g, "").replace(",", ".");
  } else {
    // Formato US/CL: 1,234,567.89 -> 1234567.89 o 1.234.567 -> 1234567
    normalized = s.replace(/,/g, "");
  }
  const n = Number(normalized);
  return isNaN(n) ? NaN : n;
}

// Simulación de clientes (sin API)
const CLIENTES_SIMULADOS = [
  { id: "ebanx", nombre: "Ebanx", rut: "76.123.456-7" },
  { id: "fraser", nombre: "Fraser", rut: "77.987.654-3" },
];

const CLIENTE_META = {
  ebanx: {
    rut: "76.123.456-7",
    nombre: "Ebanx",
    linea: "Contabilidad Outsourcing",
    director: "Luis Caceres",
    gerente: "Eduardo Cortés",
    supervisor: "Pablo Isla",
  },
  fraser: {
    rut: "77.987.654-3",
    nombre: "Fraser",
    linea: "Contabilidad & Nómina",
    director: "Eduardo Gómez",
    gerente: "Luis Ramírez",
    supervisor: "Ana Soto",
  },
};


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
  { fecha: mk(d.getFullYear(), d.getMonth(), 8), monto: base, estado: i % 3 === 0 ? "Pendiente" : (i % 6 === 0 ? "Pagada" : "Emitida") },
  { fecha: mk(d.getFullYear(), d.getMonth(), 20), monto: Math.round(base * 0.6), estado: i % 4 === 0 ? "Pendiente" : (i % 7 === 0 ? "Pagada" : "Emitida") }
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
  { fecha: mk(d.getFullYear(), d.getMonth(), 10), monto: base, estado: i % 5 === 0 ? "Pendiente" : (i % 4 === 0 ? "Pagada" : "Emitida") }
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

// (sin calendario)

const GestionCobranza = () => {
  const [clientes, setClientes] = useState([]);
  const [clienteId, setClienteId] = useState("all");
  const [archivo, setArchivo] = useState(null);
  const [procesando, setProcesando] = useState(false);
  const [mensaje, setMensaje] = useState("");
  const [ultimaImportacion, setUltimaImportacion] = useState([]);
  const [tipo, setTipo] = useState("pendientes"); // 'emitidas' | 'pendientes' | 'todas'
  // programación acordada (planeado)
  const [programacionByCliente, setProgramacionByCliente] = useState(() => {
    const s = localStorage.getItem("cobranza_programacion");
    if (s) {
      try { return JSON.parse(s); } catch (e) {}
    }
    return {};
  });
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

  // Persistir programación en localStorage
  useEffect(() => {
    localStorage.setItem("cobranza_programacion", JSON.stringify(programacionByCliente));
  }, [programacionByCliente]);

  // Helper para saber si considerar factura por 'tipo'
  const matchTipo = (estado) => {
    if (tipo === "todas") return true;
    const st = String(estado || "").toLowerCase();
    return tipo === "emitidas" ? st.includes("emit") : st.includes("pend");
  };

  // (sin calendario)

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

  // Meses helper para tablas: (enero -> mes actual) y (mes actual -> diciembre)
  const mesesActualADiciembre = useMemo(() => {
    const t = new Date();
    const list = [];
    for (let m = t.getMonth(); m < 12; m++) {
      const d = new Date(t.getFullYear(), m, 1);
      const key = ymKey(d);
      list.push({ key, label: ymLabel(key), date: d });
    }
    return list;
  }, []);

  const mesesEneroActual = useMemo(() => {
    const t = new Date();
    const list = [];
    for (let m = 0; m <= t.getMonth(); m++) {
      const d = new Date(t.getFullYear(), m, 1);
      const key = ymKey(d);
      list.push({ key, label: ymLabel(key), date: d });
    }
    return list;
  }, []);

  // CxC (solo Emitidas + Pendientes) para tablas estilo Excel
  const totalPorMesKeyCxC = useMemo(() => {
    const map = {};
    const ids = clienteId === "all" ? Object.keys(facturasByCliente) : [clienteId];
    for (const cid of ids) {
      const datos = facturasByCliente[cid] || [];
      for (const f of datos) {
        if (!f.fecha || isNaN(f.fecha)) continue;
        const st = String(f.estado || "").toLowerCase();
        if (!(st.includes("emit") || st.includes("pend"))) continue; // excluye pagadas y otros
        const key = ymKey(f.fecha);
        map[key] = (map[key] || 0) + (Number(f.monto) || 0);
      }
    }
    return map;
  }, [facturasByCliente, clienteId]);

  const totalCxC_EneroActual = useMemo(
    () => mesesEneroActual.reduce((sum, m) => sum + (Number(totalPorMesKeyCxC[m.key]) || 0), 0),
    [mesesEneroActual, totalPorMesKeyCxC]
  );

  // Asegurar programación base para cliente seleccionado
  useEffect(() => {
    if (clienteId === "all") return;
    setProgramacionByCliente((prev) => {
      if (prev[clienteId]) return prev;
      const curKey = mesesActualADiciembre[0]?.key;
      // semilla simple: plan del mes actual = 30% del total CxC (Enero->Mes actual)
      return {
        ...prev,
        [clienteId]: curKey ? { [curKey]: Math.round(totalCxC_EneroActual * 0.3) } : {},
      };
    });
  }, [clienteId, mesesActualADiciembre, totalCxC_EneroActual]);

  const currentMonthKey = useMemo(() => mesesActualADiciembre[0]?.key, [mesesActualADiciembre]);

  // Total por mes (independiente de ventana) según filtro cliente y tipo
  const totalPorMesKey = useMemo(() => {
    const map = {};
    const ids = clienteId === "all" ? Object.keys(facturasByCliente) : [clienteId];
    for (const cid of ids) {
      const datos = facturasByCliente[cid] || [];
      for (const f of datos) {
        if (!f.fecha || isNaN(f.fecha)) continue;
        if (!matchTipo(f.estado)) continue;
        const key = ymKey(f.fecha);
        map[key] = (map[key] || 0) + (Number(f.monto) || 0);
      }
    }
    return map;
  }, [facturasByCliente, clienteId, matchTipo]);


  const realMesActual = useMemo(() => (currentMonthKey ? (totalPorMesKey[currentMonthKey] || 0) : 0), [currentMonthKey, totalPorMesKey]);

  // Saldo por cobrar: total CxC (enero->mes actual) - programado mes actual
  const saldoPorCobrar = useMemo(() => {
    if (clienteId === "all") return 0;
    const plan = currentMonthKey ? (programacionByCliente?.[clienteId]?.[currentMonthKey] || 0) : 0;
    return Math.max(0, totalCxC_EneroActual - plan);
  }, [clienteId, programacionByCliente, currentMonthKey, totalCxC_EneroActual]);

  // Indicador: clientes con más meses en mora (conteo de meses con pendientes vencidos)
  const clientesMesesMora = useMemo(() => {
    const hoy = new Date();
    const out = [];
    const ids = clienteId === "all" ? Object.keys(facturasByCliente) : [clienteId];
    for (const cid of ids) {
      const datos = facturasByCliente[cid] || [];
      const setMeses = new Set();
      for (const f of datos) {
        const st = String(f.estado || "").toLowerCase();
        if (!f.fecha || isNaN(f.fecha)) continue;
        if (!st.includes("pend")) continue;
        if (f.fecha < hoy) setMeses.add(ymKey(f.fecha));
      }
      if (setMeses.size > 0) out.push({ clienteId: cid, meses: setMeses.size });
    }
    return out
      .map((r) => ({ ...r, nombre: clientes.find((c) => String(c.id) === String(r.clienteId))?.nombre || r.clienteId }))
      .sort((a, b) => b.meses - a.meses)
      .slice(0, 6);
  }, [facturasByCliente, clientes, clienteId]);

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

  // Pagado este mes (monto total con estado 'Pagada' en mes actual)
  const pagadoMesActual = useMemo(() => {
    const ids = clienteId === "all" ? Object.keys(facturasByCliente) : [clienteId];
    const now = new Date();
    const y = now.getFullYear();
    const m = now.getMonth();
    let total = 0;
    for (const cid of ids) {
      const datos = facturasByCliente[cid] || [];
      for (const f of datos) {
        if (!f.fecha || isNaN(f.fecha)) continue;
        const st = String(f.estado || "").toLowerCase();
        if (!st.includes("pag")) continue;
        if (f.fecha.getFullYear() === y && f.fecha.getMonth() === m) {
          total += Number(f.monto) || 0;
        }
      }
    }
    return total;
  }, [facturasByCliente, clienteId]);

  // Pagado este mes por cliente (para barras horizontales)
  const pagadoMesActualPorCliente = useMemo(() => {
    const now = new Date();
    const y = now.getFullYear();
    const m = now.getMonth();
    const ids = clienteId === "all" ? Object.keys(facturasByCliente) : [clienteId];
    const out = [];
    for (const cid of ids) {
      const datos = facturasByCliente[cid] || [];
      let total = 0;
      for (const f of datos) {
        if (!f.fecha || isNaN(f.fecha)) continue;
        const st = String(f.estado || "").toLowerCase();
        if (!st.includes("pag")) continue;
        if (f.fecha.getFullYear() === y && f.fecha.getMonth() === m) total += Number(f.monto) || 0;
      }
      out.push({ nombre: clientes.find((c) => String(c.id) === String(cid))?.nombre || cid, total });
    }
    return out.sort((a, b) => b.total - a.total).slice(0, 8);
  }, [facturasByCliente, clienteId, clientes]);

  // Aging por cliente (0-30, 31-60, 61-90, >90 días) sobre pendientes
  const agingPorCliente = useMemo(() => {
    const now = new Date();
    const ids = clienteId === "all" ? Object.keys(facturasByCliente) : [clienteId];
    const out = [];
    for (const cid of ids) {
      const datos = facturasByCliente[cid] || [];
      const bucket = { nombre: clientes.find((c) => String(c.id) === String(cid))?.nombre || cid, d0_30: 0, d31_60: 0, d61_90: 0, d90: 0 };
      for (const f of datos) {
        if (!f.fecha || isNaN(f.fecha)) continue;
        const st = String(f.estado || "").toLowerCase();
        if (!st.includes("pend")) continue; // aging solo sobre pendientes
        const diffDays = Math.floor((now - f.fecha) / (1000 * 60 * 60 * 24));
        const monto = Number(f.monto) || 0;
        if (diffDays <= 30) bucket.d0_30 += monto;
        else if (diffDays <= 60) bucket.d31_60 += monto;
        else if (diffDays <= 90) bucket.d61_90 += monto;
        else bucket.d90 += monto;
      }
      out.push(bucket);
    }
    return out;
  }, [facturasByCliente, clienteId, clientes]);

  // Serie CxC vs Programado por mes del año actual
  const serieCxCvsProgramado = useMemo(() => {
    const t = new Date();
    const year = t.getFullYear();
    const meses = Array.from({ length: t.getMonth() + 1 }, (_, i) => new Date(year, i, 1));
    return meses.map((d) => {
      const key = ymKey(d);
      const label = ymLabel(key).split(" ")[0];
      const cxc = Number(totalPorMesKeyCxC[key]) || 0;
      const prog = clienteId === "all" ? 0 : Number(programacionByCliente?.[clienteId]?.[key]) || 0;
      return { mes: label, cxc, programado: prog };
    });
  }, [totalPorMesKeyCxC, programacionByCliente, clienteId]);

  // Pareto: concentración de CxC por cliente (Emitidas+Pendientes)
  const paretoCxCPorCliente = useMemo(() => {
    const ids = clienteId === "all" ? Object.keys(facturasByCliente) : [clienteId];
    const rows = [];
    let totalGeneral = 0;
    for (const cid of ids) {
      const datos = facturasByCliente[cid] || [];
      let total = 0;
      for (const f of datos) {
        if (!f.fecha || isNaN(f.fecha)) continue;
        const st = String(f.estado || "").toLowerCase();
        if (!(st.includes("emit") || st.includes("pend"))) continue;
        total += Number(f.monto) || 0;
      }
      rows.push({ nombre: clientes.find((c) => String(c.id) === String(cid))?.nombre || cid, total });
      totalGeneral += total;
    }
    rows.sort((a, b) => b.total - a.total);
    let acumulado = 0;
    const out = rows.map((r) => {
      acumulado += r.total;
      return { ...r, acumuladoPct: totalGeneral ? (acumulado / totalGeneral) * 100 : 0 };
    });
    return out.slice(0, 10);
  }, [facturasByCliente, clienteId, clientes]);

  // Heatmap cliente × mes (Pendientes) usando mesesEneroActual
  const heatmapPendientes = useMemo(() => {
    const ids = clienteId === "all" ? Object.keys(facturasByCliente) : [clienteId];
    const rows = [];
    let max = 0;
    for (const cid of ids) {
      const row = { cliente: clientes.find((c) => String(c.id) === String(cid))?.nombre || cid, celdas: [] };
      for (const m of mesesEneroActual) {
        let sum = 0;
        const datos = facturasByCliente[cid] || [];
        for (const f of datos) {
          if (!f.fecha || isNaN(f.fecha)) continue;
          const st = String(f.estado || "").toLowerCase();
          if (!st.includes("pend")) continue;
          if (ymKey(f.fecha) === m.key) sum += Number(f.monto) || 0;
        }
        row.celdas.push({ key: m.key, label: m.label.split(" ")[0], value: sum });
        if (sum > max) max = sum;
      }
      rows.push(row);
    }
    return { rows, max };
  }, [facturasByCliente, clienteId, clientes, mesesEneroActual]);

  // Conteo de clientes por supervisor (según meta)
  const clientesPorSupervisor = useMemo(() => {
    const ids = clienteId === "all" ? clientes.map((c) => String(c.id)) : [String(clienteId)];
    const map = {};
    for (const cid of ids) {
      const sup = CLIENTE_META[cid]?.supervisor || "N/D";
      map[sup] = (map[sup] || 0) + 1;
    }
    return Object.entries(map).map(([supervisor, count]) => ({ supervisor, count }));
  }, [clientes, clienteId]);

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

  // Importar desde un ArrayBuffer (reutilizable para input file o fetch de un asset)
  const importarExcelDesdeBuffer = async (data) => {
    const wb = XLSX.read(data, { type: "array", cellDates: true });
    // Usa la primera hoja con contenido; si la primera está vacía, intenta con las siguientes
    let rows = [];
    let usedSheet = null;
    for (const name of wb.SheetNames) {
      const ws = wb.Sheets[name];
      const r = XLSX.utils.sheet_to_json(ws, { header: 1, defval: "" });
      if (r && r.length) { rows = r; usedSheet = name; break; }
    }
    if (!rows.length) throw new Error("El archivo está vacío.");

    // Detectar fila de encabezados real
    const headerRowIdx = findHeaderRow(rows);
    let headers = rows[headerRowIdx] || [];
    let cols = detectColumns(headers);
    // Si no encontramos montos ni saldo en esta fila, probar con la fila siguiente (super-encabezado + encabezado real)
    if ((cols.totalIdx === -1 && cols.netoIdx === -1 && cols.saldoIdx === -1 && cols.debeIdx === -1 && cols.haberIdx === -1) && rows[headerRowIdx + 1]) {
      headers = rows[headerRowIdx + 1];
      cols = detectColumns(headers);
    }
    const startIdx = rows.findIndex(r => r === headers);
    const dataRows = rows.slice(startIdx + 1);
    const { dateIdx, dueIdx, totalIdx, netoIdx, ivaIdx, exentoIdx, statusIdx, saldoIdx, debeIdx, haberIdx, numberIdx, currencyIdx } = cols;

    const nuevas = [];

    // Fallback específico EBANX: si no hay columnas de fecha detectadas, intenta con header fijo (fila 16 index-based)
    const tryParseEbanx = () => {
      const hdrIdx = 16;
      const hdr = rows[hdrIdx] || [];
      const toLower = (v) => (v ? String(v).toLowerCase() : "");
      const findIx = (cands) => hdr.findIndex((h) => cands.some((c) => toLower(h).includes(c)));
      const ixEmi = findIx(["emisión", "emision"]);
      const ixVto = findIx(["vcto", "vto", "venc"]);
      const ixDebe = findIx(["debe"]);
      const ixHaber = findIx(["haber"]);
      const ixNum = findIx(["nº", "n°", "nro", "numero", "número"]);
      const ixDesc = findIx(["descripción", "descripcion"]);
      if (ixDebe === -1) return 0;
      const body = rows.slice(hdrIdx + 1);
      let count = 0;
      for (const r of body) {
        const cells = (r || []).map((x) => (x == null ? "" : x));
        const joined = cells.map(String).join(" ").trim().toLowerCase();
        if (!cells.length) continue;
        if (joined.includes("total")) continue;
        if (/[-=]{6,}/.test(joined)) continue;
        const em = parseDateDayFirst(cells[ixEmi]);
        const vt = parseDateDayFirst(cells[ixVto]);
        const debe = parseAmount(cells[ixDebe]);
        const haber = parseAmount(cells[ixHaber]);
        if ((isNaN(debe) || debe <= 0) && (isNaN(haber) || haber <= 0)) continue;
        // Regla MVP: solo cargos que crean deuda (Debe>0)
        if (isNaN(debe) || debe <= 0) continue;
        // Requiere al menos una fecha válida
        if (!(em || vt)) continue;
        nuevas.push({
          fecha: em || vt,
          vencimiento: vt || null,
          monto: debe,
          estado: "Pendiente",
          numero: ixNum !== -1 ? String(cells[ixNum]) : undefined,
          descripcion: ixDesc !== -1 ? String(cells[ixDesc]) : undefined,
          moneda: "CLP",
        });
        count++;
      }
      return count;
    };

    if (dateIdx === -1 && dueIdx === -1) {
      const parsed = tryParseEbanx();
      if (!parsed) throw new Error("No pude detectar una columna de fecha (emisión o vencimiento).");
    } else {
      for (let i = 0; i < dataRows.length; i++) {
        const row = dataRows[i] || [];
        const fecha = normalizeDate(row[dateIdx]);
        const vencimiento = dueIdx !== -1 ? normalizeDate(row[dueIdx]) : null;
        let monto = NaN;
        if (totalIdx !== -1) monto = parseAmount(row[totalIdx]);
        else if (netoIdx !== -1) {
          const neto = parseAmount(row[netoIdx]);
          const iva = ivaIdx !== -1 ? parseAmount(row[ivaIdx]) : 0;
          const exento = exentoIdx !== -1 ? parseAmount(row[exentoIdx]) : 0;
          monto = [neto, iva, exento].some((x) => !isNaN(x)) ? (isNaN(neto) ? 0 : neto) + (isNaN(iva) ? 0 : iva) + (isNaN(exento) ? 0 : exento) : NaN;
        } else if (saldoIdx !== -1) {
          const s = parseAmount(row[saldoIdx]);
          monto = isNaN(s) ? NaN : Math.abs(s);
        } else if (debeIdx !== -1 || haberIdx !== -1) {
          const d = debeIdx !== -1 ? parseAmount(row[debeIdx]) : NaN;
          const h = haberIdx !== -1 ? parseAmount(row[haberIdx]) : NaN;
          const candidates = [Math.abs(d), Math.abs(h)].filter((x) => !isNaN(x) && x !== 0);
          monto = candidates.length ? Math.max(...candidates) : NaN;
        }
        let estadoRaw = statusIdx !== -1 ? String(row[statusIdx]) : "Emitida";
        if (statusIdx === -1 && saldoIdx !== -1) {
          const saldo = parseAmount(row[saldoIdx]);
          if (!isNaN(saldo)) estadoRaw = saldo <= 0 ? "Pagada" : "Pendiente";
        }
        const numero = numberIdx !== -1 ? String(row[numberIdx]) : undefined;
        const moneda = currencyIdx !== -1 ? String(row[currencyIdx]).toUpperCase() : "CLP";
        const fechaBase = fecha || vencimiento;
        if (!fechaBase || isNaN(monto)) continue;
        nuevas.push({ fecha: fechaBase, monto, estado: estadoRaw, numero, vencimiento, moneda });
      }
    }
  setFacturasByCliente((prev) => ({
      ...prev,
      [clienteId]: [...(prev[clienteId] || []), ...nuevas],
    }));
  setMensaje(`Se procesaron ${nuevas.length} facturas.`);
  return nuevas;
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
      const nuevas = await importarExcelDesdeBuffer(data);
      setUltimaImportacion(nuevas || []);
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

  const cargarDesdeRepo = async () => {
    setMensaje("");
    if (!clienteId || clienteId === 'all') {
      setMensaje("Seleccione un cliente específico para cargar.");
      return;
    }
    setProcesando(true);
    try {
      const url = "/excel/auxiliar%20evanx.xlsx"; // servido desde /public/excel
      const res = await fetch(url);
      if (!res.ok) throw new Error(`No pude leer ${url} (${res.status}).`);
      const buf = await res.arrayBuffer();
      const nuevas = await importarExcelDesdeBuffer(buf);
      setUltimaImportacion(nuevas || []);
    } catch (err) {
      console.error(err);
      setMensaje(err.message || "No se pudo cargar el archivo del repositorio.");
    } finally {
      setProcesando(false);
    }
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
      {/* Selector principal de cliente (arriba) */}
      <div className="mb-4 bg-white/5 border border-white/10 rounded-xl p-3 flex flex-col md:flex-row md:items-center md:justify-between gap-3">
        <div className="flex items-center gap-3">
          <span className="text-sm text-gray-300">Cliente</span>
          <select
            value={clienteId}
            onChange={(e) => setClienteId(e.target.value)}
            className="bg-white/10 text-white rounded-lg px-3 py-2 outline-none border border-white/10 focus:border-blue-500 min-w-[220px]"
          >
            <option value="all">Todos los clientes</option>
            {clientes.map((c) => (
              <option key={c.id} value={c.id} className="bg-slate-900">
                {c.nombre}
              </option>
            ))}
          </select>
        </div>
        <div className="text-xs text-gray-400">
          Mostrando: {clienteId === 'all' ? 'Todos los clientes' : (CLIENTE_META[clienteId]?.nombre || clienteId)}
        </div>
      </div>
  {/* Resumen cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
        <div className="bg-gray-900/60 rounded-xl p-6 border border-gray-800 hover:border-gray-700 transition-colors">
          <div className="flex items-center justify-between">
            <div>
      <p className="text-sm text-gray-400">Total pendiente</p>
              <p className="text-2xl font-bold text-rose-300">{resumenCards.totalPend.toLocaleString("es-CL", { style: "currency", currency: "CLP", maximumFractionDigits: 0 })}</p>
      <p className="text-xs text-gray-500 mt-1">{clienteId === 'all' ? 'Todos los clientes' : CLIENTE_META[clienteId]?.nombre}</p>
            </div>
            <DollarSign className="w-8 h-8 text-rose-400" />
          </div>
        </div>
        <div className="bg-gray-900/60 rounded-xl p-6 border border-gray-800 hover:border-gray-700 transition-colors">
          <div className="flex items-center justify-between">
            <div>
      <p className="text-sm text-gray-400">Total emitido</p>
              <p className="text-2xl font-bold text-emerald-300">{resumenCards.totalEmit.toLocaleString("es-CL", { style: "currency", currency: "CLP", maximumFractionDigits: 0 })}</p>
      <p className="text-xs text-gray-500 mt-1">{clienteId === 'all' ? 'Todos los clientes' : CLIENTE_META[clienteId]?.nombre}</p>
            </div>
            <FileSpreadsheet className="w-8 h-8 text-emerald-400" />
          </div>
        </div>
        <div className="bg-gray-900/60 rounded-xl p-6 border border-gray-800 hover:border-gray-700 transition-colors">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400">Clientes en mora</p>
              <p className="text-2xl font-bold text-blue-300">{resumenCards.moraCount}</p>
      <p className="text-xs text-gray-500 mt-1">{clienteId === 'all' ? 'Conjunto completo' : 'Solo cliente seleccionado'}</p>
            </div>
            <Users className="w-8 h-8 text-blue-400" />
          </div>
        </div>
        <div className="bg-gray-900/60 rounded-xl p-6 border border-gray-800 hover:border-gray-700 transition-colors">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-400">Facturas cargadas</p>
              <p className="text-2xl font-bold text-gray-200">{resumenCards.countFact}</p>
      <p className="text-xs text-gray-500 mt-1">{clienteId === 'all' ? 'Todos los clientes' : CLIENTE_META[clienteId]?.nombre}</p>
            </div>
            <CalendarDays className="w-8 h-8 text-gray-400" />
          </div>
        </div>
      </div>

      {/* Ingresar Factura + Última importación */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <form
          onSubmit={procesarArchivo}
          className="bg-white/5 border border-white/10 rounded-xl p-4 backdrop-blur-sm"
        >
          <div className="flex items-center gap-2 mb-3">
            <FileSpreadsheet className="w-5 h-5 text-emerald-400" />
            <h2 className="text-lg font-semibold">Ingresar Factura</h2>
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            <input
              id="archivo-excel-cobranza"
              type="file"
              accept=".xlsx,.xls"
              onChange={onFileChange}
              className="hidden"
            />
            <button
              type="button"
              onClick={() => document.getElementById('archivo-excel-cobranza')?.click()}
              className="inline-flex items-center justify-center gap-2 px-3 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 text-sm"
            >
              <Upload className="w-4 h-4" /> Seleccionar archivo
            </button>
            <span className="text-xs text-gray-400 max-w-[220px] truncate">
              {archivo?.name || 'Ningún archivo seleccionado'}
            </span>
            <button
              type="submit"
              disabled={procesando || !archivo || clienteId === 'all'}
              className="inline-flex items-center justify-center gap-2 px-3 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-sm"
              title={clienteId === 'all' ? 'Seleccione un cliente para procesar' : undefined}
            >
              <Upload className="w-4 h-4" /> Procesar
            </button>
            <button
              type="button"
              onClick={cargarDesdeRepo}
              disabled={procesando || clienteId === 'all'}
              className="inline-flex items-center justify-center gap-2 px-3 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-sm"
              title="Probar con el archivo del repositorio (public/excel)"
            >
              <Upload className="w-4 h-4" /> Probar desde repo
            </button>
            <button
              type="button"
              onClick={limpiarDatosCliente}
              disabled={clienteId === 'all'}
              className="inline-flex items-center justify-center gap-2 px-3 py-2 rounded-lg bg-slate-700 hover:bg-slate-600 disabled:opacity-50 text-sm"
              title="Limpiar datos cargados para este cliente"
            >
              <RefreshCw className="w-4 h-4" /> Limpiar
            </button>
          </div>

          {mensaje && (
            <div className="mt-3 text-sm text-blue-300">{mensaje}</div>
          )}

          <div className="mt-4 flex items-center gap-3 text-sm text-gray-300">
            <Info className="w-4 h-4 text-yellow-400" />
            <p>
              Acepta encabezados flexibles: Fecha/Emisión, Vencimiento (opcional), Total (o Neto+IVA), Estado (opcional) o Saldo (para inferir), N° Factura (opcional), Moneda. También puedes usar "Probar desde repo" si el archivo está en public/excel/.
            </p>
          </div>
        </form>

        <div className="bg-white/5 border border-white/10 rounded-xl p-4">
          <div className="flex items-center justify-between mb-2">
            <h2 className="text-lg font-semibold">Última importación</h2>
            <span className="text-xs text-gray-400">{new Date().toLocaleString('es-CL')}</span>
          </div>
          {ultimaImportacion?.length ? (
            <>
              <div className="text-sm text-gray-300 mb-2">
                {ultimaImportacion.length} filas | Total Debe: {ultimaImportacion.reduce((a,b)=>a+(Number(b.monto)||0),0).toLocaleString('es-CL',{style:'currency',currency:'CLP',maximumFractionDigits:0})}
              </div>
              <div className="max-h-64 overflow-auto rounded-lg border border-white/5">
                <table className="w-full text-sm">
                  <thead className="bg-white/5 text-gray-300">
                    <tr>
                      <th className="px-2 py-1 text-left">Emisión</th>
                      <th className="px-2 py-1 text-left">Vcto.</th>
                      <th className="px-2 py-1 text-left">Nº</th>
                      <th className="px-2 py-1 text-left">Descripción</th>
                      <th className="px-2 py-1 text-right">Debe</th>
                    </tr>
                  </thead>
                  <tbody>
                    {ultimaImportacion.slice(0,50).map((r,idx)=> (
                      <tr key={idx} className="odd:bg-white/0 even:bg-white/5">
                        <td className="px-2 py-1">{r.fecha ? new Date(r.fecha).toLocaleDateString('es-CL') : ''}</td>
                        <td className="px-2 py-1">{r.vencimiento ? new Date(r.vencimiento).toLocaleDateString('es-CL') : ''}</td>
                        <td className="px-2 py-1">{r.numero || ''}</td>
                        <td className="px-2 py-1 truncate max-w-[240px]" title={r.descripcion || ''}>{r.descripcion || ''}</td>
                        <td className="px-2 py-1 text-right">{(Number(r.monto)||0).toLocaleString('es-CL',{style:'currency',currency:'CLP',maximumFractionDigits:0})}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {ultimaImportacion.length>50 && (
                <div className="mt-1 text-xs text-gray-400">Mostrando 50 de {ultimaImportacion.length} filas…</div>
              )}
            </>
          ) : (
            <div className="text-sm text-gray-400">Aún no hay importaciones en esta sesión.</div>
          )}
        </div>
      </div>

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

      {/* Secciones estilo Excel del requerimiento */}
      {clienteId !== "all" && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
          {/* Información del cliente */}
          <div className="bg-white/5 border border-white/10 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-3">
              <Info className="w-5 h-5 text-yellow-400" />
              <h3 className="text-lg font-semibold">Información</h3>
            </div>
            {(() => {
              const meta = CLIENTE_META[clienteId] || {};
              return (
                <dl className="text-sm text-gray-300 grid grid-cols-1 gap-2">
                  <div className="flex justify-between"><dt className="text-gray-400">Rut</dt><dd className="font-medium">{meta.rut || "-"}</dd></div>
                  <div className="flex justify-between"><dt className="text-gray-400">Nombre</dt><dd className="font-medium">{meta.nombre || "-"}</dd></div>
                  <div className="flex justify-between"><dt className="text-gray-400">Línea de Servicio</dt><dd className="font-medium">{meta.linea || "-"}</dd></div>
                  <div className="flex justify-between"><dt className="text-gray-400">Director BDO</dt><dd className="font-medium">{meta.director || "-"}</dd></div>
                  <div className="flex justify-between"><dt className="text-gray-400">Gerente BDO</dt><dd className="font-medium">{meta.gerente || "-"}</dd></div>
                  <div className="flex justify-between"><dt className="text-gray-400">Supervisor BDO</dt><dd className="font-medium">{meta.supervisor || "-"}</dd></div>
                </dl>
              );
            })()}
          </div>

          {/* Cuentas por cobrar: Enero -> Mes actual + Total */}
          <div className="bg-white/5 border border-white/10 rounded-xl p-4 lg:col-span-2">
            <div className="flex items-center gap-2 mb-3">
              <FileSpreadsheet className="w-5 h-5 text-emerald-400" />
              <h3 className="text-lg font-semibold">Cuentas por cobrar (Enero → Mes actual)</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead>
                  <tr>
                    {mesesEneroActual.map((m) => (
                      <th key={m.key} className="px-2 py-2 text-left text-gray-300 font-medium whitespace-nowrap">{m.label}</th>
                    ))}
                    <th className="px-2 py-2 text-left text-gray-300 font-semibold">Total</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    {mesesEneroActual.map((m) => (
                      <td key={m.key} className="px-2 py-2 whitespace-nowrap">
                        {(totalPorMesKeyCxC[m.key] || 0).toLocaleString("es-CL", { style: "currency", currency: "CLP", maximumFractionDigits: 0 })}
                      </td>
                    ))}
                    <td className="px-2 py-2 font-semibold">
                      {totalCxC_EneroActual.toLocaleString("es-CL", { style: "currency", currency: "CLP", maximumFractionDigits: 0 })}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* Programación siguiente acordada: Mes actual -> Diciembre + Saldo */}
          <div className="bg-white/5 border border-white/10 rounded-xl p-4 lg:col-span-3">
            <div className="flex items-center gap-2 mb-3">
              <CalendarDays className="w-5 h-5 text-sky-400" />
              <h3 className="text-lg font-semibold">Programación acordada (Mes actual → Diciembre)</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead>
                  <tr>
                    {mesesActualADiciembre.map((m) => (
                      <th key={m.key} className="px-2 py-2 text-left text-gray-300 font-medium whitespace-nowrap">{m.label}</th>
                    ))}
                    <th className="px-2 py-2 text-left text-gray-300 font-semibold">Saldo por cobrar</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    {mesesActualADiciembre.map((m, idx) => {
                      const v = programacionByCliente?.[clienteId]?.[m.key] || 0;
                      const editable = idx === 0; // solo mes actual editable, resto referencial
                      return (
                        <td key={m.key} className="px-2 py-2 whitespace-nowrap">
                          {editable ? (
                            <input
                              type="number"
                              min={0}
                              step={1000}
                              value={v}
                              onChange={(e) => {
                                const nv = Number(e.target.value || 0);
                                setProgramacionByCliente((prev) => ({
                                  ...prev,
                                  [clienteId]: { ...(prev[clienteId] || {}), [m.key]: nv },
                                }));
                              }}
                              className="w-36 bg-white/10 text-white rounded-lg px-2 py-1 outline-none border border-white/10 focus:border-blue-500"
                            />
                          ) : (
                            <span className="text-gray-300">{v.toLocaleString("es-CL", { style: "currency", currency: "CLP", maximumFractionDigits: 0 })}</span>
                          )}
                        </td>
                      );
                    })}
                    <td className="px-2 py-2 font-semibold text-rose-300">
                      {saldoPorCobrar.toLocaleString("es-CL", { style: "currency", currency: "CLP", maximumFractionDigits: 0 })}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            <p className="mt-2 text-xs text-gray-400">
              Saldo por cobrar = Total (Cuentas por cobrar Enero → Mes actual) – Programado Mes actual.
            </p>
          </div>
        </div>
      )}

  {/* Panel de indicadores y totales */}
  <div className="space-y-6">
          {/* Aging por cliente (pendientes) */}
          <div className="bg-white/5 border border-white/10 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-3">
              <Users className="w-5 h-5 text-pink-400" />
              <h3 className="text-lg font-semibold">Aging de pendientes por cliente</h3>
            </div>
            <div className="h-56 select-none cursor-default" onMouseDown={(e) => e.preventDefault()} style={{ WebkitTapHighlightColor: 'transparent' }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={agingPorCliente} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="nombre" tick={{ fill: "#cbd5e1", fontSize: 12 }} interval={0} angle={-20} textAnchor="end" height={60} />
                  <YAxis tick={{ fill: "#cbd5e1" }} />
                  <Tooltip formatter={(v) => v.toLocaleString("es-CL", { style: "currency", currency: "CLP", maximumFractionDigits: 0 })} contentStyle={{ backgroundColor: "#0f172a", border: "1px solid #334155", color: "#e2e8f0" }} />
                  <Legend />
                  <Bar dataKey="d0_30" stackId="a" fill="#60a5fa" name="0-30" background={false} />
                  <Bar dataKey="d31_60" stackId="a" fill="#34d399" name="31-60" background={false} />
                  <Bar dataKey="d61_90" stackId="a" fill="#f59e0b" name="61-90" background={false} />
                  <Bar dataKey="d90" stackId="a" fill="#ef4444" name=">90" background={false} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* CxC vs Programado (año actual) */}
          <div className="bg-white/5 border border-white/10 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-3">
              <Sparkles className="w-5 h-5 text-emerald-400" />
              <h3 className="text-lg font-semibold">CxC vs Programado (año actual)</h3>
            </div>
            <div className="h-56 select-none cursor-default">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={serieCxCvsProgramado} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="mes" tick={{ fill: "#cbd5e1" }} />
                  <YAxis tick={{ fill: "#cbd5e1" }} />
                  <Tooltip formatter={(v) => v.toLocaleString("es-CL", { style: "currency", currency: "CLP", maximumFractionDigits: 0 })} contentStyle={{ backgroundColor: "#0f172a", border: "1px solid #334155", color: "#e2e8f0" }} />
                  <Legend />
                  <Line type="monotone" dataKey="cxc" stroke="#60a5fa" strokeWidth={2} name="CxC" />
                  <Line type="monotone" dataKey="programado" stroke="#34d399" strokeWidth={2} name="Programado" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Pagado en el mes por cliente */}
          <div className="bg-white/5 border border-white/10 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-3">
              <Sparkles className="w-5 h-5 text-violet-400" />
              <h3 className="text-lg font-semibold">Pagado en el mes por cliente</h3>
            </div>
            <div className="h-56 select-none cursor-default" onMouseDown={(e) => e.preventDefault()} style={{ WebkitTapHighlightColor: 'transparent' }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={pagadoMesActualPorCliente} layout="vertical" margin={{ top: 5, right: 10, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis type="number" tick={{ fill: "#cbd5e1" }} />
                  <YAxis dataKey="nombre" type="category" tick={{ fill: "#cbd5e1", fontSize: 12 }} width={80} />
                  <Tooltip formatter={(v) => v.toLocaleString("es-CL", { style: "currency", currency: "CLP", maximumFractionDigits: 0 })} contentStyle={{ backgroundColor: "#0f172a", border: "1px solid #334155", color: "#e2e8f0" }} />
                  <Bar dataKey="total" fill="#a78bfa" radius={[0, 6, 6, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Pareto de concentración CxC por cliente */}
          <div className="bg-white/5 border border-white/10 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-3">
              <Sparkles className="w-5 h-5 text-amber-400" />
              <h3 className="text-lg font-semibold">Pareto CxC por cliente</h3>
            </div>
            <div className="h-64 select-none cursor-default">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={paretoCxCPorCliente} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                  <CartesianGrid stroke="#334155" strokeDasharray="3 3" />
                  <XAxis dataKey="nombre" tick={{ fill: '#cbd5e1', fontSize: 12 }} interval={0} angle={-20} textAnchor="end" height={60} />
                  <YAxis yAxisId="left" tick={{ fill: '#cbd5e1' }} />
                  <YAxis yAxisId="right" orientation="right" tick={{ fill: '#cbd5e1' }} domain={[0, 100]} />
                  <Tooltip formatter={(v) => (typeof v === 'number' ? v.toLocaleString('es-CL', { style: 'currency', currency: 'CLP', maximumFractionDigits: 0 }) : v)} contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #334155', color: '#e2e8f0' }} />
                  <Legend />
                  <Bar yAxisId="left" dataKey="total" name="CxC" fill="#60a5fa" />
                  <Line yAxisId="right" type="monotone" dataKey="acumuladoPct" name="Acumulado %" stroke="#f59e0b" strokeWidth={2} />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Heatmap pendientes cliente × mes */}
          <div className="bg-white/5 border border-white/10 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-3">
              <Sparkles className="w-5 h-5 text-rose-400" />
              <h3 className="text-lg font-semibold">Pendientes por cliente × mes</h3>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full text-xs">
                <thead>
                  <tr>
                    <th className="px-2 py-1 text-left text-gray-300 font-medium">Cliente</th>
                    {mesesEneroActual.map((m) => (
                      <th key={m.key} className="px-2 py-1 text-center text-gray-300 font-medium whitespace-nowrap">{m.label.split(' ')[0]}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {heatmapPendientes.rows.map((row) => (
                    <tr key={row.cliente}>
                      <td className="px-2 py-1 text-gray-300 whitespace-nowrap">{row.cliente}</td>
                      {row.celdas.map((c) => {
                        const intensity = heatmapPendientes.max ? Math.min(1, c.value / heatmapPendientes.max) : 0;
                        const bg = `rgba(244,63,94,${0.15 + intensity * 0.7})`;
                        return (
                          <td key={c.key} className="px-2 py-1 text-center" style={{ backgroundColor: bg }} title={`${c.label}: ${c.value.toLocaleString('es-CL', { style: 'currency', currency: 'CLP', maximumFractionDigits: 0 })}`}>
                            {c.value ? c.value.toLocaleString('es-CL', { maximumFractionDigits: 0 }) : ''}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
          <div className="bg-white/5 border border-white/10 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-3">
              <Sparkles className="w-5 h-5 text-violet-400" />
              <h3 className="text-lg font-semibold">Indicadores</h3>
            </div>
            <div className="grid grid-cols-1 gap-3">
              <div className="flex items-center justify-between bg-gray-900/60 rounded-lg p-3 border border-gray-800">
                <span className="text-sm text-gray-300">Mes actual: Programado vs Real</span>
                <span className="text-sm font-semibold">
                  {(programacionByCliente?.[clienteId]?.[currentMonthKey] || 0).toLocaleString("es-CL", { style: "currency", currency: "CLP", maximumFractionDigits: 0 })}
                  {" / "}
                  {realMesActual.toLocaleString("es-CL", { style: "currency", currency: "CLP", maximumFractionDigits: 0 })}
                </span>
              </div>
              <div className="bg-gray-900/60 rounded-lg p-3 border border-gray-800">
                <div className="text-sm text-gray-300 mb-2">Clientes con más meses en mora</div>
                {clientesMesesMora.length === 0 ? (
                  <div className="text-gray-400 text-sm">Sin mora registrada.</div>
                ) : (
                  <ul className="text-sm text-gray-300 space-y-1">
                    {clientesMesesMora.map((r) => (
                      <li key={r.clienteId} className="flex items-center justify-between">
                        <span>{r.nombre}</span>
                        <span className="font-medium">{r.meses} meses</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
              <div className="flex items-center justify-between bg-gray-900/60 rounded-lg p-3 border border-gray-800">
                <span className="text-sm text-gray-300">Pagado este mes</span>
                <span className="text-sm font-semibold">
                  {pagadoMesActual.toLocaleString("es-CL", { style: "currency", currency: "CLP", maximumFractionDigits: 0 })}
                </span>
              </div>
              <div className="bg-gray-900/60 rounded-lg p-3 border border-gray-800">
                <div className="text-sm text-gray-300 mb-2">Clientes por supervisor</div>
                <ul className="text-sm text-gray-300 space-y-1">
                  {clientesPorSupervisor.map((r) => (
                    <li key={r.supervisor} className="flex items-center justify-between">
                      <span>{r.supervisor}</span>
                      <span className="font-medium">{r.count}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
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
  );
};

export default GestionCobranza;
