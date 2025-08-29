import React, { useState } from "react";
import { ShieldCheck, ChevronDown, ChevronRight, Lock } from "lucide-react";

const VerificadorDatosSection_v2 = ({
  cierreId,
  enabled = false,
  titulo = "Verificación de Datos",
  descripcion = "Verificar discrepancias y consolidar datos"
}) => {
  const [expandido, setExpandido] = useState(false);

  return (
    <section className={`
      border rounded-lg backdrop-blur-sm transition-all duration-200
      ${enabled ? 'border-purple-500/30 bg-gray-800/50' : 'border-gray-600 bg-gray-800/30'}
    `}>
      <div 
        className={`
          flex items-center justify-between p-4 transition-colors
          ${enabled 
            ? 'cursor-pointer hover:bg-gray-800/70' 
            : 'opacity-60 cursor-not-allowed'
          }
        `}
        onClick={() => enabled && setExpandido(!expandido)}
      >
        <div className="flex items-center gap-3">
          <div className={`
            flex items-center justify-center w-12 h-12 rounded-lg
            ${enabled ? 'bg-purple-600' : 'bg-gray-600'}
          `}>
            {enabled ? (
              <ShieldCheck size={24} className="text-white" />
            ) : (
              <Lock size={24} className="text-white" />
            )}
          </div>

          <div>
            <h2 className={`text-xl font-semibold ${enabled ? 'text-white' : 'text-gray-400'}`}>
              {titulo}
              {!enabled && (
                <span className="ml-2 text-sm font-normal text-gray-500">
                  (Bloqueado)
                </span>
              )}
            </h2>
            <p className="text-sm text-gray-400">{descripcion}</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-sm font-medium text-green-400">
            Procesado (Placeholder)
          </span>
          
          {enabled && (
            <div className="text-gray-400 hover:text-white transition-colors">
              {expandido ? <ChevronDown size={20} /> : <ChevronRight size={20} />}
            </div>
          )}
        </div>
      </div>

      {expandido && (
        <div className="border-t border-gray-700/50 p-4">
          <div className="text-center py-8 text-gray-400">
            <ShieldCheck size={48} className="mx-auto mb-4 opacity-50" />
            <p className="mb-2">Sección en desarrollo</p>
            <p className="text-sm">Esta sección será implementada en la siguiente iteración</p>
          </div>
        </div>
      )}
    </section>
  );
};

export default VerificadorDatosSection_v2;
