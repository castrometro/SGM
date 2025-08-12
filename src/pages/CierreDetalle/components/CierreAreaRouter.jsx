import { Suspense } from 'react';
import CierreProgresoContabilidad from '../areas/Contabilidad/CierreProgresoContabilidad';
import CierreProgresoNomina from '../areas/Nomina/CierreProgresoNomina';
import CierreProgresoRRHH from '../areas/RRHH/CierreProgresoRRHH';

const CierreAreaRouter = ({ cierre, cliente, tipoModulo = "contabilidad" }) => {
  
  const renderComponentePorArea = () => {
    switch (tipoModulo) {
      case "contabilidad":
        return (
          <Suspense fallback={<div className="text-white text-center">Cargando componentes de contabilidad...</div>}>
            <CierreProgresoContabilidad cierre={cierre} cliente={cliente} />
          </Suspense>
        );
      
      case "nomina":
        return <CierreProgresoNomina cierre={cierre} cliente={cliente} />;
      
      case "rrhh":
        return <CierreProgresoRRHH cierre={cierre} cliente={cliente} />;
      
      default:
        return (
          <div className="bg-gray-800 p-6 rounded-lg text-center">
            <h3 className="text-lg font-semibold text-white mb-2">Área no reconocida</h3>
            <p className="text-gray-300">El tipo de módulo "{tipoModulo}" no está configurado.</p>
          </div>
        );
    }
  };

  return (
    <div className="space-y-6">
      {/* Título del área */}
      <div className="flex items-center gap-3 mb-4">
        <div className="flex items-center gap-2">
          <div className={`w-3 h-3 rounded-full ${
            tipoModulo === 'contabilidad' ? 'bg-blue-500' :
            tipoModulo === 'nomina' ? 'bg-green-500' :
            tipoModulo === 'rrhh' ? 'bg-purple-500' : 'bg-gray-500'
          }`}></div>
          <h2 className="text-xl font-bold text-white capitalize">
            {tipoModulo === 'rrhh' ? 'Recursos Humanos' : tipoModulo}
          </h2>
        </div>
        <span className="text-gray-400 text-sm">
          Periodo: {cierre?.periodo}
        </span>
      </div>

      {/* Componente específico del área */}
      {renderComponentePorArea()}
    </div>
  );
};

export default CierreAreaRouter;
