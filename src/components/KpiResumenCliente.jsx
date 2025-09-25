import React, { useMemo } from 'react';

// Formateadores básicos
const formatNumber = (v) => (v === null || v === undefined || isNaN(v) ? '—' : new Intl.NumberFormat('es-CL').format(Number(v)));
const formatCurrency = (v) => (v === null || v === undefined || isNaN(v) ? '—' : new Intl.NumberFormat('es-CL',{ style:'currency', currency:'CLP', minimumFractionDigits:0, maximumFractionDigits:0 }).format(Number(v)));
const formatPercent = (v) => (v === null || v === undefined || isNaN(v) ? '—' : `${Number(v).toFixed(1)}%`);

// Config de métricas por área; cada métrica: key, label, derive(resumen), format, importance
const METRICS_CONFIG = {
  Nomina: [
    { key:'empleados_activos', label:'Empleados Activos', derive: r => r?.empleados_activos ?? r?.total_empleados ?? null, format: formatNumber },
    { key:'haber_imponible', label:'Hab. Imponibles', derive: r => r?.totales_categorias?.haber_imponible ?? null, format: formatCurrency, accent:'positive' },
    { key:'haber_no_imponible', label:'Hab. No Imponibles', derive: r => r?.totales_categorias?.haber_no_imponible ?? null, format: formatCurrency, accent:'neutral' },
    { key:'descuento_legal', label:'Desc. Legales', derive: r => r?.totales_categorias?.descuento_legal ?? null, format: formatCurrency, accent:'negative' },
    { key:'promedio_imponible', label:'Prom. Imponible / Emp', derive: r => {
        const total = r?.totales_categorias?.haber_imponible;
        const empleados = r?.empleados_activos ?? r?.total_empleados;
        if (!total || !empleados) return null;
        return total / empleados;
      }, format: formatCurrency },
  ],
  Contabilidad: [
    { key:'estado', label:'Estado Cierre', derive: r => r?.estado_ultimo_cierre ?? r?.estado_cierre_actual ?? null, format: v => v || '—' },
    { key:'ingresos_mes', label:'Ingresos Mes', derive: r => r?.ingresos_mes ?? r?.ingresos ?? null, format: formatCurrency, accent:'positive' },
    { key:'egresos_mes', label:'Egresos Mes', derive: r => r?.egresos_mes ?? r?.egresos ?? null, format: formatCurrency, accent:'negative' },
    { key:'margen_bruto', label:'Margen Bruto', derive: r => {
        const ing = r?.ingresos_mes ?? r?.ingresos;
        const eg = r?.egresos_mes ?? r?.egresos;
        if (ing == null || eg == null) return null;
        return ing - eg;
      }, format: formatCurrency, accent:'neutral' },
    { key:'margen_pct', label:'Margen %', derive: r => {
        const ing = r?.ingresos_mes ?? r?.ingresos;
        const eg = r?.egresos_mes ?? r?.egresos;
        if (!ing || ing === 0 || eg == null) return null;
        return ((ing - eg) / ing) * 100;
      }, format: formatPercent, accent:'neutral' },
  ]
};

const accentClasses = {
  positive: 'text-emerald-400',
  negative: 'text-rose-400',
  neutral: 'text-indigo-300'
};

const KpiResumenCliente = ({ resumen, areaActiva }) => {
  const area = areaActiva === 'Nomina' ? 'Nomina' : (areaActiva === 'Contabilidad' ? 'Contabilidad' : 'Nomina');
  const config = METRICS_CONFIG[area] || [];

  const metrics = useMemo(() => {
    return config.map(m => {
      let valueRaw = null;
      try { valueRaw = m.derive(resumen); } catch { valueRaw = null; }
      return { ...m, valueRaw, valueFormatted: m.format(valueRaw) };
    });
  }, [config, resumen]);

  // Mostrar siempre primeras 4 más cualquier adicional que tenga valor (hasta 6)
  const visible = metrics.filter((m,i) => i < 4 || (m.valueRaw !== null && m.valueRaw !== undefined)).slice(0,6);
  const emptyValues = visible.every(v => v.valueRaw === null || v.valueRaw === undefined);

  return (
    <div className="bg-gray-800 p-6 rounded-lg shadow-lg">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold">KPIs del Cliente</h2>
        <span className="text-[11px] text-gray-500 uppercase tracking-wide">{area}</span>
      </div>
      {emptyValues && (
        <p className="text-gray-400 italic text-sm">Sin datos suficientes para KPIs rápidos.</p>
      )}
      {!emptyValues && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {visible.map(m => (
            <div key={m.key} className="bg-gray-700/60 border border-gray-600/30 rounded-md p-4 flex flex-col gap-1 hover:border-gray-500/50 transition">
              <span className="text-[11px] uppercase tracking-wide text-gray-400">{m.label}</span>
              <span className={`text-lg font-semibold tabular-nums ${m.accent ? accentClasses[m.accent] : 'text-gray-200'}`}>{m.valueFormatted}</span>
            </div>
          ))}
        </div>
      )}
      <div className="mt-4 flex flex-wrap gap-3 text-[11px] text-gray-500">
        <span className="inline-flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-emerald-400" /> Positivo</span>
        <span className="inline-flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-rose-400" /> Negativo</span>
        <span className="inline-flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-indigo-300" /> Neutro</span>
      </div>
    </div>
  );
};

export default KpiResumenCliente;
