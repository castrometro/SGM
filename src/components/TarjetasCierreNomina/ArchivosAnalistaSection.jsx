import { useState, useEffect } from "react";
import { UserCheck, ChevronDown, ChevronRight, Lock } from "lucide-react";
import ArchivosAnalistaContainer from "./ArchivosAnalista/ArchivosAnalistaContainer";

const ArchivosAnalistaSection = ({
  cierreId,
  cliente,
  disabled = false
}) => {
  const [expandido, setExpandido] = useState(true);
  const [estadoArchivos, setEstadoArchivos] = useState({});

  // Función para determinar el estado general de la sección
  const calcularEstadoGeneral = () => {
    const estados = Object.values(estadoArchivos);
    if (estados.length === 0) return "Pendiente";
    
    // Si todos están procesados, la sección está procesada
    const todosProcessados = estados.every(estado => estado === "procesado");
    return todosProcessados ? "Procesado" : "Pendiente";
  };

  const estadoGeneral = calcularEstadoGeneral();
  const colorEstado = estadoGeneral === "Procesado" ? "text-green-400" : "text-yellow-400";

  return (
    <section className="space-y-6">
      {/* Header de la sección - ahora clicable (solo si no está disabled) */}
      <div 
        className={`flex items-center justify-between p-3 -m-3 rounded-lg transition-colors ${
          disabled 
            ? 'opacity-60 cursor-not-allowed' 
            : 'cursor-pointer hover:bg-gray-800/50'
        }`}
        onClick={() => !disabled && setExpandido(!expandido)}
      >
        <div className="flex items-center gap-3">
          <div className={`flex items-center justify-center w-10 h-10 rounded-lg ${
            disabled ? 'bg-gray-600' : 'bg-green-600'
          }`}>
            {disabled ? (
              <Lock size={20} className="text-white" />
            ) : (
              <UserCheck size={20} className="text-white" />
            )}
          </div>
          <div>
            <h2 className={`text-xl font-semibold ${disabled ? 'text-gray-400' : 'text-white'}`}>
              Archivos del Analista
              {disabled && (
                <span className="ml-2 text-sm font-normal text-gray-500">
                  (Bloqueado - Datos Consolidados)
                </span>
              )}
            </h2>
            <p className="text-gray-400 text-sm">
              {disabled 
                ? 'Los archivos están bloqueados porque los datos ya han sido consolidados'
                : 'Archivos complementarios gestionados por el analista'
              }
            </p>
          </div>
        </div>
        
        <div className="flex items-center gap-3">
          {!expandido && !disabled && (
            <span className={`text-sm font-medium ${colorEstado}`}>
              {estadoGeneral}
            </span>
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
      
      {/* Contenedor de archivos del analista - solo se muestra cuando está expandido y no disabled */}
      {expandido && !disabled && (
        <ArchivosAnalistaContainer
          cierreId={cierreId}
          cliente={cliente}
          disabled={disabled}
          onEstadosChange={setEstadoArchivos}
        />
      )}
    </section>
  );
};

export default ArchivosAnalistaSection;
