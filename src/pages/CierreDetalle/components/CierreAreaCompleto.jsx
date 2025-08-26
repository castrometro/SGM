import React from 'react';

// Importar componentes de barras de información específicas
import CierreInfoBarContabilidad from './CierreInfoBar';
import CierreInfoBarPayroll from './CierreInfoBarPayroll';


// Importar componentes de progreso específicos por área
import CierreProgresoContabilidad from '../areas/Contabilidad/CierreProgresoContabilidad';
import CierreProgresoPayroll from '../areas/Payroll/CierreProgresoPayroll';


const CierreAreaCompleto = ({ cierre, cliente, tipoModulo, onCierreActualizado }) => {

  const renderComponentesPorArea = () => {
    switch (tipoModulo) {
      case "contabilidad":
        return {
          infoBar: (
            <CierreInfoBarContabilidad
              cierre={cierre}
              cliente={cliente}
              onCierreActualizado={onCierreActualizado}
            />
          ),
          progreso: (
            <CierreProgresoContabilidad
              cierre={cierre}
              cliente={cliente}
            />
          ),
          titulo: "Contabilidad",
          color: "blue"
        };


      case "payroll":
        return {
          infoBar: (
            <CierreInfoBarPayroll
              cierre={cierre}
              cliente={cliente}
              onCierreActualizado={onCierreActualizado}
            />
          ),
          progreso: (
            <CierreProgresoPayroll
              cierre={cierre}
              cliente={cliente}
            />
          ),
          titulo: "Payroll",
          color: "green"
        };

     

      default:
        return {
          infoBar: (
            <CierreInfoBarGenerico
              cierre={cierre}
              cliente={cliente}
              onCierreActualizado={onCierreActualizado}
              tipoModulo={tipoModulo}
            />
          ),
          progreso: (
            <div className="bg-gray-800 p-6 rounded-lg text-center">
              <h3 className="text-lg font-semibold text-white mb-2">Área no reconocida</h3>
              <p className="text-gray-300">El tipo de módulo "{tipoModulo}" no está configurado.</p>
            </div>
          ),
          titulo: tipoModulo || "Desconocido",
          color: "gray"
        };
    }
  };

  const { infoBar, progreso, titulo, color } = renderComponentesPorArea();

  const getColorClasses = (color) => {
    const colorMap = {
      blue: 'bg-blue-500',
      green: 'bg-green-500',
      purple: 'bg-purple-500',
      gray: 'bg-gray-500'
    };
    return colorMap[color] || 'bg-gray-500';
  };

  return (
    <div className="space-y-6">
      {/* Barra de información específica del área */}
      {infoBar}

      {/* Título del área con indicador visual */}
      <div className="flex items-center gap-3 mb-4">
        <div className="flex items-center gap-2">
          <div className={`w-3 h-3 rounded-full ${getColorClasses(color)}`}></div>
          <h2 className="text-xl font-bold text-white">
            {titulo}
          </h2>
        </div>
      </div>

      {/* Componente de progreso específico del área */}
      <div className="bg-gray-900 p-6 rounded-lg">
        {progreso}
      </div>
    </div>
  );
};

export default CierreAreaCompleto;
