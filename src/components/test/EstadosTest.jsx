/**
 * Archivo de prueba para verificar que todos los estados se muestran correctamente
 * 
 * Puedes usar este componente temporalmente para verificar que todos los estados
 * del backend tienen su correspondiente mapeo en el frontend.
 */

import EstadoBadge from '../components/EstadoBadge';

const EstadosTest = () => {
  // Estados del modelo Django CierreContabilidad
  const estadosBackend = [
    'pendiente',
    'procesando', 
    'clasificacion',
    'incidencias',
    'sin_incidencias',
    'generando_reportes',
    'en_revision',
    'rechazado',
    'aprobado',
    'finalizado',
    'completo'
  ];

  return (
    <div className="p-8 bg-gray-100 min-h-screen">
      <h1 className="text-2xl font-bold mb-6">Test de Estados - CierreContabilidad</h1>
      
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-lg font-semibold mb-4">Estados disponibles:</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {estadosBackend.map(estado => (
            <div key={estado} className="flex items-center justify-between p-3 border rounded">
              <div className="flex flex-col">
                <span className="text-sm text-gray-600">Backend:</span>
                <code className="text-xs bg-gray-100 px-1 rounded">{estado}</code>
              </div>
              <div className="flex flex-col items-end">
                <span className="text-sm text-gray-600 mb-1">Frontend:</span>
                <EstadoBadge estado={estado} size="sm" />
              </div>
            </div>
          ))}
        </div>
        
        <div className="mt-8">
          <h3 className="text-md font-semibold mb-3">Ejemplo: Sin Incidencias</h3>
          <div className="flex items-center gap-4 p-4 bg-gray-50 rounded">
            <span>Estado sin_incidencias se muestra como:</span>
            <EstadoBadge estado="sin_incidencias" size="md" />
          </div>
        </div>

        <div className="mt-4">
          <h3 className="text-md font-semibold mb-3">Ejemplo: Finalizado</h3>
          <div className="flex items-center gap-4 p-4 bg-gray-50 rounded">
            <span>Estado finalizado se muestra como:</span>
            <EstadoBadge estado="finalizado" size="md" />
          </div>
        </div>
      </div>
    </div>
  );
};

export default EstadosTest;
