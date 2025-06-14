import { useState, useEffect } from 'react';
import { X, Check, AlertTriangle, Clock, FileText, Plus, Edit2, Trash2, Save, XCircle } from 'lucide-react';
import { 
  obtenerClasificacionesArchivo,
  registrarVistaClasificaciones,
  crearClasificacionArchivo,
  actualizarClasificacionArchivo,
  eliminarClasificacionArchivo
} from '../api/contabilidad';

const ModalClasificacionRegistrosRaw = ({ isOpen, onClose, uploadId, clienteId, onDataChanged }) => {
  const [registros, setRegistros] = useState([]);
  const [loading, setLoading] = useState(false);
  const [estadisticas, setEstadisticas] = useState({});
  const [filtro, setFiltro] = useState('todos'); // todos, procesados, pendientes, errores
  
  // Estados para CRUD
  const [editandoId, setEditandoId] = useState(null);
  const [registroEditando, setRegistroEditando] = useState(null);
  const [creandoNuevo, setCreandoNuevo] = useState(false);
  const [nuevoRegistro, setNuevoRegistro] = useState({
    numero_cuenta: '',
    clasificaciones: {}
  });

  useEffect(() => {
    if (isOpen && uploadId && clienteId) {
      // Registrar que se abrió el modal manualmente
      registrarVistaClasificaciones(clienteId, uploadId)
        .then(() => {
          // Después de registrar, cargar los datos
          cargarRegistros();
        })
        .catch((err) => {
          console.error("Error al registrar vista del modal:", err);
          // Aunque falle el registro, cargar los datos igual
          cargarRegistros();
        });
    }
  }, [isOpen, uploadId, clienteId]);

  const cargarRegistros = async () => {
    setLoading(true);
    try {
      const data = await obtenerClasificacionesArchivo(uploadId);
      setRegistros(data);
      calcularEstadisticas(data);
    } catch (error) {
      console.error("Error cargando registros:", error);
    } finally {
      setLoading(false);
    }
  };

  const calcularEstadisticas = (data) => {
    const total = data.length;
    const procesados = data.filter(r => r.procesado).length;
    const conErrores = data.filter(r => r.errores_mapeo && r.errores_mapeo.trim() !== '').length;
    const pendientes = total - procesados;
    
    setEstadisticas({ total, procesados, pendientes, conErrores });
  };

  // Funciones CRUD
  const handleIniciarEdicion = (registro) => {
    setEditandoId(registro.id);
    setRegistroEditando({
      numero_cuenta: registro.numero_cuenta,
      clasificaciones: { ...registro.clasificaciones }
    });
  };

  const handleCancelarEdicion = () => {
    setEditandoId(null);
    setRegistroEditando(null);
  };

  const handleGuardarEdicion = async () => {
    try {
      await actualizarClasificacionArchivo(editandoId, registroEditando);
      await cargarRegistros();
      setEditandoId(null);
      setRegistroEditando(null);
      if (onDataChanged) onDataChanged();
    } catch (error) {
      console.error("Error al actualizar registro:", error);
      alert("Error al actualizar el registro");
    }
  };

  const handleEliminar = async (id) => {
    if (window.confirm("¿Estás seguro de que quieres eliminar este registro?")) {
      try {
        await eliminarClasificacionArchivo(id);
        await cargarRegistros();
        if (onDataChanged) onDataChanged();
      } catch (error) {
        console.error("Error al eliminar registro:", error);
        alert("Error al eliminar el registro");
      }
    }
  };

  const handleIniciarCreacion = () => {
    // Obtener sets disponibles desde registros existentes
    const setsDisponibles = registros.length > 0 
      ? Object.keys(registros[0].clasificaciones)
      : [];
    
    const clasificacionesVacias = {};
    setsDisponibles.forEach(set => {
      clasificacionesVacias[set] = '';
    });

    setNuevoRegistro({
      numero_cuenta: '',
      clasificaciones: clasificacionesVacias
    });
    setCreandoNuevo(true);
  };

  const handleCancelarCreacion = () => {
    setCreandoNuevo(false);
    setNuevoRegistro({ numero_cuenta: '', clasificaciones: {} });
  };

  const handleGuardarNuevo = async () => {
    if (!nuevoRegistro.numero_cuenta.trim()) {
      alert("El número de cuenta es requerido");
      return;
    }

    try {
      await crearClasificacionArchivo({
        upload: uploadId,
        numero_cuenta: nuevoRegistro.numero_cuenta,
        clasificaciones: nuevoRegistro.clasificaciones,
        fila_excel: registros.length + 2 // Siguiente fila disponible
      });
      await cargarRegistros();
      handleCancelarCreacion();
      if (onDataChanged) onDataChanged();
    } catch (error) {
      console.error("Error al crear registro:", error);
      alert("Error al crear el registro");
    }
  };

  const handleCambioEdicion = (campo, valor) => {
    if (campo === 'numero_cuenta') {
      setRegistroEditando(prev => ({ ...prev, numero_cuenta: valor }));
    } else {
      setRegistroEditando(prev => ({
        ...prev,
        clasificaciones: { ...prev.clasificaciones, [campo]: valor }
      }));
    }
  };

  const handleCambioNuevo = (campo, valor) => {
    if (campo === 'numero_cuenta') {
      setNuevoRegistro(prev => ({ ...prev, numero_cuenta: valor }));
    } else {
      setNuevoRegistro(prev => ({
        ...prev,
        clasificaciones: { ...prev.clasificaciones, [campo]: valor }
      }));
    }
  };

  const registrosFiltrados = registros.filter(registro => {
    switch (filtro) {
      case 'procesados':
        return registro.procesado;
      case 'pendientes':
        return !registro.procesado && (!registro.errores_mapeo || registro.errores_mapeo.trim() === '');
      case 'errores':
        return registro.errores_mapeo && registro.errores_mapeo.trim() !== '';
      default:
        return true;
    }
  });

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-60 z-50 flex justify-center items-center">
      <div className="bg-gray-900 rounded-lg shadow-lg p-6 w-full max-w-6xl max-h-[90vh] relative flex flex-col">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-400 hover:text-white"
        >
          <X size={24} />
        </button>

        <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
          <FileText size={20} />
          Registros de Clasificación Raw
        </h2>

        {/* Estadísticas */}
        <div className="grid grid-cols-4 gap-4 mb-6">
          <div className="bg-gray-800 p-3 rounded-lg text-center">
            <div className="text-2xl font-bold text-blue-400">{estadisticas.total || 0}</div>
            <div className="text-sm text-gray-400">Total</div>
          </div>
          <div className="bg-gray-800 p-3 rounded-lg text-center">
            <div className="text-2xl font-bold text-green-400">{estadisticas.procesados || 0}</div>
            <div className="text-sm text-gray-400">Procesados</div>
          </div>
          <div className="bg-gray-800 p-3 rounded-lg text-center">
            <div className="text-2xl font-bold text-yellow-400">{estadisticas.pendientes || 0}</div>
            <div className="text-sm text-gray-400">Pendientes</div>
          </div>
          <div className="bg-gray-800 p-3 rounded-lg text-center">
            <div className="text-2xl font-bold text-red-400">{estadisticas.conErrores || 0}</div>
            <div className="text-sm text-gray-400">Con Errores</div>
          </div>
        </div>

        {/* Controles */}
        <div className="flex gap-2 mb-4">
          <select
            value={filtro}
            onChange={(e) => setFiltro(e.target.value)}
            className="bg-gray-800 text-white px-3 py-1 rounded border border-gray-600"
          >
            <option value="todos">Todos los registros</option>
            <option value="procesados">Solo procesados</option>
            <option value="pendientes">Solo pendientes</option>
            <option value="errores">Solo con errores</option>
          </select>
          
          <button
            onClick={handleIniciarCreacion}
            className="bg-green-600 hover:bg-green-500 px-3 py-1 rounded text-white font-medium transition shadow flex items-center gap-2"
          >
            <Plus size={16} />
            Nuevo
          </button>
        </div>

        {/* Tabla de registros */}
        <div className="flex-1 overflow-hidden">
          {loading ? (
            <div className="flex justify-center items-center h-32">
              <div className="animate-spin w-8 h-8 border-2 border-blue-400 border-t-transparent rounded-full"></div>
            </div>
          ) : (
            <div className="h-full overflow-auto border border-gray-600 rounded">
              <table className="w-full text-sm">
                <thead className="bg-gray-700 sticky top-0">
                  <tr>
                    <th className="px-3 py-2 text-left">Estado</th>
                    <th className="px-3 py-2 text-left">Fila Excel</th>
                    <th className="px-3 py-2 text-left">Número Cuenta</th>
                    <th className="px-3 py-2 text-left">Clasificaciones</th>
                    <th className="px-3 py-2 text-left">Cuenta Mapeada</th>
                    <th className="px-3 py-2 text-left">Errores</th>
                    <th className="px-3 py-2 text-left">Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  {/* Fila para crear nuevo registro */}
                  {creandoNuevo && (
                    <tr className="border-t border-gray-600 bg-green-900/20">
                      <td className="px-3 py-2">
                        <span className="text-green-400">Nuevo</span>
                      </td>
                      <td className="px-3 py-2 text-gray-400">-</td>
                      <td className="px-3 py-2">
                        <input
                          type="text"
                          value={nuevoRegistro.numero_cuenta}
                          onChange={(e) => handleCambioNuevo('numero_cuenta', e.target.value)}
                          className="w-full bg-gray-800 text-white px-2 py-1 rounded border border-gray-600"
                          placeholder="Número de cuenta"
                        />
                      </td>
                      <td className="px-3 py-2">
                        <div className="flex flex-wrap gap-1">
                          {Object.entries(nuevoRegistro.clasificaciones).map(([set, valor]) => (
                            <div key={set} className="flex items-center gap-1">
                              <span className="text-gray-300 text-xs">{set}:</span>
                              <input
                                type="text"
                                value={valor}
                                onChange={(e) => handleCambioNuevo(set, e.target.value)}
                                className="bg-gray-800 text-white px-1 py-1 rounded border border-gray-600 text-xs w-20"
                              />
                            </div>
                          ))}
                        </div>
                      </td>
                      <td className="px-3 py-2">-</td>
                      <td className="px-3 py-2">-</td>
                      <td className="px-3 py-2">
                        <div className="flex gap-1">
                          <button
                            onClick={handleGuardarNuevo}
                            className="p-1 text-green-400 hover:text-green-300"
                            title="Guardar"
                          >
                            <Save size={16} />
                          </button>
                          <button
                            onClick={handleCancelarCreacion}
                            className="p-1 text-red-400 hover:text-red-300"
                            title="Cancelar"
                          >
                            <XCircle size={16} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  )}
                  
                  {registrosFiltrados.map((registro) => (
                    <tr key={registro.id} className="border-t border-gray-600 hover:bg-gray-700/50">
                      <td className="px-3 py-2">
                        {registro.procesado ? (
                          <span className="flex items-center gap-1 text-green-400">
                            <Check size={16} />
                            Procesado
                          </span>
                        ) : registro.errores_mapeo && registro.errores_mapeo.trim() !== '' ? (
                          <span className="flex items-center gap-1 text-red-400">
                            <AlertTriangle size={16} />
                            Error
                          </span>
                        ) : (
                          <span className="flex items-center gap-1 text-yellow-400">
                            <Clock size={16} />
                            Pendiente
                          </span>
                        )}
                      </td>
                      <td className="px-3 py-2 text-gray-400">{registro.fila_excel}</td>
                      <td className="px-3 py-2">
                        {editandoId === registro.id ? (
                          <input
                            type="text"
                            value={registroEditando.numero_cuenta}
                            onChange={(e) => handleCambioEdicion('numero_cuenta', e.target.value)}
                            className="w-full bg-gray-800 text-white px-2 py-1 rounded border border-gray-600 font-mono"
                          />
                        ) : (
                          <span className="font-mono text-blue-300">{registro.numero_cuenta}</span>
                        )}
                      </td>
                      <td className="px-3 py-2">
                        {editandoId === registro.id ? (
                          <div className="flex flex-wrap gap-1">
                            {Object.entries(registroEditando.clasificaciones).map(([set, valor]) => (
                              <div key={set} className="flex items-center gap-1">
                                <span className="text-gray-300 text-xs">{set}:</span>
                                <input
                                  type="text"
                                  value={valor}
                                  onChange={(e) => handleCambioEdicion(set, e.target.value)}
                                  className="bg-gray-800 text-white px-1 py-1 rounded border border-gray-600 text-xs w-20"
                                />
                              </div>
                            ))}
                          </div>
                        ) : (
                          <div className="flex flex-wrap gap-1">
                            {Object.entries(registro.clasificaciones).map(([set, valor]) => (
                              <span key={set} className="inline-block bg-blue-900/50 px-2 py-1 rounded text-xs">
                                <span className="text-gray-300">{set}:</span> <span className="text-white">{valor}</span>
                              </span>
                            ))}
                          </div>
                        )}
                      </td>
                      <td className="px-3 py-2">
                        {registro.cuenta_mapeada ? (
                          <span className="text-green-300">✓ Mapeada</span>
                        ) : (
                          <span className="text-gray-500">-</span>
                        )}
                      </td>
                      <td className="px-3 py-2">
                        {registro.errores_mapeo && registro.errores_mapeo.trim() !== '' ? (
                          <span className="text-red-400 text-xs">{registro.errores_mapeo}</span>
                        ) : (
                          <span className="text-gray-500">-</span>
                        )}
                      </td>
                      <td className="px-3 py-2">
                        {editandoId === registro.id ? (
                          <div className="flex gap-1">
                            <button
                              onClick={handleGuardarEdicion}
                              className="p-1 text-green-400 hover:text-green-300"
                              title="Guardar"
                            >
                              <Save size={16} />
                            </button>
                            <button
                              onClick={handleCancelarEdicion}
                              className="p-1 text-red-400 hover:text-red-300"
                              title="Cancelar"
                            >
                              <XCircle size={16} />
                            </button>
                          </div>
                        ) : (
                          <div className="flex gap-1">
                            <button
                              onClick={() => handleIniciarEdicion(registro)}
                              className="p-1 text-blue-400 hover:text-blue-300"
                              title="Editar"
                            >
                              <Edit2 size={16} />
                            </button>
                            <button
                              onClick={() => handleEliminar(registro.id)}
                              className="p-1 text-red-400 hover:text-red-300"
                              title="Eliminar"
                            >
                              <Trash2 size={16} />
                            </button>
                          </div>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              
              {registrosFiltrados.length === 0 && (
                <div className="text-center text-gray-400 py-8">
                  No hay registros que coincidan con el filtro seleccionado
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="mt-4 flex justify-between items-center text-sm text-gray-400">
          <span>Mostrando {registrosFiltrados.length} de {registros.length} registros</span>
          <button
            onClick={onClose}
            className="bg-gray-700 hover:bg-gray-600 px-4 py-2 rounded text-white transition"
          >
            Cerrar
          </button>
        </div>
      </div>
    </div>
  );
};

export default ModalClasificacionRegistrosRaw;
