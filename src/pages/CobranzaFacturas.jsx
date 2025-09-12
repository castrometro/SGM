import React, { useEffect, useMemo, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Upload, FileSpreadsheet, CheckCircle2, Clock, ArrowLeft, PlusCircle, AlertTriangle, X } from 'lucide-react';
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

      <div className="bg-white/5 border border-white/10 rounded-xl p-4">
        <div className="flex items-center gap-2 mb-3">
          <FileSpreadsheet className="w-5 h-5 text-emerald-400" />
          <h3 className="text-lg font-semibold">Listado de facturas</h3>
        </div>
        <div className="max-h-[70vh] overflow-auto rounded-lg border border-white/5">
          <table className="w-full text-sm">
            <thead className="bg-white/5 text-gray-300">
              <tr>
                <th className="px-3 py-2 text-left">Cod. Doc.</th>
                <th className="px-3 py-2 text-left">Numero</th>
                <th className="px-3 py-2 text-left">Nº de Cuenta</th>
                <th className="px-3 py-2 text-left">Nombre Cuenta</th>
                <th className="px-3 py-2 text-left">Fecha Emisión</th>
                <th className="px-3 py-2 text-left">Vencimiento</th>
                <th className="px-3 py-2 text-right">Debe</th>
                <th className="px-3 py-2 text-right">Haber</th>
                <th className="px-3 py-2 text-left">Estado</th>
                <th className="px-3 py-2 text-right">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {facturas.length ? facturas.map((f,idx) => (
                <tr key={idx} className="odd:bg-white/0 even:bg-white/5">
                  <td className="px-3 py-2">{f.tipoDocumento || '-'}</td>
                  <td className="px-3 py-2">
                    <button onClick={()=>setDetalleIdx(idx)} className="text-sky-300 hover:underline">{f.numero || '-'}</button>
                  </td>
                  <td className="px-3 py-2">{f.numeroCuenta || '-'}</td>
                  <td className="px-3 py-2">{f.nombreCuenta || '-'}</td>
                  <td className="px-3 py-2">{fmtDate(f.emision)}</td>
                  <td className="px-3 py-2">{fmtDate(f.vencimiento)}</td>
                  <td className="px-3 py-2 text-right">{fmtMonto(f.debe)}</td>
                  <td className="px-3 py-2 text-right">{fmtMonto(f.haber)}</td>
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
                  <td colSpan={10} className="px-3 py-6 text-center text-gray-400">Sin facturas aún. Sube un auxiliar o agrega manualmente.</td>
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
