import React from 'react';
import { Calendar } from 'lucide-react';

const TarjetasMetricasMovimientos = ({ tarjetasMetrics, selectedCard, handleSelectCard, obtenerIconoTipo }) => {
  const cards = [
    { key: 'ingreso', label: 'Ingresos', value: tarjetasMetrics.ingresos, icon: obtenerIconoTipo('ingreso') },
    { key: 'finiquito', label: 'Finiquitos', value: tarjetasMetrics.finiquitos, icon: obtenerIconoTipo('finiquito') },
    { key: 'dias_ausencia_justificados', label: 'Días ausencia justificados', value: tarjetasMetrics.diasAusJustificados, icon: <Calendar className="w-5 h-5 text-emerald-400" /> },
    { key: 'vacaciones', label: 'Días de vacaciones', value: tarjetasMetrics.vacacionesDias, icon: <Calendar className="w-5 h-5 text-yellow-400" /> },
    { key: 'ausencias_sin_justificar', label: 'Ausencias sin justificar', value: tarjetasMetrics.ausSinJustificar, icon: <Calendar className="w-5 h-5 text-red-400" /> }
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
      {cards.map(c => (
        <div key={c.key} onClick={() => handleSelectCard(c.key)}
             className={`bg-gray-900/60 rounded-xl p-4 border transition-colors duration-200 cursor-pointer ${selectedCard===c.key ? 'border-teal-600 ring-1 ring-teal-600/40' : 'border-gray-800 hover:border-gray-700'}`}>
          <div className="flex items-center justify-between mb-1">
            {c.icon}
            <span className="text-2xl font-bold text-white">{c.value}</span>
          </div>
          <p className="text-sm text-gray-300">{c.label}</p>
        </div>
      ))}
    </div>
  );
};

export default TarjetasMetricasMovimientos;
