import React, { useState } from 'react';
import { Database, Cloud, FileText, Info } from 'lucide-react';

/**
 * Badge que indica la fuente de datos del dashboard
 * @param {object} metadata - Objeto _metadata de la respuesta API o {source, fecha_generacion} legacy
 * @param {string} size - Tamaño del badge: 'sm', 'md', 'lg'
 */
const DataSourceBadge = ({ metadata, size = 'md' }) => {
  const [showTooltip, setShowTooltip] = useState(false);

  if (!metadata) {
    return null;
  }

  // Soporte para formato legacy (source: 'redis'|'bd') y nuevo (_metadata.fuente)
  let fuente, descripcion, generado_en, cached_at, ttl_estimado, fecha_informe, tablas_consultadas;
  
  if (metadata.fuente) {
    // Formato nuevo con _metadata
    ({ fuente, descripcion, generado_en, cached_at, ttl_estimado, fecha_informe, tablas_consultadas } = metadata);
  } else if (metadata.source) {
    // Formato legacy del informe persistente
    fuente = metadata.source === 'redis' ? 'cache_redis' : 'query_directo_bd';
    fecha_informe = metadata.fecha_generacion;
  } else {
    return null;
  }

  // Configuración por tipo de fuente
  const sourceConfig = {
    query_directo_bd: {
      label: 'Base de Datos',
      shortLabel: 'BD',
      icon: Database,
      color: 'bg-green-500/20 text-green-400 border-green-500/40',
      dotColor: 'bg-green-500',
      description: 'Datos consultados directamente desde la base de datos',
      priority: 'high'
    },
    cache_redis: {
      label: 'Caché Temporal',
      shortLabel: 'Cache',
      icon: Cloud,
      color: 'bg-blue-500/20 text-blue-400 border-blue-500/40',
      dotColor: 'bg-blue-500',
      description: 'Datos recuperados de caché Redis (pueden no estar actualizados)',
      priority: 'medium'
    },
    informe_persistente: {
      label: 'Informe Histórico',
      shortLabel: 'Histórico',
      icon: FileText,
      color: 'bg-gray-500/20 text-gray-400 border-gray-500/40',
      dotColor: 'bg-gray-500',
      description: 'Informe generado previamente y almacenado de forma permanente',
      priority: 'low'
    }
  };

  const config = sourceConfig[fuente] || sourceConfig.query_directo_bd;
  const Icon = config.icon;

  // Tamaños
  const sizeClasses = {
    sm: {
      container: 'px-2 py-1 text-xs gap-1.5',
      icon: 12,
      dot: 'w-1.5 h-1.5'
    },
    md: {
      container: 'px-3 py-1.5 text-sm gap-2',
      icon: 14,
      dot: 'w-2 h-2'
    },
    lg: {
      container: 'px-4 py-2 text-base gap-2.5',
      icon: 16,
      dot: 'w-2.5 h-2.5'
    }
  };

  const sizeClass = sizeClasses[size] || sizeClasses.md;

  // Formatear fechas
  const formatearFecha = (isoString) => {
    if (!isoString) return null;
    try {
      const fecha = new Date(isoString);
      return fecha.toLocaleString('es-CL', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch (e) {
      return isoString;
    }
  };

  // Formatear TTL
  const formatearTTL = (segundos) => {
    if (!segundos || segundos < 0) return null;
    if (segundos < 60) return `${segundos}s`;
    if (segundos < 3600) return `${Math.floor(segundos / 60)}m`;
    if (segundos < 86400) return `${Math.floor(segundos / 3600)}h`;
    return `${Math.floor(segundos / 86400)}d`;
  };

  return (
    <div className="relative inline-block">
      <div
        className={`
          flex items-center ${sizeClass.container}
          ${config.color}
          border rounded-lg font-medium
          transition-all duration-200
          hover:scale-105 cursor-help
        `}
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
      >
        {/* Dot indicator */}
        <span className={`${sizeClass.dot} ${config.dotColor} rounded-full animate-pulse`} />
        
        {/* Icon */}
        <Icon size={sizeClass.icon} className="flex-shrink-0" />
        
        {/* Label */}
        <span className="whitespace-nowrap">
          {size === 'sm' ? config.shortLabel : config.label}
        </span>

        {/* Info icon */}
        <Info size={sizeClass.icon - 2} className="opacity-60 ml-0.5" />
      </div>

      {/* Tooltip detallado */}
      {showTooltip && (
        <div className="absolute z-50 top-full mt-2 left-0 min-w-[320px] max-w-[400px]">
          <div className="bg-gray-900 border border-gray-700 rounded-lg shadow-xl p-4">
            {/* Header */}
            <div className="flex items-start gap-3 mb-3">
              <div className={`p-2 rounded-lg ${config.color}`}>
                <Icon size={20} />
              </div>
              <div className="flex-1">
                <h3 className="text-sm font-bold text-white mb-1">{config.label}</h3>
                <p className="text-xs text-gray-400">{descripcion || config.description}</p>
              </div>
            </div>

            {/* Divider */}
            <div className="border-t border-gray-700 my-3" />

            {/* Detalles técnicos */}
            <div className="space-y-2 text-xs">
              {/* Fecha generación o cache */}
              {generado_en && (
                <div className="flex justify-between items-center">
                  <span className="text-gray-500">Generado:</span>
                  <span className="text-gray-300 font-mono">{formatearFecha(generado_en)}</span>
                </div>
              )}

              {cached_at && (
                <div className="flex justify-between items-center">
                  <span className="text-gray-500">En cache desde:</span>
                  <span className="text-gray-300 font-mono">{formatearFecha(cached_at)}</span>
                </div>
              )}

              {fecha_informe && (
                <div className="flex justify-between items-center">
                  <span className="text-gray-500">Fecha informe:</span>
                  <span className="text-gray-300 font-mono">{formatearFecha(fecha_informe)}</span>
                </div>
              )}

              {/* TTL si es cache */}
              {ttl_estimado && (
                <div className="flex justify-between items-center">
                  <span className="text-gray-500">Expira en:</span>
                  <span className={`font-mono ${ttl_estimado < 60 ? 'text-yellow-400' : 'text-blue-400'}`}>
                    {formatearTTL(ttl_estimado)}
                  </span>
                </div>
              )}

              {/* Tablas consultadas */}
              {tablas_consultadas && tablas_consultadas.length > 0 && (
                <div className="pt-2 border-t border-gray-700">
                  <div className="text-gray-500 mb-1">Tablas consultadas:</div>
                  <div className="flex flex-wrap gap-1">
                    {tablas_consultadas.map((tabla, idx) => (
                      <span
                        key={idx}
                        className="px-2 py-0.5 bg-gray-800 text-gray-300 rounded text-[10px] font-mono"
                      >
                        {tabla}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Footer con advertencia si es cache/histórico */}
            {fuente !== 'query_directo_bd' && (
              <>
                <div className="border-t border-gray-700 my-3" />
                <div className="flex items-start gap-2 text-xs">
                  <span className="text-yellow-500">⚠️</span>
                  <p className="text-gray-400">
                    {fuente === 'cache_redis' 
                      ? 'Los datos pueden no estar completamente actualizados. Re-consolida el cierre para actualizar.'
                      : 'Este es un informe histórico. No refleja cambios recientes en los datos.'
                    }
                  </p>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default DataSourceBadge;
