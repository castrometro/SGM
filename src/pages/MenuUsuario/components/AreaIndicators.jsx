import { DollarSign, Calculator, Users } from "lucide-react";

const AreaIndicators = ({ usuario }) => {
  const areas = usuario?.areas || [];
  
  if (areas.length === 0) {
    return null;
  }

  const getAreaIcon = (areaName) => {
    switch (areaName) {
      case 'Contabilidad':
        return <Calculator className="w-4 h-4" />;
      case 'Payroll':
        return <DollarSign className="w-4 h-4" />;
      default:
        return <Users className="w-4 h-4" />;
    }
  };

  const getAreaColor = (areaName) => {
    switch (areaName) {
      case 'Contabilidad':
        return 'bg-blue-500';
      case 'Payroll':
        return 'bg-green-500';
      default:
        return 'bg-gray-500';
    }
  };

  return (
    <div className="flex flex-wrap gap-2 mb-6">
      <span className="text-sm text-gray-300 mr-2">Áreas activas:</span>
      {areas.map((area, index) => (
        <div
          key={index}
          className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-white text-sm font-medium ${getAreaColor(area.nombre)}`}
        >
          {getAreaIcon(area.nombre)}
          {area.nombre}
        </div>
      ))}
    </div>
  );
};

export default AreaIndicators;
