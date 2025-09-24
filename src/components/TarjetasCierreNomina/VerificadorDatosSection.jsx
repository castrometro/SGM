import { useState } from "react";
import { ShieldCheck, ChevronDown, ChevronRight, Lock, Loader2 } from "lucide-react";
import VerificacionControl from "./VerificadorDatos/VerificacionControl";
import DiscrepanciasViewer from "./VerificadorDatos/DiscrepanciasViewer";

const VerificadorDatosSection = ({ 
  cierre, 
  disabled = false, 
  onCierreActualizado, 
  onEstadoChange, 
  deberiaDetenerPolling = false,
  
  // 🎯 Props para acordeón
  expandido = true,
  onToggleExpansion,
}) => {
  // 🎯 Estado local para recibir estadoDiscrepancias del componente hijo
  const [estadoDiscrepancias, setEstadoDiscrepancias] = useState(null);

  // 🎯 Callback para recibir estadoDiscrepancias del componente hijo
  const handleEstadoDiscrepanciasChange = (estado) => {
    setEstadoDiscrepancias(estado);
  };

  const obtenerColorEstado = () => {
    // Sin datos de verificación aún
    if (!estadoDiscrepancias) {
      if (cierre?.estado === 'creado' || cierre?.estado === 'archivos_pendientes') {
        return 'text-gray-500'; // Más tenue para estados iniciales
      } else if (cierre?.estado === 'archivos_completos') {
        return 'text-blue-400'; // Azul para "listo para verificar"
      } else if (cierre?.estado === 'verificacion_datos') {
        return 'text-yellow-400'; // Amarillo para "procesando"
      } else {
        return 'text-gray-400';
      }
    }
    
    // Con datos de verificación
    return estadoDiscrepancias.requiere_correccion ? 'text-red-400' : 'text-green-400';
  };

  const obtenerMensajeDescriptivo = () => {
    // Prioridad: si el backend reporta consolidación en curso, mostrarlo explícitamente
    if (cierre?.estado_consolidacion === 'consolidando') {
      return 'Consolidando datos de nómina...';
    }
    if (!estadoDiscrepancias) {
      // Mensajes según el estado del cierre cuando no hay verificación
      if (cierre?.estado === 'creado' || cierre?.estado === 'archivos_pendientes') {
        return 'Complete la carga de archivos para habilitar la verificación';
      } else if (cierre?.estado === 'archivos_completos') {
        return 'Todos los archivos cargados - Listo para verificar consistencia de datos';
      } else if (cierre?.estado === 'verificacion_datos') {
        return 'Procesando verificación de consistencia...';
      } else {
        return 'Verificación de consistencia entre Libro de Remuneraciones y Novedades';
      }
    } else {
      // Mensaje cuando ya hay datos de verificación
      return 'Verificación de consistencia entre Libro de Remuneraciones y Novedades';
    }
  };

  return (
    <section className="space-y-6">
      {/* Header unificado - maneja tanto disabled como normal */}
      <div 
        className={`flex items-center justify-between p-3 -m-3 rounded-lg transition-colors ${
          disabled 
            ? 'opacity-60 cursor-not-allowed' 
            : 'cursor-pointer hover:bg-gray-800/50'
        }`}
        onClick={() => !disabled && onToggleExpansion && onToggleExpansion()}
      >
        <div className="flex items-center gap-3">
          <div className={`flex items-center justify-center w-10 h-10 rounded-lg ${
            disabled ? 'bg-gray-600' : 'bg-orange-600'
          }`}>
            {disabled ? (
              <Lock size={20} className="text-white" />
            ) : (
              <ShieldCheck size={20} className="text-white" />
            )}
          </div>
          <div>
            <h2 className={`text-xl font-semibold ${disabled ? 'text-gray-400' : 'text-white'}`}>
              Verificación de Datos
              {disabled && (
                <span className="ml-2 text-sm font-normal text-gray-500">
                  (Bloqueado - Datos Consolidados)
                </span>
              )}
            </h2>
            <div className="flex items-center gap-2 text-sm">
              <p className="text-gray-400 flex items-center gap-2">
                {cierre?.estado_consolidacion === 'consolidando' && (
                  <Loader2 size={16} className="animate-spin text-yellow-400" />
                )}
                {disabled 
                  ? 'La verificación está bloqueada porque los datos ya han sido consolidados'
                  : obtenerMensajeDescriptivo()
                }
              </p>
              {!disabled && estadoDiscrepancias && (
                <span className={`${obtenerColorEstado()} font-medium`}>
                  • {estadoDiscrepancias.total_discrepancias || 0} discrepancias
                  {estadoDiscrepancias.total_discrepancias === 0 && estadoDiscrepancias.verificacion_completada && (
                    <span className="ml-2 text-green-300">✅ Verificación exitosa</span>
                  )}
                </span>
              )}
            </div>
          </div>
        </div>
        
        <div className="flex items-center gap-3">
          {!disabled && !expandido && estadoDiscrepancias && estadoDiscrepancias.total_discrepancias > 0 && (
            <div className="flex items-center gap-2 text-sm">
              <span className="text-white">
                {estadoDiscrepancias.total_discrepancias} discrepancias detectadas
              </span>
            </div>
          )}
          {disabled ? (
            <span className="text-sm font-medium text-gray-500">Bloqueado</span>
          ) : (
            expandido ? (
              <ChevronDown size={20} className="text-gray-400" />
            ) : (
              <ChevronRight size={20} className="text-gray-400" />
            )
          )}
        </div>
      </div>

      {/* Contenido condicional - solo se muestra cuando está expandido y no disabled */}
      {expandido && !disabled && (
        <div className="space-y-6">
          {/* 🎯 COMPONENTE DE CONTROL DE VERIFICACIÓN */}
          <VerificacionControl
            cierre={cierre}
            disabled={disabled}
            onEstadoChange={onEstadoChange}
            onCierreActualizado={onCierreActualizado}
            deberiaDetenerPolling={deberiaDetenerPolling}
            onEstadoDiscrepanciasChange={handleEstadoDiscrepanciasChange}
          />

          {/* 🎯 COMPONENTE DE VISUALIZACIÓN DE DISCREPANCIAS */}
          <DiscrepanciasViewer
            cierreId={cierre?.id}
            estadoDiscrepancias={estadoDiscrepancias}
            visible={expandido && !disabled}
          />
        </div>
      )}

    </section>
  );
};

export default VerificadorDatosSection;
