import React from 'react';
import { Search, ArrowUpDown, ChevronLeft, ChevronRight } from 'lucide-react';
import { formatearMonedaChilena } from '../../../utils/formatters';

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
  selectedCat
}) => {
  const denseClasses = { rowText: dense ? 'text-xs' : 'text-sm', pad: dense ? 'px-3 py-2' : 'px-3 py-2' };
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
                <th className="px-3 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider w-[50%]">
                  <button onClick={()=>setConceptSort(s=>({ key:'name', dir: s.key==='name' && s.dir==='asc'?'desc':'asc'}))} className="inline-flex items-center gap-1">Concepto <ArrowUpDown size={12} className="text-gray-400" /></button>
                </th>
                <th className="px-2 py-3 text-center text-xs font-medium text-gray-300 uppercase tracking-wider w-[15%]">Empleados</th>
                <th className="px-3 py-3 text-right text-xs font-medium text-gray-300 uppercase tracking-wider w-[35%]">
                  <button onClick={()=>setConceptSort(s=>({ key:'total', dir: s.key==='total' && s.dir==='asc'?'desc':'asc'}))} className="inline-flex items-center gap-1">Total <ArrowUpDown size={12} className="text-gray-400" /></button>
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {conceptosOrdenadosPaginados.total === 0 ? (
                <tr>
                  <td colSpan="3" className="px-6 py-8 text-center text-sm text-gray-500">
                    {!selectedCat ? 'Seleccione una categoría en la parte superior para ver sus conceptos.' : 'No hay conceptos que coincidan con el filtro.'}
                  </td>
                </tr>
              ) : (
                <>
                  {conceptosOrdenadosPaginados.pageItems.map(c => {
                    const selected = compareSelected.has(c.nombre);
                    return (
                      <tr key={c.nombre} onClick={()=>toggleCompare(c.nombre)} className={`cursor-pointer ${selected? 'bg-teal-900/30 hover:bg-teal-900/40':'hover:bg-gray-800'} ${dense? 'odd:bg-gray-900/10':'odd:bg-gray-900/20'}`} title={c.empleados>0 ? `${c.empleados} empleados con este concepto` : 'Sin empleados con este concepto'}>
                        <td className={`${denseClasses.pad} ${denseClasses.rowText} text-white flex items-center gap-2 truncate`}>{selected && <span className="inline-block w-2 h-2 rounded-full bg-teal-400" />}<span className="truncate">{c.nombre}</span></td>
                        <td className={`px-2 ${dense? 'py-2':'py-3'} text-center ${denseClasses.rowText} text-gray-300 tabular-nums`}>{c.empleados>0 ? c.empleados : '-'}</td>
                        <td className={`${denseClasses.pad} text-right ${denseClasses.rowText} text-teal-400 font-medium`}>{formatearMonedaChilena(c.total)}</td>
                      </tr>
                    );
                  })}
                  {Array.from({ length: Math.max(0, conceptPageSize - conceptosOrdenadosPaginados.pageItems.length) }).map((_,i)=>(
                    <tr key={`filler-${i}`} className={`${dense? 'odd:bg-gray-900/10':'odd:bg-gray-900/20'} invisible`}>
                      <td className={`${denseClasses.pad}`}> </td>
                      <td className={`px-2 ${dense? 'py-2':'py-3'}`}> </td>
                      <td className={`${denseClasses.pad}`}> </td>
                    </tr>
                  ))}
                  <tr>
                    <td colSpan="3" className="px-4 py-3">
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
    </div>
  );
};

export default TablaConceptosLibro;
