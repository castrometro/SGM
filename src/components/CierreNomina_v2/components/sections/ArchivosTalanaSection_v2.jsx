import React, { useState } from "react";
import { Database, ChevronDown, ChevronRight, Lock } from "lucide-react";
import LibroRemuneracionesCard_v2 from "../cards/LibroRemuneracionesCard_v2";
import MovimientosMesCard_v2 from "../cards/MovimientosMesCard_v2";

const ArchivosTalanaSection_v2 = ({ 
  cierreId, 
  enabled = false,
  titulo = "Archivos de Talana",
  descripcion = "Subir y procesar archivos de Talana"
}) => {
  const [expandido, setExpandido] = useState(true);

  return (
    <div className={`
      border rounded-lg transition-all duration-200
      ${enabled 
        ? 'border-blue-500/30 bg-gray-800/30' 
        : 'border-gray-600/30 bg-gray-800/10'
      }
    `}>
      
      {/* 🎯 HEADER DE LA SECCIÓN */}
      <div 
        className={`
          p-4 cursor-pointer flex items-center justify-between
          ${enabled ? 'hover:bg-gray-800/50' : 'opacity-60 cursor-not-allowed'}
        `}
        onClick={() => enabled && setExpandido(!expandido)}
      >
        <div className="flex items-center gap-3">
          <div className={`
            flex items-center justify-center w-12 h-12 rounded-lg
            ${enabled ? 'bg-blue-600' : 'bg-gray-600'}
          `}>
            {enabled ? (
              <Database size={24} className="text-white" />
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
          {!enabled && (
            <span className="px-2 py-1 bg-gray-600/20 text-gray-400 rounded text-xs">
              Bloqueado
            </span>
          )}
          
          {enabled && (
            <div className="text-gray-400 hover:text-white transition-colors">
              {expandido ? <ChevronDown size={20} /> : <ChevronRight size={20} />}
            </div>
          )}
        </div>
      </div>

      {/* 🎯 CONTENIDO DE LA SECCIÓN */}
      {expandido && (
        <div className="border-t border-gray-700/50 p-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            
            {/* 📄 TARJETA LIBRO DE REMUNERACIONES */}
            <LibroRemuneracionesCard_v2
              cierreId={cierreId}
              enabled={enabled}
            />

            {/* 📊 TARJETA MOVIMIENTOS DEL MES */}
            <MovimientosMesCard_v2
              cierreId={cierreId}
              enabled={enabled}
            />

          </div>

          {/* 🎯 INFORMACIÓN ADICIONAL */}
          <div className="mt-4 p-3 bg-gray-900/50 rounded-lg border border-gray-700/30">
            <div className="text-sm text-gray-400">
              <p className="mb-1">
                <strong className="text-gray-300">Estado de la Sección:</strong> {enabled ? 'Habilitada' : 'Bloqueada'}
              </p>
              <p>
                <strong className="text-gray-300">Requisitos:</strong> 
                Ambos archivos deben estar procesados para continuar con la siguiente fase.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ArchivosTalanaSection_v2;
