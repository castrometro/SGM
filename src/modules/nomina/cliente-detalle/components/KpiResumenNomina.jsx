// src/modules/nomina/cliente-detalle/components/KpiResumenNomina.jsx
import { Users, DollarSign, TrendingUp, TrendingDown } from "lucide-react";

/**
 * Resumen de KPIs de Nómina
 * Muestra métricas clave del último cierre
 */
const KpiResumenNomina = ({ resumen }) => {
  if (!resumen) {
    return (
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <p className="text-gray-400">No hay datos de cierre disponibles</p>
      </div>
    );
  }

  const kpis = resumen.kpis || {};
  const totalesCat = resumen.totales_categorias || {};

  // Calcular métricas
  const totalEmpleados = resumen.total_empleados || kpis.total_empleados || 0;
  const liquidoEstimado = kpis.liquido_estimado || 0;
  const totalHaberes = (Number(totalesCat.haber_imponible || 0) + Number(totalesCat.haber_no_imponible || 0));
  const totalDescuentos = (
    Number(totalesCat.descuento_legal || 0) + 
    Number(totalesCat.otro_descuento || 0) + 
    Number(totalesCat.impuesto || 0)
  );
  const promedioLiquido = totalEmpleados > 0 ? (liquidoEstimado / totalEmpleados) : 0;

  const formatMoney = (value) => {
    return new Intl.NumberFormat('es-CL', {
      style: 'currency',
      currency: 'CLP',
      minimumFractionDigits: 0
    }).format(value);
  };

  const metricas = [
    {
      label: "Total Empleados",
      value: totalEmpleados,
      icon: Users,
      color: "text-teal-400",
      bg: "bg-teal-500/20",
      border: "border-teal-500/30",
      format: (v) => v.toLocaleString('es-CL')
    },
    {
      label: "Líquido Total",
      value: liquidoEstimado,
      icon: DollarSign,
      color: "text-emerald-400",
      bg: "bg-emerald-500/20",
      border: "border-emerald-500/30",
      format: formatMoney
    },
    {
      label: "Promedio Líquido",
      value: promedioLiquido,
      icon: TrendingUp,
      color: "text-blue-400",
      bg: "bg-blue-500/20",
      border: "border-blue-500/30",
      format: formatMoney
    },
    {
      label: "Total Haberes",
      value: totalHaberes,
      icon: TrendingUp,
      color: "text-purple-400",
      bg: "bg-purple-500/20",
      border: "border-purple-500/30",
      format: formatMoney
    },
    {
      label: "Total Descuentos",
      value: totalDescuentos,
      icon: TrendingDown,
      color: "text-red-400",
      bg: "bg-red-500/20",
      border: "border-red-500/30",
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
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
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

      {/* Totales por categoría (opcional, detallado) */}
      {Object.keys(totalesCat).length > 0 && (
        <div className="mt-6 pt-6 border-t border-gray-700">
          <h4 className="text-sm font-semibold text-gray-300 mb-3">Detalle por Categoría</h4>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
            {Object.entries(totalesCat).map(([key, value]) => (
              <div key={key} className="bg-gray-700/30 rounded p-3">
                <p className="text-xs text-gray-400 mb-1 capitalize">
                  {key.replace(/_/g, ' ')}
                </p>
                <p className="text-sm font-semibold text-white">
                  {formatMoney(Number(value))}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default KpiResumenNomina;
