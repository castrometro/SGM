import React, { useEffect, useMemo, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Upload, FileSpreadsheet, CheckCircle2, Clock, ArrowLeft, PlusCircle, AlertTriangle, X } from 'lucide-react';
import * as XLSX from 'xlsx';

// Estructura de la factura
// {
//   numero: string, emision: Date, vencimiento: Date, estado: 'pendiente'|'esperando comprobante'|'cobrada',
//   numeroCuenta, nombreCuenta, tipoDocumento, nombreTipoDocumento, numeroReferencia, tipoMovimiento,
//   numeroComprobante, codigoCorrelativoDctoCompra, fechaComprobante, debe, haber, saldo, descripcion
// }

const STORAGE_KEY = 'cobranza_facturas_by_cliente_v1';

function loadAll() {
  try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}'); } catch { return {}; }
}
function saveAll(map) {
  try { localStorage.setItem(STORAGE_KEY, JSON.stringify(map)); } catch {}
}

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
  const [mapByCliente, setMapByCliente] = useState(() => loadAll());
  const facturas = useMemo(() => mapByCliente[clienteId] || [], [mapByCliente, clienteId]);
  const [detalleIdx, setDetalleIdx] = useState(null);

  useEffect(() => { saveAll(mapByCliente); }, [mapByCliente]);

  const setFacturas = (rows) => setMapByCliente(prev => ({ ...prev, [clienteId]: rows }));

  const parseUpload = async (file) => {
    if (!file) return;
    const buf = await file.arrayBuffer();
    const wb = XLSX.read(buf, { type: 'array' });
    const ws = wb.Sheets[wb.SheetNames[0]];
    const rows = XLSX.utils.sheet_to_json(ws, { defval: '' });
    // Mapeo heurístico de columnas
    const mapCol = (obj, keys) => {
      for (const k of keys) {
        const f = Object.keys(obj).find(h => h.toLowerCase().includes(k));
        if (f) return obj[f];
      }
      return '';
    };
    const parsed = rows.map(r => {
      const numero = String(mapCol(r, ['numero','nº','nro','factura','doc'])).trim();
      const emision = normalizeDate(mapCol(r, ['emision','emisión','fecha emision','fecha emisión','fecha']));
      const venc = normalizeDate(mapCol(r, ['venc','vto','vencimiento','fecha venc']));
      let estado = String(mapCol(r, ['estado','situacion','situación'])).toLowerCase().trim();
      if (!['pendiente','esperando comprobante','cobrada'].includes(estado)) estado = 'pendiente';

      const numeroCuenta = String(mapCol(r, ['numero de cuenta','n° cuenta','nº cuenta','cuenta numero','num cuenta','cuenta'])).trim();
      const nombreCuenta = String(mapCol(r, ['nombre de cuenta','cuenta nombre','razon social','razón social','cliente','nombre cliente'])).trim();
      const tipoDocumento = String(mapCol(r, ['tipo de documento','tipo documento','tdoc'])).trim();
      const nombreTipoDocumento = String(mapCol(r, ['nombre tipo de documento','nombre tipo documento','ntdoc'])).trim();
      const numeroReferencia = String(mapCol(r, ['numero de referencia','nro referencia','nº referencia','referencia'])).trim();
      const tipoMovimiento = String(mapCol(r, ['tipo de movimiento','tipo movimiento'])).trim();
      const numeroComprobante = String(mapCol(r, ['numero de comprobante','nro comprobante','nº comprobante','comprobante'])).trim();
      const codigoCorrelativoDctoCompra = String(mapCol(r, ['codigo correlativo de dcto compra','código correlativo de dcto compra','correlativo compra','codigo correlativo','código correlativo'])).trim();
      const fechaComprobante = normalizeDate(mapCol(r, ['fecha de comprobante','fecha comprobante']));
      const debe = parseMonto(mapCol(r, ['debe','cargo']));
      const haber = parseMonto(mapCol(r, ['haber','abono']));
      const saldo = parseMonto(mapCol(r, ['saldo']));
      const descripcion = String(mapCol(r, ['descripcion','descripción','glosa','detalle'])).trim();

      return { numero, emision, vencimiento: venc, estado,
        numeroCuenta, nombreCuenta, tipoDocumento, nombreTipoDocumento, numeroReferencia, tipoMovimiento,
        numeroComprobante, codigoCorrelativoDctoCompra, fechaComprobante, debe, haber, saldo, descripcion };
    }).filter(r => r.numero);
    setFacturas(parsed);
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

  return (
    <div className="min-h-screen bg-gray-950 text-white p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <button onClick={()=>navigate(-1)} className="px-3 py-1.5 text-xs rounded-md bg-white/10 hover:bg-white/20 flex items-center gap-2"><ArrowLeft className="w-4 h-4"/> Volver</button>
          <h1 className="text-2xl font-bold text-teal-400">Facturas de {clienteId}</h1>
        </div>
        <div className="flex items-center gap-2">
          <label className="px-3 py-1.5 text-xs rounded-md bg-indigo-600 hover:bg-indigo-500 cursor-pointer flex items-center gap-2">
            <Upload className="w-4 h-4" /> Subir auxiliar
            <input type="file" accept=".xlsx,.xls,.csv" className="hidden" onChange={onFile} />
          </label>
          <button onClick={agregarFilaManual} className="px-3 py-1.5 text-xs rounded-md bg-teal-600 hover:bg-teal-500 flex items-center gap-2"><PlusCircle className="w-4 h-4"/> Agregar</button>
        </div>
      </div>

      <div className="bg-white/5 border border-white/10 rounded-xl p-4">
        <div className="flex items-center gap-2 mb-3">
          <FileSpreadsheet className="w-5 h-5 text-emerald-400" />
          <h3 className="text-lg font-semibold">Listado de facturas</h3>
        </div>
        <div className="max-h-[70vh] overflow-auto rounded-lg border border-white/5">
          <table className="w-full text-sm">
            <thead className="bg-white/5 text-gray-300">
              <tr>
                <th className="px-3 py-2 text-left">Factura</th>
                <th className="px-3 py-2 text-left">Emisión</th>
                <th className="px-3 py-2 text-left">Vencimiento</th>
                <th className="px-3 py-2 text-left">Estado</th>
                <th className="px-3 py-2 text-right">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {facturas.length ? facturas.map((f,idx) => (
                <tr key={idx} className="odd:bg-white/0 even:bg-white/5">
                  <td className="px-3 py-2">
                    <button onClick={()=>setDetalleIdx(idx)} className="text-sky-300 hover:underline">{f.numero}</button>
                  </td>
                  <td className="px-3 py-2">{fmtDate(f.emision)}</td>
                  <td className="px-3 py-2">{fmtDate(f.vencimiento)}</td>
                  <td className="px-3 py-2">
                    {f.estado === 'cobrada' ? (
                      <span className="inline-flex items-center gap-1 text-emerald-300"><CheckCircle2 className="w-4 h-4"/> Cobrada</span>
                    ) : f.estado === 'esperando comprobante' ? (
                      <span className="inline-flex items-center gap-1 text-amber-300"><Clock className="w-4 h-4"/> Esperando comprobante</span>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-rose-300"><AlertTriangle className="w-4 h-4"/> Pendiente</span>
                    )}
                  </td>
                  <td className="px-3 py-2 text-right">
                    {f.estado === 'pendiente' && (
                      <button onClick={()=>actualizarEstado(idx,'esperando comprobante')} className="px-2 py-1 text-xs rounded-md bg-blue-600 hover:bg-blue-500">Generar Pago</button>
                    )}
                    {f.estado === 'esperando comprobante' && (
                      <label className="px-2 py-1 text-xs rounded-md bg-teal-600 hover:bg-teal-500 cursor-pointer inline-flex items-center gap-2">
                        Subir comprobante
                        <input type="file" accept="image/*,application/pdf" className="hidden" onChange={()=>actualizarEstado(idx,'cobrada')} />
                      </label>
                    )}
                    {f.estado === 'cobrada' && (
                      <span className="text-xs text-emerald-400">—</span>
                    )}
                  </td>
                </tr>
              )) : (
                <tr>
                  <td colSpan={5} className="px-3 py-6 text-center text-gray-400">Sin facturas aún. Sube un auxiliar o agrega manualmente.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal Detalle */}
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
                      {f.estado === 'cobrada' ? (
                        <span className="inline-flex items-center gap-1 text-emerald-300"><CheckCircle2 className="w-4 h-4"/> Cobrada</span>
                      ) : f.estado === 'esperando comprobante' ? (
                        <span className="inline-flex items-center gap-1 text-amber-300"><Clock className="w-4 h-4"/> Esperando comprobante</span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-rose-300"><AlertTriangle className="w-4 h-4"/> Pendiente</span>
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
