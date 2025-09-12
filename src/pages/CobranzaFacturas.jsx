import React, { useEffect, useMemo, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Upload, FileSpreadsheet, CheckCircle2, Clock, ArrowLeft, PlusCircle, AlertTriangle, X, Coins, Search } from 'lucide-react';
import * as XLSX from 'xlsx';
import { parseAuxiliarCXC } from '../api/cobranza';

// Estructura de la factura
// {
//   numero: string, emision: Date, vencimiento: Date, estado: 'pendiente'|'esperando comprobante'|'cobrada',
//   numeroCuenta, nombreCuenta, tipoDocumento, nombreTipoDocumento, numeroReferencia, tipoMovimiento,
//   numeroComprobante, codigoCorrelativoDctoCompra, fechaComprobante, debe, haber, saldo, descripcion
// }

// Sin persistencia: estado en memoria por cliente durante la sesión

function normalizeDate(v) {
  if (!v) return null;
  if (v instanceof Date && !isNaN(v)) return v;
  // fechas desde Excel pueden venir como serial
  if (typeof v === 'number') {
    const date = XLSX.SSF.parse_date_code(v);
    if (date) return new Date(date.y, date.m - 1, date.d);
  }
  const d = new Date(v);
  return isNaN(d) ? null : d;
}

function parseMonto(v) {
  if (v === null || v === undefined) return 0;
  if (typeof v === 'number') return v;
  const s = String(v).toString().trim();
  if (!s) return 0;
  // Remover símbolos de moneda y miles, soportar , como decimal
  const cleaned = s.replace(/[^0-9,.-]/g, '').replace(/\./g, '').replace(',', '.');
  const n = Number(cleaned);
  return isNaN(n) ? 0 : n;
}

export default function CobranzaFacturas() {
  const { clienteId } = useParams();
  const navigate = useNavigate();
  const [mapByCliente, setMapByCliente] = useState({});
  const facturas = useMemo(() => mapByCliente[clienteId] || [], [mapByCliente, clienteId]);
  const [detalleIdx, setDetalleIdx] = useState(null);

  // NUEVO: filtros
  const [periodo, setPeriodo] = useState('all'); // all | last1 | last3 | last6
  const [busqueda, setBusqueda] = useState('');

  // No persistimos en localStorage ni backend

  const setFacturas = (rows) => setMapByCliente(prev => ({ ...prev, [clienteId]: rows }));

  const parseUpload = async (file) => {
    if (!file) return;
    try {
      const data = await parseAuxiliarCXC(file);
      console.log('[CobranzaFacturas] parseAuxiliarCXC raw response:', data);

      // Mapear a facturas planas para la tabla
      const facturasParsed = [];
      for (const cuenta of data.cuentas || []) {
        for (const f of cuenta.facturas || []) {
          facturasParsed.push({
            numero: String(f.numero || f['numero'] || '').trim(),
            emision: normalizeDate(f.fecha_emision || f['fecha_emision'] || f['fecha'] || null),
            vencimiento: normalizeDate(f.fecha_vcto || f['fecha_vcto'] || f['vencimiento'] || null),
            estado: 'pendiente',
            numeroCuenta: cuenta.numero_cuenta || f.numero_cuenta,
            nombreCuenta: cuenta.nombre_cuenta || f.nombre_cuenta,
            tipoDocumento: f.tipo_documento_codigo || f.tipo_documento || f.tipo_documento_repetido || '',
            nombreTipoDocumento: f.tipo_documento || '',
            numeroReferencia: f.numero_referencia || '',
            tipoMovimiento: f.tipo_movimiento || '',
            numeroComprobante: f.numero_comprobante || '',
            codigoCorrelativoDctoCompra: f.correlativo_doc_compra || f.codigo_correlativo_dcto_compra || '',
            fechaComprobante: normalizeDate(f.fecha_comprobante || null),
            debe: parseMonto(f.debe),
            haber: parseMonto(f.haber),
            saldo: parseMonto(f.saldo),
            descripcion: f.descripcion || ''
          });
        }
      }

      console.log('[CobranzaFacturas] mapped facturas (first 5):', facturasParsed.slice(0, 5));
      setFacturas(facturasParsed);
    } catch (err) {
      console.error('[CobranzaFacturas] parseUpload error:', err);
    }
  };

  const onFile = (e) => parseUpload(e.target.files?.[0]);

  const fmtDate = (d) => d ? new Date(d).toLocaleDateString('es-CL') : '';
  const fmtMonto = (v) => (Number(v)||0).toLocaleString('es-CL', { style:'currency', currency:'CLP', maximumFractionDigits: 0 });

  const actualizarEstado = (idx, nuevo) => {
    setFacturas(facturas.map((f,i)=> i===idx ? { ...f, estado: nuevo } : f));
  };

  const agregarFilaManual = () => {
    const now = new Date();
    setFacturas([
      { numero: `F-${String(facturas.length+1).padStart(4,'0')}`, emision: now, vencimiento: now, estado: 'pendiente',
        numeroCuenta:'', nombreCuenta:'', tipoDocumento:'', nombreTipoDocumento:'', numeroReferencia:'', tipoMovimiento:'',
        numeroComprobante:'', codigoCorrelativoDctoCompra:'', fechaComprobante:null, debe:0, haber:0, saldo:0, descripcion:'' },
      ...facturas,
    ]);
  };

  // Helpers de fecha para filtro por periodo (usa vencimiento como base)
  const startDateByPeriodo = useMemo(() => {
    const today = new Date();
    const firstDayThisMonth = new Date(today.getFullYear(), today.getMonth(), 1);
    const subMonths = (d, m) => new Date(d.getFullYear(), d.getMonth() - m, 1);
    if (periodo === 'last1') return subMonths(firstDayThisMonth, 1);
    if (periodo === 'last3') return subMonths(firstDayThisMonth, 3);
    if (periodo === 'last6') return subMonths(firstDayThisMonth, 6);
    return null; // all
  }, [periodo]);

  // Helper: inicio de día para comparar fechas sin horas
  const startOfDay = (d) => {
    if (!d) return null;
    const x = new Date(d);
    x.setHours(0,0,0,0);
    return x;
  };
  const hoy = useMemo(() => {
    const d = new Date();
    d.setHours(0,0,0,0);
    return d;
  }, []);

  // NUEVO: helper para estado visual "Vencida"
  const esVencida = (f) => {
    if (!f) return false;
    if (Number(f.saldo) >= 0) return false;        // respeta la regla de estados solo saldo < 0
    if (f.estado === 'cobrada') return false;      // cobradas no son vencidas
    const vto = startOfDay(f.vencimiento);
    return vto && vto < hoy;
  };

  // NUEVO: facturas filtradas por periodo (vencimiento) y búsqueda (Nº cuenta o Nº referencia)
  const facturasFiltradas = useMemo(() => {
    const q = (busqueda || '').toString().trim().toLowerCase();
    return (facturas || []).filter(f => {
      // Filtro periodo por vencimiento
      if (startDateByPeriodo) {
        const vto = f.vencimiento ? new Date(f.vencimiento) : null;
        if (!vto || vto < startDateByPeriodo) return false;
      }
      // Filtro búsqueda por Nº de cuenta o Nº de referencia
      if (q) {
        const ncta = (f.numeroCuenta || '').toString().toLowerCase();
        const nref = (f.numeroReferencia || '').toString().toLowerCase();
        if (!ncta.includes(q) && !nref.includes(q)) return false;
      }
      return true;
    });
  }, [facturas, startDateByPeriodo, busqueda]);

  // NUEVO: Totales sobre el subconjunto filtrado (agrego facturasVencidas)
  const totales = useMemo(() => {
    const asNumber = v => Number(v) || 0;
    const absNeg = v => (v < 0 ? -v : 0);
    const rows = facturasFiltradas;

    const pendientesRows = rows.filter(r => asNumber(r.saldo) < 0 && r.estado !== 'cobrada');
    const cobradasRows  = rows.filter(r => r.estado === 'cobrada');

    const facturasPendientes = pendientesRows.length;
    const facturasCobradas   = cobradasRows.length;

    const montoPendiente = pendientesRows.reduce((acc, r) => acc + absNeg(asNumber(r.saldo)), 0);
    const montoCobrado   = cobradasRows.reduce((acc, r) => {
      const haber = asNumber(r.haber);
      const saldo = asNumber(r.saldo);
      return acc + (haber !== 0 ? haber : absNeg(saldo));
    }, 0);

    // NUEVO: conteo de vencidas (saldo < 0, no cobradas, vto < hoy)
    const facturasVencidas = rows.filter(r => asNumber(r.saldo) < 0 && r.estado !== 'cobrada' && (() => {
      const vto = r.vencimiento ? new Date(r.vencimiento) : null;
      if (!vto) return false;
      vto.setHours(0,0,0,0);
      return vto < hoy;
    })()).length;

    return { facturasPendientes, facturasCobradas, montoPendiente, montoCobrado, facturasVencidas };
  }, [facturasFiltradas, hoy]);

  // Derivar filas ordenadas y coloreadas por Nº de Referencia (solo si hay duplicados)
  const filasAgrupadas = useMemo(() => {
    const base = facturasFiltradas; // <-- usar filtradas
    const refMap = new Map();
    base.forEach((f, i) => {
      const key = (f.numeroReferencia || '').toString().trim().toLowerCase();
      if (!key) return;
      const arr = refMap.get(key) || [];
      arr.push(i);
      refMap.set(key, arr);
    });

    const palette = [
      '#0ea5e933', '#22c55e33', '#eab30833', '#f9731633',
      '#a78bfa33', '#ec489933', '#14b8a633', '#f59e0b33',
      '#06b6d433', '#10b98133', '#84cc1633', '#fb718533',
    ];

    const colorByKey = {};
    let cidx = 0;
    for (const [key, idxs] of refMap.entries()) {
      if (idxs.length >= 2) {
        colorByKey[key] = palette[cidx % palette.length];
        cidx++;
      }
    }

    // construir filas con metadata de grupo y ordenar para contigüidad
    const rows = base.map((f, i) => {
      const key = (f.numeroReferencia || '').toString().trim().toLowerCase();
      return {
        ...f,
        _idx: facturas.indexOf(f), // índice original en la lista completa
        _groupKey: key,
        _groupColor: colorByKey[key] || null,
      };
    });

    rows.sort((a, b) => {
      const ag = a._groupColor ? 0 : 1;
      const bg = b._groupColor ? 0 : 1;
      if (ag !== bg) return ag - bg;
      if (a._groupKey !== b._groupKey) return a._groupKey.localeCompare(b._groupKey);

      const da = a.emision ? new Date(a.emision).getTime() : 0;
      const db = b.emision ? new Date(b.emision).getTime() : 0;
      if (da !== db) return da - db;

      return String(a.numero || '').localeCompare(String(b.numero || ''));
    });

    return rows;
  }, [facturasFiltradas, facturas]);

  return (
    <div className="min-h-screen bg-gray-950 text-white p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <button onClick={()=>navigate(-1)} className="px-3 py-1.5 text-xs rounded-md bg-white/10 hover:bg-white/20 flex items-center gap-2"><ArrowLeft className="w-4 h-4"/> Volver</button>
          <h1 className="text-2xl font-bold text-teal-400">Facturas por Cobrar a {clienteId}</h1>
        </div>
        <div className="flex items-center gap-2">
          <label className="px-3 py-1.5 text-xs rounded-md bg-indigo-600 hover:bg-indigo-500 cursor-pointer flex items-center gap-2">
            <Upload className="w-4 h-4" /> Subir auxiliar
            <input type="file" accept=".xlsx,.xls" className="hidden" onChange={onFile} />
          </label>
          <button onClick={agregarFilaManual} className="px-3 py-1.5 text-xs rounded-md bg-teal-600 hover:bg-teal-500 flex items-center gap-2"><PlusCircle className="w-4 h-4"/> Agregar</button>
        </div>
      </div>

      {/* NUEVO: Tarjetas de totales */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-3 mb-4">
        {/* Facturas pendientes */}
        <div className="rounded-lg border border-white/10 bg-white/5 p-4">
          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-400">Facturas pendientes</span>
            <AlertTriangle className="w-4 h-4 text-rose-300" />
          </div>
          <div className="mt-1 text-2xl font-semibold">{totales.facturasPendientes.toLocaleString('es-CL')}</div>
        </div>
        {/* Facturas cobradas */}
        <div className="rounded-lg border border-white/10 bg-white/5 p-4">
          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-400">Facturas cobradas</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-300" />
          </div>
          <div className="mt-1 text-2xl font-semibold">{totales.facturasCobradas.toLocaleString('es-CL')}</div>
        </div>
        {/* Monto pendiente */}
        <div className="rounded-lg border border-white/10 bg-white/5 p-4">
          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-400">Monto pendiente por cobrar</span>
            <Clock className="w-4 h-4 text-amber-300" />
          </div>
          <div className="mt-1 text-2xl font-semibold">{fmtMonto(totales.montoPendiente)}</div>
        </div>
        {/* Monto cobrado */}
        <div className="rounded-lg border border-white/10 bg-white/5 p-4">
          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-400">Monto cobrado</span>
            <Coins className="w-4 h-4 text-teal-300" />
          </div>
          <div className="mt-1 text-2xl font-semibold">{fmtMonto(totales.montoCobrado)}</div>
        </div>
        {/* NUEVO: Facturas vencidas */}
        <div className="rounded-lg border border-white/10 bg-white/5 p-4">
          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-400">Facturas vencidas</span>
            <AlertTriangle className="w-4 h-4 text-red-400" />
          </div>
          <div className="mt-1 text-2xl font-semibold">{totales.facturasVencidas.toLocaleString('es-CL')}</div>
        </div>
      </div>

      {/* NUEVO: Filtros (periodo y búsqueda) */}
      <div className="flex flex-col sm:flex-row gap-3 items-start sm:items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <label className="text-xs text-gray-400">Periodo:</label>
          <select
            value={periodo}
            onChange={e=>setPeriodo(e.target.value)}
            className="bg-white/10 border border-white/10 rounded-md text-sm px-2 py-1 focus:outline-none"
          >
            <option value="all">Todos</option>
            <option value="last1">Último mes</option>
            <option value="last3">Últimos 3 meses</option>
            <option value="last6">Últimos 6 meses</option>
          </select>
        </div>
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 text-gray-400 absolute left-2 top-1/2 -translate-y-1/2" />
          <input
            value={busqueda}
            onChange={e=>setBusqueda(e.target.value)}
            placeholder="Buscar por Nº de cuenta o Nº de referencia…"
            className="w-full pl-8 pr-3 py-1.5 bg-white/10 border border-white/10 rounded-md text-sm focus:outline-none placeholder:text-gray-500"
          />
        </div>
      </div>

      {/* Listado (agrupado y coloreado) */}
      <div className="bg-white/5 border border-white/10 rounded-xl p-4">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <FileSpreadsheet className="w-5 h-5 text-emerald-400" />
            <h3 className="text-lg font-semibold">Listado de facturas</h3>
          </div>
          <div className="text-xs text-gray-400">Agrupadas por “Nº de Referencia” (mismo color)</div>
        </div>
        <div className="max-h-[70vh] overflow-auto rounded-lg border border-white/5">
          <table className="w-full text-sm">
            <thead className="bg-white/5 text-gray-300">
              <tr>
                <th className="px-3 py-2 text-left">Cod. Doc.</th>
                <th className="px-3 py-2 text-left">Numero</th>
                <th className="px-3 py-2 text-left">Nº de Cuenta</th>
                <th className="px-3 py-2 text-left">Nº de Referencia</th>
                <th className="px-3 py-2 text-left">Nombre Cuenta</th>
                <th className="px-3 py-2 text-left">Fecha Emisión</th>
                <th className="px-3 py-2 text-left">Vencimiento</th>
                <th className="px-3 py-2 text-right">Debe</th>
                <th className="px-3 py-2 text-right">Haber</th>
                <th className="px-3 py-2 text-right">Saldo</th>
                <th className="px-3 py-2 text-left">Estado</th>
                <th className="px-3 py-2 text-right">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {filasAgrupadas.length ? filasAgrupadas.map((row) => (
                <tr
                  key={`${row._groupKey}-${row._idx}`}
                  className="odd:bg-white/0 even:bg-white/5"
                  style={row._groupColor ? { backgroundColor: row._groupColor } : undefined}
                >
                  <td className="px-3 py-2" title={row.nombreTipoDocumento || ''}>{row.tipoDocumento || '-'}</td>
                  <td className="px-3 py-2">
                    <button onClick={()=>setDetalleIdx(row._idx)} className="text-sky-300 hover:underline">{row.numero || '-'}</button>
                  </td>
                  <td className="px-3 py-2">{row.numeroCuenta || '-'}</td>
                  <td className="px-3 py-2">{row.numeroReferencia || '-'}</td>
                  <td className="px-3 py-2">{row.nombreCuenta || '-'}</td>
                  <td className="px-3 py-2">{fmtDate(row.emision)}</td>
                  <td className="px-3 py-2">{fmtDate(row.vencimiento)}</td>
                  <td className="px-3 py-2 text-right">{fmtMonto(row.debe)}</td>
                  <td className="px-3 py-2 text-right">{fmtMonto(row.haber)}</td>
                  <td className="px-3 py-2 text-right">{fmtMonto(row.saldo)}</td>
                  {/* Estado: solo si saldo < 0; mostrar 'Vencida' si aplica */}
                  <td className="px-3 py-2">
                    {Number(row.saldo) < 0 ? (
                      row.estado === 'cobrada' ? (
                        <span className="inline-flex items-center gap-1 text-emerald-300"><CheckCircle2 className="w-4 h-4"/> Cobrada</span>
                      ) : esVencida(row) ? (
                        <span className="inline-flex items-center gap-1 text-red-300"><AlertTriangle className="w-4 h-4"/> Vencida</span>
                      ) : row.estado === 'esperando comprobante' ? (
                        <span className="inline-flex items-center gap-1 text-amber-300"><Clock className="w-4 h-4"/> Esperando comprobante</span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-rose-300"><AlertTriangle className="w-4 h-4"/> Pendiente</span>
                      )
                    ) : (
                      <span className="text-xs text-gray-400">—</span>
                    )}
                  </td>
                  {/* Acciones: solo si saldo < 0 (sin cambios; Vencida se comporta como 'pendiente') */}
                  <td className="px-3 py-2 text-right">
                    {Number(row.saldo) < 0 ? (
                      <>
                        {row.estado === 'pendiente' && (
                          <button onClick={()=>actualizarEstado(row._idx,'esperando comprobante')} className="px-2 py-1 text-xs rounded-md bg-blue-600 hover:bg-blue-500">Generar Pago</button>
                        )}
                        {row.estado === 'esperando comprobante' && (
                          <label className="px-2 py-1 text-xs rounded-md bg-teal-600 hover:bg-teal-500 cursor-pointer inline-flex items-center gap-2">
                            Subir comprobante
                            <input type="file" accept="image/*,application/pdf" className="hidden" onChange={()=>actualizarEstado(row._idx,'cobrada')} />
                          </label>
                        )}
                        {row.estado === 'cobrada' && (
                          <span className="text-xs text-emerald-400">—</span>
                        )}
                      </>
                    ) : (
                      <span className="text-xs text-gray-500">—</span>
                    )}
                  </td>
                </tr>
              )) : (
                <tr>
                  <td colSpan={12} className="px-3 py-6 text-center text-gray-400">Sin facturas aún. Sube un auxiliar o agrega manualmente.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal Detalle: reflejar 'Vencida' también */}
      {detalleIdx !== null && facturas[detalleIdx] && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div className="absolute inset-0 bg-black/60" onClick={()=>setDetalleIdx(null)} />
          <div className="relative bg-slate-900 border border-slate-700 rounded-xl w-full max-w-lg p-4 shadow-2xl">
            <button onClick={()=>setDetalleIdx(null)} className="absolute top-2 right-2 text-slate-300 hover:text-white"><X className="w-5 h-5"/></button>
            <h2 className="text-lg font-semibold mb-3">Detalle de factura</h2>
            {(() => {
              const f = facturas[detalleIdx];
              return (
                <div className="space-y-3 text-sm">
                  <div className="grid grid-cols-2 gap-3">
                    <div className="flex justify-between"><span className="text-gray-400">Factura</span><span className="text-white font-medium">{f.numero}</span></div>
                    <div className="flex justify-between"><span className="text-gray-400">Número cuenta</span><span>{f.numeroCuenta || '-'}</span></div>
                    <div className="flex justify-between"><span className="text-gray-400">Nombre cuenta</span><span className="truncate max-w-[180px]" title={f.nombreCuenta}>{f.nombreCuenta || '-'}</span></div>
                    <div className="flex justify-between"><span className="text-gray-400">Tipo doc.</span><span>{f.tipoDocumento || '-'}</span></div>
                    <div className="flex justify-between"><span className="text-gray-400">Nombre tipo doc.</span><span className="truncate max-w-[180px]" title={f.nombreTipoDocumento}>{f.nombreTipoDocumento || '-'}</span></div>
                    <div className="flex justify-between"><span className="text-gray-400">Nº referencia</span><span>{f.numeroReferencia || '-'}</span></div>
                    <div className="flex justify-between"><span className="text-gray-400">Tipo mov.</span><span>{f.tipoMovimiento || '-'}</span></div>
                    <div className="flex justify-between"><span className="text-gray-400">Nº comprobante</span><span>{f.numeroComprobante || '-'}</span></div>
                    <div className="flex justify-between"><span className="text-gray-400">Cod. correlativo dcto compra</span><span className="truncate max-w-[180px]" title={f.codigoCorrelativoDctoCompra}>{f.codigoCorrelativoDctoCompra || '-'}</span></div>
                    <div className="flex justify-between"><span className="text-gray-400">Fecha comprobante</span><span>{fmtDate(f.fechaComprobante)}</span></div>
                    <div className="flex justify-between"><span className="text-gray-400">Emisión</span><span>{fmtDate(f.emision)}</span></div>
                    <div className="flex justify-between"><span className="text-gray-400">Vencimiento</span><span>{fmtDate(f.vencimiento)}</span></div>
                  </div>
                  <div className="grid grid-cols-3 gap-3">
                    <div className="flex justify-between"><span className="text-gray-400">Debe</span><span className="tabular-nums">{fmtMonto(f.debe)}</span></div>
                    <div className="flex justify-between"><span className="text-gray-400">Haber</span><span className="tabular-nums">{fmtMonto(f.haber)}</span></div>
                    <div className="flex justify-between"><span className="text-gray-400">Saldo</span><span className="tabular-nums">{fmtMonto(f.saldo)}</span></div>
                  </div>
                  <div className="flex justify-between items-center"><span className="text-gray-400">Estado</span>
                    <span>
                      {Number(f.saldo) < 0 ? (
                        f.estado === 'cobrada' ? (
                          <span className="inline-flex items-center gap-1 text-emerald-300"><CheckCircle2 className="w-4 h-4"/> Cobrada</span>
                        ) : esVencida(f) ? (
                          <span className="inline-flex items-center gap-1 text-red-300"><AlertTriangle className="w-4 h-4"/> Vencida</span>
                        ) : f.estado === 'esperando comprobante' ? (
                          <span className="inline-flex items-center gap-1 text-amber-300"><Clock className="w-4 h-4"/> Esperando comprobante</span>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-rose-300"><AlertTriangle className="w-4 h-4"/> Pendiente</span>
                        )
                      ) : (
                        <span className="text-xs text-gray-400">No aplica (saldo ≥ 0)</span>
                      )}
                    </span>
                  </div>
                  <div>
                    <div className="text-gray-400 mb-1">Descripción</div>
                    <div className="text-gray-200 whitespace-pre-wrap max-h-48 overflow-auto bg-white/5 rounded-md p-2 border border-white/10">{f.descripcion || '-'}</div>
                  </div>
                </div>
              );
            })()}
            <div className="mt-4 text-right">
              <button onClick={()=>setDetalleIdx(null)} className="px-3 py-1.5 text-xs rounded-md bg-white/10 hover:bg-white/20">Cerrar</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
