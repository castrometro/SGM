import React, { useMemo } from 'react';

// Formateadores básicos
const formatNumber = (v) => (v === null || v === undefined || isNaN(v) ? '—' : new Intl.NumberFormat('es-CL').format(Number(v)));
const formatCurrency = (v) => (v === null || v === undefined || isNaN(v) ? '—' : new Intl.NumberFormat('es-CL',{ style:'currency', currency:'CLP', minimumFractionDigits:0, maximumFractionDigits:0 }).format(Number(v)));
const formatPercent = (v) => (v === null || v === undefined || isNaN(v) ? '—' : `${Number(v).toFixed(2)}%`);

// Config de métricas por área; cada métrica: key, label, derive(resumen), format, importance
const METRICS_CONFIG = {
  Nomina: [
    // 👥 Dotación y Rotación
    { 
      key:'total_empleados', 
      label:'Dotación Actual', 
      derive: r => r?.total_empleados ?? r?.empleados_activos ?? null, 
      format: formatNumber,
      section: 'dotacion'
    },
    
    // 💰 Haberes
    { 
      key:'total_haberes', 
      label:'Total Haberes', 
      derive: r => {
        const imp = r?.totales_categorias?.haber_imponible ?? 0;
        const noImp = r?.totales_categorias?.haber_no_imponible ?? 0;
        return imp + noImp || null;
      }, 
      format: formatCurrency, 
      accent:'positive',
      section: 'haberes'
    },
    { 
      key:'haber_imponible', 
      label:'Haberes Imponibles', 
      derive: r => r?.totales_categorias?.haber_imponible ?? null, 
      format: formatCurrency, 
      accent:'positive',
      section: 'haberes'
    },
    { 
      key:'haber_no_imponible', 
      label:'Haberes No Imponibles', 
      derive: r => r?.totales_categorias?.haber_no_imponible ?? null, 
      format: formatCurrency, 
      accent:'neutral',
      section: 'haberes'
    },
    
    // 📉 Descuentos
    { 
      key:'descuento_legal', 
      label:'Descuentos Legales', 
      derive: r => r?.totales_categorias?.descuento_legal ?? null, 
      format: formatCurrency, 
      accent:'negative',
      section: 'descuentos'
    },
    { 
      key:'otro_descuento', 
      label:'Otros Descuentos', 
      derive: r => r?.totales_categorias?.otro_descuento ?? null, 
      format: formatCurrency, 
      accent:'negative',
      section: 'descuentos'
    },
    
    // 🏢 Aportes
    { 
      key:'aporte_patronal', 
      label:'Aportes Patronales', 
      derive: r => r?.totales_categorias?.aporte_patronal ?? null, 
      format: formatCurrency, 
      accent:'neutral',
      section: 'aportes'
    },
    
    // 📊 Tasas de Rotación
    { 
      key:'tasa_ingreso', 
      label:'Tasa de Ingreso', 
      derive: r => {
        const ingresos = r?.kpis?.movimientos_por_tipo?.ingreso?.empleados_unicos ?? 0;
        const empleados = r?.total_empleados ?? r?.empleados_activos;
        if (!empleados || empleados === 0) return null;
        return (ingresos / empleados) * 100;
      }, 
      format: formatPercent, 
      accent:'positive',
      section: 'rotacion'
    },
    { 
      key:'tasa_finiquito', 
      label:'Tasa de Finiquitos', 
      derive: r => {
        const finiquitos = r?.kpis?.movimientos_por_tipo?.finiquito?.empleados_unicos ?? 0;
        const empleados = r?.total_empleados ?? r?.empleados_activos;
        if (!empleados || empleados === 0) return null;
        return (finiquitos / empleados) * 100;
      }, 
      format: formatPercent, 
      accent:'negative',
      section: 'rotacion'
    },
    { 
      key:'rotacion_mensual', 
      label:'Rotación Mensual', 
      derive: r => {
        const finiquitos = r?.kpis?.movimientos_por_tipo?.finiquito?.empleados_unicos ?? 0;
        const empleados = r?.total_empleados ?? r?.empleados_activos;
        if (!empleados || empleados === 0) return null;
        return (finiquitos / empleados) * 100;
      }, 
      format: formatPercent, 
      accent:'neutral',
      section: 'rotacion',
      tooltip: 'Aproximación: (Finiquitos / Dotación Actual) × 100'
    },
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

  // Filtrar solo métricas con valores para mostrar
  const metricasConValor = useMemo(() => {
    return metrics.filter(m => m.valueRaw !== null && m.valueRaw !== undefined);
  }, [metrics]);

  const emptyValues = metrics.every(v => v.valueRaw === null || v.valueRaw === undefined);

  return (
    <div className="bg-gradient-to-br from-gray-800 via-gray-800 to-gray-900 rounded-xl shadow-2xl overflow-hidden">
      {/* Header con gradiente */}
      <div className="bg-gradient-to-r from-blue-600/20 to-purple-600/20 border-b border-gray-700/50 p-6">
        <div className="flex items-center justify-between">
          <div className="flex flex-col gap-2">
            <h2 className="text-2xl font-bold text-white">Indicadores Clave</h2>
            <div className="flex items-center gap-4 text-xs">
              <div className="flex items-center gap-2 bg-gray-900/50 px-3 py-1.5 rounded-full border border-gray-700/50">
                <span className="text-gray-400">Período:</span>
                <span className="text-white font-semibold">{periodo}</span>
              </div>
              <div className="flex items-center gap-2 bg-gray-900/50 px-3 py-1.5 rounded-full border border-gray-700/50">
                <span className="text-gray-400">Fuente:</span>
                <span className={`font-semibold ${sourceColor}`}>
                  {sourceIcon} {sourceInfo === 'redis' ? 'Redis' : sourceInfo === 'db' ? 'Base de Datos' : 'N/A'}
                </span>
              </div>
            </div>
          </div>
          <div className="px-4 py-2 bg-gray-900/70 rounded-lg border border-gray-700/50">
            <span className="text-xs text-gray-400 uppercase tracking-wider">{area}</span>
          </div>
        </div>
      </div>
      
      {/* Contenido */}
      <div className="p-6">
        {emptyValues && (
          <div className="text-center py-12">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gray-700/50 mb-4">
              <svg className="w-8 h-8 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <p className="text-gray-400 text-sm">Sin datos suficientes para mostrar indicadores.</p>
          </div>
        )}
        
        {!emptyValues && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {metricasConValor.map((m, idx) => (
              <div 
                key={m.key}
                className="group relative bg-gradient-to-br from-gray-700/40 to-gray-800/40 rounded-lg p-5 border border-gray-700/50 hover:border-gray-600 hover:shadow-lg transition-all duration-300 hover:-translate-y-1"
                title={m.tooltip}
              >
                {/* Indicador de color según accent */}
                <div className={`absolute top-0 left-0 w-1 h-full rounded-l-lg ${
                  m.accent === 'positive' ? 'bg-emerald-500' : 
                  m.accent === 'negative' ? 'bg-rose-500' : 
                  'bg-indigo-500'
                }`} />
                
                <div className="flex flex-col gap-2 ml-2">
                  <div className="flex items-start justify-between">
                    <span className="text-xs font-medium text-gray-400 uppercase tracking-wider">
                      {m.label}
                    </span>
                    {m.tooltip && (
                      <svg className="w-4 h-4 text-gray-500 group-hover:text-gray-400 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    )}
                  </div>
                  
                  <span className={`text-2xl font-bold tabular-nums ${
                    m.accent === 'positive' ? 'text-emerald-400' : 
                    m.accent === 'negative' ? 'text-rose-400' : 
                    m.accent === 'neutral' ? 'text-indigo-300' :
                    'text-gray-100'
                  }`}>
                    {m.valueFormatted}
                  </span>
                </div>
                
                {/* Efecto de brillo en hover */}
                <div className="absolute inset-0 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none">
                  <div className="absolute inset-0 rounded-lg bg-gradient-to-br from-white/5 to-transparent" />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
      
      {/* Footer con leyenda */}
      {!emptyValues && (
        <div className="px-6 pb-6">
          <div className="flex items-center justify-center gap-6 pt-4 border-t border-gray-700/50">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-emerald-500 shadow-lg shadow-emerald-500/50" />
              <span className="text-xs text-gray-400">Positivo</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-rose-500 shadow-lg shadow-rose-500/50" />
              <span className="text-xs text-gray-400">Negativo</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-indigo-500 shadow-lg shadow-indigo-500/50" />
              <span className="text-xs text-gray-400">Neutro</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default KpiResumenCliente;
