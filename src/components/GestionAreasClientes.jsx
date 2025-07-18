import { useState, useEffect } from 'react';
import { Settings, Plus, Trash2, Save, AlertTriangle, Users, Building2, UserPlus } from 'lucide-react';
import { 
  obtenerClientesSinAreas, 
  asignarAreasCliente, 
  migrarClientesAreasDirectas,
  obtenerClientesArea,
  obtenerAnalistasArea,
  asignarClienteAnalista,
  removerAsignacion,
  obtenerClientesAsignados
} from '../api/analistas';

const GestionAreasClientes = () => {
  const [clientesSinAreas, setClientesSinAreas] = useState([]);
  const [clientesDelArea, setClientesDelArea] = useState([]);
  const [analistasDelArea, setAnalistasDelArea] = useState([]);
  const [areas, setAreas] = useState([]);
  const [loading, setLoading] = useState(false);
  const [mensaje, setMensaje] = useState(null);
  const [clienteSeleccionado, setClienteSeleccionado] = useState(null);
  const [areasSeleccionadas, setAreasSeleccionadas] = useState([]);
  const [mostrarAsignaciones, setMostrarAsignaciones] = useState(false);
  const [clienteParaAsignar, setClienteParaAsignar] = useState(null);
  const [analistaSeleccionado, setAnalistaSeleccionado] = useState('');
  const [asignacionesActuales, setAsignacionesActuales] = useState({});

  useEffect(() => {
    cargarDatos();
  }, []);

  const cargarDatos = async () => {
    try {
      setLoading(true);
      const [clientesRes, areasRes, clientesAreaRes, analistasRes] = await Promise.all([
        obtenerClientesSinAreas(),
        fetch('/api/areas/').then(res => res.json()),
        obtenerClientesArea(),
        obtenerAnalistasArea()
      ]);
      
      setClientesSinAreas(clientesRes);
      setAreas(areasRes);
      setClientesDelArea(clientesAreaRes);
      setAnalistasDelArea(analistasRes);
      
      // Cargar asignaciones actuales para cada analista
      const asignaciones = {};
      for (const analista of analistasRes) {
        try {
          const clientesAsignados = await obtenerClientesAsignados(analista.id);
          asignaciones[analista.id] = clientesAsignados;
        } catch (error) {
          console.error(`Error cargando asignaciones para analista ${analista.id}:`, error);
          asignaciones[analista.id] = [];
        }
      }
      setAsignacionesActuales(asignaciones);
      
    } catch (error) {
      console.error('Error cargando datos:', error);
      setMensaje({ tipo: 'error', texto: 'Error al cargar datos' });
    } finally {
      setLoading(false);
    }
  };

  const handleAsignarClienteAnalista = async () => {
    if (!clienteParaAsignar || !analistaSeleccionado) {
      setMensaje({ tipo: 'error', texto: 'Debe seleccionar un cliente y un analista' });
      return;
    }

    try {
      setLoading(true);
      await asignarClienteAnalista(analistaSeleccionado, clienteParaAsignar.id);
      
      setMensaje({ tipo: 'success', texto: 'Cliente asignado correctamente' });
      setClienteParaAsignar(null);
      setAnalistaSeleccionado('');
      setMostrarAsignaciones(false);
      cargarDatos();
    } catch (error) {
      console.error('Error asignando cliente:', error);
      setMensaje({ tipo: 'error', texto: 'Error al asignar cliente' });
    } finally {
      setLoading(false);
    }
  };

  const handleRemoverAsignacion = async (analistaId, clienteId) => {
    try {
      setLoading(true);
      await removerAsignacion(analistaId, clienteId);
      
      setMensaje({ tipo: 'success', texto: 'Asignación removida correctamente' });
      cargarDatos();
    } catch (error) {
      console.error('Error removiendo asignación:', error);
      setMensaje({ tipo: 'error', texto: 'Error al remover asignación' });
    } finally {
      setLoading(false);
    }
  };

  const handleAsignarAreas = async (clienteId) => {
    if (areasSeleccionadas.length === 0) {
      setMensaje({ tipo: 'error', texto: 'Debe seleccionar al menos un área' });
      return;
    }

    try {
      setLoading(true);
      await asignarAreasCliente(clienteId, areasSeleccionadas);
      
      setMensaje({ tipo: 'success', texto: 'Áreas asignadas correctamente' });
      setClienteSeleccionado(null);
      setAreasSeleccionadas([]);
      cargarDatos();
    } catch (error) {
      console.error('Error asignando áreas:', error);
      setMensaje({ tipo: 'error', texto: 'Error al asignar áreas' });
    } finally {
      setLoading(false);
    }
  };

  const handleMigrarClientes = async () => {
    if (!confirm('¿Desea migrar todos los clientes con servicios a áreas directas? Esta acción no se puede deshacer.')) {
      return;
    }

    try {
      setLoading(true);
      const resultado = await migrarClientesAreasDirectas();
      
      setMensaje({ 
        tipo: 'success', 
        texto: `Migración completada: ${resultado.clientes_migrados} clientes migrados` 
      });
      cargarDatos();
    } catch (error) {
      console.error('Error en migración:', error);
      setMensaje({ tipo: 'error', texto: 'Error en la migración' });
    } finally {
      setLoading(false);
    }
  };

  const toggleAreaSeleccionada = (areaId) => {
    setAreasSeleccionadas(prev => 
      prev.includes(areaId) 
        ? prev.filter(id => id !== areaId)
        : [...prev, areaId]
    );
  };

  const obtenerAreasCliente = (cliente) => {
    if (cliente.areas && cliente.areas.length > 0) {
      return cliente.areas.map(area => area.nombre).join(', ');
    }
    if (cliente.areas_efectivas && cliente.areas_efectivas.length > 0) {
      return cliente.areas_efectivas.map(area => area.nombre).join(', ');
    }
    return 'Sin áreas';
  };

  const clienteYaAsignado = (cliente) => {
    return Object.values(asignacionesActuales).some(asignaciones => 
      asignaciones.some(asignacion => asignacion.id === cliente.id)
    );
  };

  const getAnalistaAsignado = (cliente) => {
    for (const [analistaId, asignaciones] of Object.entries(asignacionesActuales)) {
      const asignacion = asignaciones.find(asig => asig.id === cliente.id);
      if (asignacion) {
        const analista = analistasDelArea.find(a => a.id === parseInt(analistaId));
        return analista;
      }
    }
    return null;
  };

  return (
    <div className="bg-gray-800 rounded-lg p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center">
          <Settings className="w-6 h-6 text-blue-400 mr-2" />
          <h2 className="text-xl font-bold text-white">Gestión de Clientes y Asignaciones</h2>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setMostrarAsignaciones(!mostrarAsignaciones)}
            className="flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
          >
            <Users className="w-4 h-4 mr-2" />
            {mostrarAsignaciones ? 'Ocultar Asignaciones' : 'Mostrar Asignaciones'}
          </button>
          <button
            onClick={handleMigrarClientes}
            disabled={loading}
            className="flex items-center px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:opacity-50 rounded-lg transition-colors"
          >
            <Plus className="w-4 h-4 mr-2" />
            Migrar Clientes
          </button>
        </div>
      </div>

      {mensaje && (
        <div className={`mb-4 p-3 rounded-lg ${
          mensaje.tipo === 'error' 
            ? 'bg-red-600/20 border border-red-500/30 text-red-300' 
            : 'bg-green-600/20 border border-green-500/30 text-green-300'
        }`}>
          {mensaje.texto}
        </div>
      )}

      {loading && (
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white"></div>
          <span className="ml-2 text-white">Cargando...</span>
        </div>
      )}

      {/* Modal para asignar cliente */}
      {clienteParaAsignar && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-gray-800 p-6 rounded-lg max-w-md w-full mx-4">
            <h3 className="text-xl font-bold text-white mb-4">
              Asignar Cliente: {clienteParaAsignar.nombre}
            </h3>
            <div className="mb-4">
              <label className="block text-white text-sm font-medium mb-2">
                Seleccionar Analista:
              </label>
              <select
                value={analistaSeleccionado}
                onChange={(e) => setAnalistaSeleccionado(e.target.value)}
                className="w-full p-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
              >
                <option value="">Seleccionar analista...</option>
                {analistasDelArea.map(analista => (
                  <option key={analista.id} value={analista.id}>
                    {analista.nombre} {analista.apellido} ({analista.correo_bdo})
                  </option>
                ))}
              </select>
            </div>
            <div className="flex gap-2">
              <button
                onClick={handleAsignarClienteAnalista}
                disabled={!analistaSeleccionado || loading}
                className="flex-1 bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white py-2 px-4 rounded-lg"
              >
                Asignar
              </button>
              <button
                onClick={() => {
                  setClienteParaAsignar(null);
                  setAnalistaSeleccionado('');
                }}
                className="flex-1 bg-gray-600 hover:bg-gray-700 text-white py-2 px-4 rounded-lg"
              >
                Cancelar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Clientes del área actual */}
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-white mb-3">
          Clientes del Área ({clientesDelArea.length})
        </h3>
        
        {clientesDelArea.length === 0 ? (
          <div className="text-center py-8 text-gray-400">
            <Building2 className="w-12 h-12 mx-auto mb-2 opacity-50" />
            <p>No hay clientes en esta área</p>
          </div>
        ) : (
          <div className="grid gap-4">
            {clientesDelArea.map(cliente => {
              const yaAsignado = clienteYaAsignado(cliente);
              const analistaAsignado = getAnalistaAsignado(cliente);
              
              return (
                <div key={cliente.id} className="bg-gray-700 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <h4 className="font-semibold text-white">{cliente.nombre}</h4>
                      <p className="text-gray-400 text-sm">{cliente.rut}</p>
                      <p className="text-blue-400 text-sm">
                        Áreas: {obtenerAreasCliente(cliente)}
                      </p>
                      {yaAsignado && analistaAsignado && (
                        <p className="text-green-400 text-sm">
                          Asignado a: {analistaAsignado.nombre} {analistaAsignado.apellido}
                        </p>
                      )}
                    </div>
                    <div className="flex gap-2">
                      {yaAsignado && analistaAsignado ? (
                        <button
                          onClick={() => handleRemoverAsignacion(analistaAsignado.id, cliente.id)}
                          disabled={loading}
                          className="px-3 py-1 bg-red-600 hover:bg-red-700 disabled:opacity-50 rounded text-sm"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      ) : (
                        <button
                          onClick={() => setClienteParaAsignar(cliente)}
                          disabled={loading}
                          className="flex items-center px-3 py-1 bg-green-600 hover:bg-green-700 disabled:opacity-50 rounded text-sm"
                        >
                          <UserPlus className="w-4 h-4 mr-1" />
                          Asignar
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Mostrar asignaciones detalladas */}
      {mostrarAsignaciones && (
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-white mb-3">
            Asignaciones por Analista
          </h3>
          <div className="grid gap-4">
            {analistasDelArea.map(analista => (
              <div key={analista.id} className="bg-gray-700 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <div>
                    <h4 className="font-semibold text-white">
                      {analista.nombre} {analista.apellido}
                    </h4>
                    <p className="text-gray-400 text-sm">{analista.correo_bdo}</p>
                  </div>
                  <span className="text-blue-400 text-sm">
                    {asignacionesActuales[analista.id]?.length || 0} clientes
                  </span>
                </div>
                {asignacionesActuales[analista.id]?.length > 0 && (
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2 mt-3">
                    {asignacionesActuales[analista.id].map(cliente => (
                      <div key={cliente.id} className="bg-gray-600 rounded p-2 flex items-center justify-between">
                        <span className="text-white text-sm">{cliente.nombre}</span>
                        <button
                          onClick={() => handleRemoverAsignacion(analista.id, cliente.id)}
                          className="text-red-400 hover:text-red-300 p-1"
                          title="Remover asignación"
                        >
                          <Trash2 className="w-3 h-3" />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Lista de clientes sin áreas */}
      <div className="mb-6">
        <h3 className="text-lg font-semibold text-white mb-3">
          Clientes sin Áreas Asignadas ({clientesSinAreas.length})
        </h3>
        
        {clientesSinAreas.length === 0 ? (
          <div className="text-center py-8 text-gray-400">
            <AlertTriangle className="w-12 h-12 mx-auto mb-2 opacity-50" />
            <p>Todos los clientes tienen áreas asignadas</p>
          </div>
        ) : (
          <div className="grid gap-4">
            {clientesSinAreas.map(cliente => (
              <div key={cliente.id} className="bg-gray-700 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <div>
                    <h4 className="font-semibold text-white">{cliente.nombre}</h4>
                    <p className="text-gray-400 text-sm">{cliente.rut}</p>
                  </div>
                  <button
                    onClick={() => setClienteSeleccionado(
                      clienteSeleccionado === cliente.id ? null : cliente.id
                    )}
                    className="px-3 py-1 bg-blue-600 hover:bg-blue-700 rounded text-sm"
                  >
                    {clienteSeleccionado === cliente.id ? 'Cancelar' : 'Asignar Áreas'}
                  </button>
                </div>

                {clienteSeleccionado === cliente.id && (
                  <div className="mt-4 p-3 bg-gray-600 rounded">
                    <p className="text-white text-sm mb-2">Selecciona las áreas:</p>
                    <div className="grid grid-cols-2 gap-2 mb-3">
                      {areas.map(area => (
                        <label key={area.id} className="flex items-center">
                          <input
                            type="checkbox"
                            checked={areasSeleccionadas.includes(area.id)}
                            onChange={() => toggleAreaSeleccionada(area.id)}
                            className="mr-2"
                          />
                          <span className="text-white text-sm">{area.nombre}</span>
                        </label>
                      ))}
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleAsignarAreas(cliente.id)}
                        disabled={areasSeleccionadas.length === 0 || loading}
                        className="flex items-center px-3 py-1 bg-green-600 hover:bg-green-700 disabled:opacity-50 rounded text-sm"
                      >
                        <Save className="w-4 h-4 mr-1" />
                        Guardar
                      </button>
                      <button
                        onClick={() => {
                          setClienteSeleccionado(null);
                          setAreasSeleccionadas([]);
                        }}
                        className="px-3 py-1 bg-gray-500 hover:bg-gray-600 rounded text-sm"
                      >
                        Cancelar
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Información sobre el bypass */}
      <div className="bg-yellow-600/20 border border-yellow-500/30 rounded-lg p-4">
        <h3 className="text-yellow-300 font-semibold mb-2">ℹ️ Información del Sistema</h3>
        <p className="text-yellow-200 text-sm">
          Esta página permite gestionar clientes por área y crear asignaciones cliente-analista. 
          Los clientes pueden tener áreas asignadas directamente o a través de servicios contratados.
          Las asignaciones se realizan solo entre usuarios de la misma área.
        </p>
      </div>
    </div>
  );
};

export default GestionAreasClientes;
