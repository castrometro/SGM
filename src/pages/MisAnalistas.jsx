import { useState, useEffect } from 'react';
import { Users, User, Building2, Calendar, AlertCircle, CheckCircle, Eye, FileText, ShieldCheck, ChevronDown, ChevronRight } from 'lucide-react';
import { obtenerMisAnalistas, obtenerClientesSupervisionados } from '../api/supervisores';

const MisAnalistas = () => {
  const [supervisorData, setSupervisorData] = useState(null);
  const [clientesSupervisionados, setClientesSupervisionados] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expandedAnalista, setExpandedAnalista] = useState(null);

  useEffect(() => {
    fetchSupervisorData();
    fetchClientesSupervisionados();
  }, []);

  const fetchSupervisorData = async () => {
    try {
      const data = await obtenerMisAnalistas();
      setSupervisorData(data);
    } catch (err) {
      setError(err.message || 'Error al cargar datos del supervisor');
    }
  };

  const fetchClientesSupervisionados = async () => {
    try {
      const data = await obtenerClientesSupervisionados();
      setClientesSupervisionados(data);
    } catch (err) {
      setError(err.message || 'Error al cargar clientes supervisados');
    } finally {
      setLoading(false);
    }
  };

  const toggleExpandAnalista = (analistaId) => {
    setExpandedAnalista(expandedAnalista === analistaId ? null : analistaId);
  };

  const handleVerClientes = (analista) => {
    // Expandir/contraer la sección de clientes del analista
    toggleExpandAnalista(analista.id);
  };

  const handleVerHistorial = (clienteId) => {
    // Navegar al historial de cierres del cliente
    window.location.href = `/menu/clientes/${clienteId}/cierres`;
  };

  const handleIrValidacion = () => {
    // Navegar a la página de validaciones
    window.location.href = '/menu/validaciones';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-64 text-white">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-400">Cargando datos del supervisor...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-900/20 border border-red-500/30 rounded-lg p-6">
        <div className="flex items-center">
          <AlertCircle className="h-6 w-6 text-red-400 mr-3" />
          <span className="text-red-300">{error}</span>
        </div>
      </div>
    );
  }

  return (
    <div className="text-white space-y-6">
      {/* Header con resumen */}
      <div className="bg-gray-800 rounded-lg border border-gray-700 p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white flex items-center">
              <Users className="h-7 w-7 text-blue-400 mr-3" />
              Mis Analistas
            </h1>
            <p className="text-gray-400 mt-1">
              Gestión y supervisión de tu equipo de analistas
            </p>
          </div>
          
          {supervisorData && (
            <div className="grid grid-cols-2 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-400">
                  {supervisorData.total_analistas}
                </div>
                <div className="text-sm text-gray-400">Analistas</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-400">
                  {supervisorData.total_clientes_supervisados}
                </div>
                <div className="text-sm text-gray-400">Clientes</div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Tabla de Analistas */}
      {supervisorData && supervisorData.analistas_supervisados && supervisorData.analistas_supervisados.length > 0 ? (
        <div className="bg-gray-800 rounded-lg border border-gray-700">
          <div className="p-6 border-b border-gray-700">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-white">
                Analistas Supervisados
              </h2>
              <button
                onClick={handleIrValidacion}
                className="flex items-center px-4 py-2 bg-yellow-600 hover:bg-yellow-700 text-white rounded-lg transition-colors"
              >
                <ShieldCheck className="h-4 w-4 mr-2" />
                Ir a Validaciones
              </button>
            </div>
          </div>
          
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-700">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Analista
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Áreas
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Clientes Asignados
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                    Acciones
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700">
                {supervisorData.analistas_supervisados.map((analista) => (
                  <>
                    <tr key={analista.id} className="hover:bg-gray-700/50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center">
                            <User className="h-5 w-5 text-white" />
                          </div>
                          <div className="ml-4">
                            <div className="text-sm font-medium text-white">
                              {analista.nombre} {analista.apellido}
                            </div>
                            <div className="text-sm text-gray-400">
                              {analista.correo_bdo}
                            </div>
                            <div className="text-xs text-gray-500">
                              {analista.cargo_bdo}
                            </div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex flex-wrap gap-1">
                          {analista.areas.map((area) => (
                            <span
                              key={area.id}
                              className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-700 text-gray-300 border border-gray-600"
                            >
                              <Building2 className="h-3 w-3 mr-1" />
                              {area.nombre}
                            </span>
                          ))}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-center">
                        <div className="text-lg font-semibold text-blue-400">
                          {analista.total_clientes}
                        </div>
                        <div className="text-xs text-gray-400">
                          cliente{analista.total_clientes !== 1 ? 's' : ''}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex space-x-2">
                          <button
                            onClick={() => handleVerClientes(analista)}
                            className="flex items-center px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors text-sm"
                            title="Ver clientes asignados"
                          >
                            {expandedAnalista === analista.id ? (
                              <ChevronDown className="h-4 w-4 mr-1" />
                            ) : (
                              <ChevronRight className="h-4 w-4 mr-1" />
                            )}
                            <Eye className="h-4 w-4 mr-1" />
                            Ver Clientes
                          </button>
                        </div>
                      </td>
                    </tr>
                    
                    {/* Fila expandible con clientes */}
                    {expandedAnalista === analista.id && analista.clientes_asignados && (
                      <tr>
                        <td colSpan="4" className="px-6 py-4 bg-gray-900/50">
                          <div className="space-y-3">
                            <h4 className="text-sm font-medium text-gray-300 flex items-center">
                              <User className="h-4 w-4 mr-2" />
                              Clientes de {analista.nombre} {analista.apellido}
                            </h4>
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                              {analista.clientes_asignados.map((cliente) => (
                                <div
                                  key={cliente.id}
                                  className="bg-gray-800 border border-gray-600 rounded-lg p-3 hover:border-gray-500 transition-colors"
                                >
                                  <div className="flex items-start justify-between">
                                    <div className="flex-1">
                                      <div className="font-medium text-white text-sm">
                                        {cliente.nombre}
                                      </div>
                                      <div className="text-gray-400 text-xs">{cliente.rut}</div>
                                    </div>
                                    <button
                                      onClick={() => handleVerHistorial(cliente.id)}
                                      className="flex items-center px-2 py-1 bg-green-600 hover:bg-green-700 text-white rounded transition-colors text-xs"
                                      title="Ver historial de cierres"
                                    >
                                      <FileText className="h-3 w-3 mr-1" />
                                      Historial
                                    </button>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}
                  </>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        supervisorData && (
          <div className="bg-gray-800 rounded-lg border border-gray-700 p-6 text-center">
            <Users className="h-12 w-12 text-gray-500 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-white mb-2">
              No tienes analistas asignados
            </h3>
            <p className="text-gray-400">
              Aún no se te han asignado analistas para supervisar.
            </p>
          </div>
        )
      )}

      {/* Resumen adicional de todos los clientes supervisados */}
      {clientesSupervisionados.length > 0 && (
        <div className="bg-gray-800 rounded-lg border border-gray-700">
          <div className="p-6 border-b border-gray-700">
            <h2 className="text-lg font-semibold text-white">
              Resumen General de Clientes Supervisados
            </h2>
            <p className="text-gray-400 text-sm mt-1">
              Vista consolidada de todos los clientes bajo tu supervisión
            </p>
          </div>
          
          <div className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {clientesSupervisionados.map((item) => (
                <div
                  key={`${item.cliente.id}-${item.analista.id}`}
                  className="border border-gray-600 rounded-lg p-3 hover:border-gray-500 transition-colors bg-gray-700"
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1">
                      <h3 className="font-medium text-white text-sm">
                        {item.cliente.nombre}
                      </h3>
                      <p className="text-xs text-gray-400">{item.cliente.rut}</p>
                    </div>
                    
                    <CheckCircle className="h-4 w-4 text-green-400 flex-shrink-0" />
                  </div>
                  
                  <div className="pt-2 border-t border-gray-600">
                    <div className="flex items-center text-xs text-gray-300 mb-1">
                      <User className="h-3 w-3 mr-1" />
                      <span className="truncate">{item.analista.nombre} {item.analista.apellido}</span>
                    </div>
                    <div className="flex items-center text-xs text-gray-500">
                      <Calendar className="h-3 w-3 mr-1" />
                      {new Date(item.fecha_asignacion).toLocaleDateString()}
                    </div>
                  </div>
                  
                  <div className="mt-2 pt-2 border-t border-gray-600">
                    <button
                      onClick={() => handleVerHistorial(item.cliente.id)}
                      className="w-full flex items-center justify-center px-2 py-1 bg-green-600 hover:bg-green-700 text-white rounded transition-colors text-xs"
                    >
                      <FileText className="h-3 w-3 mr-1" />
                      Ver Historial
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MisAnalistas;
