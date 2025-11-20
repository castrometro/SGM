import React, { useMemo } from 'react';
import { AlertOctagon, CheckCircle2, XCircle, User, UserCheck, TrendingUp, Clock } from 'lucide-react';
import { ESTADOS_INCIDENCIA, obtenerEstadoReal } from '../../../../../utils/incidenciaUtils';

export default function IncidenciasKPIs({ incidencias = [] }) {
  const stats = useMemo(() => {
    const base = Array.isArray(incidencias) ? incidencias : [];
    // Excluir ingresos informativos de todos los KPIs
    const arr = base.filter(i => i.tipo_incidencia !== 'ingreso_empleado' && !i?.datos_adicionales?.informativo);

    let aprobadas = 0;
    let rechazadas = 0;
    let turnoAnalista = 0;
    let turnoSupervisor = 0;
    let pendientes = 0;
    let mayorVar = null; // {valor, concepto, tipo}

    arr.forEach((i) => {
      const da = i.datos_adicionales || {};
      // Buscar variación porcentual en diferentes campos posibles
      const v = Number(da.delta_pct ?? da.variacion_porcentual ?? 0);
      if (mayorVar === null || Math.abs(v) > Math.abs(mayorVar.valor)) {
        mayorVar = { 
          valor: v, 
          concepto: da.concepto || i.concepto_afectado || i.concepto_codigo || '-', 
          tipo: i.tipo_comparacion 
        };
      }

      const er = obtenerEstadoReal(i);
      switch (er.estado) {
        case ESTADOS_INCIDENCIA.APROBADA_SUPERVISOR:
          aprobadas += 1; 
          break;
        case ESTADOS_INCIDENCIA.RECHAZADA_SUPERVISOR:
          rechazadas += 1; 
          break;
        case ESTADOS_INCIDENCIA.PENDIENTE:
        case ESTADOS_INCIDENCIA.RE_RESUELTA:
          turnoAnalista += 1;
          pendientes += 1; // También son pendientes
          break;
        case ESTADOS_INCIDENCIA.RESUELTA_ANALISTA:
        case ESTADOS_INCIDENCIA.RESOLUCION_SUPERVISOR_PENDIENTE:
          turnoSupervisor += 1;
          pendientes += 1; // También son pendientes
          break;
        default:
          // Estados desconocidos también son pendientes
          pendientes += 1;
          break;
      }
    });

    return {
      total: arr.length,
      aprobadas,
      rechazadas,
      turnoAnalista,
      turnoSupervisor,
      pendientes,
      mayorVar,
    };
  }, [incidencias]);

  const kpiCard = ({ icon, label, value, subtitle, color = 'text-gray-200', ring = 'ring-gray-700/40', bg = 'bg-gray-900/60' }) => (
    <div className={`${bg} rounded-xl p-4 border border-gray-800 transition-transform duration-150 hover:scale-[1.01] hover:border-gray-700`}>
      <div className="flex items-center justify-between">
        <div>
          <div className="text-xs uppercase tracking-wider text-gray-400">{label}</div>
          <div className={`mt-1 text-2xl font-semibold ${color}`}>{value}</div>
          {subtitle && <div className="text-xs text-gray-500 mt-1">{subtitle}</div>}
        </div>
        <div className={`p-2 rounded-lg bg-gray-800/60 ${ring}`}>
          {icon}
        </div>
      </div>
    </div>
  );

  const mayorVarColor = stats.mayorVar && stats.mayorVar.valor >= 0 ? 'text-green-400' : 'text-red-400';
  const mayorVarDisp = stats.mayorVar ? 
    `${stats.mayorVar.valor >= 0 ? '+' : ''}${Number(stats.mayorVar.valor).toFixed(2)}%` : 
    '—';

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-7 gap-3">
      {kpiCard({
        icon: <AlertOctagon size={18} className="text-red-300" />, label: 'Total', value: stats.total,
        color: 'text-gray-100', ring: 'ring-red-700/40'
      })}
      {kpiCard({
        icon: <CheckCircle2 size={18} className="text-green-300" />, label: 'Aprobadas', value: stats.aprobadas,
        color: 'text-green-300', ring: 'ring-green-700/40'
      })}
      {kpiCard({
        icon: <XCircle size={18} className="text-red-300" />, label: 'Rechazadas', value: stats.rechazadas,
        color: 'text-red-300', ring: 'ring-red-700/40'
      })}
      {kpiCard({
        icon: <User size={18} className="text-blue-300" />, label: 'Turno analista', value: stats.turnoAnalista,
        color: 'text-blue-300', ring: 'ring-blue-700/40'
      })}
      {kpiCard({
        icon: <UserCheck size={18} className="text-purple-300" />, label: 'Turno supervisor', value: stats.turnoSupervisor,
        color: 'text-purple-300', ring: 'ring-purple-700/40'
      })}
      {kpiCard({
        icon: <TrendingUp size={18} className={`${mayorVarColor.replace('text-', 'fill-')}`} />, label: 'Mayor variación',
        value: mayorVarDisp, subtitle: stats.mayorVar ? stats.mayorVar.concepto : '', color: mayorVarColor, ring: 'ring-teal-700/40'
      })}
      {kpiCard({
        icon: <Clock size={18} className="text-yellow-300" />, label: 'Pendientes', value: stats.pendientes,
        color: 'text-yellow-300', ring: 'ring-yellow-700/40'
      })}
    </div>
  );
}
