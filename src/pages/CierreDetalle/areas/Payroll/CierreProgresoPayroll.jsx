import React from "react";

const CierreProgresoPayroll = ({ cierre, cliente }) => {
  return (
    <div className="space-y-6">
      {/* Card principal de información */}
      <div className="bg-gray-800 p-6 rounded-lg shadow-lg">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-bold text-white">Estado del Cierre Payroll</h3>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-green-500"></div>
            <span className="text-sm text-gray-300 capitalize">{cierre?.estado || 'Pendiente'}</span>
          </div>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-gray-700 p-4 rounded">
            <h4 className="text-sm text-gray-400 mb-1">Período</h4>
            <p className="text-lg font-semibold text-white">{cierre?.periodo || '—'}</p>
          </div>
          
          <div className="bg-gray-700 p-4 rounded">
            <h4 className="text-sm text-gray-400 mb-1">Total Empleados</h4>
            <p className="text-lg font-semibold text-white">{cierre?.total_empleados || 0}</p>
          </div>
          
          <div className="bg-gray-700 p-4 rounded">
            <h4 className="text-sm text-gray-400 mb-1">Monto Total</h4>
            <p className="text-lg font-semibold text-white">
              ${cierre?.monto_total ? Number(cierre.monto_total).toLocaleString() : 0}
            </p>
          </div>
        </div>
      </div>

      {/* Barra de progreso */}
      <div className="bg-gray-800 p-6 rounded-lg shadow-lg">
        <h3 className="text-lg font-bold text-white mb-4">Progreso del Procesamiento</h3>
        
        <div className="relative">
          <div className="flex justify-between text-xs text-gray-400 mb-2">
            <span>Pendiente</span>
            <span>Procesando</span>
            <span>Completado</span>
          </div>
          
          <div className="w-full bg-gray-700 rounded-full h-2">
            <div 
              className="bg-green-500 h-2 rounded-full transition-all duration-300"
              style={{ width: `${getProgressPercentage(cierre?.estado)}%` }}
            ></div>
          </div>
          
          <div className="mt-2 text-sm text-gray-300 text-center">
            {getProgressPercentage(cierre?.estado)}% completado
          </div>
        </div>
      </div>

      {/* Acciones disponibles */}
      <div className="bg-gray-800 p-6 rounded-lg shadow-lg">
        <h3 className="text-lg font-bold text-white mb-4">Acciones Disponibles</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <button className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded transition-colors">
            Ver Empleados
          </button>
          
          <button className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded transition-colors">
            Generar Reporte
          </button>
          
          <button className="bg-yellow-600 hover:bg-yellow-700 text-white px-4 py-2 rounded transition-colors">
            Exportar Datos
          </button>
          
          <button className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded transition-colors">
            Ver Logs
          </button>
        </div>
      </div>

      {/* Estado temporal mientras desarrollamos */}
      <div className="bg-blue-900 p-4 rounded-lg border border-blue-700">
        <div className="flex items-center gap-2 mb-2">
          <svg className="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
          </svg>
          <span className="text-blue-400 font-semibold">En Desarrollo</span>
        </div>
        <p className="text-blue-200 text-sm">
          Esta es una vista inicial para cierres de payroll. Las funcionalidades específicas 
          se desarrollarán según los requerimientos del área.
        </p>
      </div>
    </div>
  );
};

// Helper function para calcular el porcentaje de progreso
const getProgressPercentage = (estado) => {
  const estadosProgreso = {
    'pendiente': 10,
    'cargando_archivos': 20,
    'mapeando_columnas': 30,
    'comparando_archivos': 40,
    'archivos_validados': 50,
    'consolidando': 60,
    'datos_consolidados': 70,
    'analizando_variaciones': 80,
    'revision_analista': 85,
    'revision_supervisor': 90,
    'aprobado': 95,
    'finalizado': 100,
    'error': 0
  };
  
  return estadosProgreso[estado] || 10;
};

export default CierreProgresoPayroll;
