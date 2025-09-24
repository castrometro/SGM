import React from 'react';
import { Users, Calendar } from 'lucide-react';

const TarjetasLibro = ({ resumen, selectedCat, setSelectedCat, formatearMonto }) => {
  const tot = resumen?.totales_categorias || {};
  const cardBase = 'group inline-flex cursor-pointer bg-gray-900/60 rounded-lg px-5 py-4 border transition-colors flex-col gap-1 w-full sm:w-auto';
  const toggle = key => setSelectedCat(prev => prev === key ? '' : key);
  return (
    <div className="flex flex-wrap gap-4">
      <div className="group inline-flex bg-gray-900/60 rounded-lg px-5 py-4 border border-gray-800 hover:border-teal-700/60 transition-colors flex-col gap-1 w-full sm:w-auto">
        <div className="flex items-center justify-between mb-1">
          <p className="text-[11px] font-medium tracking-wide text-gray-400 group-hover:text-teal-300/90 uppercase">Total Empleados</p>
          <Users className="w-5 h-5 text-teal-500" />
        </div>
        <p className="text-2xl font-semibold text-white leading-snug tabular-nums whitespace-nowrap">{resumen?.cierre?.total_empleados || 0}</p>
      </div>
      <div className="group inline-flex bg-gray-900/60 rounded-lg px-5 py-4 border border-gray-800 hover:border-teal-700/60 transition-colors flex-col gap-1 w-full sm:w-auto">
        <div className="flex items-center justify-between mb-1">
          <p className="text-[11px] font-medium tracking-wide text-gray-400 group-hover:text-teal-300/90 uppercase">Mes Cierre</p>
          <Calendar className="w-5 h-5 text-teal-500" />
        </div>
        <p className="text-2xl font-semibold text-white leading-snug tabular-nums whitespace-nowrap">{(resumen?.cierre?.periodo || '').toString().slice(0,7) || '-'}</p>
      </div>
      {['haber_imponible','haber_no_imponible','descuento_legal','otro_descuento','impuesto','aporte_patronal'].map(key => {
        const meta = {
          haber_imponible: { label: 'Haberes Imponibles', cls:'text-green-400' },
          haber_no_imponible: { label: 'Haberes No Imponibles', cls:'text-green-400' },
          descuento_legal: { label: 'Descuentos Legales', cls:'text-red-400' },
          otro_descuento: { label: 'Otros Descuentos', cls:'text-red-400' },
          impuesto: { label: 'Impuestos', cls:'text-red-300' },
          aporte_patronal: { label: 'Aportes Patronales', cls:'text-indigo-300' }
        }[key];
        const active = selectedCat === key;
        return (
          <div key={key} onClick={()=>toggle(key)} className={`${cardBase} ${active? 'border-teal-600 ring-1 ring-teal-600/30':'border-gray-800 hover:border-teal-700/60'}`}>
            <p className="text-[11px] font-medium tracking-wide text-gray-400 group-hover:text-teal-300/90 uppercase">{meta.label}</p>
            <p className={`text-2xl font-semibold leading-snug tabular-nums whitespace-nowrap ${meta.cls}`}>{formatearMonto(tot[key])}</p>
          </div>
        );
      })}
    </div>
  );
};

export default TarjetasLibro;
