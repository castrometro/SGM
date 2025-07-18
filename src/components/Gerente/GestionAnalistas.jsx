import { useEffect, useState } from "react";
import { 
  Users, 
  UserPlus, 
  Building2, 
  Target, 
  BarChart3,
  Edit,
  Trash2,
  Eye,
  Search,
  Filter,
  Download,
  RefreshCw,
  UserCheck
} from "lucide-react";
import { 
  obtenerAnalistasDetallado, 
  obtenerClientesDisponibles,
  obtenerClientesAsignados,
  asignarClienteAnalista,
  removerAsignacion,
  obtenerEstadisticasAnalista
} from "../../api/analistas";
import { obtenerSupervisoresDisponibles, asignarSupervisor } from "../../api/supervisores";
import AreaIndicator from "../AreaIndicator";

const AnalistaCard = ({ analista, onViewDetails, onEditAssignments, onAssignSupervisor }) => (
  <div className="bg-gray-800 p-6 rounded-lg border border-gray-700 hover:border-gray-600 transition-colors">
    <div className="flex items-center justify-between mb-4">
      <div className="flex items-center">
        <div className="w-12 h-12 bg-blue-600 rounded-full flex items-center justify-center">
          <Users className="w-6 h-6 text-white" />
        </div>
        <div className="ml-4">
          <h3 className="font-semibold text-white">{analista.nombre} {analista.apellido}</h3>
          <p className="text-gray-400 text-sm">{analista.correo_bdo}</p>
          {analista.supervisor_nombre && (
            <p className="text-green-400 text-xs mt-1">
              Supervisor: {analista.supervisor_nombre}
            </p>
          )}
        </div>
      </div>
      <div className="flex space-x-2">
        <button
          onClick={() => onViewDetails(analista)}
          className="p-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
          title="Ver detalles"
        >
          <Eye className="w-4 h-4" />
        </button>
        <button
          onClick={() => onAssignSupervisor(analista)}
          className="p-2 bg-purple-600 hover:bg-purple-700 rounded-lg transition-colors"
          title="Asignar supervisor"
        >
          <UserCheck className="w-4 h-4" />
        </button>
        <button
          onClick={() => onEditAssignments(analista)}
          className="p-2 bg-green-600 hover:bg-green-700 rounded-lg transition-colors"
          title="Editar asignaciones"
        >
          <Edit className="w-4 h-4" />
        </button>
      </div>
    </div>
    
    <div className="grid grid-cols-3 gap-4">
      <div className="text-center">
        <p className="text-2xl font-bold text-blue-400">{analista.clientes_asignados}</p>
        <p className="text-gray-400 text-sm">Clientes</p>
      </div>
      <div className="text-center">
        <div 
          className="text-2xl font-bold text-green-400 cursor-help"
          title={`Cierres completados: ${analista.cierres_completados}
Contabilidad: ${analista.cierres_contabilidad || 0} total
Nómina: ${analista.cierres_nomina || 0} total
Cálculo: Estados 'aprobado'+'completo'+'finalizado' (Conta) + Estado 'completado' (Nómina)`}
          onClick={() => {
            const debugInfo = `
=== DETALLE CIERRES: ${analista.nombre} ${analista.apellido} ===

CIERRES COMPLETADOS: ${analista.cierres_completados}

DESGLOSE POR ÁREA:
• Contabilidad Total: ${analista.cierres_contabilidad || 0} cierres
• Nómina Total: ${analista.cierres_nomina || 0} cierres

LÓGICA DE CÁLCULO:
- Contabilidad: Solo estados 'aprobado' + 'completo' + 'finalizado'
- Nómina: Solo estado 'completado'

OTROS CAMPOS:
- Clientes asignados: ${analista.clientes_asignados}
- Eficiencia: ${analista.eficiencia}%
- Carga trabajo: ${analista.carga_trabajo}%

Para ver estadísticas detalladas por estado, 
haz clic en "Ver detalles" del analista.
=======================================`;
            alert(debugInfo);
          }}
        >
          {analista.cierres_completados}
        </div>
        <p className="text-gray-400 text-sm">Cierres</p>
        {/* Indicador visual del desglose */}
        <div className="text-xs text-gray-500 mt-1">
          C:{analista.cierres_contabilidad || 0} | N:{analista.cierres_nomina || 0}
        </div>
      </div>
      <div className="text-center">
        <p className="text-2xl font-bold text-yellow-400">{analista.eficiencia}%</p>
        <p className="text-gray-400 text-sm">Eficiencia</p>
      </div>
    </div>

    <div className="mt-4">
      <div className="flex items-center justify-between text-sm">
        <span className="text-gray-400">Carga de trabajo</span>
        <span className="text-white">{analista.carga_trabajo}%</span>
      </div>
      <div className="w-full bg-gray-700 rounded-full h-2 mt-1">
        <div 
          className={`h-2 rounded-full ${
            analista.carga_trabajo > 80 ? 'bg-red-500' : 
            analista.carga_trabajo > 60 ? 'bg-yellow-500' : 'bg-green-500'
          }`}
          style={{ width: `${analista.carga_trabajo}%` }}
        ></div>
      </div>
    </div>

    {/* Indicadores de área del analista */}
    {analista.areas && analista.areas.length > 0 && (
      <div className="mt-4">
        <p className="text-gray-400 text-sm mb-2">Áreas de especialización:</p>
        <AreaIndicator areas={analista.areas} size="sm" />
      </div>
    )}
  </div>
);

const AsignacionModal = ({ analista, isOpen, onClose, onSave }) => {
  const [clientesDisponibles, setClientesDisponibles] = useState([]);
  const [clientesAsignados, setClientesAsignados] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [operationLoading, setOperationLoading] = useState(null); // Para mostrar loading en botones específicos

  useEffect(() => {
    if (isOpen && analista) {
      cargarDatos();
    }
  }, [isOpen, analista]);

  const cargarDatos = async () => {
    try {
      setLoading(true);
      setError(null);
      
      console.log('🔍 Cargando datos para analista:', analista.id);
      
      const [disponibles, asignados] = await Promise.all([
        obtenerClientesDisponibles(analista.id, true), // Force bypass
        obtenerClientesAsignados(analista.id)
      ]);
      
      console.log('✅ Clientes disponibles:', disponibles);
      console.log('✅ Clientes asignados:', asignados);
      
      setClientesDisponibles(disponibles || []);
      setClientesAsignados(asignados || []);
    } catch (error) {
      console.error("Error al cargar datos:", error);
      setError("Error al cargar datos de asignaciones");
      setClientesDisponibles([]);
      setClientesAsignados([]);
    } finally {
      setLoading(false);
    }
  };

  const handleAsignar = async (clienteId) => {
    try {
      setOperationLoading(`asignar-${clienteId}`);
      await asignarClienteAnalista(analista.id, clienteId);
      await cargarDatos();
      if (onSave) onSave(); // Refrescar la lista principal
    } catch (error) {
      console.error("Error al asignar cliente:", error);
      setError("Error al asignar cliente");
    } finally {
      setOperationLoading(null);
    }
  };

  const handleRemover = async (clienteId) => {
    try {
      setOperationLoading(`remover-${clienteId}`);
      await removerAsignacion(analista.id, clienteId);
      await cargarDatos();
      if (onSave) onSave(); // Refrescar la lista principal
    } catch (error) {
      console.error("Error al remover asignación:", error);
      setError("Error al remover asignación");
    } finally {
      setOperationLoading(null);
    }
  };

  const filteredDisponibles = clientesDisponibles.filter(cliente =>
    cliente.nombre.toLowerCase().includes(searchTerm.toLowerCase()) ||
    cliente.rut.includes(searchTerm)
  );

  const filteredAsignados = clientesAsignados.filter(cliente =>
    cliente.nombre.toLowerCase().includes(searchTerm.toLowerCase()) ||
    cliente.rut.includes(searchTerm)
  );

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-gray-800 rounded-lg p-6 w-full max-w-4xl max-h-[80vh] overflow-hidden">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-white">
            Gestionar Asignaciones - {analista?.nombre} {analista?.apellido}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white"
          >
            ✕
          </button>
        </div>

        {/* Mostrar error si existe */}
        {error && (
          <div className="mb-4 bg-red-600/20 border border-red-500/30 rounded-lg p-3 text-red-300 text-sm">
            {error}
          </div>
        )}

        <div className="mb-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <input
              type="text"
              placeholder="Buscar clientes..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-6 h-96 overflow-hidden">
          {/* Clientes Disponibles */}
          <div>
            <h3 className="font-semibold text-white mb-3">Clientes Disponibles ({filteredDisponibles.length})</h3>
            <div className="space-y-2 h-full overflow-y-auto">
              {loading ? (
                <div className="text-gray-400 text-center py-8">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-white mx-auto mb-2"></div>
                  Cargando...
                </div>
              ) : filteredDisponibles.length === 0 ? (
                <div className="text-gray-400 text-center py-8">
                  <p>No hay clientes disponibles</p>
                  <p className="text-sm mt-1">
                    {searchTerm ? 'Sin resultados para la búsqueda' : 'Todos los clientes están asignados'}
                  </p>
                </div>
              ) : (
                filteredDisponibles.map((cliente) => (
                  <div key={cliente.id} className="flex items-center justify-between bg-gray-700 p-3 rounded">
                    <div>
                      <p className="font-medium text-white">{cliente.nombre}</p>
                      <p className="text-gray-400 text-sm">{cliente.rut}</p>
                    </div>
                    <button
                      onClick={() => handleAsignar(cliente.id)}
                      disabled={operationLoading === `asignar-${cliente.id}` || loading}
                      className="px-3 py-1 bg-green-600 hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed rounded text-sm flex items-center gap-1"
                    >
                      {operationLoading === `asignar-${cliente.id}` ? (
                        <>
                          <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-white"></div>
                          <span>Asignando...</span>
                        </>
                      ) : (
                        'Asignar'
                      )}
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Clientes Asignados */}
          <div>
            <h3 className="font-semibold text-white mb-3">Clientes Asignados ({filteredAsignados.length})</h3>
            <div className="space-y-2 h-full overflow-y-auto">
              {loading ? (
                <div className="text-gray-400 text-center py-8">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-white mx-auto mb-2"></div>
                  Cargando...
                </div>
              ) : filteredAsignados.length === 0 ? (
                <div className="text-gray-400 text-center py-8">
                  <p>No hay clientes asignados</p>
                  <p className="text-sm mt-1">
                    {searchTerm ? 'Sin resultados para la búsqueda' : 'Asigna clientes desde la columna izquierda'}
                  </p>
                </div>
              ) : (
                filteredAsignados.map((cliente) => (
                  <div key={cliente.id} className="flex items-center justify-between bg-gray-700 p-3 rounded">
                    <div>
                      <p className="font-medium text-white">{cliente.nombre}</p>
                      <p className="text-gray-400 text-sm">{cliente.rut}</p>
                    </div>
                    <button
                      onClick={() => handleRemover(cliente.id)}
                      disabled={operationLoading === `remover-${cliente.id}` || loading}
                      className="px-3 py-1 bg-red-600 hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed rounded text-sm flex items-center gap-1"
                    >
                      {operationLoading === `remover-${cliente.id}` ? (
                        <>
                          <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-white"></div>
                          <span>Removiendo...</span>
                        </>
                      ) : (
                        'Remover'
                      )}
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        <div className="flex justify-end mt-6">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-600 hover:bg-gray-700 rounded text-white"
          >
            Cerrar
          </button>
        </div>
      </div>
    </div>
  );
};

const DetalleAnalistaModal = ({ analista, isOpen, onClose }) => {
  const [estadisticas, setEstadisticas] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (isOpen && analista) {
      cargarEstadisticas();
    }
  }, [isOpen, analista]);

  const cargarEstadisticas = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await obtenerEstadisticasAnalista(analista.id);
      setEstadisticas(data);
    } catch (error) {
      console.error("Error al cargar estadísticas:", error);
      setError("Error al cargar estadísticas del analista");
      setEstadisticas(null);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-gray-800 rounded-lg p-6 w-full max-w-3xl max-h-[80vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-white">
            Detalle del Analista - {analista?.nombre} {analista?.apellido}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white"
          >
            ✕
          </button>
        </div>

        {/* Mostrar error si existe */}
        {error && (
          <div className="bg-red-600/20 border border-red-500/30 rounded-lg p-4 text-red-300">
            <h3 className="font-semibold mb-2">Error</h3>
            <p>{error}</p>
            <button
              onClick={cargarEstadisticas}
              className="mt-3 px-4 py-2 bg-red-600 hover:bg-red-700 rounded text-white"
            >
              Reintentar
            </button>
          </div>
        )}

        {loading ? (
          <div className="text-center text-gray-400 py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white mx-auto mb-4"></div>
            Cargando estadísticas...
          </div>
        ) : estadisticas && !error ? (
          <div className="space-y-6">
            {/* Información General */}
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-gray-700 p-4 rounded">
                <h3 className="font-semibold text-white mb-2">Información Personal</h3>
                <p className="text-gray-300">Email: {analista?.correo_bdo || 'N/A'}</p>
                <p className="text-gray-300">Cargo: {analista?.cargo_bdo || 'N/A'}</p>
                <p className="text-gray-300">Fecha Registro: {analista?.fecha_registro ? new Date(analista.fecha_registro).toLocaleDateString() : 'N/A'}</p>
                
                {/* Mostrar áreas del analista */}
                {analista?.areas && analista.areas.length > 0 && (
                  <div className="mt-3">
                    <p className="text-gray-400 text-sm mb-2">Áreas:</p>
                    <AreaIndicator areas={analista.areas} size="xs" />
                  </div>
                )}
              </div>
              <div className="bg-gray-700 p-4 rounded">
                <h3 className="font-semibold text-white mb-2">Performance</h3>
                <p className="text-gray-300">Cierres Completados: {estadisticas.cierres_completados || 0}</p>
                <p className="text-gray-300">Eficiencia: {estadisticas.eficiencia || 0}%</p>
                <p className="text-gray-300">Tiempo Promedio: {estadisticas.tiempo_promedio_dias || 0} días</p>
              </div>
            </div>

            {/* Estadísticas de Cierres */}
            <div className="bg-gray-700 p-4 rounded">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-white">Estadísticas de Cierres por Estado</h3>
                <button
                  onClick={() => {
                    const debugInfo = `
=== DEBUG: Estadísticas Detalladas ===
Analista: ${analista?.nombre} ${analista?.apellido}

ENDPOINT: /analistas-detallado/${analista?.id}/estadisticas/

CÁLCULO DETALLADO:
${Object.entries(estadisticas.cierres_por_estado || {}).map(([estado, count]) => 
  `• ${estado}: ${count} cierres`
).join('\n')}

ESTADOS CONSIDERADOS "COMPLETADOS":
- 'completo' (Contabilidad)
- 'completado' (Nómina)  
- 'aprobado' (Contabilidad)
- 'finalizado' (Contabilidad)

Total Completados: ${estadisticas.cierres_completados || 0}
Eficiencia: ${estadisticas.eficiencia || 0}%
Tiempo Promedio: ${estadisticas.tiempo_promedio_dias || 0} días

FUENTES DE DATOS:
- CierreContabilidad: usuario=${analista?.id}
- CierreNomina: usuario_analista=${analista?.id}
=====================================`;
                    alert(debugInfo);
                  }}
                  className="text-xs text-gray-400 hover:text-gray-300 px-2 py-1 border border-gray-600 rounded"
                >
                  🐛 Debug
                </button>
              </div>
              <div className="grid grid-cols-3 gap-4">
                {Object.entries(estadisticas.cierres_por_estado || {}).map(([estado, count]) => {
                  const isCompleted = ['completo', 'completado', 'aprobado', 'finalizado'].includes(estado);
                  return (
                    <div key={estado} className="text-center">
                      <p className={`text-2xl font-bold ${isCompleted ? 'text-green-400' : 'text-blue-400'}`}>
                        {count}
                        {isCompleted && <span className="text-xs ml-1">✓</span>}
                      </p>
                      <p className="text-gray-400 text-sm capitalize">{estado.replace('_', ' ')}</p>
                    </div>
                  );
                })}
              </div>
              <div className="mt-4 p-3 bg-gray-600 rounded text-sm">
                <p className="text-gray-300 mb-2">
                  <span className="text-green-400">✓ Estados completados:</span> completo, completado, aprobado, finalizado
                </p>
                <p className="text-gray-400">
                  Total completados: <span className="text-green-400 font-semibold">{estadisticas.cierres_completados || 0}</span>
                </p>
              </div>
            </div>

            {/* Clientes Asignados */}
            <div className="bg-gray-700 p-4 rounded">
              <h3 className="font-semibold text-white mb-4">Clientes Asignados</h3>
              <div className="space-y-2 max-h-40 overflow-y-auto">
                {estadisticas.clientes && estadisticas.clientes.length > 0 ? (
                  estadisticas.clientes.map((cliente) => (
                    <div key={cliente.id} className="flex justify-between items-center p-2 bg-gray-600 rounded">
                      <span className="text-white">{cliente.nombre}</span>
                      <span className="text-gray-400 text-sm">{cliente.rut}</span>
                    </div>
                  ))
                ) : (
                  <p className="text-gray-400 text-center py-4">No hay clientes asignados</p>
                )}
              </div>
            </div>
          </div>
        ) : !loading && !error ? (
          <div className="text-center text-gray-400 py-8">
            <p>No se pudieron cargar las estadísticas</p>
            <button
              onClick={cargarEstadisticas}
              className="mt-3 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded text-white text-sm"
            >
              Cargar datos
            </button>
          </div>
        ) : null}

        <div className="flex justify-end mt-6">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-600 hover:bg-gray-700 rounded text-white"
          >
            Cerrar
          </button>
        </div>
      </div>
    </div>
  );
};

const SupervisorModal = ({ analista, supervisores, isOpen, onClose, onAssign }) => {
  const [selectedSupervisor, setSelectedSupervisor] = useState("");

  if (!isOpen || !analista) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    if (selectedSupervisor) {
      onAssign(selectedSupervisor);
      setSelectedSupervisor("");
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-gray-800 rounded-lg p-6 w-full max-w-md">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-white">
            Asignar Supervisor
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white"
          >
            ✕
          </button>
        </div>

        <div className="mb-4">
          <p className="text-gray-300 mb-2">
            Analista: <span className="font-semibold text-white">{analista.nombre} {analista.apellido}</span>
          </p>
          {analista.supervisor_nombre && (
            <p className="text-green-400 text-sm">
              Supervisor actual: {analista.supervisor_nombre}
            </p>
          )}
        </div>

        <form onSubmit={handleSubmit}>
          <div className="mb-6">
            <label className="block text-gray-300 font-medium mb-2">
              Seleccionar Supervisor:
            </label>
            <select
              value={selectedSupervisor}
              onChange={(e) => setSelectedSupervisor(e.target.value)}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
              required
            >
              <option value="">-- Seleccionar supervisor --</option>
              {supervisores.map((supervisor) => (
                <option key={supervisor.id} value={supervisor.id}>
                  {supervisor.nombre} {supervisor.apellido} ({supervisor.correo_bdo})
                </option>
              ))}
            </select>
            {supervisores.length === 0 && (
              <p className="text-yellow-400 text-sm mt-2">
                No hay supervisores disponibles para las áreas de este analista.
              </p>
            )}
          </div>

          <div className="flex justify-end space-x-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 bg-gray-600 hover:bg-gray-700 rounded-lg text-white transition-colors"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={!selectedSupervisor}
              className="px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-600 disabled:cursor-not-allowed rounded-lg text-white transition-colors"
            >
              Asignar
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

const GestionAnalistas = () => {
  const [analistas, setAnalistas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedAnalista, setSelectedAnalista] = useState(null);
  const [showAsignacionModal, setShowAsignacionModal] = useState(false);
  const [showDetalleModal, setShowDetalleModal] = useState(false);
  const [showSupervisorModal, setShowSupervisorModal] = useState(false);
  const [supervisoresDisponibles, setSupervisoresDisponibles] = useState([]);
  const [searchTerm, setSearchTerm] = useState("");

  useEffect(() => {
    cargarAnalistas();
  }, []);

  const cargarAnalistas = async () => {
    try {
      setLoading(true);
      const data = await obtenerAnalistasDetallado();
      
      console.log('=== DEBUG: Datos de Analistas Cargados ===');
      console.log('Total analistas:', data.length);
      console.log('Estructura de datos completa:', data);
      
      // Debug específico de cierres completados
      console.log('=== CIERRES COMPLETADOS POR ANALISTA ===');
      data.forEach(analista => {
        console.log(`${analista.nombre} ${analista.apellido}:`, {
          id: analista.id,
          cierres_completados: analista.cierres_completados,
          cierres_contabilidad: analista.cierres_contabilidad,
          cierres_nomina: analista.cierres_nomina,
          clientes_asignados: analista.clientes_asignados,
          eficiencia: analista.eficiencia,
          carga_trabajo: analista.carga_trabajo,
          areas: analista.areas?.map(a => a.nombre) || []
        });
      });
      
      const totalCierres = data.reduce((sum, a) => sum + a.cierres_completados, 0);
      console.log('TOTAL CIERRES COMPLETADOS EN SISTEMA:', totalCierres);
      console.log('========================================');
      
      setAnalistas(data);
    } catch (error) {
      console.error("Error al cargar analistas:", error);
      console.error("Detalles del error:", error.response?.data);
    } finally {
      setLoading(false);
    }
  };

  const handleViewDetails = (analista) => {
    setSelectedAnalista(analista);
    setShowDetalleModal(true);
  };

  const handleEditAssignments = (analista) => {
    setSelectedAnalista(analista);
    setShowAsignacionModal(true);
  };

  const handleAssignSupervisor = async (analista) => {
    setSelectedAnalista(analista);
    try {
      const supervisores = await obtenerSupervisoresDisponibles();
      // Filtrar supervisores que compartan al menos un área con el analista
      const supervisoresFiltrados = supervisores.filter(supervisor => {
        const supervisorAreas = supervisor.areas || [];
        const analistaAreas = analista.areas || [];
        return supervisorAreas.some(supArea => 
          analistaAreas.some(anaArea => supArea.id === anaArea.id)
        );
      });
      setSupervisoresDisponibles(supervisoresFiltrados);
      setShowSupervisorModal(true);
    } catch (error) {
      console.error("Error al cargar supervisores:", error);
    }
  };

  const handleAsignarSupervisor = async (supervisorId) => {
    try {
      await asignarSupervisor(selectedAnalista.id, supervisorId);
      await cargarAnalistas(); // Recargar los datos
      setShowSupervisorModal(false);
      setSelectedAnalista(null);
    } catch (error) {
      console.error("Error al asignar supervisor:", error);
    }
  };

  const filteredAnalistas = analistas.filter(analista => {
    const matchesSearch = analista.nombre.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         analista.apellido.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         analista.correo_bdo.toLowerCase().includes(searchTerm.toLowerCase());
    
    return matchesSearch;
  });

  return (
    <div className="text-white space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <h1 className="text-3xl font-bold mb-2">Gestión de Analistas</h1>
          <p className="text-gray-400">Administra asignaciones y supervisa el desempeño</p>
        </div>
        <div className="flex space-x-3">
          <button
            onClick={cargarAnalistas}
            className="flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Actualizar
          </button>
          <button
            onClick={() => {
              const debugInfo = `
=== DEBUG: Recuperación de Cierres Completados ===

ENDPOINT PRINCIPAL: /analistas-detallado/
Este endpoint utiliza anotaciones de Django ORM para calcular:

CÁLCULO DE CIERRES COMPLETADOS:
1. Cierres de Contabilidad (CierreContabilidad):
   - Estados considerados completados: 'aprobado', 'completo', 'finalizado'
   - Count('cierrecontabilidad', filter=Q(cierrecontabilidad__estado__in=['aprobado', 'completo', 'finalizado']))

2. Cierres de Nómina (CierreNomina):
   - Estado considerado completado: 'completado' 
   - Count('cierres_analista', filter=Q(cierres_analista__estado='completado'))

TOTAL = Cierres Contabilidad Completados + Cierres Nómina Completados

DATOS ACTUALES:
${analistas.map(a => 
  `- ${a.nombre} ${a.apellido}: ${a.cierres_completados} cierres completados`
).join('\n')}

TOTAL SISTEMA: ${analistas.reduce((sum, a) => sum + a.cierres_completados, 0)} cierres completados

ENDPOINT ESTADÍSTICAS DETALLADAS: /analistas-detallado/{id}/estadisticas/
Para ver detalles por estado de cada analista, usa el botón "Ver detalles"

CAMPOS RELACIONADOS:
- cierres_contabilidad: Total cierres de contabilidad (todos los estados)
- cierres_nomina: Total cierres de nómina (todos los estados)
- eficiencia: (cierres_completados * 100) / (clientes_asignados + 1)

NOTA: Se corrigió para incluir 'finalizado' como estado completado en Contabilidad
=================================================`;
              alert(debugInfo);
            }}
            className="flex items-center px-3 py-2 bg-orange-600 hover:bg-orange-700 rounded-lg text-sm"
          >
            🐛 Debug Cierres
          </button>
          <button className="flex items-center px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg">
            <Download className="w-4 h-4 mr-2" />
            Exportar
          </button>
        </div>
      </div>

      {/* Filtros y Búsqueda */}
      <div className="flex items-center space-x-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
          <input
            type="text"
            placeholder="Buscar analistas..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-gray-800 border border-gray-600 rounded-lg text-white"
          />
        </div>
      </div>

      {/* Resumen de Estadísticas */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-gray-800 p-4 rounded-lg border border-gray-700">
          <div className="flex items-center">
            <Users className="w-8 h-8 text-blue-400 mr-3" />
            <div>
              <p className="text-2xl font-bold">{analistas.length}</p>
              <p className="text-gray-400 text-sm">Total Analistas</p>
            </div>
          </div>
        </div>
        <div className="bg-gray-800 p-4 rounded-lg border border-gray-700">
          <div className="flex items-center">
            <Building2 className="w-8 h-8 text-green-400 mr-3" />
            <div>
              <p className="text-2xl font-bold">
                {analistas.reduce((sum, a) => sum + a.clientes_asignados, 0)}
              </p>
              <p className="text-gray-400 text-sm">Clientes Asignados</p>
            </div>
          </div>
        </div>
        <div className="bg-gray-800 p-4 rounded-lg border border-gray-700">
          <div className="flex items-center">
            <Target className="w-8 h-8 text-yellow-400 mr-3" />
            <div>
              <p className="text-2xl font-bold">
                {Math.round(analistas.reduce((sum, a) => sum + a.eficiencia, 0) / analistas.length)}%
              </p>
              <p className="text-gray-400 text-sm">Eficiencia Promedio</p>
            </div>
          </div>
        </div>
        <div className="bg-gray-800 p-4 rounded-lg border border-gray-700">
          <div className="flex items-center">
            <BarChart3 className="w-8 h-8 text-purple-400 mr-3" />
            <div>
              <p className="text-2xl font-bold">
                {analistas.reduce((sum, a) => sum + a.cierres_completados, 0)}
              </p>
              <p className="text-gray-400 text-sm">Cierres Completados</p>
            </div>
          </div>
        </div>
      </div>

      {/* Lista de Analistas */}
      {loading ? (
        <div className="text-center text-gray-400">Cargando analistas...</div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
          {filteredAnalistas.map((analista) => (
            <AnalistaCard
              key={analista.id}
              analista={analista}
              onViewDetails={handleViewDetails}
              onEditAssignments={handleEditAssignments}
              onAssignSupervisor={handleAssignSupervisor}
            />
          ))}
        </div>
      )}

      {/* Modales */}
      <AsignacionModal
        analista={selectedAnalista}
        isOpen={showAsignacionModal}
        onClose={() => setShowAsignacionModal(false)}
        onSave={cargarAnalistas}
      />

      <DetalleAnalistaModal
        analista={selectedAnalista}
        isOpen={showDetalleModal}
        onClose={() => setShowDetalleModal(false)}
      />

      <SupervisorModal
        analista={selectedAnalista}
        supervisores={supervisoresDisponibles}
        isOpen={showSupervisorModal}
        onClose={() => setShowSupervisorModal(false)}
        onAssign={handleAsignarSupervisor}
      />
    </div>
  );
};

export default GestionAnalistas;
