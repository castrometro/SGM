import { useState, useEffect } from 'react';
import { generarReporte, obtenerHistorialReportes, descargarReporte } from '../../api/gerente';

const SistemaReportes = ({ areas }) => {
  const [tipoReporte, setTipoReporte] = useState('productividad');
  const [parametros, setParametros] = useState({
    fecha_inicio: new Date().toISOString().split('T')[0],
    fecha_fin: new Date().toISOString().split('T')[0],
    area: '',
    formato: 'excel'
  });
  const [generando, setGenerando] = useState(false);
  const [historial, setHistorial] = useState([]);

  useEffect(() => {
    cargarHistorial();
  }, []);

  const cargarHistorial = async () => {
    try {
      const data = await obtenerHistorialReportes();
      setHistorial(data);
    } catch (error) {
      console.error('Error cargando historial:', error);
    }
  };

  const manejarGeneracion = async (e) => {
    e.preventDefault();
    setGenerando(true);
    
    try {
      const reporte = await generarReporte({
        tipo: tipoReporte,
        ...parametros
      });
      
      // Descargar archivo
      const link = document.createElement('a');
      link.href = reporte.url_descarga;
      link.download = reporte.nombre_archivo;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      await cargarHistorial(); // Actualizar historial
    } catch (error) {
      console.error('Error generando reporte:', error);
    }
    
    setGenerando(false);
  };

  const tiposReporte = [
    { value: 'productividad', label: 'Productividad por Analista', descripcion: 'Cierres completados, tiempo promedio, eficiencia' },
    { value: 'carga_trabajo', label: 'Carga de Trabajo', descripcion: 'Distribución de clientes por analista y área' },
    { value: 'sla_cumplimiento', label: 'Cumplimiento de SLA', descripcion: 'Tiempos de cierre vs objetivos establecidos' },
    { value: 'clientes_problematicos', label: 'Clientes Problemáticos', descripcion: 'Clientes con retrasos frecuentes o incidencias' },
    { value: 'tendencias', label: 'Análisis de Tendencias', descripcion: 'Evolución de métricas en el tiempo' },
    { value: 'rentabilidad', label: 'Análisis de Rentabilidad', descripcion: 'Tiempo invertido vs valor de servicios por cliente' }
  ];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-white">Sistema de Reportes</h2>
        <div className="text-sm text-gray-400">
          Genera reportes personalizados para análisis ejecutivo
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Generador de Reportes */}
        <div className="bg-gray-800 p-6 rounded-lg">
          <h3 className="text-xl font-semibold text-white mb-4">Generar Nuevo Reporte</h3>
          
          <form onSubmit={manejarGeneracion} className="space-y-4">
            <div>
              <label className="block text-white text-sm font-semibold mb-2">
                Tipo de Reporte
              </label>
              <select
                value={tipoReporte}
                onChange={(e) => setTipoReporte(e.target.value)}
                className="w-full p-2 rounded bg-gray-700 text-white"
              >
                {tiposReporte.map(tipo => (
                  <option key={tipo.value} value={tipo.value}>
                    {tipo.label}
                  </option>
                ))}
              </select>
              <p className="text-xs text-gray-400 mt-1">
                {tiposReporte.find(t => t.value === tipoReporte)?.descripcion}
              </p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-white text-sm font-semibold mb-2">
                  Fecha Inicio
                </label>
                <input
                  type="date"
                  value={parametros.fecha_inicio}
                  onChange={(e) => setParametros({...parametros, fecha_inicio: e.target.value})}
                  className="w-full p-2 rounded bg-gray-700 text-white"
                  required
                />
              </div>
              <div>
                <label className="block text-white text-sm font-semibold mb-2">
                  Fecha Fin
                </label>
                <input
                  type="date"
                  value={parametros.fecha_fin}
                  onChange={(e) => setParametros({...parametros, fecha_fin: e.target.value})}
                  className="w-full p-2 rounded bg-gray-700 text-white"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-white text-sm font-semibold mb-2">
                Área (Opcional)
              </label>
              <select
                value={parametros.area}
                onChange={(e) => setParametros({...parametros, area: e.target.value})}
                className="w-full p-2 rounded bg-gray-700 text-white"
              >
                <option value="">Todas las áreas</option>
                {areas.map(area => (
                  <option key={area.id} value={area.id}>
                    {area.nombre}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-white text-sm font-semibold mb-2">
                Formato de Salida
              </label>
              <select
                value={parametros.formato}
                onChange={(e) => setParametros({...parametros, formato: e.target.value})}
                className="w-full p-2 rounded bg-gray-700 text-white"
              >
                <option value="excel">Excel (.xlsx)</option>
                <option value="pdf">PDF</option>
                <option value="csv">CSV</option>
              </select>
            </div>

            <button
              type="submit"
              disabled={generando}
              className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white py-3 rounded-lg font-semibold"
            >
              {generando ? 'Generando...' : '📊 Generar Reporte'}
            </button>
          </form>
        </div>

        {/* Reportes Rápidos */}
        <div className="bg-gray-800 p-6 rounded-lg">
          <h3 className="text-xl font-semibold text-white mb-4">Reportes Rápidos</h3>
          
          <div className="space-y-3">
            <button
              onClick={() => {
                setTipoReporte('productividad');
                setParametros({
                  ...parametros,
                  fecha_inicio: new Date(Date.now() - 30*24*60*60*1000).toISOString().split('T')[0],
                  fecha_fin: new Date().toISOString().split('T')[0]
                });
              }}
              className="w-full bg-green-600 hover:bg-green-700 text-white p-3 rounded text-left"
            >
              <div className="font-semibold">📈 Productividad Últimos 30 días</div>
              <div className="text-sm opacity-75">Resumen ejecutivo mensual</div>
            </button>

            <button
              onClick={() => {
                setTipoReporte('carga_trabajo');
                setParametros({
                  ...parametros,
                  fecha_inicio: new Date().toISOString().split('T')[0],
                  fecha_fin: new Date().toISOString().split('T')[0]
                });
              }}
              className="w-full bg-yellow-600 hover:bg-yellow-700 text-white p-3 rounded text-left"
            >
              <div className="font-semibold">⚖️ Carga Actual por Analista</div>
              <div className="text-sm opacity-75">Estado actual de asignaciones</div>
            </button>

            <button
              onClick={() => {
                setTipoReporte('clientes_problematicos');
                setParametros({
                  ...parametros,
                  fecha_inicio: new Date(Date.now() - 90*24*60*60*1000).toISOString().split('T')[0],
                  fecha_fin: new Date().toISOString().split('T')[0]
                });
              }}
              className="w-full bg-red-600 hover:bg-red-700 text-white p-3 rounded text-left"
            >
              <div className="font-semibold">🚨 Clientes de Atención</div>
              <div className="text-sm opacity-75">Últimos 90 días</div>
            </button>
          </div>
        </div>
      </div>

      {/* Historial de Reportes */}
      <div className="bg-gray-800 p-6 rounded-lg">
        <h3 className="text-xl font-semibold text-white mb-4">Historial de Reportes</h3>
        
        {historial.length === 0 ? (
          <p className="text-gray-400 text-center py-8">
            No hay reportes generados aún
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-700">
                <tr>
                  <th className="p-3 text-left text-white">Fecha</th>
                  <th className="p-3 text-left text-white">Tipo</th>
                  <th className="p-3 text-left text-white">Período</th>
                  <th className="p-3 text-left text-white">Área</th>
                  <th className="p-3 text-center text-white">Formato</th>
                  <th className="p-3 text-center text-white">Estado</th>
                  <th className="p-3 text-center text-white">Acciones</th>
                </tr>
              </thead>
              <tbody>
                {historial.map((reporte) => (
                  <tr key={reporte.id} className="border-b border-gray-700">
                    <td className="p-3 text-white">
                      {new Date(reporte.fecha_generacion).toLocaleDateString()}
                    </td>
                    <td className="p-3 text-white">
                      {tiposReporte.find(t => t.value === reporte.tipo)?.label || reporte.tipo}
                    </td>
                    <td className="p-3 text-white">
                      {reporte.fecha_inicio} / {reporte.fecha_fin}
                    </td>
                    <td className="p-3 text-white">
                      {reporte.area || 'Todas'}
                    </td>
                    <td className="p-3 text-center text-white">
                      {reporte.formato.toUpperCase()}
                    </td>
                    <td className="p-3 text-center">
                      <span className={`px-2 py-1 rounded text-xs ${
                        reporte.estado === 'completado' 
                          ? 'bg-green-600 text-white'
                          : reporte.estado === 'procesando'
                            ? 'bg-yellow-600 text-white'
                            : 'bg-red-600 text-white'
                      }`}>
                        {reporte.estado}
                      </span>
                    </td>
                    <td className="p-3 text-center">
                      {reporte.estado === 'completado' && (
                        <a
                          href={reporte.url_descarga}
                          className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-sm"
                          download
                        >
                          Descargar
                        </a>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default SistemaReportes;
