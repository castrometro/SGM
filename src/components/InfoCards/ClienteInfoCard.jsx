import EstadoBadge from "../EstadoBadge";
import { Building2, FileText, Calendar, CheckCircle2 } from "lucide-react";

const ClienteInfoCard = ({ cliente, resumen, areaActiva }) => {
  // Determinar el estado del cierre según el área activa
  const getEstadoCierre = () => {
    if (!resumen) return null;
    
    // Para nómina usamos estado_cierre_actual
    if (areaActiva === "Nomina") {
      return resumen.estado_cierre_actual;
    }
    
    // Para contabilidad usamos estado_ultimo_cierre
    if (areaActiva === "Contabilidad") {
      return resumen.estado_ultimo_cierre;
    }
    
    // Fallback: intentar cualquiera de los dos campos
    return resumen.estado_cierre_actual || resumen.estado_ultimo_cierre;
  };

  return (
    <div className="bg-gradient-to-br from-gray-800 via-gray-800 to-gray-900 rounded-xl shadow-2xl overflow-hidden border border-gray-700/50">
      {/* Header con gradiente y nombre del cliente */}
      <div className="bg-gradient-to-r from-indigo-600/20 via-purple-600/20 to-pink-600/20 border-b border-gray-700/50 p-6">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-3">
              <div className="flex items-center justify-center w-12 h-12 rounded-xl bg-gradient-to-br from-indigo-500/20 to-purple-500/20 border border-indigo-500/30">
                <Building2 className="w-6 h-6 text-indigo-400" />
              </div>
              <div>
                <h2 className="text-2xl font-bold text-white leading-tight">{cliente.nombre}</h2>
                <p className="text-sm text-gray-400 mt-0.5">Cliente ID: #{cliente.id}</p>
              </div>
            </div>
            
            {/* Badges y info adicional */}
            <div className="flex flex-wrap items-center gap-2 mt-3">
              {cliente.bilingue && (
                <span className="inline-flex items-center gap-1.5 bg-blue-500/20 text-blue-300 text-xs font-medium px-3 py-1.5 rounded-full border border-blue-500/30">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129" />
                  </svg>
                  Bilingüe
                </span>
              )}
              {resumen?.source && (
                <span className={`inline-flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-full border ${
                  resumen.source === 'redis' 
                    ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30' 
                    : 'bg-amber-500/20 text-amber-300 border-amber-500/30'
                }`}>
                  {resumen.source === 'redis' ? '⚡' : '💾'}
                  {resumen.source === 'redis' ? 'Cache Activo' : 'Base de Datos'}
                </span>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Contenido principal */}
      <div className="p-6">
        {/* Grid de información básica */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          {/* RUT */}
          <div className="group bg-gradient-to-br from-gray-700/40 to-gray-800/40 rounded-lg p-4 border border-gray-700/50 hover:border-gray-600 transition-all duration-300">
            <div className="flex items-center gap-3">
              <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-purple-500/20 border border-purple-500/30">
                <FileText className="w-5 h-5 text-purple-400" />
              </div>
              <div>
                <p className="text-xs text-gray-400 uppercase tracking-wider mb-0.5">RUT</p>
                <p className="text-base font-semibold text-white">{cliente.rut || '—'}</p>
              </div>
            </div>
          </div>

          {/* Industria */}
          <div className="group bg-gradient-to-br from-gray-700/40 to-gray-800/40 rounded-lg p-4 border border-gray-700/50 hover:border-gray-600 transition-all duration-300">
            <div className="flex items-center gap-3">
              <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-blue-500/20 border border-blue-500/30">
                <Building2 className="w-5 h-5 text-blue-400" />
              </div>
              <div>
                <p className="text-xs text-gray-400 uppercase tracking-wider mb-0.5">Industria</p>
                <p className="text-base font-semibold text-white">{cliente.industria_nombre || '—'}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Grid de estado del cierre */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Último Cierre */}
          <div className="group bg-gradient-to-br from-gray-700/40 to-gray-800/40 rounded-lg p-5 border border-gray-700/50 hover:border-gray-600 hover:shadow-lg transition-all duration-300 hover:-translate-y-0.5">
            <div className="absolute top-0 left-0 w-1 h-full rounded-l-lg bg-indigo-500" />
            <div className="ml-2">
              <div className="flex items-center gap-2 mb-2">
                <Calendar className="w-4 h-4 text-indigo-400" />
                <span className="text-xs font-medium text-gray-400 uppercase tracking-wider">Último Cierre</span>
              </div>
              <p className="text-2xl font-bold text-indigo-300 tabular-nums">
                {resumen.ultimo_cierre || resumen.periodo || '—'}
              </p>
            </div>
          </div>

          {/* Estado del Cierre */}
          <div className="group bg-gradient-to-br from-gray-700/40 to-gray-800/40 rounded-lg p-5 border border-gray-700/50 hover:border-gray-600 hover:shadow-lg transition-all duration-300 hover:-translate-y-0.5">
            <div className="absolute top-0 left-0 w-1 h-full rounded-l-lg bg-emerald-500" />
            <div className="ml-2">
              <div className="flex items-center gap-2 mb-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                <span className="text-xs font-medium text-gray-400 uppercase tracking-wider">Estado</span>
              </div>
              <div className="mt-1">
                <EstadoBadge estado={getEstadoCierre()} />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Efecto de brillo sutil en el fondo */}
      <div className="absolute inset-0 rounded-xl opacity-0 hover:opacity-100 transition-opacity duration-500 pointer-events-none">
        <div className="absolute inset-0 rounded-xl bg-gradient-to-br from-white/[0.02] to-transparent" />
      </div>
    </div>
  );
};

export default ClienteInfoCard;
