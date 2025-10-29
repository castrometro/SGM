import React from 'react';
import { ArrowLeft, Sparkles, Download } from 'lucide-react';
import DataSourceBadge from '../common/DataSourceBadge';

export const HeaderMovimientos = ({ cliente, periodo, onBack, metadata }) => {
  console.log('🎨 [HeaderMovimientos] Metadata recibida:', metadata);
  
  return (
  <div className="bg-gradient-to-b from-teal-900/20 to-transparent border-b border-gray-800">
    <div className="w-full px-6 py-5">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={onBack}
            className="p-2 hover:bg-gray-800 rounded-lg transition-colors border border-gray-800"
            aria-label="Volver"
          >
            <ArrowLeft size={18} />
          </button>
          <div>
            <div className="flex items-center gap-2">
              <Sparkles className="text-teal-400" size={18} />
              <h1 className="text-2xl font-bold text-teal-400">Movimientos de Personal</h1>
            </div>
            <p className="text-gray-400">{cliente} · {periodo}</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {/* Badge de fuente de datos */}
          <DataSourceBadge metadata={metadata} size="md" />
          
          <button
            onClick={() => window.print()}
            className="bg-teal-600/90 hover:bg-teal-600 text-white px-4 py-2 rounded-lg font-medium transition-colors transition-transform duration-200 hover:scale-[1.02] flex items-center gap-2 shadow shadow-teal-900/30"
          >
            <Download size={16} />
            Exportar
          </button>
        </div>
      </div>
    </div>
  </div>
  );
};

export default HeaderMovimientos;
