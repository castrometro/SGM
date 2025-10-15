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
  // Logs para debugging
  console.log('🔍 KpiResumenCliente - Props recibidas:', {
    areaActiva,
    resumen: resumen ? {
      keys: Object.keys(resumen),
      empleados_activos: resumen.empleados_activos,
      total_empleados: resumen.total_empleados,
      totales_categorias: resumen.totales_categorias,
      ultimo_cierre: resumen.ultimo_cierre,
      estado_cierre_actual: resumen.estado_cierre_actual,
      kpis: resumen.kpis,
      source: resumen.source,
      periodo: resumen.periodo
    } : null
  });

  // Solo mostrar KPIs de Nomina, resto "En Construcción..."
  const area = areaActiva;
  
  // Extraer metadata del informe
  const sourceInfo = resumen?.source || 'unknown';
  const periodo = resumen?.periodo || resumen?.ultimo_cierre || '—';
  const sourceColor = sourceInfo === 'redis' ? 'text-emerald-400' : sourceInfo === 'db' ? 'text-amber-400' : 'text-gray-500';
  const sourceIcon = sourceInfo === 'redis' ? '⚡' : sourceInfo === 'db' ? '💾' : '❓';

  console.log('🔍 KpiResumenCliente - Área determinada:', area);

  // Solo mostrar KPIs implementados para Nomina
  if (area !== 'Nomina') {
    console.log('🔍 KpiResumenCliente - Área no es Nomina, mostrando "En Construcción..."');
    return (
      <div className="bg-gray-800 p-6 rounded-lg shadow-lg">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold">KPIs del Cliente</h2>
          <span className="text-[11px] text-gray-500 uppercase tracking-wide">{area}</span>
        </div>
        <p className="text-gray-400 italic text-sm text-center py-8">En Construcción...</p>
      </div>
    );
  }

  const config = METRICS_CONFIG[area] || [];

  const metrics = useMemo(() => {
    const result = config.map(m => {
      let valueRaw = null;
      try { 
        valueRaw = m.derive(resumen); 
        console.log(`🔍 Métrica '${m.key}' (${m.label}):`, valueRaw);
      } catch (error) { 
        console.warn(`⚠️ Error calculando métrica '${m.key}':`, error);
        valueRaw = null; 
      }
      return { ...m, valueRaw, valueFormatted: m.format(valueRaw) };
    });
    
    console.log('🔍 KpiResumenCliente - Métricas calculadas:', result.map(m => ({
      key: m.key,
      label: m.label,
      valueRaw: m.valueRaw,
      valueFormatted: m.valueFormatted
    })));
    
    return result;
  }, [config, resumen]);

  // Mostrar siempre primeras 4 más cualquier adicional que tenga valor (hasta 6)
  const visible = metrics.filter((m,i) => i < 4 || (m.valueRaw !== null && m.valueRaw !== undefined)).slice(0,6);
  const emptyValues = visible.every(v => v.valueRaw === null || v.valueRaw === undefined);

  return (
    <div className="bg-gray-800 p-6 rounded-lg shadow-lg">
      <div className="flex items-center justify-between mb-4">
        <div className="flex flex-col gap-1">
          <h2 className="text-xl font-bold">KPIs del Cliente</h2>
          <div className="flex items-center gap-3 text-[11px]">
            <span className="text-gray-400">Periodo: <span className="text-gray-200 font-medium">{periodo}</span></span>
            <span className="text-gray-400">•</span>
            <span className="text-gray-400">
              Fuente: <span className={`font-medium ${sourceColor}`}>{sourceIcon} {sourceInfo.toUpperCase()}</span>
            </span>
          </div>
        </div>
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
