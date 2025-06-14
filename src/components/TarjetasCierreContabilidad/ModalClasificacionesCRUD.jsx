import { useState, useEffect } from 'react';
import { X, Edit, Trash2, Plus } from 'lucide-react';
import { 
  obtenerClasificacionesCuenta, 
  crearClasificacionCuenta, 
  actualizarClasificacionCuenta, 
  eliminarClasificacionCuenta,
  obtenerClasificacionCompleta
} from '../../api/contabilidad';
import { obtenerCuentasCliente } from '../../api/contabilidad';

const ModalClasificacionesCRUD = ({ isOpen, onClose, clienteId, onUpdate }) => {
  const [clasificaciones, setClasificaciones] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [editando, setEditando] = useState(null);
  const [creando, setCreando] = useState(false);
  const [formData, setFormData] = useState({
    cuenta: '',
    set_clas: '',
    opcion: ''
  });

  // Datos para los selects
  const [cuentas, setCuentas] = useState([]);
  const [setsClasificacion, setSetsClasificacion] = useState([]);
  const [opcionesDisponibles, setOpcionesDisponibles] = useState([]);

  useEffect(() => {
    if (isOpen && clienteId) {
      cargarDatos();
      cargarClasificaciones();
    }
  }, [isOpen, clienteId]);

  const cargarDatos = async () => {
    try {
      setLoading(true);
      
      // Cargar cuentas del cliente
      const cuentasData = await obtenerCuentasCliente(clienteId);
      setCuentas(cuentasData);
      
      // Cargar sets de clasificación completos
      const clasificacionCompleta = await obtenerClasificacionCompleta(clienteId);
      setSetsClasificacion(clasificacionCompleta);
      
    } catch (err) {
      console.error('Error cargando datos:', err);
      setError('Error al cargar los datos necesarios');
    } finally {
      setLoading(false);
    }
  };

  const cargarClasificaciones = async () => {
    try {
      const data = await obtenerClasificacionesCuenta(clienteId);
      setClasificaciones(data);
    } catch (err) {
      console.error('Error cargando clasificaciones:', err);
      setError('Error al cargar las clasificaciones');
    }
  };

  const handleSetChange = (setId) => {
    setFormData(prev => ({ ...prev, set_clas: setId, opcion: '' }));
    
    // Actualizar opciones disponibles
    const setSeleccionado = setsClasificacion.find(s => s.id === parseInt(setId));
    setOpcionesDisponibles(setSeleccionado?.opciones || []);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    try {
      if (editando) {
        await actualizarClasificacionCuenta(editando.id, formData);
      } else {
        await crearClasificacionCuenta(formData);
      }
      
      await cargarClasificaciones();
      handleCancelar();
      if (onUpdate) onUpdate();
    } catch (err) {
      console.error('Error al guardar:', err);
      setError(err.response?.data?.detail || 'Error al guardar la clasificación');
    }
  };

  const handleEditar = (clasificacion) => {
    setEditando(clasificacion);
    setFormData({
      cuenta: clasificacion.cuenta,
      set_clas: clasificacion.set_clas,
      opcion: clasificacion.opcion
    });
    
    // Cargar opciones del set seleccionado
    const setSeleccionado = setsClasificacion.find(s => s.id === clasificacion.set_clas);
    setOpcionesDisponibles(setSeleccionado?.opciones || []);
    setCreando(true);
  };

  const handleEliminar = async (id) => {
    if (!confirm('¿Está seguro de eliminar esta clasificación?')) return;
    
    try {
      await eliminarClasificacionCuenta(id);
      await cargarClasificaciones();
      if (onUpdate) onUpdate();
    } catch (err) {
      console.error('Error al eliminar:', err);
      setError('Error al eliminar la clasificación');
    }
  };

  const handleCancelar = () => {
    setEditando(null);
    setCreando(false);
    setFormData({ cuenta: '', set_clas: '', opcion: '' });
    setOpcionesDisponibles([]);
    setError('');
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-gray-800 rounded-lg p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold text-white">
            Clasificaciones de Cuentas
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white"
          >
            <X size={24} />
          </button>
        </div>

        {error && (
          <div className="bg-red-600 text-white p-3 rounded mb-4">
            {error}
          </div>
        )}

        {/* Botón para crear nueva clasificación */}
        {!creando && (
          <button
            onClick={() => setCreando(true)}
            className="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded mb-4 flex items-center gap-2"
          >
            <Plus size={16} />
            Nueva Clasificación
          </button>
        )}

        {/* Formulario de creación/edición */}
        {creando && (
          <form onSubmit={handleSubmit} className="bg-gray-700 p-4 rounded mb-4">
            <h3 className="text-white mb-3">
              {editando ? 'Editar Clasificación' : 'Nueva Clasificación'}
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Select de Cuenta */}
              <div>
                <label className="block text-white text-sm mb-1">Cuenta</label>
                <select
                  value={formData.cuenta}
                  onChange={(e) => setFormData(prev => ({ ...prev, cuenta: e.target.value }))}
                  className="w-full p-2 bg-gray-600 text-white rounded"
                  required
                >
                  <option value="">Seleccionar cuenta...</option>
                  {cuentas.map(cuenta => (
                    <option key={cuenta.id} value={cuenta.id}>
                      {cuenta.codigo} - {cuenta.nombre}
                    </option>
                  ))}
                </select>
              </div>

              {/* Select de Set de Clasificación */}
              <div>
                <label className="block text-white text-sm mb-1">Set de Clasificación</label>
                <select
                  value={formData.set_clas}
                  onChange={(e) => handleSetChange(e.target.value)}
                  className="w-full p-2 bg-gray-600 text-white rounded"
                  required
                >
                  <option value="">Seleccionar set...</option>
                  {setsClasificacion.map(set => (
                    <option key={set.id} value={set.id}>
                      {set.nombre}
                    </option>
                  ))}
                </select>
              </div>

              {/* Select de Opción */}
              <div>
                <label className="block text-white text-sm mb-1">Opción</label>
                <select
                  value={formData.opcion}
                  onChange={(e) => setFormData(prev => ({ ...prev, opcion: e.target.value }))}
                  className="w-full p-2 bg-gray-600 text-white rounded"
                  required
                  disabled={!formData.set_clas}
                >
                  <option value="">Seleccionar opción...</option>
                  {opcionesDisponibles.map(opcion => (
                    <option key={opcion.id} value={opcion.id}>
                      {opcion.valor} - {opcion.descripcion}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="flex gap-2 mt-4">
              <button
                type="submit"
                className="bg-green-600 hover:bg-green-500 text-white px-4 py-2 rounded"
              >
                {editando ? 'Actualizar' : 'Crear'}
              </button>
              <button
                type="button"
                onClick={handleCancelar}
                className="bg-gray-600 hover:bg-gray-500 text-white px-4 py-2 rounded"
              >
                Cancelar
              </button>
            </div>
          </form>
        )}

        {/* Lista de clasificaciones */}
        {loading ? (
          <div className="text-center text-white py-4">Cargando...</div>
        ) : (
          <div className="space-y-2">
            <h3 className="text-white font-semibold mb-2">
              Clasificaciones Existentes ({clasificaciones.length})
            </h3>
            
            {clasificaciones.length === 0 ? (
              <div className="text-gray-400 text-center py-4">
                No hay clasificaciones registradas
              </div>
            ) : (
              <div className="max-h-96 overflow-y-auto">
                {clasificaciones.map(clasificacion => (
                  <div key={clasificacion.id} className="bg-gray-700 p-3 rounded flex justify-between items-center">
                    <div className="text-white">
                      <div className="font-medium">
                        {clasificacion.cuenta_codigo} - {clasificacion.cuenta_nombre}
                      </div>
                      <div className="text-sm text-gray-300">
                        {clasificacion.set_nombre}: {clasificacion.opcion_valor}
                        {clasificacion.opcion_descripcion && ` - ${clasificacion.opcion_descripcion}`}
                      </div>
                      <div className="text-xs text-gray-400">
                        Asignado: {new Date(clasificacion.fecha).toLocaleDateString()}
                        {clasificacion.asignado_por_nombre && ` por ${clasificacion.asignado_por_nombre}`}
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleEditar(clasificacion)}
                        className="text-blue-400 hover:text-blue-300"
                        title="Editar"
                      >
                        <Edit size={16} />
                      </button>
                      <button
                        onClick={() => handleEliminar(clasificacion.id)}
                        className="text-red-400 hover:text-red-300"
                        title="Eliminar"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default ModalClasificacionesCRUD;
