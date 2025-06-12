import { useState, useEffect } from 'react';
import { obtenerClientesGerente, reasignarCliente } from '../../api/gerente';
import { obtenerAnalistasDetallado } from '../../api/analistas';
import { formatDate } from '../../utils/format';

const GestionClientesAvanzada = ({ areas }) => {
  const [clientes, setClientes] = useState([]);
  const [analistas, setAnalistas] = useState([]);
  const [filtros, setFiltros] = useState({
    area: '',
    estado: '',
    asignacion: '',
    busqueda: ''
  });
  const [clienteReasignando, setClienteReasignando] = useState(null);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    cargarDatos();
  }, []);

  const cargarDatos = async () => {
    setCargando(true);
    setError('');
    try {
      const [clientesData, analistasData] = await Promise.all([
        obtenerClientesGerente(),
        obtenerAnalistasDetallado()
      ]);
      setClientes(clientesData);
      setAnalistas(analistasData);
    } catch (error) {
      console.error('Error cargando datos:', error);
      setError('Error al cargar los datos. Por favor intenta nuevamente.');
    } finally {
      setCargando(false);
    }
  };

  const clientesFiltrados = clientes.filter(cliente => {
    const cumpleBusqueda = !filtros.busqueda || 
      cliente.nombre.toLowerCase().includes(filtros.busqueda.toLowerCase()) ||
      cliente.rut.toLowerCase().includes(filtros.busqueda.toLowerCase());
    
    const cumpleArea = !filtros.area || 
      cliente.areas_activas?.includes(filtros.area);
    
    const cumpleEstado = !filtros.estado || 
      cliente.estado_cierres === filtros.estado;
    
    const cumpleAsignacion = !filtros.asignacion ||
      (filtros.asignacion === 'sin_asignar' && (!cliente.analistas_asignados || cliente.analistas_asignados.length === 0)) ||
      (filtros.asignacion === 'asignado' && cliente.analistas_asignados && cliente.analistas_asignados.length > 0);
    
    return cumpleBusqueda && cumpleArea && cumpleEstado && cumpleAsignacion;
  });

  const manejarReasignacion = async (clienteId, nuevoAnalistaId, area) => {
    try {
      await reasignarCliente(clienteId, nuevoAnalistaId, area);
      await cargarDatos(); // Recargar datos
      setClienteReasignando(null);
    } catch (error) {
      console.error('Error reasignando cliente:', error);
      setError('Error al reasignar cliente. Verifica que el analista tenga permisos en esa área.');
    }
  };

  const getEstadoColor = (estado) => {
    switch (estado) {
      case 'al_dia': return 'bg-green-600 text-white';
      case 'atrasado': return 'bg-yellow-600 text-white';
      case 'critico': return 'bg-red-600 text-white';
      default: return 'bg-gray-600 text-white';
    }
  };

  const getEstadoTexto = (estado) => {
    switch (estado) {
      case 'al_dia': return 'Al día';
      case 'atrasado': return 'Atrasado';
      case 'critico': return 'Crítico';
      default: return 'Desconocido';
    }
  };

  if (cargando) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white"></div>
        <span className="ml-2 text-white">Cargando clientes...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-600 text-white p-4 rounded-lg">
        <h3 className="font-semibold">Error</h3>
        <p>{error}</p>
        <button 
          onClick={cargarDatos}
          className="mt-2 bg-red-800 hover:bg-red-900 px-4 py-2 rounded"
        >
          Reintentar
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-white">Gestión Avanzada de Clientes</h2>
        <div className="flex gap-4">
          <button
            onClick={() => window.location.href = '/clientes/nuevo'}
            className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg"
          >
            + Nuevo Cliente
          </button>
          <button
            onClick={() => window.location.href = '/clientes/importar'}
            className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg"
          >
            📁 Importar Clientes
          </button>
        </div>
      </div>

      {/* Filtros Avanzados */}
      <div className="bg-gray-800 p-4 rounded-lg">
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <div>
            <label className="block text-white text-sm font-semibold mb-2">
              Buscar
            </label>
            <input
              type="text"
              placeholder="Nombre o RUT..."
              value={filtros.busqueda}
              onChange={(e) => setFiltros({...filtros, busqueda: e.target.value})}
              className="w-full p-2 rounded bg-gray-700 text-white"
            />
          </div>

          <div>
            <label className="block text-white text-sm font-semibold mb-2">
              Área
            </label>
            <select
              value={filtros.area}
              onChange={(e) => setFiltros({...filtros, area: e.target.value})}
              className="w-full p-2 rounded bg-gray-700 text-white"
            >
              <option value="">Todas las áreas</option>
              {areas.map(area => (
                <option key={area.id} value={area.nombre}>{area.nombre}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-white text-sm font-semibold mb-2">
              Estado Cierres
            </label>
            <select
              value={filtros.estado}
              onChange={(e) => setFiltros({...filtros, estado: e.target.value})}
              className="w-full p-2 rounded bg-gray-700 text-white"
            >
              <option value="">Todos los estados</option>
              <option value="al_dia">Al día</option>
              <option value="atrasado">Atrasado</option>
              <option value="critico">Crítico</option>
            </select>
          </div>

          <div>
            <label className="block text-white text-sm font-semibold mb-2">
              Asignación
            </label>
            <select
              value={filtros.asignacion}
              onChange={(e) => setFiltros({...filtros, asignacion: e.target.value})}
              className="w-full p-2 rounded bg-gray-700 text-white"
            >
              <option value="">Todos</option>
              <option value="asignado">Asignados</option>
              <option value="sin_asignar">Sin asignar</option>
            </select>
          </div>

          <div className="flex items-end">
            <button
              onClick={() => setFiltros({area: '', estado: '', asignacion: '', busqueda: ''})}
              className="w-full bg-gray-600 hover:bg-gray-700 text-white py-2 rounded"
            >
              Limpiar Filtros
            </button>
          </div>
        </div>
      </div>

      {/* Estadísticas Rápidas */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-gray-800 p-4 rounded-lg">
          <h3 className="text-white font-semibold">Total Clientes</h3>
          <p className="text-2xl font-bold text-blue-500">{clientesFiltrados.length}</p>
          <p className="text-sm text-gray-400">de {clientes.length} total</p>
        </div>
        <div className="bg-gray-800 p-4 rounded-lg">
          <h3 className="text-white font-semibold">Sin Asignar</h3>
          <p className="text-2xl font-bold text-red-500">
            {clientesFiltrados.filter(c => !c.analistas_asignados || c.analistas_asignados.length === 0).length}
          </p>
          <p className="text-sm text-gray-400">requieren asignación</p>
        </div>
        <div className="bg-gray-800 p-4 rounded-lg">
          <h3 className="text-white font-semibold">Al Día</h3>
          <p className="text-2xl font-bold text-green-500">
            {clientesFiltrados.filter(c => c.estado_cierres === 'al_dia').length}
          </p>
          <p className="text-sm text-gray-400">cierres al día</p>
        </div>
        <div className="bg-gray-800 p-4 rounded-lg">
          <h3 className="text-white font-semibold">Atrasados</h3>
          <p className="text-2xl font-bold text-yellow-500">
            {clientesFiltrados.filter(c => ['atrasado', 'critico'].includes(c.estado_cierres)).length}
          </p>
          <p className="text-sm text-gray-400">necesitan atención</p>
        </div>
      </div>

      {/* Tabla de Clientes */}
      <div className="bg-gray-800 rounded-lg overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-700">
            <tr>
              <th className="p-3 text-left text-white">Cliente</th>
              <th className="p-3 text-left text-white">Áreas Activas</th>
              <th className="p-3 text-center text-white">Analistas Asignados</th>
              <th className="p-3 text-center text-white">Estado Cierres</th>
              <th className="p-3 text-center text-white">Último Cierre</th>
              <th className="p-3 text-center text-white">Acciones</th>
            </tr>
          </thead>
          <tbody>
            {clientesFiltrados.map((cliente) => (
              <tr key={cliente.id} className="border-b border-gray-700 hover:bg-gray-750">
                <td className="p-3 text-white">
                  <div>
                    <div className="font-semibold">{cliente.nombre}</div>
                    <div className="text-sm text-gray-400">{cliente.rut}</div>
                  </div>
                </td>
                <td className="p-3">
                  <div className="flex flex-wrap gap-1">
                    {cliente.areas_activas?.map((area) => (
                      <span
                        key={area}
                        className="px-2 py-1 bg-blue-600 text-white text-xs rounded"
                      >
                        {area}
                      </span>
                    ))}
                  </div>
                </td>
                <td className="p-3 text-center">
                  {cliente.analistas_asignados && cliente.analistas_asignados.length > 0 ? (
                    <div className="space-y-1">
                      {cliente.analistas_asignados.map((asignacion) => (
                        <div key={asignacion.id} className="text-xs bg-gray-700 p-2 rounded">
                          <div className="text-white font-medium">{asignacion.analista_nombre}</div>
                          <div className="text-gray-400">({asignacion.area})</div>
                          <div className="text-xs text-gray-500">
                            Desde: {formatDate(asignacion.fecha_asignacion)}
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <span className="text-red-400 text-sm">Sin asignar</span>
                  )}
                </td>
                <td className="p-3 text-center">
                  <span className={`px-3 py-1 rounded text-xs font-medium ${getEstadoColor(cliente.estado_cierres)}`}>
                    {getEstadoTexto(cliente.estado_cierres)}
                  </span>
                </td>
                <td className="p-3 text-center text-white">
                  {cliente.ultimo_cierre ? formatDate(cliente.ultimo_cierre) : 'N/A'}
                </td>
                <td className="p-3 text-center">
                  <div className="flex gap-2 justify-center">
                    <button
                      onClick={() => setClienteReasignando(cliente)}
                      className="bg-blue-600 hover:bg-blue-700 text-white px-2 py-1 rounded text-xs"
                    >
                      Reasignar
                    </button>
                    <button
                      onClick={() => window.location.href = `/clientes/${cliente.id}`}
                      className="bg-green-600 hover:bg-green-700 text-white px-2 py-1 rounded text-xs"
                    >
                      Ver Detalle
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Modal de Reasignación */}
      {clienteReasignando && (
        <ModalReasignacion
          cliente={clienteReasignando}
          analistas={analistas}
          areas={areas}
          onReasignar={manejarReasignacion}
          onCerrar={() => setClienteReasignando(null)}
        />
      )}
    </div>
  );
};

const ModalReasignacion = ({ cliente, analistas, areas, onReasignar, onCerrar }) => {
  const [areaSeleccionada, setAreaSeleccionada] = useState('');
  const [analistaSeleccionado, setAnalistaSeleccionado] = useState('');

  const analistasDisponibles = analistas.filter(analista => 
    areaSeleccionada && analista.areas.some(area => area.nombre === areaSeleccionada)
  );

  const manejarSubmit = (e) => {
    e.preventDefault();
    onReasignar(cliente.id, analistaSeleccionado, areaSeleccionada);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-gray-800 p-6 rounded-lg max-w-md w-full mx-4">
        <h3 className="text-xl font-bold text-white mb-4">
          Reasignar Cliente: {cliente.nombre}
        </h3>
        
        <form onSubmit={manejarSubmit} className="space-y-4">
          <div>
            <label className="block text-white text-sm font-semibold mb-2">
              Área
            </label>
            <select
              value={areaSeleccionada}
              onChange={(e) => {
                setAreaSeleccionada(e.target.value);
                setAnalistaSeleccionado('');
              }}
              className="w-full p-2 rounded bg-gray-700 text-white"
              required
            >
              <option value="">Seleccionar área</option>
              {areas.map(area => (
                <option key={area.id} value={area.nombre}>{area.nombre}</option>
              ))}
            </select>
          </div>

          {areaSeleccionada && (
            <div>
              <label className="block text-white text-sm font-semibold mb-2">
                Analista
              </label>
              <select
                value={analistaSeleccionado}
                onChange={(e) => setAnalistaSeleccionado(e.target.value)}
                className="w-full p-2 rounded bg-gray-700 text-white"
                required
              >
                <option value="">Seleccionar analista</option>
                {analistasDisponibles.map(analista => (
                  <option key={analista.id} value={analista.id}>
                    {analista.nombre} {analista.apellido}
                  </option>
                ))}
              </select>
            </div>
          )}

          <div className="flex gap-4 pt-4">
            <button
              type="submit"
              disabled={!areaSeleccionada || !analistaSeleccionado}
              className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white py-2 rounded"
            >
              Reasignar
            </button>
            <button
              type="button"
              onClick={onCerrar}
              className="flex-1 bg-gray-600 hover:bg-gray-700 text-white py-2 rounded"
            >
              Cancelar
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default GestionClientesAvanzada;
