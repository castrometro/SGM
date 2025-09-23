import React from 'react';

const CierreProgresoNomina_v2 = ({ cierre, cliente, onCierreActualizado, className }) => {
  // Validación básica de props
  if (!cierre || !cliente) {
    return (
      <div className="text-white text-center py-6">
        Cargando datos de cierre de nómina...
      </div>
    );
  }

  return (
    <div className={`space-y-6 ${className || ''}`}>
      {/* Header temporal para debug */}
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <h2 className="text-xl font-semibold text-white mb-4">
          🚧 Cierre Progreso V2 - En Construcción
        </h2>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-gray-400">Cliente:</span>
            <span className="text-white ml-2">{cliente.nombre}</span>
          </div>
          <div>
            <span className="text-gray-400">Estado:</span>
            <span className="text-blue-400 ml-2">{cierre.estado}</span>
          </div>
          <div>
            <span className="text-gray-400">Período:</span>
            <span className="text-white ml-2">{cierre.periodo}</span>
          </div>
          <div>
            <span className="text-gray-400">ID:</span>
            <span className="text-gray-300 ml-2">{cierre.id}</span>
          </div>
        </div>
      </div>

      {/* Placeholder para futuras secciones */}
      <div className="bg-gray-900/50 rounded-lg p-8 border border-gray-600 border-dashed text-center">
        <div className="text-gray-400 text-lg mb-2">
          🎯 Próximas implementaciones:
        </div>
        <ul className="text-gray-500 text-sm space-y-1">
          <li>• Lógica de mostrar/ocultar secciones según estado</li>
          <li>• Dashboard de incidencias para estados avanzados</li>
          <li>• Secciones básicas para estados iniciales</li>
        </ul>
      </div>
    </div>
  );
};

export default CierreProgresoNomina_v2;