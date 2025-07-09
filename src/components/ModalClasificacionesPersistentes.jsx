import { useState, useEffect } from 'react';
import { X, Check, AlertTriangle, Clock, Plus, Edit2, Trash2, Save, XCircle, Settings, Database, FolderPlus, Globe, CheckSquare, FileText } from 'lucide-react';
import { 
  obtenerClasificacionesPersistentesDetalladas,
  registrarVistaClasificacionesPersistentes,
  crearClasificacionPersistente,
  actualizarClasificacionPersistente,
  eliminarClasificacionPersistente,
  obtenerSetsCliente,
  crearSet,
  actualizarSet,
  eliminarSet,
  obtenerOpcionesSet,
  crearOpcion,
  actualizarOpcion,
  eliminarOpcion,
  registrarActividadTarjeta,
  clasificacionMasivaPersistente,
  obtenerEstadisticasClasificacionesPersistentes,
  obtenerCuentasCliente
} from '../api/contabilidad';

const ModalClasificacionesPersistentes = ({ isOpen, onClose, clienteId, cierreId, cliente, onDataChanged }) => {
  console.log('🏗️ ModalClasificacionesPersistentes props:', { 
    isOpen, 
    clienteId,
    cierreId,
    clienteExiste: !!cliente,
    clienteBilingue: cliente?.bilingue,
    onDataChanged: !!onDataChanged 
  });

  // Función auxiliar para registrar actividades CRUD
  const registrarActividad = async (tipo, accion, descripcion, detalles = {}) => {
    try {
      if (!clienteId) {
        console.warn('No hay clienteId para registrar actividad');
        return;
      }

      await registrarActividadTarjeta(
        clienteId,
        tipo, 
        accion,
        descripcion,
        {
          cierre_id: cierreId,
          accion_origen: "modal_clasificaciones_persistentes",
          ...detalles
        },
        cierreId
      );
    } catch (error) {
      console.warn('Error registrando actividad:', error);
      // No fallar la operación principal por un error de logging
    }
  };

  // Estados principales
  const [loading, setLoading] = useState(false);
  const [clasificaciones, setClasificaciones] = useState([]);
  const [cuentas, setCuentas] = useState([]);
  const [estadisticas, setEstadisticas] = useState({});
  
  // Estados para navegación de pestañas
  const [pestanaActiva, setPestanaActiva] = useState('clasificaciones'); // 'clasificaciones' | 'sets' | 'cuentas'
  
  // Estados para CRUD de clasificaciones
  const [editandoId, setEditandoId] = useState(null);
  const [clasificacionEditando, setClasificacionEditando] = useState(null);
  const [creandoNuevo, setCreandoNuevo] = useState(false);
  const [nuevaClasificacion, setNuevaClasificacion] = useState({
    cuenta: '',
    set_clas: '',
    opcion: ''
  });
  
  // Estados para filtros de búsqueda
  const [filtros, setFiltros] = useState({
    busquedaCuenta: '',
    setsSeleccionados: [],
    soloSinClasificar: false,
    soloClasificados: false
  });

  // Estados para gestión de sets y opciones
  const [sets, setSets] = useState([]);
  const [loadingSets, setLoadingSets] = useState(false);
  const [editandoSet, setEditandoSet] = useState(null);
  const [creandoSet, setCreandoSet] = useState(false);
  const [nuevoSet, setNuevoSet] = useState('');
  const [setEditando, setSetEditando] = useState('');
  
  // Estados para opciones
  const [editandoOpcion, setEditandoOpcion] = useState(null);
  const [creandoOpcionPara, setCreandoOpcionPara] = useState(null);
  const [nuevaOpcion, setNuevaOpcion] = useState({
    valor: '',
    valor_en: '',
    descripcion: '',
    descripcion_en: ''
  });
  const [opcionEditando, setOpcionEditando] = useState({
    valor: '',
    valor_en: '',
    descripcion: '',
    descripcion_en: ''
  });

  // Estados para clasificación masiva
  const [modoClasificacionMasiva, setModoClasificacionMasiva] = useState(false);
  const [cuentasSeleccionadas, setCuentasSeleccionadas] = useState(new Set());
  const [setMasivo, setSetMasivo] = useState('');
  const [opcionMasiva, setOpcionMasiva] = useState('');

  // Estados para manejo bilingüe
  const [idiomaMostrado, setIdiomaMostrado] = useState('es');

  useEffect(() => {
    console.log('🎯 useEffect ejecutado:', { 
      isOpen, 
      clienteId, 
      cliente: !!cliente,
      clienteBilingue: cliente?.bilingue
    });
    
    if (isOpen && clienteId) {
      console.log('✅ Condiciones cumplidas - iniciando carga de datos persistentes');
      
      // Registrar timestamp de apertura
      window.modalClasificacionesPersistentesOpenTime = Date.now();
      
      // Registrar que se abrió el modal
      registrarVistaClasificacionesPersistentes(clienteId, cierreId)
        .then(() => {
          console.log('📋 Vista registrada - cargando datos persistentes');
          
          // Registrar actividad de vista del modal
          registrarActividad(
            "clasificacion",
            "view_persistent_data",
            `Abrió modal de clasificaciones persistentes`,
            {}
          ).catch(logErr => console.warn("Error registrando vista del modal:", logErr));
          
          // Cargar los datos persistentes
          cargarClasificaciones();
          cargarSets();
          cargarCuentas();
          cargarEstadisticas();
        })
        .catch((err) => {
          console.error("Error al registrar vista del modal:", err);
          // Aunque falle el registro, cargar los datos igual
          console.log('📋 Error en registro - cargando datos de todos modos');
          cargarClasificaciones();
          cargarSets();
          cargarCuentas();
          cargarEstadisticas();
        });
    } else {
      console.log('❌ Condiciones no cumplidas para carga');
    }
  }, [isOpen, clienteId]);

  const cargarClasificaciones = async () => {
    setLoading(true);
    try {
      const data = await obtenerClasificacionesPersistentesDetalladas(clienteId);
      setClasificaciones(data);
      console.log('📊 Clasificaciones persistentes cargadas:', data.length);
    } catch (error) {
      console.error("Error cargando clasificaciones persistentes:", error);
      setClasificaciones([]);
    } finally {
      setLoading(false);
    }
  };

  const cargarSets = async () => {
    setLoadingSets(true);
    try {
      const data = await obtenerSetsCliente(clienteId);
      setSets(data);
      console.log('📋 Sets cargados:', data.length);
    } catch (error) {
      console.error("Error cargando sets:", error);
      setSets([]);
    } finally {
      setLoadingSets(false);
    }
  };

  const cargarCuentas = async () => {
    try {
      const data = await obtenerCuentasCliente(clienteId);
      setCuentas(data);
      console.log('🏦 Cuentas cargadas:', data.length);
    } catch (error) {
      console.error("Error cargando cuentas:", error);
      setCuentas([]);
    }
  };

  const cargarEstadisticas = async () => {
    try {
      const data = await obtenerEstadisticasClasificacionesPersistentes(clienteId);
      setEstadisticas(data);
      console.log('📈 Estadísticas cargadas:', data);
    } catch (error) {
      console.error("Error cargando estadísticas:", error);
      setEstadisticas({});
    }
  };

  // Función para cerrar el modal
  const handleClose = () => {
    // Registrar tiempo de sesión
    const sessionTime = Date.now() - (window.modalClasificacionesPersistentesOpenTime || Date.now());
    const sessionMinutes = Math.round(sessionTime / 60000);
    
    registrarActividad(
      "clasificacion",
      "close_persistent_modal",
      `Cerró modal de clasificaciones persistentes después de ${sessionMinutes} minutos`,
      {
        session_time_ms: sessionTime,
        session_minutes: sessionMinutes
      }
    ).catch(logErr => console.warn("Error registrando cierre del modal:", logErr));
    
    onClose();
  };

  // Funciones de CRUD para clasificaciones
  const handleCrearClasificacion = async () => {
    if (!nuevaClasificacion.cuenta || !nuevaClasificacion.set_clas || !nuevaClasificacion.opcion) {
      alert('Todos los campos son requeridos');
      return;
    }

    try {
      setLoading(true);
      const created = await crearClasificacionPersistente(nuevaClasificacion);
      
      await registrarActividad(
        "clasificacion",
        "create",
        `Creó clasificación persistente para cuenta ${nuevaClasificacion.cuenta}`,
        { clasificacion_id: created.id, ...nuevaClasificacion }
      );

      setNuevaClasificacion({ cuenta: '', set_clas: '', opcion: '' });
      setCreandoNuevo(false);
      await cargarClasificaciones();
      await cargarEstadisticas();
      
      if (onDataChanged) onDataChanged();
    } catch (error) {
      console.error('Error creando clasificación:', error);
      alert('Error creando clasificación: ' + (error.response?.data?.error || error.message));
    } finally {
      setLoading(false);
    }
  };

  const handleActualizarClasificacion = async () => {
    if (!clasificacionEditando) return;

    try {
      setLoading(true);
      await actualizarClasificacionPersistente(editandoId, clasificacionEditando);
      
      await registrarActividad(
        "clasificacion",
        "update",
        `Actualizó clasificación persistente ID ${editandoId}`,
        { clasificacion_id: editandoId, changes: clasificacionEditando }
      );

      setEditandoId(null);
      setClasificacionEditando(null);
      await cargarClasificaciones();
      await cargarEstadisticas();
      
      if (onDataChanged) onDataChanged();
    } catch (error) {
      console.error('Error actualizando clasificación:', error);
      alert('Error actualizando clasificación: ' + (error.response?.data?.error || error.message));
    } finally {
      setLoading(false);
    }
  };

  const handleEliminarClasificacion = async (id) => {
    if (!confirm('¿Está seguro de que desea eliminar esta clasificación?')) return;

    try {
      setLoading(true);
      await eliminarClasificacionPersistente(id);
      
      await registrarActividad(
        "clasificacion",
        "delete",
        `Eliminó clasificación persistente ID ${id}`,
        { clasificacion_id: id }
      );

      await cargarClasificaciones();
      await cargarEstadisticas();
      
      if (onDataChanged) onDataChanged();
    } catch (error) {
      console.error('Error eliminando clasificación:', error);
      alert('Error eliminando clasificación: ' + (error.response?.data?.error || error.message));
    } finally {
      setLoading(false);
    }
  };

  // Funciones para clasificación masiva
  const handleClasificacionMasiva = async () => {
    if (cuentasSeleccionadas.size === 0 || !setMasivo || !opcionMasiva) {
      alert('Seleccione cuentas, set y opción para la clasificación masiva');
      return;
    }

    if (!confirm(`¿Clasificar ${cuentasSeleccionadas.size} cuentas seleccionadas?`)) return;

    try {
      setLoading(true);
      const cuentaIds = Array.from(cuentasSeleccionadas);
      await clasificacionMasivaPersistente(cuentaIds, setMasivo, opcionMasiva);
      
      await registrarActividad(
        "clasificacion",
        "bulk_classify",
        `Clasificación masiva: ${cuentaIds.length} cuentas`,
        { 
          cuenta_ids: cuentaIds, 
          set_id: setMasivo, 
          opcion_id: opcionMasiva,
          total_cuentas: cuentaIds.length
        }
      );

      setCuentasSeleccionadas(new Set());
      setSetMasivo('');
      setOpcionMasiva('');
      setModoClasificacionMasiva(false);
      await cargarClasificaciones();
      await cargarEstadisticas();
      
      if (onDataChanged) onDataChanged();
    } catch (error) {
      console.error('Error en clasificación masiva:', error);
      alert('Error en clasificación masiva: ' + (error.response?.data?.error || error.message));
    } finally {
      setLoading(false);
    }
  };

  // Filtrar clasificaciones
  const clasificacionesFiltradas = clasificaciones.filter(clasificacion => {
    if (filtros.busquedaCuenta && !clasificacion.cuenta_codigo?.toLowerCase().includes(filtros.busquedaCuenta.toLowerCase()) &&
        !clasificacion.cuenta_nombre?.toLowerCase().includes(filtros.busquedaCuenta.toLowerCase())) {
      return false;
    }
    
    if (filtros.setsSeleccionados.length > 0 && !filtros.setsSeleccionados.includes(clasificacion.set_clas_id)) {
      return false;
    }
    
    return true;
  });

  // Renderizar el modal solo si está abierto
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-800 rounded-lg shadow-xl w-full max-w-7xl h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-700">
          <div className="flex items-center gap-3">
            <Database className="text-green-400" size={24} />
            <div>
              <h2 className="text-xl font-bold text-white">
                Gestión de Clasificaciones Persistentes
              </h2>
              <p className="text-sm text-gray-400">
                {cliente?.nombre || `Cliente ${clienteId}`} {cliente?.bilingue && '(Bilingüe)'}
              </p>
            </div>
          </div>
          <button
            onClick={handleClose}
            className="text-gray-400 hover:text-white transition"
          >
            <X size={24} />
          </button>
        </div>

        {/* Estadísticas */}
        <div className="px-6 py-4 bg-gray-900 border-b border-gray-700">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-green-400">{estadisticas.total_clasificaciones || 0}</div>
              <div className="text-xs text-gray-400">Total Clasificaciones</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-400">{estadisticas.total_cuentas || 0}</div>
              <div className="text-xs text-gray-400">Total Cuentas</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-yellow-400">{estadisticas.cuentas_sin_clasificar || 0}</div>
              <div className="text-xs text-gray-400">Sin Clasificar</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-400">{sets.length}</div>
              <div className="text-xs text-gray-400">Sets Disponibles</div>
            </div>
          </div>
        </div>

        {/* Navegación de pestañas */}
        <div className="flex border-b border-gray-700">
          <button
            onClick={() => setPestanaActiva('clasificaciones')}
            className={`px-6 py-3 font-medium transition ${
              pestanaActiva === 'clasificaciones'
                ? 'text-green-400 border-b-2 border-green-400'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            <Database size={16} className="inline mr-2" />
            Clasificaciones ({clasificacionesFiltradas.length})
          </button>
          <button
            onClick={() => setPestanaActiva('sets')}
            className={`px-6 py-3 font-medium transition ${
              pestanaActiva === 'sets'
                ? 'text-blue-400 border-b-2 border-blue-400'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            <FolderPlus size={16} className="inline mr-2" />
            Sets ({sets.length})
          </button>
          <button
            onClick={() => setPestanaActiva('cuentas')}
            className={`px-6 py-3 font-medium transition ${
              pestanaActiva === 'cuentas'
                ? 'text-yellow-400 border-b-2 border-yellow-400'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            <FileText size={16} className="inline mr-2" />
            Cuentas ({cuentas.length})
          </button>
        </div>

        {/* Contenido */}
        <div className="flex-1 overflow-hidden">
          {pestanaActiva === 'clasificaciones' && (
            <div className="h-full flex flex-col">
              {/* Filtros y controles */}
              <div className="p-4 border-b border-gray-700 bg-gray-900">
                <div className="flex gap-4 items-center flex-wrap">
                  <input
                    type="text"
                    placeholder="Buscar cuenta..."
                    value={filtros.busquedaCuenta}
                    onChange={(e) => setFiltros(prev => ({ ...prev, busquedaCuenta: e.target.value }))}
                    className="px-3 py-1 bg-gray-800 border border-gray-600 rounded text-white"
                  />
                  <button
                    onClick={() => setCreandoNuevo(true)}
                    className="px-3 py-1 bg-green-600 hover:bg-green-500 text-white rounded flex items-center gap-2"
                  >
                    <Plus size={16} />
                    Nueva Clasificación
                  </button>
                  <button
                    onClick={() => setModoClasificacionMasiva(!modoClasificacionMasiva)}
                    className={`px-3 py-1 rounded flex items-center gap-2 ${
                      modoClasificacionMasiva 
                        ? 'bg-orange-600 hover:bg-orange-500' 
                        : 'bg-blue-600 hover:bg-blue-500'
                    } text-white`}
                  >
                    <CheckSquare size={16} />
                    {modoClasificacionMasiva ? 'Cancelar Masiva' : 'Clasificación Masiva'}
                  </button>
                </div>

                {/* Controles de clasificación masiva */}
                {modoClasificacionMasiva && (
                  <div className="mt-3 p-3 bg-orange-900/20 border border-orange-500/30 rounded">
                    <div className="flex gap-3 items-center flex-wrap">
                      <select
                        value={setMasivo}
                        onChange={(e) => setSetMasivo(e.target.value)}
                        className="px-2 py-1 bg-gray-800 border border-gray-600 rounded text-white"
                      >
                        <option value="">Seleccionar Set</option>
                        {sets.map(set => (
                          <option key={set.id} value={set.id}>{set.nombre}</option>
                        ))}
                      </select>
                      <select
                        value={opcionMasiva}
                        onChange={(e) => setOpcionMasiva(e.target.value)}
                        className="px-2 py-1 bg-gray-800 border border-gray-600 rounded text-white"
                        disabled={!setMasivo}
                      >
                        <option value="">Seleccionar Opción</option>
                        {/* Aquí necesitarías cargar las opciones del set seleccionado */}
                      </select>
                      <button
                        onClick={handleClasificacionMasiva}
                        disabled={cuentasSeleccionadas.size === 0 || !setMasivo || !opcionMasiva}
                        className="px-3 py-1 bg-orange-600 hover:bg-orange-500 disabled:bg-gray-600 text-white rounded"
                      >
                        Clasificar {cuentasSeleccionadas.size} seleccionadas
                      </button>
                    </div>
                  </div>
                )}
              </div>

              {/* Lista de clasificaciones */}
              <div className="flex-1 overflow-auto p-4">
                {loading ? (
                  <div className="flex items-center justify-center h-32">
                    <div className="text-gray-400">Cargando clasificaciones...</div>
                  </div>
                ) : clasificacionesFiltradas.length === 0 ? (
                  <div className="text-center text-gray-400 mt-8">
                    <Database size={48} className="mx-auto mb-4 text-gray-600" />
                    <p>No hay clasificaciones que mostrar</p>
                    <button
                      onClick={() => setCreandoNuevo(true)}
                      className="mt-4 px-4 py-2 bg-green-600 hover:bg-green-500 text-white rounded"
                    >
                      Crear Primera Clasificación
                    </button>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {/* Formulario de nueva clasificación */}
                    {creandoNuevo && (
                      <div className="p-4 bg-green-900/20 border border-green-500/30 rounded">
                        <h4 className="font-medium text-green-400 mb-3">Nueva Clasificación</h4>
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                          <select
                            value={nuevaClasificacion.cuenta}
                            onChange={(e) => setNuevaClasificacion(prev => ({ ...prev, cuenta: e.target.value }))}
                            className="px-2 py-1 bg-gray-800 border border-gray-600 rounded text-white"
                          >
                            <option value="">Seleccionar Cuenta</option>
                            {cuentas.map(cuenta => (
                              <option key={cuenta.id} value={cuenta.id}>
                                {cuenta.codigo} - {cuenta.nombre}
                              </option>
                            ))}
                          </select>
                          <select
                            value={nuevaClasificacion.set_clas}
                            onChange={(e) => setNuevaClasificacion(prev => ({ ...prev, set_clas: e.target.value }))}
                            className="px-2 py-1 bg-gray-800 border border-gray-600 rounded text-white"
                          >
                            <option value="">Seleccionar Set</option>
                            {sets.map(set => (
                              <option key={set.id} value={set.id}>{set.nombre}</option>
                            ))}
                          </select>
                          <select
                            value={nuevaClasificacion.opcion}
                            onChange={(e) => setNuevaClasificacion(prev => ({ ...prev, opcion: e.target.value }))}
                            className="px-2 py-1 bg-gray-800 border border-gray-600 rounded text-white"
                            disabled={!nuevaClasificacion.set_clas}
                          >
                            <option value="">Seleccionar Opción</option>
                            {/* Aquí necesitarías cargar las opciones del set seleccionado */}
                          </select>
                        </div>
                        <div className="flex gap-2 mt-3">
                          <button
                            onClick={handleCrearClasificacion}
                            className="px-3 py-1 bg-green-600 hover:bg-green-500 text-white rounded"
                          >
                            <Save size={16} className="inline mr-1" />
                            Guardar
                          </button>
                          <button
                            onClick={() => {
                              setCreandoNuevo(false);
                              setNuevaClasificacion({ cuenta: '', set_clas: '', opcion: '' });
                            }}
                            className="px-3 py-1 bg-gray-600 hover:bg-gray-500 text-white rounded"
                          >
                            <XCircle size={16} className="inline mr-1" />
                            Cancelar
                          </button>
                        </div>
                      </div>
                    )}

                    {/* Lista de clasificaciones existentes */}
                    {clasificacionesFiltradas.map(clasificacion => (
                      <div
                        key={clasificacion.id}
                        className={`p-3 border rounded ${
                          modoClasificacionMasiva
                            ? 'bg-gray-700 border-gray-600 cursor-pointer hover:bg-gray-650'
                            : 'bg-gray-750 border-gray-650'
                        }`}
                        onClick={() => {
                          if (modoClasificacionMasiva && clasificacion.cuenta_id) {
                            const newSelection = new Set(cuentasSeleccionadas);
                            if (newSelection.has(clasificacion.cuenta_id)) {
                              newSelection.delete(clasificacion.cuenta_id);
                            } else {
                              newSelection.add(clasificacion.cuenta_id);
                            }
                            setCuentasSeleccionadas(newSelection);
                          }
                        }}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            {modoClasificacionMasiva && (
                              <input
                                type="checkbox"
                                checked={cuentasSeleccionadas.has(clasificacion.cuenta_id)}
                                onChange={() => {}} // Manejado en el onClick del div
                                className="rounded"
                              />
                            )}
                            <div>
                              <div className="font-medium text-white">
                                {clasificacion.cuenta_codigo} - {clasificacion.cuenta_nombre}
                              </div>
                              <div className="text-sm text-gray-400">
                                {clasificacion.set_nombre}: {clasificacion.opcion_valor}
                              </div>
                            </div>
                          </div>
                          {!modoClasificacionMasiva && (
                            <div className="flex gap-2">
                              <button
                                onClick={() => {
                                  setEditandoId(clasificacion.id);
                                  setClasificacionEditando({
                                    cuenta: clasificacion.cuenta_id,
                                    set_clas: clasificacion.set_clas_id,
                                    opcion: clasificacion.opcion_id
                                  });
                                }}
                                className="p-1 text-blue-400 hover:text-blue-300"
                              >
                                <Edit2 size={16} />
                              </button>
                              <button
                                onClick={() => handleEliminarClasificacion(clasificacion.id)}
                                className="p-1 text-red-400 hover:text-red-300"
                              >
                                <Trash2 size={16} />
                              </button>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          {pestanaActiva === 'sets' && (
            <div className="p-4">
              <div className="text-center text-gray-400 mt-8">
                <FolderPlus size={48} className="mx-auto mb-4 text-gray-600" />
                <p>Gestión de sets - En desarrollo</p>
              </div>
            </div>
          )}

          {pestanaActiva === 'cuentas' && (
            <div className="p-4">
              <div className="text-center text-gray-400 mt-8">
                <FileText size={48} className="mx-auto mb-4 text-gray-600" />
                <p>Gestión de cuentas - En desarrollo</p>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-gray-700 bg-gray-900">
          <div className="flex justify-between items-center">
            <div className="text-sm text-gray-400">
              💾 Los cambios se guardan directamente en la base de datos
            </div>
            <button
              onClick={handleClose}
              className="px-4 py-2 bg-gray-600 hover:bg-gray-500 text-white rounded"
            >
              Cerrar
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ModalClasificacionesPersistentes;
