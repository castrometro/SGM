// src/modules/contabilidad/cliente-detalle/components/KpiResumenContabilidad.jsx
import { FileText, DollarSign, TrendingUp, TrendingDown, Scale } from "lucide-react";

/**
 * Resumen de KPIs de Contabilidad
 * Muestra métricas clave del último cierre
 */
const KpiResumenContabilidad = ({ resumen }) => {
  if (!resumen) {
    return (
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <p className="text-gray-400">No hay datos de cierre disponibles</p>
      </div>
    );
  }

  const kpis = resumen.kpis || {};

  // Calcular métricas
  const totalMovimientos = kpis.total_movimientos || 0;
  const totalDebe = kpis.total_debe || 0;
  const totalHaber = kpis.total_haber || 0;
  const diferencia = Math.abs(totalDebe - totalHaber);
  const estaBalanceado = diferencia < 1; // Tolerancia de 1 peso

  const formatMoney = (value) => {
    return new Intl.NumberFormat('es-CL', {
      style: 'currency',
      currency: 'CLP',
      minimumFractionDigits: 0
    }).format(value);
  };

  const metricas = [
    {
      label: "Total Movimientos",
      value: totalMovimientos,
      icon: FileText,
      color: "text-purple-400",
      bg: "bg-purple-500/20",
      border: "border-purple-500/30",
      format: (v) => v.toLocaleString('es-CL')
    },
    {
      label: "Total Debe",
      value: totalDebe,
      icon: TrendingUp,
      color: "text-blue-400",
      bg: "bg-blue-500/20",
      border: "border-blue-500/30",
      format: formatMoney
    },
    {
      label: "Total Haber",
      value: totalHaber,
      icon: TrendingDown,
      color: "text-indigo-400",
      bg: "bg-indigo-500/20",
      border: "border-indigo-500/30",
      format: formatMoney
    },
    {
      label: "Diferencia",
      value: diferencia,
      icon: Scale,
      color: estaBalanceado ? "text-emerald-400" : "text-red-400",
      bg: estaBalanceado ? "bg-emerald-500/20" : "bg-red-500/20",
      border: estaBalanceado ? "border-emerald-500/30" : "border-red-500/30",
      format: formatMoney
    },
  ];

  return (
    <div className="bg-gray-800 rounded-lg p-6 shadow-lg border border-gray-700">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-white">Resumen del Cierre</h3>
          <p className="text-sm text-gray-400 mt-1">
            Métricas clave del período {resumen.periodo || resumen.ultimo_cierre}
          </p>
        </div>
        {resumen.source && (
          <span className={`text-xs px-3 py-1 rounded-full ${
            resumen.source === 'redis' 
              ? 'bg-emerald-500/20 text-emerald-300' 
              : 'bg-amber-500/20 text-amber-300'
          }`}>
            {resumen.source === 'redis' ? '⚡ Cache' : '💾 DB'}
          </span>
        )}
      </div>
      
      {/* Estado de balance */}
      {estaBalanceado ? (
        <div className="mb-6 p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-lg">
          <div className="flex items-center gap-2">
            <Scale className="w-5 h-5 text-emerald-400" />
            <div>
              <p className="text-sm font-semibold text-emerald-300">Contabilidad Balanceada</p>
              <p className="text-xs text-gray-400 mt-0.5">El debe y el haber están equilibrados</p>
            </div>
          </div>
        </div>
      ) : (
        <div className="mb-6 p-4 bg-red-500/10 border border-red-500/30 rounded-lg">
          <div className="flex items-center gap-2">
            <Scale className="w-5 h-5 text-red-400" />
            <div>
              <p className="text-sm font-semibold text-red-300">Descuadre Detectado</p>
              <p className="text-xs text-gray-400 mt-0.5">
                Diferencia de {formatMoney(diferencia)} entre debe y haber
              </p>
            </div>
          </div>
        </div>
      )}
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {metricas.map((metrica, idx) => {
          const Icon = metrica.icon;
          return (
            <div
              key={idx}
              className={`bg-gradient-to-br from-gray-700/40 to-gray-800/40 rounded-lg p-4 
                border ${metrica.border} hover:border-gray-600 transition-all duration-300 
                hover:shadow-lg hover:-translate-y-0.5`}
            >
              <div className="flex items-center gap-3 mb-3">
                <div className={`flex items-center justify-center w-10 h-10 rounded-lg 
                  ${metrica.bg} border ${metrica.border}`}>
                  <Icon className={`w-5 h-5 ${metrica.color}`} />
                </div>
              </div>
              
              <p className="text-xs text-gray-400 uppercase tracking-wider mb-1">
                {metrica.label}
              </p>
              <p className={`text-xl font-bold ${metrica.color} tabular-nums`}>
                {metrica.format(metrica.value)}
              </p>
            </div>
          );
        })}
      </div>

      {/* Detalle adicional si está disponible */}
      {kpis.cuentas_con_movimientos !== undefined && (
        <div className="mt-6 pt-6 border-t border-gray-700">
          <h4 className="text-sm font-semibold text-gray-300 mb-3">Información Adicional</h4>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            <div className="bg-gray-700/30 rounded p-3">
              <p className="text-xs text-gray-400 mb-1">Cuentas Activas</p>
              <p className="text-sm font-semibold text-white">
                {kpis.cuentas_con_movimientos?.toLocaleString('es-CL') || '—'}
              </p>
            </div>
            {kpis.periodo_analizado && (
              <div className="bg-gray-700/30 rounded p-3">
                <p className="text-xs text-gray-400 mb-1">Período</p>
                <p className="text-sm font-semibold text-white">
                  {kpis.periodo_analizado}
                </p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default KpiResumenContabilidad;
