import { useState, useEffect } from "react";
import { UserCheck, ChevronDown, ChevronRight } from "lucide-react";
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
      {/* Header de la sección - ahora clicable */}
      <div 
        className="flex items-center justify-between cursor-pointer hover:bg-gray-800/50 p-3 -m-3 rounded-lg transition-colors"
        onClick={() => setExpandido(!expandido)}
      >
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-10 h-10 bg-green-600 rounded-lg">
            <UserCheck size={20} className="text-white" />
          </div>
          <div>
            <h2 className="text-xl font-semibold text-white">Archivos del Analista</h2>
            <p className="text-gray-400 text-sm">Archivos complementarios gestionados por el analista</p>
          </div>
        </div>
        
        <div className="flex items-center gap-3">
          {!expandido && (
            <span className={`text-sm font-medium ${colorEstado}`}>
              {estadoGeneral}
            </span>
          )}
          {expandido ? (
            <ChevronDown size={20} className="text-gray-400" />
          ) : (
            <ChevronRight size={20} className="text-gray-400" />
          )}
        </div>
      </div>
      
      {/* Contenedor de archivos del analista - solo se muestra cuando está expandido */}
      {expandido && (
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
