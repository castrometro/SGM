import React from 'react';

const TablaResumenMovimientos = ({
  tablaRef,
  tarjetasMetrics,
  selectedCard,
  selectedTipo,
  setSelectedTipo,
  compareSelected,
  toggleCompare,
  obtenerIconoTipo,
  prettifyEtiqueta,
  datos,
  obtenerClaseColorEmpleado,
  obtenerIndiceColorEmpleado,
  comparativoTarjetas
}) => {
  const formatRut = (rut) => {
    if (!rut) return '-';
    const raw = String(rut).trim();
    // Eliminar puntos, guiones y espacios; conservar dígitos y K/k
    const cleaned = raw.replace(/[^0-9kK]/g, '');
    if (cleaned.length < 2) return raw; // no formateable
    const cuerpo = cleaned.slice(0, -1);
    const dv = cleaned.slice(-1).toUpperCase();
    return `${cuerpo}-${dv}`;
  };
  const rowsBase = [
    { key: 'ingreso', name: 'Ingresos', value: tarjetasMetrics.ingresos, empleados: tarjetasMetrics.ingresosEmp, tipo: 'count' },
    { key: 'finiquito', name: 'Finiquitos', value: tarjetasMetrics.finiquitos, empleados: tarjetasMetrics.finiquitosEmp, tipo: 'count' },
    { key: 'dias_ausencia_justificados', name: 'Días ausencia justificados', value: tarjetasMetrics.diasAusJustificados, empleados: tarjetasMetrics.diasAusJustEmp, tipo: 'dias' },
    { key: 'vacaciones', name: 'Días de vacaciones', value: tarjetasMetrics.vacacionesDias, empleados: tarjetasMetrics.vacacionesEmp, tipo: 'dias' },
    { key: 'ausencias_sin_justificar', name: 'Ausencias sin justificar', value: tarjetasMetrics.ausSinJustificar, empleados: tarjetasMetrics.ausSinJustEmp, tipo: 'count' },
  ];
  const rows = selectedCard ? rowsBase.filter(r=> r.key === selectedCard) : rowsBase;
  const showComparativo = !!comparativoTarjetas;

  return (
    <div ref={tablaRef} className="bg-gray-900/60 rounded-xl p-6 border border-gray-800 w-full flex flex-col min-h-[420px]">
      <div className="bg-gray-900/60 rounded-xl border border-gray-800 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-800/80 border-b border-gray-700">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Tipo / Métrica</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-300 uppercase tracking-wider">Actual</th>
                {showComparativo && <th className="px-4 py-3 text-right text-xs font-medium text-gray-300 uppercase tracking-wider">Anterior</th>}
                {showComparativo && <th className="px-4 py-3 text-right text-xs font-medium text-gray-300 uppercase tracking-wider">Δ</th>}
                {showComparativo && <th className="px-4 py-3 text-right text-xs font-medium text-gray-300 uppercase tracking-wider">Δ%</th>}
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-300 uppercase tracking-wider">Empleados</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-300 uppercase tracking-wider">Comparar</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {rows.length === 0 && (
                <tr>
                  <td colSpan={showComparativo? 7 : 4} className="px-4 py-8 text-center text-gray-500">Sin datos</td>
                </tr>
              )}
              {rows.map(r => {
                const selected = selectedTipo === r.key;
                const comp = comparativoTarjetas?.[r.key] || null;
                const anterior = comp ? comp.anterior : null;
                const delta = comp ? comp.delta : null;
                const pct = comp ? comp.pct : null;
                const deltaCls = delta === null || delta === 0 ? 'text-gray-400' : (delta > 0 ? 'text-emerald-400':'text-rose-400');
                return (
                  <React.Fragment key={r.key}>
                    <tr
                      className={`group hover:bg-gray-800 cursor-pointer ${selected ? 'bg-gray-900 ring-1 ring-teal-700/40' : 'odd:bg-gray-900/20'} transition-colors`}
                      onClick={() => setSelectedTipo(prev => prev === r.key ? null : r.key)}
                    >
                      <td className="px-4 py-3 text-white">
                        <span className="inline-flex items-center gap-2">
                          {obtenerIconoTipo(r.key.includes('ausencia') || r.key==='vacaciones' ? 'ausencia' : (r.key==='ausencias_sin_justificar' ? 'ausencia' : r.key))} {prettifyEtiqueta(r.name.toLowerCase().replace(/\s+/g,'_'))}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right text-gray-300 tabular-nums font-medium">{r.value}</td>
                      {showComparativo && <td className="px-4 py-3 text-right text-gray-400 tabular-nums">{anterior !== null ? anterior : '--'}</td>}
                      {showComparativo && <td className={`px-4 py-3 text-right tabular-nums font-medium ${deltaCls}`}>{delta===null? '--': (delta>0? '+':'')+delta}</td>}
                      {showComparativo && <td className={`px-4 py-3 text-right tabular-nums ${deltaCls}`}>{pct===null? '--': (pct>0?'+':'')+pct.toFixed(1)+'%'}</td>}
                      <td className="px-4 py-3 text-right text-gray-300">{r.empleados ?? '-'}</td>
                      <td className="px-4 py-3 text-right text-gray-300">
                        <button
                          type="button"
                          onClick={(e)=> { e.stopPropagation(); toggleCompare(r.key); }}
                          className={`text-[10px] px-2 py-1 rounded-md border ${compareSelected.has(r.key) ? 'bg-teal-600/30 border-teal-500 text-teal-200' : 'bg-gray-800/50 border-gray-700 text-gray-400 hover:border-gray-600'}`}
                        >{compareSelected.has(r.key) ? 'Quitar' : 'Comparar'}</button>
                      </td>
                    </tr>
                    {selected && (
                      <tr>
                        <td colSpan={showComparativo? 7 : 4} className="px-4 py-3 bg-gray-900/50">
                          <div className="overflow-y-auto max-h-96 rounded-lg border border-gray-800">
                            <table className="w-full">
                              <thead className="bg-gray-800/80 border-b border-gray-700 sticky top-0 z-10">
                                {(() => {
                                  const isIF = r.key === 'ingreso' || r.key === 'finiquito';
                                  if (isIF) return (
                                    <tr>
                                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase">RUT</th>
                                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase">Fecha</th>
                                    </tr>
                                  );
                                  return (
                                    <tr>
                                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase">RUT</th>
                                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase">Categoría/Subtipo</th>
                                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase">Fecha Inicio</th>
                                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase">Fecha Fin</th>
                                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-300 uppercase">Días</th>
                                    </tr>
                                  );
                                })()}
                              </thead>
                              <tbody className="divide-y divide-gray-800">
                                {(() => {
                                  const base = datos?.movimientos || [];
                                  let eventos = [];
                                  if (r.key === 'ingreso') eventos = base.filter(m => m.categoria === 'ingreso');
                                  else if (r.key === 'finiquito') eventos = base.filter(m => m.categoria === 'finiquito');
                                  else if (r.key === 'vacaciones') eventos = base.filter(m => m.categoria === 'ausencia' && (m.subtipo || '').trim() === 'vacaciones');
                                  else if (r.key === 'ausencias_sin_justificar') eventos = base.filter(m => m.categoria === 'ausencia' && ((m.subtipo || '').trim() === 'sin_justificar' || !(m.subtipo)));
                                  else if (r.key === 'dias_ausencia_justificados') eventos = base.filter(m => m.categoria === 'ausencia' && !['sin_justificar','vacaciones',''].includes((m.subtipo || '').trim()));
                                  const rowsDet = eventos.map(ev => {
                                    const dias = Number(ev.dias_en_periodo ?? ev.dias_evento ?? 0) || 0;
                                    const rut = (ev?.empleado?.rut || ev?.rut || '-')
                                    return {
                                      rut,
                                      cat: ev.categoria === 'ausencia' ? (ev.subtipo || 'sin_subtipo') : ev.categoria,
                                      fi: ev.fecha_inicio || '-',
                                      ff: ev.fecha_fin || ev.fecha_inicio || '-',
                                      dias,
                                      id: ev.id,
                                      color: (ev.categoria === 'ausencia') ? obtenerClaseColorEmpleado(ev.empleado) : '',
                                      colorIdx: (ev.categoria === 'ausencia') ? obtenerIndiceColorEmpleado(ev.empleado) : 999
                                    };
                                  });
                                  if (rowsDet.length === 0) return (
                                    <tr>
                                      <td colSpan={r.key === 'ingreso' || r.key === 'finiquito' ? 2 : 5} className="px-4 py-6 text-center text-gray-500">Sin eventos</td>
                                    </tr>
                                  );
                                  const isIF = r.key === 'ingreso' || r.key === 'finiquito';
                                  return rowsDet
                                    .sort((a,b)=> a.colorIdx - b.colorIdx || (new Date(a.fi||'1970-01-01') - new Date(b.fi||'1970-01-01')))
                                    .map(rw => {
                                      if (isIF) {
                                        const fecha = rw.fi && rw.fi !== '-' ? new Date(rw.fi).toLocaleDateString('es-CL') : (rw.ff && rw.ff !== '-' ? new Date(rw.ff).toLocaleDateString('es-CL') : '-');
                                        return (
                                          <tr key={rw.id} className="hover:bg-gray-800/60">
                                            <td className="px-4 py-3 text-gray-300 text-sm">{formatRut(rw.rut)}</td>
                                            <td className="px-4 py-3 text-white text-sm">{fecha}</td>
                                          </tr>
                                        );
                                      }
                                      return (
                                        <tr key={rw.id} className={`hover:bg-gray-800/60 ${rw.color}`}>
                                          <td className="px-4 py-3 text-gray-300 text-sm">{formatRut(rw.rut)}</td>
                                          <td className="px-4 py-3 text-white text-sm">{prettifyEtiqueta(rw.cat)}</td>
                                          <td className="px-4 py-3 text-gray-300 text-sm">{rw.fi ? new Date(rw.fi).toLocaleDateString('es-CL') : '-'}</td>
                                          <td className="px-4 py-3 text-gray-300 text-sm">{rw.ff ? new Date(rw.ff).toLocaleDateString('es-CL') : '-'}</td>
                                          <td className="px-4 py-3 text-gray-200 text-sm text-right">{rw.dias}</td>
                                        </tr>
                                      );
                                    });
                                })()}
                              </tbody>
                            </table>
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default TablaResumenMovimientos;
