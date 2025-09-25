import React, { useState } from 'react';
import { Search, ArrowUpDown, ChevronLeft, ChevronRight } from 'lucide-react';
import { formatearMonedaChilena } from '../../../utils/formatters';
import { reclasificarConceptoConsolidado } from '../../../api/nomina';

const TablaConceptosLibro = ({
  conceptosOrdenadosPaginados,
  conceptQuery,
  setConceptQuery,
  dense,
  setDense,
  conceptSort,
  setConceptSort,
  conceptPageSize,
  setConceptPage,
  compareSelected,
  toggleCompare,
  selectedCat,
  resumenAnterior,
  resumenActual,
  allowReclasificar = true
}) => {
  const denseClasses = { rowText: dense ? 'text-xs' : 'text-sm', pad: dense ? 'px-3 py-2' : 'px-3 py-2' };
  const [modal, setModal] = useState(null); // { nombre }
  const [tipoNuevo, setTipoNuevo] = useState('');
  const [motivo, setMotivo] = useState('');
  const [loading, setLoading] = useState(false);
  const [feedback, setFeedback] = useState('');

  async function onReclasificar(e){
    e.preventDefault();
    if(!modal) return;
    try{
      setLoading(true); setFeedback('');
      await reclasificarConceptoConsolidado(modal.cierreId, modal.nombre, tipoNuevo, motivo||null);
      setFeedback('Reclasificación aplicada. Recargando...');
      // Señal básica: forzar reload página (padre debería volver a pedir resumen)
      setTimeout(()=>{ window.location.reload(); }, 800);
    }catch(err){
      setFeedback(err?.response?.data?.error || 'Error al reclasificar');
    }finally{ setLoading(false); }
  }
  // Map previo de conceptos (solo si hay resumenAnterior)
  const prevConceptMap = React.useMemo(()=> {
    const m = new Map();
    if (resumenAnterior?.conceptos) {
      for (const c of resumenAnterior.conceptos) m.set(c.nombre, c);
    }
    return m;
  }, [resumenAnterior]);

  // Mostrar columnas comparativas sólo si hay categoría seleccionada y existe anterior
  const showComparativo = !!selectedCat && !!resumenAnterior;

  return (
    <div className="bg-gray-900/60 rounded-xl p-6 border border-gray-800 w-full min-h-[320px] flex flex-col">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-gray-300">Detalle de conceptos</h3>
        <div className="flex items-center gap-3">
          <div className="relative w-56 max-w-full">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={14} />
            <input value={conceptQuery} onChange={e=>setConceptQuery(e.target.value)} placeholder="Buscar concepto..." className="w-full pl-9 pr-3 py-2 bg-gray-800/80 border border-gray-700 rounded-lg text-white focus:ring-2 focus:ring-teal-500 text-sm placeholder-gray-500" />
          </div>
          <button onClick={()=>setDense(d=>!d)} className={`text-xs px-3 py-1.5 rounded-full border ${dense? 'bg-teal-600/20 text-teal-300 border-teal-700':'bg-gray-900 text-gray-300 border-gray-700 hover:border-gray-600'}`}>{dense? 'Modo compacto':'Modo cómodo'}</button>
        </div>
      </div>
      <div className="bg-gray-900/60 rounded-xl border border-gray-800 overflow-hidden flex-1 flex flex-col">
        <div className="overflow-x-auto flex-1">
          <table className="w-full table-fixed">
            <thead className="bg-gray-800/80 border-b border-gray-700">
              <tr>
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider ${showComparativo? 'w-[32%]':'w-[50%]'}">
                  <button onClick={()=>setConceptSort(s=>({ key:'name', dir: s.key==='name' && s.dir==='asc'?'desc':'asc'}))} className="inline-flex items-center gap-1">Concepto <ArrowUpDown size={12} className="text-gray-400" /></button>
                </th>
                <th className="px-2 py-3 text-center text-xs font-medium text-gray-300 uppercase tracking-wider w-[10%]">Emp</th>
                {!showComparativo && (
                  <th className="px-3 py-3 text-right text-xs font-medium text-gray-300 uppercase tracking-wider w-[40%]">
                    <button onClick={()=>setConceptSort(s=>({ key:'total', dir: s.key==='total' && s.dir==='asc'?'desc':'asc'}))} className="inline-flex items-center gap-1">Total <ArrowUpDown size={12} className="text-gray-400" /></button>
                  </th>
                )}
                {showComparativo && (
                  <>
                    <th className="px-3 py-3 text-right text-xs font-medium text-gray-300 uppercase tracking-wider w-[14%]">Actual</th>
                    <th className="px-3 py-3 text-right text-xs font-medium text-gray-300 uppercase tracking-wider w-[14%]">Anterior</th>
                    <th className="px-3 py-3 text-right text-xs font-medium text-gray-300 uppercase tracking-wider w-[15%]">Δ</th>
                    <th className="px-3 py-3 text-right text-xs font-medium text-gray-300 uppercase tracking-wider w-[15%]">Δ%</th>
                  </>
                )}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {conceptosOrdenadosPaginados.total === 0 ? (
                <tr>
                  <td colSpan={showComparativo? 6 : 3} className="px-6 py-8 text-center text-sm text-gray-500">
                    {!selectedCat ? 'Seleccione una categoría en la parte superior para ver sus conceptos.' : 'No hay conceptos que coincidan con el filtro.'}
                  </td>
                </tr>
              ) : (
                <>
                  {conceptosOrdenadosPaginados.pageItems.map(c => {
                    const selected = compareSelected.has(c.nombre);
                    const prev = prevConceptMap.get(c.nombre);
                    const prevTotal = prev ? Number(prev.total||0) : 0;
                    const delta = Number(c.total||0) - prevTotal;
                    const pct = prevTotal !== 0 ? (delta / prevTotal) * 100 : (prev ? 0 : null);
                    return (
                      <tr key={c.nombre} className={`group cursor-pointer ${selected? 'bg-teal-900/30 hover:bg-teal-900/40':'hover:bg-gray-800'} ${dense? 'odd:bg-gray-900/10':'odd:bg-gray-900/20'}`} title={c.empleados>0 ? `${c.empleados} empleados con este concepto` : 'Sin empleados con este concepto'}>
                        <td className={`${denseClasses.pad} ${denseClasses.rowText} text-white flex items-center gap-2 truncate`} onClick={()=>toggleCompare(c.nombre)}>{selected && <span className="inline-block w-2 h-2 rounded-full bg-teal-400" />}<span className="truncate">{c.nombre}</span>
                          {allowReclasificar && (
                            <button onClick={(ev)=>{ev.stopPropagation(); setModal({ nombre: c.nombre, cierreId: window.location.pathname.split('/').filter(Boolean).at(-2) }); setTipoNuevo(''); setMotivo(''); setFeedback('');}} className="ml-auto opacity-0 group-hover:opacity-100 transition text-[10px] px-2 py-1 rounded bg-indigo-700/30 text-indigo-300 border border-indigo-600/40 hover:bg-indigo-700/50">Reclasificar</button>
                          )}
                        </td>
                        <td className={`px-2 ${dense? 'py-2':'py-3'} text-center ${denseClasses.rowText} text-gray-300 tabular-nums`}>{c.empleados>0 ? c.empleados : '-'}</td>
                        {!showComparativo && (
                          <td className={`${denseClasses.pad} text-right ${denseClasses.rowText} text-teal-400 font-medium`}>{formatearMonedaChilena(c.total)}</td>
                        )}
                        {showComparativo && (
                          <>
                            <td className={`${denseClasses.pad} text-right ${denseClasses.rowText} text-teal-300 font-medium tabular-nums`}>{formatearMonedaChilena(c.total)}</td>
                            <td className={`${denseClasses.pad} text-right ${denseClasses.rowText} text-gray-400 tabular-nums`}>{prev ? formatearMonedaChilena(prevTotal) : '--'}</td>
                            <td className={`${denseClasses.pad} text-right ${denseClasses.rowText} tabular-nums font-medium ${delta>0? 'text-emerald-400': (delta<0? 'text-rose-400':'text-gray-400')}`}>{prev || delta!==0 ? formatearMonedaChilena(delta) : '--'}</td>
                            <td className={`${denseClasses.pad} text-right ${denseClasses.rowText} tabular-nums ${delta===0? 'text-gray-500': (delta>0? 'text-emerald-400':'text-rose-400')}`}>{pct===null? '--': `${pct.toFixed(1)}%`}</td>
                          </>
                        )}
                      </tr>
                    );
                  })}
                  {Array.from({ length: Math.max(0, conceptPageSize - conceptosOrdenadosPaginados.pageItems.length) }).map((_,i)=>(
                    <tr key={`filler-${i}`} className={`${dense? 'odd:bg-gray-900/10':'odd:bg-gray-900/20'} invisible`}>
                      <td className={`${denseClasses.pad}`}> </td>
                      <td className={`px-2 ${dense? 'py-2':'py-3'}`}> </td>
                      <td className={`${denseClasses.pad}`}> </td>
                      {showComparativo && (<><td className={`${denseClasses.pad}`}></td><td className={`${denseClasses.pad}`}></td><td className={`${denseClasses.pad}`}></td></>)}
                    </tr>
                  ))}
                  <tr>
                    <td colSpan={showComparativo? 6 : 3} className="px-4 py-3">
                      <div className="flex items-center justify-between text-xs text-gray-400">
                        <div>Mostrando {conceptosOrdenadosPaginados.start + 1}-{conceptosOrdenadosPaginados.end} de {conceptosOrdenadosPaginados.total}</div>
                        <div className="flex items-center gap-2">
                          <div className="text-gray-500">10 por página</div>
                          <button onClick={()=>setConceptPage(p=>Math.max(1,p-1))} className="px-2 py-1 rounded border border-gray-700 text-gray-300 disabled:opacity-50" disabled={conceptosOrdenadosPaginados.page <= 1}><ChevronLeft size={14} /></button>
                          <button onClick={()=>setConceptPage(p=>p+1)} className="px-2 py-1 rounded border border-gray-700 text-gray-300 disabled:opacity-50" disabled={conceptosOrdenadosPaginados.page >= conceptosOrdenadosPaginados.pages}><ChevronRight size={14} /></button>
                        </div>
                      </div>
                    </td>
                  </tr>
                </>
              )}
            </tbody>
          </table>
        </div>
      </div>
    {allowReclasificar && modal && (
      <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
        <form onSubmit={onReclasificar} className="bg-gray-900 w-full max-w-md rounded-xl border border-gray-700 p-6 space-y-4">
          <h4 className="text-sm font-semibold text-gray-200">Reclasificar concepto</h4>
          <div className="text-xs text-gray-400">{modal.nombre}</div>
          <div className="space-y-2">
            <label className="block text-xs text-gray-300">Nuevo tipo</label>
            <select value={tipoNuevo} onChange={e=>setTipoNuevo(e.target.value)} required className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-600">
              <option value="" disabled>Seleccionar...</option>
              <option value="haber_imponible">Haber Imponible</option>
              <option value="haber_no_imponible">Haber No Imponible</option>
              <option value="descuento_legal">Descuento Legal</option>
              <option value="otro_descuento">Otro Descuento</option>
              <option value="impuesto">Impuesto</option>
              <option value="aporte_patronal">Aporte Patronal</option>
              <option value="informativo">Informativo</option>
            </select>
          </div>
          <div className="space-y-2">
            <label className="block text-xs text-gray-300">Motivo (opcional)</label>
            <textarea value={motivo} onChange={e=>setMotivo(e.target.value)} rows={3} className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-sm resize-none" placeholder="Ej: Ajuste manual tras revisión" />
          </div>
            {feedback && <div className="text-xs text-indigo-300">{feedback}</div>}
          <div className="flex justify-end gap-2 pt-2">
            <button type="button" disabled={loading} onClick={()=>setModal(null)} className="px-3 py-1.5 text-xs rounded border border-gray-600 text-gray-300 hover:bg-gray-800">Cancelar</button>
            <button type="submit" disabled={loading || !tipoNuevo} className="px-3 py-1.5 text-xs rounded bg-indigo-600 hover:bg-indigo-500 text-white disabled:opacity-50">{loading? 'Guardando...':'Aplicar'}</button>
          </div>
        </form>
      </div>
    )}
    </div>
  );
};

export default TablaConceptosLibro;
