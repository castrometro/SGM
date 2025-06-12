import { Calculator, UserCheck } from "lucide-react";

const AreaIndicator = ({ areas, size = "sm", className = "", showLabel = false }) => {
  // Validar que areas sea un array válido
  if (!areas || !Array.isArray(areas) || areas.length === 0) {
    return null;
  }
  
  // Verificar que cada área tenga la propiedad nombre
  const areaNames = areas.map(area => area?.nombre).filter(Boolean);
  
  // Si no hay nombres válidos, no mostrar nada
  if (areaNames.length === 0) {
    return null;
  }
  
  const tieneContabilidad = areaNames.includes("Contabilidad");
  const tieneNomina = areaNames.includes("Nomina");
  
  const sizeClasses = {
    xs: "text-xs px-2 py-0.5",
    sm: "text-xs px-2 py-1",
    md: "text-sm px-3 py-1.5",
    lg: "text-sm px-4 py-2"
  };
  
  const iconSizes = {
    xs: "w-3 h-3",
    sm: "w-3 h-3", 
    md: "w-4 h-4",
    lg: "w-5 h-5"
  };
  
  const getAreaDescription = () => {
    if (tieneContabilidad && tieneNomina) {
      return "Gestión integral de contabilidad y nómina";
    } else if (tieneContabilidad) {
      return "Gestión de contabilidad y cierres contables";
    } else if (tieneNomina) {
      return "Gestión de nómina y remuneraciones";
    }
    return "";
  };
  
  return (
    <div 
      className={`flex items-center gap-2 ${className}`}
      title={getAreaDescription()}
    >
      {showLabel && (
        <span className="text-xs text-gray-400 whitespace-nowrap">
          {tieneContabilidad && tieneNomina ? "Áreas:" : "Área:"}
        </span>
      )}
      <div className="flex items-center gap-1.5">
        {tieneContabilidad && (
          <div 
            className={`flex items-center gap-1 bg-blue-600/20 text-blue-300 rounded-full border border-blue-500/30 transition-all duration-200 hover:bg-blue-600/30 hover:border-blue-400/50 cursor-help ${sizeClasses[size]}`}
            title="Área de Contabilidad - Gestión de cierres contables y estados financieros"
          >
            <Calculator className={iconSizes[size]} />
            <span className="whitespace-nowrap">Contabilidad</span>
          </div>
        )}
        {tieneNomina && (
          <div 
            className={`flex items-center gap-1 bg-purple-600/20 text-purple-300 rounded-full border border-purple-500/30 transition-all duration-200 hover:bg-purple-600/30 hover:border-purple-400/50 cursor-help ${sizeClasses[size]}`}
            title="Área de Nómina - Gestión de remuneraciones y procesamiento de nóminas"
          >
            <UserCheck className={iconSizes[size]} />
            <span className="whitespace-nowrap">Nómina</span>
          </div>
        )}
      </div>
    </div>
  );
};

export default AreaIndicator;
