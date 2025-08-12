import { useState, useEffect } from "react";

const CierreProgresoRRHH = ({ cierre, cliente }) => {
  const [indicadoresPersonal, setIndicadoresPersonal] = useState(false);
  const [reportesRRHH, setReportesRRHH] = useState(false);

  useEffect(() => {
    const fetchEstadosRRHH = async () => {
      try {
        // TODO: Implementar APIs específicas de RRHH
        console.log('Cargando estados de RRHH para cierre:', cierre.id);
        
        // Simulación de lógica de RRHH
        setIndicadoresPersonal(cierre.estado !== 'pendiente');
        setReportesRRHH(cierre.estado === 'finalizado');
      } catch (error) {
        console.error('Error al cargar estados de RRHH:', error);
      }
    };

    if (cierre && cliente) fetchEstadosRRHH();
  }, [cierre, cliente]);

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {/* Paso 1: Indicadores de Personal */}
      <div className={`bg-gray-800 p-6 rounded-lg border-2 ${indicadoresPersonal ? 'border-green-500' : 'border-gray-600'}`}>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white">Indicadores de Personal</h3>
          <div className={`w-6 h-6 rounded-full ${indicadoresPersonal ? 'bg-green-500' : 'bg-gray-500'}`}>
            {indicadoresPersonal && (
              <svg className="w-4 h-4 text-white m-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
              </svg>
            )}
          </div>
        </div>
        <p className="text-gray-300 text-sm mb-4">
          Calcular indicadores de rotación, ausentismo y productividad
        </p>
        <button 
          className={`w-full py-2 px-4 rounded ${
            indicadoresPersonal 
              ? 'bg-green-600 text-white' 
              : 'bg-blue-600 hover:bg-blue-700 text-white'
          }`}
          disabled={indicadoresPersonal}
        >
          {indicadoresPersonal ? 'Completado' : 'Calcular Indicadores'}
        </button>
      </div>

      {/* Paso 2: Reportes de RRHH */}
      <div className={`bg-gray-800 p-6 rounded-lg border-2 ${reportesRRHH ? 'border-green-500' : 'border-gray-600'}`}>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white">Reportes de RRHH</h3>
          <div className={`w-6 h-6 rounded-full ${reportesRRHH ? 'bg-green-500' : 'bg-gray-500'}`}>
            {reportesRRHH && (
              <svg className="w-4 h-4 text-white m-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
              </svg>
            )}
          </div>
        </div>
        <p className="text-gray-300 text-sm mb-4">
          Generar reportes de gestión humana y análisis organizacional
        </p>
        <button 
          className={`w-full py-2 px-4 rounded ${
            reportesRRHH 
              ? 'bg-green-600 text-white' 
              : indicadoresPersonal 
                ? 'bg-blue-600 hover:bg-blue-700 text-white'
                : 'bg-gray-600 text-gray-400 cursor-not-allowed'
          }`}
          disabled={!indicadoresPersonal || reportesRRHH}
        >
          {reportesRRHH ? 'Completado' : 'Generar Reportes'}
        </button>
      </div>
    </div>
  );
};

export default CierreProgresoRRHH;
