import { useState, useEffect } from 'react';
import { X, Check, AlertTriangle, Clock, FileText, Plus, Edit2, Trash2, Save, XCircle, Settings, Database, FolderPlus } from 'lucide-react';
import { 
  obtenerClasificacionesArchivo,
  registrarVistaClasificaciones,
  registrarVistaSetsClasificacion,
  crearClasificacionArchivo,
  actualizarClasificacionArchivo,
  eliminarClasificacionArchivo,
  obtenerSetsCliente,
  crearSet,
  actualizarSet,
  eliminarSet,
  obtenerOpcionesSet,
  crearOpcion,
  actualizarOpcion,
  eliminarOpcion
} from '../api/contabilidad';

const ModalClasificacionRegistrosRaw = ({ isOpen, onClose, uploadId, clienteId, onDataChanged }) => {
  const [registros, setRegistros] = useState([]);
  const [loading, setLoading] = useState(false);
  const [estadisticas, setEstadisticas] = useState({});
  
  // Estados para navegación de pestañas
  const [pestanaActiva, setPestanaActiva] = useState('registros'); // 'registros' | 'sets'
  
  // Estados para CRUD de registros
  const [editandoId, setEditandoId] = useState(null);
  const [registroEditando, setRegistroEditando] = useState(null);
  const [creandoNuevo, setCreandoNuevo] = useState(false);
  const [nuevoRegistro, setNuevoRegistro] = useState({
    numero_cuenta: '',
    clasificaciones: {}
  });
  
  // Estados para selección de sets y opciones en creación/edición
  const [setSeleccionado, setSetSeleccionado] = useState('');
  const [opcionSeleccionada, setOpcionSeleccionada] = useState('');

  // Estados para gestión de sets y opciones
  const [sets, setSets] = useState([]);
  const [loadingSets, setLoadingSets] = useState(false);
  const [editandoSet, setEditandoSet] = useState(null);
  const [creandoSet, setCreandoSet] = useState(false);
  const [nuevoSet, setNuevoSet] = useState('');
  const [setEditando, setSetEditando] = useState('');
  
  // Estados para opciones
  const [opcionesPorSet, setOpcionesPorSet] = useState({});
  const [editandoOpcion, setEditandoOpcion] = useState(null);
  const [creandoOpcionPara, setCreandoOpcionPara] = useState(null);
  const [nuevaOpcion, setNuevaOpcion] = useState('');
  const [opcionEditando, setOpcionEditando] = useState('');

  useEffect(() => {
    if (isOpen && uploadId && clienteId) {
      // Registrar que se abrió el modal manualmente
      registrarVistaClasificaciones(clienteId, uploadId)
        .then(() => {
          // Después de registrar, cargar los datos
          cargarRegistros();
          // Cargar sets también
          cargarSets();
        })
        .catch((err) => {
          console.error("Error al registrar vista del modal:", err);
          // Aunque falle el registro, cargar los datos igual
          cargarRegistros();
          cargarSets();
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

  const cargarSets = async () => {
    setLoadingSets(true);
    try {
      const setsData = await obtenerSetsCliente(clienteId);
      console.log("Sets obtenidos del servidor:", setsData);
      setSets(setsData);
      
      // Cargar opciones para cada set
      const opcionesPromises = setsData.map(async (set) => {
        try {
          const opciones = await obtenerOpcionesSet(set.id);
          console.log(`Opciones para set ${set.id} (${set.nombre}):`, opciones);
          return { setId: set.id, opciones };
        } catch (error) {
          console.error(`Error cargando opciones para set ${set.id}:`, error);
          return { setId: set.id, opciones: [] };
        }
      });
      
      const opcionesResults = await Promise.all(opcionesPromises);
      const opcionesPorSetObj = {};
      opcionesResults.forEach(({ setId, opciones }) => {
        opcionesPorSetObj[setId] = opciones;
      });
      console.log("Objeto final de opciones por set:", opcionesPorSetObj);
      setOpcionesPorSet(opcionesPorSetObj);
      
    } catch (error) {
      console.error("Error cargando sets:", error);
      setSets([]);
    } finally {
      setLoadingSets(false);
    }
  };

  const calcularEstadisticas = (data) => {
    const total = data.length;
    // Eliminar estadísticas de procesado ya que esa etapa es más adelante
    setEstadisticas({ total });
  };

  // ==================== FUNCIONES AUXILIARES PARA SETS/OPCIONES ====================
  const obtenerSetsDisponibles = () => {
    return sets || [];
  };

  const obtenerOpcionesParaSet = (setId) => {
    if (!setId || !opcionesPorSet || !opcionesPorSet[setId]) {
      console.log(`No se encontraron opciones para setId: ${setId}`, { opcionesPorSet, setId });
      return [];
    }
    console.log(`Opciones para setId ${setId}:`, opcionesPorSet[setId]);
    return opcionesPorSet[setId] || [];
  };

  const agregarClasificacionARegistro = () => {
    if (!setSeleccionado || !opcionSeleccionada) {
      alert("Debe seleccionar un set y una opción");
      return;
    }

    const setEncontrado = sets.find(s => s.id === parseInt(setSeleccionado));
    if (!setEncontrado) return;

    if (creandoNuevo) {
      setNuevoRegistro(prev => ({
        ...prev,
        clasificaciones: {
          ...prev.clasificaciones,
          [setEncontrado.nombre]: opcionSeleccionada
        }
      }));
    } else if (editandoId) {
      setRegistroEditando(prev => ({
        ...prev,
        clasificaciones: {
          ...prev.clasificaciones,
          [setEncontrado.nombre]: opcionSeleccionada
        }
      }));
    }

    // Limpiar selección
    setSetSeleccionado('');
    setOpcionSeleccionada('');
  };

  const eliminarClasificacionDeRegistro = (setNombre) => {
    if (creandoNuevo) {
      setNuevoRegistro(prev => {
        const nuevasClasificaciones = { ...prev.clasificaciones };
        delete nuevasClasificaciones[setNombre];
        return { ...prev, clasificaciones: nuevasClasificaciones };
      });
    } else if (editandoId) {
      setRegistroEditando(prev => {
        const nuevasClasificaciones = { ...prev.clasificaciones };
        delete nuevasClasificaciones[setNombre];
        return { ...prev, clasificaciones: nuevasClasificaciones };
      });
    }
  };

  const manejarCambioPestana = async (nuevaPestana) => {
    // Si ya está en esa pestaña, no hacer nada
    if (pestanaActiva === nuevaPestana) return;
    
    // Si va a la pestaña de sets, registrar el acceso
    if (nuevaPestana === 'sets') {
      try {
        await registrarVistaSetsClasificacion(clienteId);
      } catch (error) {
        console.error("Error al registrar vista de sets:", error);
        // Continuar aunque falle el registro
      }
    }
    
    setPestanaActiva(nuevaPestana);
  };

  // ==================== FUNCIONES CRUD PARA SETS ====================
  const handleCrearSet = async () => {
    if (!nuevoSet.trim()) {
      alert("El nombre del set es requerido");
      return;
    }
    try {
      console.log("Creando nuevo set:", nuevoSet.trim());
      const resultado = await crearSet(clienteId, nuevoSet.trim());
      console.log("Set creado exitosamente:", resultado);
      setNuevoSet('');
      setCreandoSet(false);
      console.log("Recargando sets...");
      await cargarSets();
      console.log("Sets recargados exitosamente");
    } catch (error) {
      console.error("Error creando set:", error);
      alert("Error al crear el set");
    }
  };

  const handleEditarSet = async () => {
    if (!setEditando.trim()) {
      alert("El nombre del set es requerido");
      return;
    }
    try {
      await actualizarSet(editandoSet, setEditando.trim());
      setEditandoSet(null);
      setSetEditando('');
      await cargarSets();
    } catch (error) {
      console.error("Error editando set:", error);
      alert("Error al editar el set");
    }
  };

  const handleEliminarSet = async (setId) => {
    if (window.confirm("¿Estás seguro de eliminar este set? Se eliminarán también todas sus opciones.")) {
      try {
        await eliminarSet(setId);
        await cargarSets();
      } catch (error) {
        console.error("Error eliminando set:", error);
        alert("Error al eliminar el set");
      }
    }
  };

  // ==================== FUNCIONES CRUD PARA OPCIONES ====================
  const handleCrearOpcion = async (setId) => {
    if (!nuevaOpcion.trim()) {
      alert("El valor de la opción es requerido");
      return;
    }
    try {
      await crearOpcion(setId, nuevaOpcion.trim());
      setNuevaOpcion('');
      setCreandoOpcionPara(null);
      await cargarSets(); // Recargar para actualizar opciones
    } catch (error) {
      console.error("Error creando opción:", error);
      alert("Error al crear la opción");
    }
  };

  const handleEditarOpcion = async (opcionId) => {
    if (!opcionEditando.trim()) {
      alert("El valor de la opción es requerido");
      return;
    }
    try {
      await actualizarOpcion(opcionId, opcionEditando.trim());
      setEditandoOpcion(null);
      setOpcionEditando('');
      await cargarSets();
    } catch (error) {
      console.error("Error editando opción:", error);
      alert("Error al editar la opción");
    }
  };

  const handleEliminarOpcion = async (opcionId) => {
    if (window.confirm("¿Estás seguro de eliminar esta opción?")) {
      try {
        await eliminarOpcion(opcionId);
        await cargarSets();
      } catch (error) {
        console.error("Error eliminando opción:", error);
        alert("Error al eliminar la opción");
      }
    }
  };

  // ==================== FUNCIONES CRUD PARA REGISTROS ====================
  const handleIniciarCreacion = () => {
    setNuevoRegistro({
      numero_cuenta: '',
      clasificaciones: {}
    });
    setCreandoNuevo(true);
    // Limpiar selecciones
    setSetSeleccionado('');
    setOpcionSeleccionada('');
  };

  const handleCancelarCreacion = () => {
    setCreandoNuevo(false);
    setNuevoRegistro({ numero_cuenta: '', clasificaciones: {} });
    // Limpiar selecciones
    setSetSeleccionado('');
    setOpcionSeleccionada('');
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

  const handleIniciarEdicion = (registro) => {
    setEditandoId(registro.id);
    setRegistroEditando({
      numero_cuenta: registro.numero_cuenta,
      clasificaciones: { ...registro.clasificaciones }
    });
    // Limpiar selecciones
    setSetSeleccionado('');
    setOpcionSeleccionada('');
  };

  const handleCancelarEdicion = () => {
    setEditandoId(null);
    setRegistroEditando(null);
    // Limpiar selecciones
    setSetSeleccionado('');
    setOpcionSeleccionada('');
  };

  const handleGuardarEdicion = async () => {
    try {
      await actualizarClasificacionArchivo(editandoId, registroEditando);
      await cargarRegistros();
      setEditandoId(null);
      setRegistroEditando(null);
      if (onDataChanged) onDataChanged();
    } catch (error) {
      console.error("Error al editar registro:", error);
      alert("Error al editar el registro");
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

  const registrosFiltrados = registros || []; // Mostrar todos los registros sin filtrar por procesado

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
          <Database size={20} />
          Gestión de Clasificaciones
        </h2>

        {/* Pestañas de navegación */}
        <div className="flex space-x-4 mb-6 border-b border-gray-600">
          <button
            onClick={() => manejarCambioPestana('registros')}
            className={`pb-2 px-1 text-sm font-medium transition ${
              pestanaActiva === 'registros'
                ? 'text-blue-400 border-b-2 border-blue-400'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            <FileText className="inline mr-1" size={16} />
            Registros Raw ({estadisticas.total || 0})
          </button>
          <button
            onClick={() => manejarCambioPestana('sets')}
            className={`pb-2 px-1 text-sm font-medium transition ${
              pestanaActiva === 'sets'
                ? 'text-blue-400 border-b-2 border-blue-400'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            <Settings className="inline mr-1" size={16} />
            Sets y Opciones ({sets.length})
          </button>
        </div>

        {/* Contenido de la pestaña Registros */}
        {pestanaActiva === 'registros' && (
          <>
            {/* Estadísticas simplificadas */}
            <div className="grid grid-cols-1 gap-4 mb-6">
              <div className="bg-gray-800 p-3 rounded-lg text-center">
                <div className="text-2xl font-bold text-blue-400">{estadisticas.total || 0}</div>
                <div className="text-sm text-gray-400">Total de Registros</div>
              </div>
            </div>

        {/* Controles */}
        <div className="flex gap-2 mb-4">
          <button
            onClick={handleIniciarCreacion}
            className="bg-green-600 hover:bg-green-500 px-3 py-1 rounded text-white font-medium transition shadow flex items-center gap-2"
          >
            <Plus size={16} />
            Nuevo Registro
          </button>
        </div>

        {/* Tabla de registros con scroll mejorado */}
        <div className="flex-1 overflow-hidden">
          {loading ? (
            <div className="flex justify-center items-center h-32">
              <div className="animate-spin w-8 h-8 border-2 border-blue-400 border-t-transparent rounded-full"></div>
            </div>
          ) : (
            <div className="h-full overflow-auto border border-gray-600 rounded" style={{ maxHeight: '400px' }}>
              <table className="w-full text-sm">
                <thead className="bg-gray-700 sticky top-0 z-10">
                  <tr>
                    <th className="px-3 py-2 text-left">Fila Excel</th>
                    <th className="px-3 py-2 text-left">Número Cuenta</th>
                    <th className="px-3 py-2 text-left">Clasificaciones</th>
                    <th className="px-3 py-2 text-left">Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  {/* Fila para crear nuevo registro */}
                  {creandoNuevo && (
                    <tr className="border-t border-gray-600 bg-green-900/20">
                      <td className="px-3 py-2 text-gray-400">Nuevo</td>
                      <td className="px-3 py-2">
                        <input
                          type="text"
                          value={nuevoRegistro.numero_cuenta}
                          onChange={(e) => setNuevoRegistro(prev => ({ ...prev, numero_cuenta: e.target.value }))}
                          className="w-full bg-gray-800 text-white px-2 py-1 rounded border border-gray-600 focus:border-blue-500 focus:outline-none"
                          placeholder="Ingrese el número de cuenta..."
                          autoFocus
                        />
                      </td>
                      <td className="px-3 py-2">
                        {/* Clasificaciones actuales */}
                        {Object.keys(nuevoRegistro.clasificaciones || {}).length > 0 && (
                          <div className="mb-3">
                            <div className="text-xs text-gray-400 mb-1">Clasificaciones agregadas:</div>
                            <div className="flex flex-wrap gap-1">
                              {Object.entries(nuevoRegistro.clasificaciones || {}).map(([set, valor]) => (
                                <div key={set} className="flex items-center gap-1 bg-blue-900/50 px-2 py-1 rounded text-xs border border-blue-700/50">
                                  <span className="text-blue-300 font-medium">{set}:</span>
                                  <span className="text-white">{valor}</span>
                                  <button
                                    onClick={() => eliminarClasificacionDeRegistro(set)}
                                    className="text-red-400 hover:text-red-300 ml-1 hover:bg-red-900/30 rounded p-0.5 transition"
                                    title="Eliminar clasificación"
                                  >
                                    <XCircle size={12} />
                                  </button>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                        
                        {/* Selector de nueva clasificación */}
                        <div className="border-t border-gray-600 pt-2">
                          <div className="text-xs text-gray-400 mb-2">Agregar nueva clasificación:</div>
                          {obtenerSetsDisponibles().length === 0 ? (
                            <div className="text-xs text-yellow-400 bg-yellow-900/20 p-2 rounded border border-yellow-700/50">
                              ⚠️ No hay sets disponibles. Ve a la pestaña "Sets y Opciones" para crear sets primero.
                            </div>
                          ) : (
                            <div className="flex gap-2 items-center flex-wrap">
                              <select
                                value={setSeleccionado}
                                onChange={(e) => {
                                  console.log(`Set seleccionado cambiado a: ${e.target.value}`);
                                  setSetSeleccionado(e.target.value);
                                  setOpcionSeleccionada(''); // Reset opción cuando cambia set
                                  console.log(`Opciones disponibles para este set:`, obtenerOpcionesParaSet(e.target.value));
                                }}
                                className="bg-gray-800 text-white px-2 py-1 rounded border border-gray-600 text-xs focus:border-blue-500 focus:outline-none"
                              >
                                <option value="">🏷️ Seleccionar Set...</option>
                                {obtenerSetsDisponibles().map(set => (
                                  <option key={set.id} value={set.id}>{set.nombre}</option>
                                ))}
                              </select>
                              
                              {setSeleccionado && (
                                <>
                                  {obtenerOpcionesParaSet(setSeleccionado).length === 0 ? (
                                    <div className="text-xs text-yellow-400">⚠️ Este set no tiene opciones</div>
                                  ) : (
                                    <select
                                      value={opcionSeleccionada}
                                      onChange={(e) => setOpcionSeleccionada(e.target.value)}
                                      className="bg-gray-800 text-white px-2 py-1 rounded border border-gray-600 text-xs focus:border-blue-500 focus:outline-none"
                                    >
                                      <option value="">📋 Seleccionar Opción...</option>
                                      {obtenerOpcionesParaSet(setSeleccionado).map(opcion => (
                                        <option key={opcion.id} value={opcion.valor}>{opcion.valor}</option>
                                      ))}
                                    </select>
                                  )}
                                </>
                              )}
                              
                              {setSeleccionado && opcionSeleccionada && (
                                <button
                                  onClick={agregarClasificacionARegistro}
                                  className="bg-green-600 hover:bg-green-500 px-2 py-1 rounded text-white text-xs font-medium transition flex items-center gap-1"
                                  title="Agregar clasificación"
                                >
                                  <Plus size={14} />
                                  Agregar
                                </button>
                              )}
                            </div>
                          )}
                        </div>
                      </td>
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
                      <td className="px-3 py-2 text-gray-400">{registro.fila_excel}</td>
                      <td className="px-3 py-2">
                        {editandoId === registro.id ? (
                          <input
                            type="text"
                            value={registroEditando.numero_cuenta}
                            onChange={(e) => setRegistroEditando(prev => ({ ...prev, numero_cuenta: e.target.value }))}
                            className="w-full bg-gray-800 text-white px-2 py-1 rounded border border-gray-600 font-mono focus:border-blue-500 focus:outline-none"
                          />
                        ) : (
                          <span className="font-mono text-blue-300">{registro.numero_cuenta}</span>
                        )}
                      </td>
                      <td className="px-3 py-2">
                        {editandoId === registro.id ? (
                          <div>
                            {/* Clasificaciones actuales */}
                            {Object.keys(registroEditando.clasificaciones || {}).length > 0 && (
                              <div className="mb-3">
                                <div className="text-xs text-gray-400 mb-1">Clasificaciones actuales:</div>
                                <div className="flex flex-wrap gap-1">
                                  {Object.entries(registroEditando.clasificaciones || {}).map(([set, valor]) => (
                                    <div key={set} className="flex items-center gap-1 bg-blue-900/50 px-2 py-1 rounded text-xs border border-blue-700/50">
                                      <span className="text-blue-300 font-medium">{set}:</span>
                                      <span className="text-white">{valor}</span>
                                      <button
                                        onClick={() => eliminarClasificacionDeRegistro(set)}
                                        className="text-red-400 hover:text-red-300 ml-1 hover:bg-red-900/30 rounded p-0.5 transition"
                                        title="Eliminar clasificación"
                                      >
                                        <XCircle size={12} />
                                      </button>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                            
                            {/* Selector de nueva clasificación */}
                            <div className="border-t border-gray-600 pt-2">
                              <div className="text-xs text-gray-400 mb-2">Agregar nueva clasificación:</div>
                              {obtenerSetsDisponibles().length === 0 ? (
                                <div className="text-xs text-yellow-400 bg-yellow-900/20 p-2 rounded border border-yellow-700/50">
                                  ⚠️ No hay sets disponibles.
                                </div>
                              ) : (
                                <div className="flex gap-2 items-center flex-wrap">
                                  <select
                                    value={setSeleccionado}
                                    onChange={(e) => {
                                      console.log(`Set seleccionado cambiado (modo edición) a: ${e.target.value}`);
                                      setSetSeleccionado(e.target.value);
                                      setOpcionSeleccionada('');
                                      console.log(`Opciones disponibles para este set (modo edición):`, obtenerOpcionesParaSet(e.target.value));
                                    }}
                                    className="bg-gray-800 text-white px-2 py-1 rounded border border-gray-600 text-xs focus:border-blue-500 focus:outline-none"
                                  >
                                    <option value="">🏷️ Set...</option>
                                    {obtenerSetsDisponibles().map(set => (
                                      <option key={set.id} value={set.id}>{set.nombre}</option>
                                    ))}
                                  </select>
                                  
                                  {setSeleccionado && obtenerOpcionesParaSet(setSeleccionado).length > 0 && (
                                    <select
                                      value={opcionSeleccionada}
                                      onChange={(e) => setOpcionSeleccionada(e.target.value)}
                                      className="bg-gray-800 text-white px-2 py-1 rounded border border-gray-600 text-xs focus:border-blue-500 focus:outline-none"
                                    >
                                      <option value="">📋 Opción...</option>
                                      {obtenerOpcionesParaSet(setSeleccionado).map(opcion => (
                                        <option key={opcion.id} value={opcion.valor}>{opcion.valor}</option>
                                      ))}
                                    </select>
                                  )}
                                  
                                  {setSeleccionado && opcionSeleccionada && (
                                    <button
                                      onClick={agregarClasificacionARegistro}
                                      className="bg-green-600 hover:bg-green-500 px-2 py-1 rounded text-white text-xs font-medium transition flex items-center gap-1"
                                      title="Agregar"
                                    >
                                      <Plus size={12} />
                                    </button>
                                  )}
                                </div>
                              )}
                            </div>
                          </div>
                        ) : (
                          <div className="flex flex-wrap gap-1">
                            {Object.entries(registro.clasificaciones || {}).map(([set, valor]) => (
                              <span key={set} className="inline-block bg-blue-900/50 px-2 py-1 rounded text-xs">
                                <span className="text-gray-300">{set}:</span> <span className="text-white">{valor}</span>
                              </span>
                            ))}
                          </div>
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
                              className="p-1 text-gray-400 hover:text-gray-300"
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
            </div>
          )}
        </div>
          </>
        )}

        {/* Contenido de la pestaña Sets y Opciones */}
        {pestanaActiva === 'sets' && (
          <div className="flex-1 overflow-hidden">
            {loadingSets ? (
              <div className="flex justify-center items-center h-32">
                <div className="animate-spin w-8 h-8 border-2 border-blue-400 border-t-transparent rounded-full"></div>
              </div>
            ) : (
              <div className="h-full overflow-auto" style={{ maxHeight: '500px' }}>
                {/* Header para crear nuevo set */}
                <div className="mb-6 p-4 bg-gray-800 rounded-lg">
                  <h3 className="text-lg font-medium text-white mb-3 flex items-center gap-2">
                    <FolderPlus size={18} />
                    Gestión de Sets de Clasificación
                  </h3>
                  
                  <div className="flex gap-2 items-center">
                    {creandoSet ? (
                      <>
                        <input
                          type="text"
                          value={nuevoSet}
                          onChange={(e) => setNuevoSet(e.target.value)}
                          placeholder="Nombre del nuevo set"
                          className="flex-1 bg-gray-700 text-white px-3 py-2 rounded border border-gray-600"
                          onKeyPress={(e) => e.key === 'Enter' && handleCrearSet()}
                        />
                        <button
                          onClick={handleCrearSet}
                          className="bg-green-600 hover:bg-green-500 px-3 py-2 rounded text-white font-medium transition"
                        >
                          <Save size={16} />
                        </button>
                        <button
                          onClick={() => {
                            setCreandoSet(false);
                            setNuevoSet('');
                          }}
                          className="bg-gray-600 hover:bg-gray-500 px-3 py-2 rounded text-white font-medium transition"
                        >
                          <XCircle size={16} />
                        </button>
                      </>
                    ) : (
                      <button
                        onClick={() => setCreandoSet(true)}
                        className="bg-blue-600 hover:bg-blue-500 px-4 py-2 rounded text-white font-medium transition flex items-center gap-2"
                      >
                        <Plus size={16} />
                        Nuevo Set
                      </button>
                    )}
                  </div>
                </div>

                {/* Lista de sets */}
                <div className="space-y-4">
                  {sets.map((set) => (
                    <div key={set.id} className="bg-gray-800 rounded-lg p-4 border border-gray-700">
                      {/* Header del set */}
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-2">
                          {editandoSet === set.id ? (
                            <input
                              type="text"
                              value={setEditando}
                              onChange={(e) => setSetEditando(e.target.value)}
                              className="bg-gray-700 text-white px-2 py-1 rounded border border-gray-600 font-medium"
                              onKeyPress={(e) => e.key === 'Enter' && handleEditarSet()}
                            />
                          ) : (
                            <h4 className="text-white font-medium">{set.nombre}</h4>
                          )}
                          <span className="text-gray-400 text-sm">
                            ({opcionesPorSet[set.id]?.length || 0} opciones)
                          </span>
                        </div>
                        
                        <div className="flex gap-1">
                          {editandoSet === set.id ? (
                            <>
                              <button
                                onClick={handleEditarSet}
                                className="p-1 text-green-400 hover:text-green-300"
                                title="Guardar"
                              >
                                <Save size={16} />
                              </button>
                              <button
                                onClick={() => {
                                  setEditandoSet(null);
                                  setSetEditando('');
                                }}
                                className="p-1 text-gray-400 hover:text-gray-300"
                                title="Cancelar"
                              >
                                <XCircle size={16} />
                              </button>
                            </>
                          ) : (
                            <>
                              <button
                                onClick={() => {
                                  setEditandoSet(set.id);
                                  setSetEditando(set.nombre);
                                }}
                                className="p-1 text-blue-400 hover:text-blue-300"
                                title="Editar nombre"
                              >
                                <Edit2 size={16} />
                              </button>
                              <button
                                onClick={() => handleEliminarSet(set.id)}
                                className="p-1 text-red-400 hover:text-red-300"
                                title="Eliminar set"
                              >
                                <Trash2 size={16} />
                              </button>
                            </>
                          )}
                        </div>
                      </div>

                      {/* Opciones del set */}
                      <div className="space-y-2">
                        <div className="flex flex-wrap gap-2">
                          {opcionesPorSet[set.id]?.map((opcion) => (
                            <div key={opcion.id} className="flex items-center gap-1 bg-blue-900/30 px-2 py-1 rounded">
                              {editandoOpcion === opcion.id ? (
                                <input
                                  type="text"
                                  value={opcionEditando}
                                  onChange={(e) => setOpcionEditando(e.target.value)}
                                  className="bg-gray-700 text-white px-1 py-0.5 rounded border border-gray-600 text-sm w-20"
                                  onKeyPress={(e) => e.key === 'Enter' && handleEditarOpcion(opcion.id)}
                                />
                              ) : (
                                <span className="text-white text-sm">{opcion.valor}</span>
                              )}
                              
                              <div className="flex gap-0.5 ml-1">
                                {editandoOpcion === opcion.id ? (
                                  <>
                                    <button
                                      onClick={() => handleEditarOpcion(opcion.id)}
                                      className="text-green-400 hover:text-green-300"
                                      title="Guardar"
                                    >
                                      <Save size={12} />
                                    </button>
                                    <button
                                      onClick={() => {
                                        setEditandoOpcion(null);
                                        setOpcionEditando('');
                                      }}
                                      className="text-gray-400 hover:text-gray-300"
                                      title="Cancelar"
                                    >
                                      <XCircle size={12} />
                                    </button>
                                  </>
                                ) : (
                                  <>
                                    <button
                                      onClick={() => {
                                        setEditandoOpcion(opcion.id);
                                        setOpcionEditando(opcion.valor);
                                      }}
                                      className="text-blue-400 hover:text-blue-300"
                                      title="Editar"
                                    >
                                      <Edit2 size={12} />
                                    </button>
                                    <button
                                      onClick={() => handleEliminarOpcion(opcion.id)}
                                      className="text-red-400 hover:text-red-300"
                                      title="Eliminar"
                                    >
                                      <Trash2 size={12} />
                                    </button>
                                  </>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>

                        {/* Agregar nueva opción */}
                        <div className="flex gap-2 items-center">
                          {creandoOpcionPara === set.id ? (
                            <>
                              <input
                                type="text"
                                value={nuevaOpcion}
                                onChange={(e) => setNuevaOpcion(e.target.value)}
                                placeholder="Nueva opción"
                                className="bg-gray-700 text-white px-2 py-1 rounded border border-gray-600 text-sm"
                                onKeyPress={(e) => e.key === 'Enter' && handleCrearOpcion(set.id)}
                              />
                              <button
                                onClick={() => handleCrearOpcion(set.id)}
                                className="text-green-400 hover:text-green-300"
                                title="Agregar opción"
                              >
                                <Save size={14} />
                              </button>
                              <button
                                onClick={() => {
                                  setCreandoOpcionPara(null);
                                  setNuevaOpcion('');
                                }}
                                className="text-gray-400 hover:text-gray-300"
                                title="Cancelar"
                              >
                                <XCircle size={14} />
                              </button>
                            </>
                          ) : (
                            <button
                              onClick={() => setCreandoOpcionPara(set.id)}
                              className="text-blue-400 hover:text-blue-300 flex items-center gap-1 text-sm"
                              title="Agregar opción"
                            >
                              <Plus size={14} />
                              Agregar opción
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                {sets.length === 0 && (
                  <div className="text-center py-8 text-gray-400">
                    <Database size={48} className="mx-auto mb-2 opacity-50" />
                    <p>No hay sets de clasificación creados</p>
                    <p className="text-sm">Crea el primer set para comenzar</p>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Footer */}
        <div className="mt-6 flex justify-end">
          <button
            onClick={onClose}
            className="bg-gray-600 hover:bg-gray-500 px-4 py-2 rounded text-white font-medium transition"
          >
            Cerrar
          </button>
        </div>
      </div>
    </div>
  );
};

export default ModalClasificacionRegistrosRaw;
