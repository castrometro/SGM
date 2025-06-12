import { useState, useEffect } from 'react';
import { obtenerAnalistasDetallado, actualizarAnalista } from '../../api/analistas';
import { obtenerAreas } from '../../api/areas';

const GestionAnalistas = () => {
  const [analistas, setAnalistas] = useState([]);
  const [areas, setAreas] = useState([]);
  const [analistaEditando, setAnalistaEditando] = useState(null);
  const [mostrarFormulario, setMostrarFormulario] = useState(false);

  useEffect(() => {
    cargarDatos();
  }, []);

  const cargarDatos = async () => {
    try {
      const [analistasData, areasData] = await Promise.all([
        obtenerAnalistasDetallado(),
        obtenerAreas()
      ]);
      setAnalistas(analistasData);
      setAreas(areasData);
    } catch (error) {
      console.error('Error cargando datos:', error);
    }
  };

  const manejarEdicion = (analista) => {
    setAnalistaEditando(analista);
    setMostrarFormulario(true);
  };

  const guardarCambios = async (datosAnalista) => {
    try {
      await actualizarAnalista(analistaEditando.id, datosAnalista);
      await cargarDatos(); // Recargar datos
      setMostrarFormulario(false);
      setAnalistaEditando(null);
    } catch (error) {
      console.error('Error guardando cambios:', error);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-white">Gestión de Analistas</h2>
        <button
          onClick={() => setMostrarFormulario(true)}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg"
        >
          + Nuevo Analista
        </button>
      </div>

      {/* Tabla de Analistas */}
      <div className="bg-gray-800 rounded-lg overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-700">
            <tr>
              <th className="p-4 text-left text-white">Analista</th>
              <th className="p-4 text-left text-white">Áreas</th>
              <th className="p-4 text-center text-white">Clientes Asignados</th>
              <th className="p-4 text-center text-white">Productividad</th>
              <th className="p-4 text-center text-white">Estado</th>
              <th className="p-4 text-center text-white">Acciones</th>
            </tr>
          </thead>
          <tbody>
            {analistas.map((analista) => (
              <tr key={analista.id} className="border-b border-gray-700">
                <td className="p-4 text-white">
                  <div>
                    <div className="font-semibold">{analista.nombre} {analista.apellido}</div>
                    <div className="text-sm text-gray-400">{analista.correo_bdo}</div>
                  </div>
                </td>
                <td className="p-4">
                  <div className="flex flex-wrap gap-1">
                    {analista.areas.map((area) => (
                      <span
                        key={area.id}
                        className="px-2 py-1 bg-blue-600 text-white text-xs rounded"
                      >
                        {area.nombre}
                      </span>
                    ))}
                  </div>
                </td>
                <td className="p-4 text-center text-white">
                  {analista.clientes_asignados || 0}
                </td>
                <td className="p-4 text-center">
                  <span className={`px-2 py-1 rounded text-xs ${
                    analista.eficiencia >= 80 
                      ? 'bg-green-600 text-white' 
                      : analista.eficiencia >= 60 
                        ? 'bg-yellow-600 text-white'
                        : 'bg-red-600 text-white'
                  }`}>
                    {analista.eficiencia}%
                  </span>
                </td>
                <td className="p-4 text-center">
                  <span className={`px-2 py-1 rounded text-xs ${
                    analista.is_active 
                      ? 'bg-green-600 text-white' 
                      : 'bg-red-600 text-white'
                  }`}>
                    {analista.is_active ? 'Activo' : 'Inactivo'}
                  </span>
                </td>
                <td className="p-4 text-center">
                  <div className="flex gap-2 justify-center">
                    <button
                      onClick={() => manejarEdicion(analista)}
                      className="bg-yellow-600 hover:bg-yellow-700 text-white px-3 py-1 rounded text-sm"
                    >
                      Editar
                    </button>
                    <button
                      onClick={() => window.location.href = `/analistas/${analista.id}/detalle`}
                      className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-sm"
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

      {/* Modal de Edición */}
      {mostrarFormulario && (
        <FormularioAnalista
          analista={analistaEditando}
          areas={areas}
          onGuardar={guardarCambios}
          onCancelar={() => {
            setMostrarFormulario(false);
            setAnalistaEditando(null);
          }}
        />
      )}
    </div>
  );
};

const FormularioAnalista = ({ analista, areas, onGuardar, onCancelar }) => {
  const [formData, setFormData] = useState({
    nombre: analista?.nombre || '',
    apellido: analista?.apellido || '',
    correo_bdo: analista?.correo_bdo || '',
    areas: analista?.areas?.map(a => a.id) || [],
    is_active: analista?.is_active ?? true
  });

  const manejarSubmit = (e) => {
    e.preventDefault();
    onGuardar(formData);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-gray-800 p-6 rounded-lg max-w-md w-full mx-4">
        <h3 className="text-xl font-bold text-white mb-4">
          {analista ? 'Editar Analista' : 'Nuevo Analista'}
        </h3>
        
        <form onSubmit={manejarSubmit} className="space-y-4">
          <div>
            <label className="block text-white text-sm font-semibold mb-2">
              Nombre
            </label>
            <input
              type="text"
              value={formData.nombre}
              onChange={(e) => setFormData({...formData, nombre: e.target.value})}
              className="w-full p-2 rounded bg-gray-700 text-white"
              required
            />
          </div>

          <div>
            <label className="block text-white text-sm font-semibold mb-2">
              Apellido
            </label>
            <input
              type="text"
              value={formData.apellido}
              onChange={(e) => setFormData({...formData, apellido: e.target.value})}
              className="w-full p-2 rounded bg-gray-700 text-white"
              required
            />
          </div>

          <div>
            <label className="block text-white text-sm font-semibold mb-2">
              Email BDO
            </label>
            <input
              type="email"
              value={formData.correo_bdo}
              onChange={(e) => setFormData({...formData, correo_bdo: e.target.value})}
              className="w-full p-2 rounded bg-gray-700 text-white"
              required
            />
          </div>

          <div>
            <label className="block text-white text-sm font-semibold mb-2">
              Áreas
            </label>
            <div className="space-y-2">
              {areas.map((area) => (
                <label key={area.id} className="flex items-center text-white">
                  <input
                    type="checkbox"
                    checked={formData.areas.includes(area.id)}
                    onChange={(e) => {
                      const nuevasAreas = e.target.checked
                        ? [...formData.areas, area.id]
                        : formData.areas.filter(id => id !== area.id);
                      setFormData({...formData, areas: nuevasAreas});
                    }}
                    className="mr-2"
                  />
                  {area.nombre}
                </label>
              ))}
            </div>
          </div>

          <div>
            <label className="flex items-center text-white">
              <input
                type="checkbox"
                checked={formData.is_active}
                onChange={(e) => setFormData({...formData, is_active: e.target.checked})}
                className="mr-2"
              />
              Activo
            </label>
          </div>

          <div className="flex gap-4 pt-4">
            <button
              type="submit"
              className="flex-1 bg-blue-600 hover:bg-blue-700 text-white py-2 rounded"
            >
              Guardar
            </button>
            <button
              type="button"
              onClick={onCancelar}
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

export default GestionAnalistas;
