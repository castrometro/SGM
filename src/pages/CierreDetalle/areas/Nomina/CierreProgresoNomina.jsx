import { useState, useEffect } from "react";

const CierreProgresoNomina = ({ cierre, cliente }) => {
  const [consolidacionDatos, setConsolidacionDatos] = useState(false);
  const [verificacionIncidencias, setVerificacionIncidencias] = useState(false);
  const [generacionReportes, setGeneracionReportes] = useState(false);

  useEffect(() => {
    const fetchEstadosNomina = async () => {
      try {
        // TODO: Implementar APIs específicas de nómina
        console.log('Cargando estados de nómina para cierre:', cierre.id);
        
        // Simulación de lógica de nómina
        setConsolidacionDatos(cierre.estado !== 'pendiente');
        setVerificacionIncidencias(['datos_consolidados', 'con_incidencias', 'sin_incidencias'].includes(cierre.estado));
        setGeneracionReportes(cierre.estado === 'finalizado');
      } catch (error) {
        console.error('Error al cargar estados de nómina:', error);
      }
    };

    if (cierre && cliente) fetchEstadosNomina();
  }, [cierre, cliente]);

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {/* Paso 1: Consolidación de Datos */}
      <div className={`bg-gray-800 p-6 rounded-lg border-2 ${consolidacionDatos ? 'border-green-500' : 'border-gray-600'}`}>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white">Consolidación de Datos</h3>
          <div className={`w-6 h-6 rounded-full ${consolidacionDatos ? 'bg-green-500' : 'bg-gray-500'}`}>
            {consolidacionDatos && (
              <svg className="w-4 h-4 text-white m-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
              </svg>
            )}
          </div>
        </div>
        <p className="text-gray-300 text-sm mb-4">
          Consolidar datos de empleados, sueldos y movimientos del período
        </p>
        <button 
          className={`w-full py-2 px-4 rounded ${
            consolidacionDatos 
              ? 'bg-green-600 text-white' 
              : 'bg-blue-600 hover:bg-blue-700 text-white'
          }`}
          disabled={consolidacionDatos}
        >
          {consolidacionDatos ? 'Completado' : 'Iniciar Consolidación'}
        </button>
      </div>

      {/* Paso 2: Verificación de Incidencias */}
      <div className={`bg-gray-800 p-6 rounded-lg border-2 ${verificacionIncidencias ? 'border-green-500' : 'border-gray-600'}`}>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white">Verificación de Incidencias</h3>
          <div className={`w-6 h-6 rounded-full ${verificacionIncidencias ? 'bg-green-500' : 'bg-gray-500'}`}>
            {verificacionIncidencias && (
              <svg className="w-4 h-4 text-white m-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
              </svg>
            )}
          </div>
        </div>
        <p className="text-gray-300 text-sm mb-4">
          Revisar y resolver incidencias en los datos de nómina
        </p>
        <button 
          className={`w-full py-2 px-4 rounded ${
            verificacionIncidencias 
              ? 'bg-green-600 text-white' 
              : consolidacionDatos 
                ? 'bg-blue-600 hover:bg-blue-700 text-white'
                : 'bg-gray-600 text-gray-400 cursor-not-allowed'
          }`}
          disabled={!consolidacionDatos || verificacionIncidencias}
        >
          {verificacionIncidencias ? 'Completado' : 'Verificar Incidencias'}
        </button>
      </div>

      {/* Paso 3: Generación de Reportes */}
      <div className={`bg-gray-800 p-6 rounded-lg border-2 ${generacionReportes ? 'border-green-500' : 'border-gray-600'}`}>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white">Generación de Reportes</h3>
          <div className={`w-6 h-6 rounded-full ${generacionReportes ? 'bg-green-500' : 'bg-gray-500'}`}>
            {generacionReportes && (
              <svg className="w-4 h-4 text-white m-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
              </svg>
            )}
          </div>
        </div>
        <p className="text-gray-300 text-sm mb-4">
          Generar libro de remuneraciones y reportes finales
        </p>
        <button 
          className={`w-full py-2 px-4 rounded ${
            generacionReportes 
              ? 'bg-green-600 text-white' 
              : verificacionIncidencias 
                ? 'bg-blue-600 hover:bg-blue-700 text-white'
                : 'bg-gray-600 text-gray-400 cursor-not-allowed'
          }`}
          disabled={!verificacionIncidencias || generacionReportes}
        >
          {generacionReportes ? 'Completado' : 'Generar Reportes'}
        </button>
      </div>
    </div>
  );
};

export default CierreProgresoNomina;
