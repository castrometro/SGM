import React from 'react';
import { Calendar } from 'lucide-react';

const TarjetasMetricasMovimientos = ({ tarjetasMetrics, selectedCard, handleSelectCard, obtenerIconoTipo, comparativo }) => {
  const cards = [
    { key: 'ingreso', label: 'Ingresos', value: tarjetasMetrics.ingresos, icon: obtenerIconoTipo('ingreso') },
    { key: 'finiquito', label: 'Finiquitos', value: tarjetasMetrics.finiquitos, icon: obtenerIconoTipo('finiquito') },
    { key: 'dias_ausencia_justificados', label: 'Días ausencia justificados', value: tarjetasMetrics.diasAusJustificados, icon: <Calendar className="w-5 h-5 text-emerald-400" /> },
    { key: 'vacaciones', label: 'Días de vacaciones', value: tarjetasMetrics.vacacionesDias, icon: <Calendar className="w-5 h-5 text-yellow-400" /> },
    { key: 'ausencias_sin_justificar', label: 'Ausencias sin justificar', value: tarjetasMetrics.ausSinJustificar, icon: <Calendar className="w-5 h-5 text-red-400" /> }
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
      {cards.map(c => {
        const delta = comparativo?.[c.key]?.delta ?? null;
        const pct = comparativo?.[c.key]?.pct ?? null;
        const pos = delta !== null ? delta > 0 : false;
        const deltaCls = delta === null || delta === 0 ? 'text-gray-400' : (pos ? 'text-emerald-400':'text-rose-400');
        return (
          <div key={c.key} onClick={() => handleSelectCard(c.key)}
               className={`bg-gray-900/60 rounded-xl p-4 border transition-colors duration-200 cursor-pointer ${selectedCard===c.key ? 'border-teal-600 ring-1 ring-teal-600/40' : 'border-gray-800 hover:border-gray-700'}`}>
            <div className="flex items-center justify-between mb-1">
              {c.icon}
              <span className="text-2xl font-bold text-white tabular-nums">{c.value}</span>
            </div>
            <p className="text-sm text-gray-300 mb-1">{c.label}</p>
            {comparativo && (
              <div className={`text-[11px] font-medium tabular-nums ${deltaCls}`}>
                {delta===null? '—' : `${delta>0?'+':''}${delta}`} {pct!==null? <span className="text-[10px] text-gray-400 ml-1">{pct>0?'+':''}{pct.toFixed(1)}%</span> : null}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};

export default TarjetasMetricasMovimientos;
