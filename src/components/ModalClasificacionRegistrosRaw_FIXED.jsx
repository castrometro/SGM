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
      setSets(setsData);
      
      // Limpiar opciones anteriores para evitar mezcla
      setOpcionesPorSet({});
      
      // Cargar opciones para cada set de forma secuencial para evitar conflictos
      const nuevasOpciones = {};
      for (const set of setsData) {
        try {
          const opciones = await obtenerOpcionesSet(set.id);
          nuevasOpciones[set.id] = opciones;
        } catch (error) {
          console.error(`Error cargando opciones para set ${set.id}:`, error);
          nuevasOpciones[set.id] = [];
        }
      }
      
      // Actualizar todas las opciones de una vez
      setOpcionesPorSet(nuevasOpciones);
      
    } catch (error) {
      console.error("Error cargando sets:", error);
      setSets([]);
    } finally {
      setLoadingSets(false);
    }
  };

  const calcularEstadisticas = (data) => {
    const total = data.length;
    setEstadisticas({ total });
  };

  // ==================== FUNCIONES AUXILIARES PARA SETS/OPCIONES ====================
  const obtenerSetsDisponibles = () => {
    return sets || [];
  };

  const obtenerOpcionesParaSet = (setId) => {
    if (!setId || !opcionesPorSet || !opcionesPorSet[setId]) return [];
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
      await crearSet(clienteId, nuevoSet.trim());
      setNuevoSet('');
      setCreandoSet(false);
      await cargarSets();
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

  const registrosFiltrados = registros || [];

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-60 z-50 flex justify-center items-center p-4">
      <div 
        className="bg-gray-900 rounded-lg shadow-xl w-full overflow-hidden flex flex-col"
        style={{ 
          maxWidth: '95vw',
          maxHeight: '90vh',
          width: '1200px'
        }}
      >
        {/* Header del modal - sticky */}
        <div className="flex justify-between items-center p-6 border-b border-gray-700 bg-gray-900 sticky top-0 z-20">
          <h2 className="text-xl font-semibold text-white flex items-center gap-2">
            <Database size={20} />
            Gestión de Clasificaciones
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white transition-colors"
          >
            <X size={24} />
          </button>
        </div>

        {/* Pestañas de navegación - sticky */}
        <div className="bg-gray-800 border-b border-gray-700 sticky top-[88px] z-10">
          <div className="flex space-x-4 p-4">
            <button
              onClick={() => manejarCambioPestana('registros')}
              className={`px-4 py-2 rounded font-medium transition-colors flex items-center gap-2 ${
                pestanaActiva === 'registros'
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-400 hover:text-white hover:bg-gray-700'
              }`}
            >
              <FileText size={16} />
              Registros ({registros.length})
            </button>
            <button
              onClick={() => manejarCambioPestana('sets')}
              className={`px-4 py-2 rounded font-medium transition-colors flex items-center gap-2 ${
                pestanaActiva === 'sets'
                  ? 'bg-green-600 text-white'
                  : 'text-gray-400 hover:text-white hover:bg-gray-700'
              }`}
            >
              <Settings size={16} />
              Sets y Opciones ({sets.length})
            </button>
          </div>
        </div>

        {/* Contenido principal con scroll */}
        <div className="flex-1 overflow-hidden bg-gray-900">
          {/* Contenido de la pestaña Registros */}
          {pestanaActiva === 'registros' && (
            <div className="h-full flex flex-col">
              {/* Estadísticas y botón crear */}
              <div className="bg-gray-800 p-4 border-b border-gray-700">
                <div className="flex justify-between items-center">
                  <div className="flex items-center gap-4 text-sm text-gray-300">
                    <span>Total de Registros: <strong className="text-white">{estadisticas.total || 0}</strong></span>
                  </div>
                  <button
                    onClick={handleIniciarCreacion}
                    className="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded font-medium transition flex items-center gap-2"
                  >
                    <Plus size={16} />
                    Nuevo Registro
                  </button>
                </div>
              </div>

              {/* Tabla con scroll */}
              <div className="flex-1 overflow-auto">
                {loading ? (
                  <div className="flex justify-center items-center h-32">
                    <div className="animate-spin w-8 h-8 border-2 border-blue-400 border-t-transparent rounded-full"></div>
                  </div>
                ) : registrosFiltrados.length === 0 ? (
                  <div className="text-center py-8 text-gray-400">
                    <FileText size={48} className="mx-auto mb-2 opacity-50" />
                    <p>No hay registros de clasificación disponibles</p>
                  </div>
                ) : (
                  <table className="w-full">
                    <thead className="bg-gray-800 sticky top-0 z-10">
                      <tr>
                        <th className="px-3 py-2 text-left text-xs font-medium text-gray-300 uppercase tracking-wider border-b border-gray-700">
                          Fila
                        </th>
                        <th className="px-3 py-2 text-left text-xs font-medium text-gray-300 uppercase tracking-wider border-b border-gray-700">
                          Número Cuenta
                        </th>
                        <th className="px-3 py-2 text-left text-xs font-medium text-gray-300 uppercase tracking-wider border-b border-gray-700">
                          Clasificaciones
                        </th>
                        <th className="px-3 py-2 text-left text-xs font-medium text-gray-300 uppercase tracking-wider border-b border-gray-700">
                          Acciones
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-gray-900 divide-y divide-gray-700">
                      {/* Fila de creación de nuevo registro */}
                      {creandoNuevo && (
                        <tr className="bg-gray-800 border-l-4 border-l-blue-500">
                          <td className="px-3 py-2 text-gray-400 text-sm">Nuevo</td>
                          <td className="px-3 py-2">
                            <input
                              type="text"
                              value={nuevoRegistro.numero_cuenta}
                              onChange={(e) => setNuevoRegistro(prev => ({ ...prev, numero_cuenta: e.target.value }))}
                              placeholder="Número de cuenta"
                              className="w-full bg-gray-700 text-white px-2 py-1 rounded border border-gray-600 focus:border-blue-500 focus:outline-none"
                            />
                          </td>
                          <td className="px-3 py-2">
                            {/* Clasificaciones agregadas */}
                            {Object.keys(nuevoRegistro.clasificaciones).length > 0 && (
                              <div className="mb-2">
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
                                  ⚠️ No hay sets disponibles.
                                </div>
                              ) : (
                                <div className="flex gap-2 items-center flex-wrap">
                                  <select
                                    value={setSeleccionado}
                                    onChange={(e) => {
                                      setSetSeleccionado(e.target.value);
                                      setOpcionSeleccionada('');
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
                                className="p-1 text-gray-400 hover:text-gray-300"
                                title="Cancelar"
                              >
                                <XCircle size={16} />
                              </button>
                            </div>
                          </td>
                        </tr>
                      )}
                      
                      {/* Filas de registros existentes */}
                      {registrosFiltrados.map((registro) => (
                        <tr key={registro.id} className="hover:bg-gray-800/50 transition-colors">
                          <td className="px-3 py-2 text-gray-400 text-sm">{registro.fila_excel}</td>
                          <td className="px-3 py-2">
                            {editandoId === registro.id ? (
                              <input
                                type="text"
                                value={registroEditando.numero_cuenta}
                                onChange={(e) => setRegistroEditando(prev => ({ ...prev, numero_cuenta: e.target.value }))}
                                className="w-full bg-gray-700 text-white px-2 py-1 rounded border border-gray-600 focus:border-blue-500 focus:outline-none"
                              />
                            ) : (
                              <span className="text-white font-mono">{registro.numero_cuenta}</span>
                            )}
                          </td>
                          <td className="px-3 py-2">
                            {editandoId === registro.id ? (
                              <div>
                                {/* Clasificaciones agregadas */}
                                {Object.keys(registroEditando.clasificaciones).length > 0 && (
                                  <div className="mb-2">
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
                                          setSetSeleccionado(e.target.value);
                                          setOpcionSeleccionada('');
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
                )}
              </div>
            </div>
          )}

          {/* Contenido de la pestaña Sets y Opciones */}
          {pestanaActiva === 'sets' && (
            <div className="h-full flex flex-col">
              {/* Header para crear nuevo set */}
              <div className="bg-gray-800 p-4 border-b border-gray-700">
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

              {/* Contenedor de sets con scroll */}
              <div className="flex-1 overflow-auto p-4">
                {loadingSets ? (
                  <div className="flex justify-center items-center h-32">
                    <div className="animate-spin w-8 h-8 border-2 border-blue-400 border-t-transparent rounded-full"></div>
                  </div>
                ) : sets.length === 0 ? (
                  <div className="text-center py-8 text-gray-400">
                    <Database size={48} className="mx-auto mb-2 opacity-50" />
                    <p>No hay sets de clasificación creados</p>
                    <p className="text-sm">Crea el primer set para comenzar</p>
                  </div>
                ) : (
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
                )}
              </div>
            </div>
          )}
        </div>

        {/* Footer - sticky */}
        <div className="bg-gray-800 px-6 py-4 border-t border-gray-700 sticky bottom-0 z-10">
          <div className="flex justify-between items-center">
            <div className="text-sm text-gray-400">
              {pestanaActiva === 'registros' ? (
                `Mostrando ${registros.length} registros de clasificación`
              ) : (
                `Gestionando ${sets.length} sets con ${Object.values(opcionesPorSet).flat().length} opciones`
              )}
            </div>
            <button
              onClick={onClose}
              className="bg-gray-600 hover:bg-gray-500 text-white px-4 py-2 rounded font-medium transition"
            >
              Cerrar
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ModalClasificacionRegistrosRaw;
