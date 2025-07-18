// src/components/Gerente/AdminSistema.jsx
import { useState, useEffect } from 'react';
import { 
  obtenerUsuarios, 
  crearUsuario, 
  actualizarUsuario,
  eliminarUsuario,
  obtenerClientes,
  crearCliente,
  actualizarCliente,
  eliminarCliente,
  obtenerAreas,
  obtenerIndustrias,
  obtenerMetricasSistema
} from '../../api/gerente';
import { 
  Users, 
  UserPlus, 
  Building, 
  Plus,
  Edit3,
  Trash2,
  Shield,
  Activity,
  Server,
  Database,
  Clock,
  AlertCircle,
  CheckCircle,
  Settings,
  Mail,
  Phone,
  FileText,
  Package,
  Bug
} from 'lucide-react';

const AdminSistema = () => {
  const [activeTab, setActiveTab] = useState('usuarios');
  const [usuarios, setUsuarios] = useState([]);
  const [clientes, setClientes] = useState([]);
  const [areas, setAreas] = useState([]);
  const [industrias, setIndustrias] = useState([]);
  const [metricas, setMetricas] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showDebug, setShowDebug] = useState(false);
  
  // Estado para bloqueo de desarrollo
  const [enDesarrollo] = useState(true); // Cambiar a false cuando esté listo
  
  // Estados para formularios
  const [showUserForm, setShowUserForm] = useState(false);
  const [showClientForm, setShowClientForm] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [showDeleteClientConfirm, setShowDeleteClientConfirm] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [editingClient, setEditingClient] = useState(null);
  const [deletingUser, setDeletingUser] = useState(null);
  const [deletingClient, setDeletingClient] = useState(null);
  const [userForm, setUserForm] = useState({
    nombre: '',
    apellido: '',
    correo_bdo: '',
    tipo_usuario: 'analista',
    area: '',
    cargo_bdo: '',
    is_active: true,
    password: '',
    password_confirm: ''
  });
  const [clientForm, setClientForm] = useState({
    nombre: '',
    rut: '',
    bilingue: false,
    industria: '',
    areas: [] // Agregar areas al formulario
  });

  useEffect(() => {
    cargarDatos();
  }, [activeTab]);

  const cargarDatos = async () => {
    try {
      setLoading(true);
      setError('');
      
      if (activeTab === 'usuarios') {
        console.log('Cargando usuarios y áreas...');
        try {
          const [usuariosData, areasData] = await Promise.all([
            obtenerUsuarios(),
            obtenerAreas()
          ]);
          console.log('Usuarios obtenidos:', usuariosData);
          console.log('Áreas obtenidas:', areasData);
          setUsuarios(usuariosData || []);
          setAreas(areasData || []);
        } catch (userError) {
          console.error('Error específico al cargar usuarios:', userError);
          setError(`Error al cargar usuarios: ${userError.message || userError}`);
        }
      } else if (activeTab === 'clientes') {
        console.log('Cargando clientes e industrias...');
        try {
          const [clientesData, industriasData] = await Promise.all([
            obtenerClientes(),
            obtenerIndustrias()
          ]);
          console.log('Clientes obtenidos:', clientesData);
          console.log('Industrias obtenidas:', industriasData);
          setClientes(clientesData || []);
          setIndustrias(industriasData || []);
        } catch (clientError) {
          console.error('Error específico al cargar clientes:', clientError);
          setError(`Error al cargar clientes: ${clientError.message || clientError}`);
        }
      } else if (activeTab === 'sistema') {
        console.log('Cargando métricas...');
        try {
          const metricasData = await obtenerMetricasSistema();
          console.log('Métricas obtenidas:', metricasData);
          setMetricas(metricasData);
        } catch (metricasError) {
          console.error('Error específico al cargar métricas:', metricasError);
          setError(`Error al cargar métricas: ${metricasError.message || metricasError}`);
        }
      }
      
    } catch (err) {
      console.error('Error general cargando datos:', err);
      setError(`Error general del sistema: ${err.message || err}`);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateUser = async (e) => {
    e.preventDefault();
    
    // Limpiar errores previos
    setError('');
    
    // Validar que las contraseñas coincidan
    if (userForm.password !== userForm.password_confirm) {
      setError('Las contraseñas no coinciden');
      return;
    }
    
    // Validar longitud mínima de contraseña
    if (userForm.password.length < 8) {
      setError('La contraseña debe tener al menos 8 caracteres');
      return;
    }
    
    try {
      await crearUsuario(userForm);
      setShowUserForm(false);
      setUserForm({
        nombre: '',
        apellido: '',
        correo_bdo: '',
        password: '',
        password_confirm: '',
        tipo_usuario: 'analista',
        area: '',
        cargo_bdo: '',
        is_active: true
      });
      await cargarDatos();
    } catch (err) {
      console.error('Error creando usuario:', err);
      
      // Extraer mensaje específico del error
      let errorMessage = 'Error al crear el usuario';
      if (err.response && err.response.data && err.response.data.error) {
        errorMessage = err.response.data.error;
      } else if (err.message) {
        errorMessage = err.message;
      }
      
      setError(errorMessage);
    }
  };

  const handleUpdateUser = async (e) => {
    e.preventDefault();
    try {
      await actualizarUsuario(editingUser.id, userForm);
      setEditingUser(null);
      setShowUserForm(false);
      setUserForm({
        nombre: '',
        apellido: '',
        correo_bdo: '',
        tipo_usuario: 'analista',
        area: '',
        cargo_bdo: '',
        is_active: true
      });
      await cargarDatos();
    } catch (err) {
      console.error('Error actualizando usuario:', err);
      setError('Error al actualizar el usuario');
    }
  };

  const handleCreateClient = async (e) => {
    e.preventDefault();
    try {
      setError(''); // Limpiar errores previos
      
      // Automáticamente asignar área de Contabilidad si no se especifica
      const clienteData = {
        ...clientForm,
        areas: clientForm.areas.length > 0 ? clientForm.areas : ['Contabilidad']
      };
      
      if (editingClient) {
        // Actualizar cliente existente
        await actualizarCliente(editingClient.id, clienteData);
        setEditingClient(null);
      } else {
        // Crear nuevo cliente
        await crearCliente(clienteData);
      }
      
      setShowClientForm(false);
      setClientForm({
        nombre: '',
        rut: '',
        bilingue: false,
        industria: '',
        areas: []
      });
      await cargarDatos();
    } catch (err) {
      console.error('Error con cliente:', err);
      if (err.response?.data?.error) {
        setError(err.response.data.error);
      } else {
        setError(`Error al ${editingClient ? 'actualizar' : 'crear'} el cliente`);
      }
    }
  };

  const handleEditUser = (usuario) => {
    setEditingUser(usuario);
    setUserForm({
      nombre: usuario.nombre,
      apellido: usuario.apellido,
      correo_bdo: usuario.email, // El backend envía email pero internamente usa correo_bdo
      tipo_usuario: usuario.tipo_usuario,
      area: usuario.area,
      cargo_bdo: usuario.cargo_bdo || '',
      is_active: usuario.activo
    });
    setShowUserForm(true);
  };

  const handleEditClient = (cliente) => {
    setEditingClient(cliente);
    setClientForm({
      nombre: cliente.nombre,
      rut: cliente.rut,
      bilingue: cliente.bilingue || false,
      industria: cliente.industria || '',
      areas: cliente.areas_efectivas ? cliente.areas_efectivas.map(area => area.nombre) : []
    });
    setShowClientForm(true);
  };

  const handleDeleteClient = (cliente) => {
    setDeletingClient(cliente);
    setShowDeleteClientConfirm(true);
  };

  const confirmDeleteClient = async () => {
    try {
      await eliminarCliente(deletingClient.id);
      setShowDeleteClientConfirm(false);
      setDeletingClient(null);
      await cargarDatos();
    } catch (err) {
      console.error('Error eliminando cliente:', err);
      if (err.response?.data?.error) {
        setError(err.response.data.error);
      } else {
        setError('Error al eliminar el cliente');
      }
      setShowDeleteClientConfirm(false);
    }
  };

  const handleOpenClientForm = () => {
    setEditingClient(null);
    setClientForm({
      nombre: '',
      rut: '',
      bilingue: false,
      industria: '',
      areas: ['Contabilidad'] // Por defecto, asignar Contabilidad
    });
    setShowClientForm(true);
  };

  const getRoleColor = (role) => {
    const colors = {
      'gerente': 'bg-red-100 text-red-800 border-red-200',
      'supervisor': 'bg-blue-100 text-blue-800 border-blue-200',
      'analista': 'bg-green-100 text-green-800 border-green-200'
    };
    return colors[role] || 'bg-gray-100 text-gray-800 border-gray-200';
  };

  const formatearFecha = (fecha) => {
    if (!fecha) return 'Nunca';
    
    try {
      const date = new Date(fecha);
      // Verificar si la fecha es válida
      if (isNaN(date.getTime())) return 'Fecha inválida';
      
      return date.toLocaleDateString('es-CL', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch (error) {
      console.error('Error formateando fecha:', error, fecha);
      return 'Error en fecha';
    }
  };

  const handleOpenUserForm = () => {
    setError(''); // Limpiar errores previos
    setEditingUser(null);
    setUserForm({
      nombre: '',
      apellido: '',
      correo_bdo: '',
      password: '',
      password_confirm: '',
      tipo_usuario: 'analista',
      area: '',
      cargo_bdo: '',
      is_active: true
    });
    setShowUserForm(true);
  };

  const handleDeleteUser = (usuario) => {
    setDeletingUser(usuario);
    setShowDeleteConfirm(true);
  };

  const confirmDeleteUser = async () => {
    try {
      await eliminarUsuario(deletingUser.id);
      setShowDeleteConfirm(false);
      setDeletingUser(null);
      await cargarDatos();
    } catch (err) {
      console.error('Error eliminando usuario:', err);
      
      let errorMessage = 'Error al eliminar el usuario';
      if (err.response && err.response.data && err.response.data.error) {
        errorMessage = err.response.data.error;
      } else if (err.message) {
        errorMessage = err.message;
      }
      
      setError(errorMessage);
      setShowDeleteConfirm(false);
      setDeletingUser(null);
    }
  };

  const tabs = [
    { id: 'usuarios', label: 'Usuarios', icon: Users },
    { id: 'clientes', label: 'Clientes', icon: Building },
    { id: 'sistema', label: 'Sistema', icon: Server }
  ];

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold mb-2">Administración del Sistema</h1>
          <p className="text-gray-400">Gestión de usuarios, clientes y configuración del sistema</p>
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-700 mb-6">
          <nav className="flex space-x-8">
            {tabs.map((tab) => {
              const IconComponent = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`py-2 px-1 border-b-2 font-medium text-sm flex items-center ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-500'
                      : 'border-transparent text-gray-400 hover:text-gray-300 hover:border-gray-300'
                  }`}
                >
                  <IconComponent className="w-4 h-4 mr-2" />
                  {tab.label}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Error */}
        {error && (
          <div className="bg-red-600 text-white p-4 rounded-lg mb-6 flex items-center">
            <AlertCircle className="w-5 h-5 mr-2" />
            {error}
          </div>
        )}

        {/* Tab Content: Usuarios */}
        {activeTab === 'usuarios' && (
          <div>
            <div className="flex justify-between items-center mb-6">
              <div className="flex items-center space-x-3">
                <h2 className="text-xl font-semibold">Gestión de Usuarios</h2>
                <button
                  onClick={() => setShowDebug(!showDebug)}
                  className="text-gray-500 hover:text-gray-300 p-1 rounded transition-colors"
                  title="Toggle Debug Info"
                >
                  <Bug className="w-4 h-4" />
                </button>
              </div>
              <button
                onClick={handleOpenUserForm}
                className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg flex items-center"
              >
                <UserPlus className="w-4 h-4 mr-2" />
                Nuevo Usuario
              </button>
            </div>

            {/* Debug Info - Collapsible */}
            {showDebug && (
              <div className="bg-gray-800 p-3 rounded-lg mb-4 text-sm border-l-4 border-yellow-500">
                <p className="text-gray-300">
                  <strong>🐛 Debug Info:</strong><br/>
                  • Usuarios cargados: {usuarios.length}<br/>
                  • Estado loading: {loading ? 'Sí' : 'No'}<br/>
                  • Áreas disponibles: {areas.length} ({areas.join(', ')})<br/>
                  • Error: {error || 'Ninguno'}
                </p>
                {usuarios.length > 0 && (
                  <div className="mt-2 text-xs text-gray-400">
                    <strong>Usuarios encontrados:</strong><br/>
                    {usuarios.map((u, index) => (
                      <div key={index}>
                        • {u.nombre} {u.apellido} ({u.area || 'Sin área'}) 
                        - Último acceso: {u.ultimo_acceso ? formatearFecha(u.ultimo_acceso) : 'Nunca'}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Loading State */}
            {loading && (
              <div className="bg-gray-800 p-8 rounded-lg text-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-4"></div>
                <p className="text-gray-400">Cargando usuarios...</p>
              </div>
            )}

            {/* Empty State */}
            {!loading && usuarios.length === 0 && !error && (
              <div className="bg-gray-800 p-8 rounded-lg text-center">
                <Users className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-300 mb-2">No hay usuarios</h3>
                <p className="text-gray-400 mb-4">Comienza creando tu primer usuario del sistema</p>
                <button
                  onClick={handleOpenUserForm}
                  className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg flex items-center mx-auto"
                >
                  <UserPlus className="w-4 h-4 mr-2" />
                  Crear Primer Usuario
                </button>
              </div>
            )}

            {/* Lista de Usuarios */}
            {!loading && usuarios.length > 0 && (
              <div className="bg-gray-800 rounded-lg overflow-hidden">
                <table className="w-full">
                  <thead className="bg-gray-700">
                    <tr>
                      <th className="px-4 py-3 text-left text-sm font-medium">Usuario</th>
                      <th className="px-4 py-3 text-left text-sm font-medium">Rol</th>
                      <th className="px-4 py-3 text-left text-sm font-medium">Área</th>
                      <th className="px-4 py-3 text-left text-sm font-medium">Estado</th>
                      <th className="px-4 py-3 text-left text-sm font-medium">Último Acceso</th>
                      <th className="px-4 py-3 text-left text-sm font-medium">Acciones</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-700">
                    {usuarios.map((usuario) => (
                      <tr key={usuario.id} className="hover:bg-gray-750">
                        <td className="px-4 py-3">
                          <div>
                            <div className="font-medium">{usuario.nombre} {usuario.apellido}</div>
                            <div className="text-sm text-gray-400 flex items-center">
                              <Mail className="w-3 h-3 mr-1" />
                              {usuario.email}
                            </div>
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium border ${getRoleColor(usuario.tipo_usuario)}`}>
                            <Shield className="w-3 h-3 mr-1" />
                            {usuario.tipo_usuario}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-sm">{usuario.area || 'Sin asignar'}</td>
                        <td className="px-4 py-3">
                          {usuario.activo ? (
                            <span className="inline-flex items-center text-green-400 text-sm">
                              <CheckCircle className="w-4 h-4 mr-1" />
                              Activo
                            </span>
                          ) : (
                            <span className="inline-flex items-center text-red-400 text-sm">
                              <AlertCircle className="w-4 h-4 mr-1" />
                              Inactivo
                            </span>
                          )}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-400">
                          {usuario.ultimo_acceso ? formatearFecha(usuario.ultimo_acceso) : 'Nunca'}
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex space-x-2">
                            <button
                              onClick={() => handleEditUser(usuario)}
                              className="bg-gray-600 hover:bg-gray-700 px-3 py-1 rounded text-sm flex items-center"
                            >
                              <Edit3 className="w-3 h-3 mr-1" />
                              Editar
                            </button>
                            <button
                              onClick={() => handleDeleteUser(usuario)}
                              className="bg-red-600 hover:bg-red-700 px-3 py-1 rounded text-sm flex items-center"
                            >
                              <Trash2 className="w-3 h-3 mr-1" />
                              Eliminar
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* Tab Content: Clientes */}
        {activeTab === 'clientes' && (
          <div>
            <div className="flex justify-between items-center mb-6">
              <div>
                <h2 className="text-xl font-semibold">Gestión de Clientes de Contabilidad</h2>
                <p className="text-gray-400 text-sm mt-1">
                  Mostrando solo clientes con área de Contabilidad (directa o por servicios)
                </p>
              </div>
              <button
                onClick={handleOpenClientForm}
                className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-lg flex items-center"
              >
                <Plus className="w-4 h-4 mr-2" />
                Nuevo Cliente
              </button>
            </div>

            {/* Filtros de clientes */}
            <div className="bg-gray-800 rounded-lg p-4 mb-6">
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2">
                  <span className="text-sm text-gray-400">Filtros:</span>
                  <span className="px-2 py-1 bg-blue-600 text-xs rounded">
                    Área: Contabilidad
                  </span>
                </div>
                <div className="text-sm text-gray-400">
                  Total: {clientes.length} clientes
                </div>
              </div>
            </div>

            {/* Tabla de Clientes */}
            <div className="bg-gray-800 rounded-lg overflow-hidden">
              <table className="w-full">
                <thead className="bg-gray-700">
                  <tr>
                    <th className="px-4 py-3 text-left">Nombre</th>
                    <th className="px-4 py-3 text-left">RUT</th>
                    <th className="px-4 py-3 text-left">Áreas</th>
                    <th className="px-4 py-3 text-left">Bilingüe</th>
                    <th className="px-4 py-3 text-left">Industria</th>
                    <th className="px-4 py-3 text-left">Fecha Registro</th>
                    <th className="px-4 py-3 text-center">Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  {clientes.map((cliente) => (
                    <tr key={cliente.id} className="border-t border-gray-700 hover:bg-gray-750">
                      <td className="px-4 py-3 font-medium">{cliente.nombre}</td>
                      <td className="px-4 py-3 text-gray-300">{cliente.rut}</td>
                      <td className="px-4 py-3">
                        <div className="flex flex-wrap gap-1">
                          {cliente.areas_efectivas && cliente.areas_efectivas.length > 0 ? (
                            cliente.areas_efectivas.map((area, index) => (
                              <span
                                key={index}
                                className={`px-2 py-1 rounded text-xs ${
                                  area.nombre === 'Contabilidad' 
                                    ? 'bg-blue-600 text-white' 
                                    : 'bg-gray-600 text-gray-300'
                                }`}
                              >
                                {area.nombre}
                              </span>
                            ))
                          ) : (
                            <span className="px-2 py-1 bg-gray-600 text-gray-300 rounded text-xs">
                              Sin áreas
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-1 rounded text-xs ${
                          cliente.bilingue ? 'bg-green-600' : 'bg-gray-600'
                        }`}>
                          {cliente.bilingue ? 'Sí' : 'No'}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-gray-300">{cliente.industria_nombre || 'Sin especificar'}</td>
                      <td className="px-4 py-3 text-gray-300">{formatearFecha(cliente.fecha_registro)}</td>
                      <td className="px-4 py-3">
                        <div className="flex items-center justify-center space-x-2">
                          <button
                            onClick={() => handleEditClient(cliente)}
                            className="p-1 text-blue-400 hover:text-blue-300"
                            title="Editar cliente"
                          >
                            <Edit3 className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => handleDeleteClient(cliente)}
                            className="p-1 text-red-400 hover:text-red-300"
                            title="Eliminar cliente"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              
              {clientes.length === 0 && (
                <div className="text-center py-8 text-gray-400">
                  <Building className="w-12 h-12 mx-auto mb-2 opacity-50" />
                  <p>No hay clientes de Contabilidad registrados</p>
                  <button
                    onClick={handleOpenClientForm}
                    className="mt-2 text-blue-400 hover:text-blue-300"
                  >
                    Crear el primer cliente
                  </button>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Tab Content: Sistema */}
        {activeTab === 'sistema' && metricas && (
          <div>
            <h2 className="text-xl font-semibold mb-6">Métricas del Sistema</h2>
            
            {/* Métricas Generales */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
              <div className="bg-gray-800 p-4 rounded-lg">
                <div className="flex items-center">
                  <Users className="w-8 h-8 text-blue-500" />
                  <div className="ml-3">
                    <p className="text-sm text-gray-400">Usuarios Totales</p>
                    <p className="text-2xl font-bold">{metricas.usuarios_totales || 0}</p>
                  </div>
                </div>
              </div>
              <div className="bg-gray-800 p-4 rounded-lg">
                <div className="flex items-center">
                  <Building className="w-8 h-8 text-green-500" />
                  <div className="ml-3">
                    <p className="text-sm text-gray-400">Clientes Activos</p>
                    <p className="text-2xl font-bold">{metricas.clientes_activos || 0}</p>
                  </div>
                </div>
              </div>
              <div className="bg-gray-800 p-4 rounded-lg">
                <div className="flex items-center">
                  <Database className="w-8 h-8 text-purple-500" />
                  <div className="ml-3">
                    <p className="text-sm text-gray-400">Registros DB</p>
                    <p className="text-2xl font-bold">{metricas.registros_db || 0}</p>
                  </div>
                </div>
              </div>
              <div className="bg-gray-800 p-4 rounded-lg">
                <div className="flex items-center">
                  <Activity className="w-8 h-8 text-orange-500" />
                  <div className="ml-3">
                    <p className="text-sm text-gray-400">Actividad Hoy</p>
                    <p className="text-2xl font-bold">{metricas.actividad_hoy || 0}</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Estado del Sistema */}
            <div className="bg-gray-800 p-6 rounded-lg mb-6">
              <h3 className="text-lg font-semibold mb-4 flex items-center">
                <Server className="w-5 h-5 mr-2" />
                Estado del Sistema
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="font-medium mb-3">Servicios</h4>
                  <div className="space-y-2">
                    {metricas.servicios && Object.entries(metricas.servicios).map(([servicio, estado]) => (
                      <div key={servicio} className="flex justify-between items-center">
                        <span className="text-sm">{servicio}</span>
                        <span className={`px-2 py-1 rounded text-xs ${
                          estado === 'activo' ? 'bg-green-600' : 'bg-red-600'
                        }`}>
                          {estado}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
                <div>
                  <h4 className="font-medium mb-3">Recursos</h4>
                  <div className="space-y-3">
                    {metricas.recursos && Object.entries(metricas.recursos).map(([recurso, valor]) => (
                      <div key={recurso}>
                        <div className="flex justify-between text-sm mb-1">
                          <span>{recurso}</span>
                          <span>{valor}%</span>
                        </div>
                        <div className="w-full bg-gray-700 rounded-full h-2">
                          <div 
                            className={`h-2 rounded-full ${
                              valor > 80 ? 'bg-red-500' : valor > 60 ? 'bg-yellow-500' : 'bg-green-500'
                            }`}
                            style={{ width: `${valor}%` }}
                          ></div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Modal: Formulario Usuario */}
        {showUserForm && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-gray-800 p-6 rounded-lg w-full max-w-md">
              <h3 className="text-lg font-semibold mb-4">
                {editingUser ? 'Editar Usuario' : 'Nuevo Usuario'}
              </h3>
              <form onSubmit={editingUser ? handleUpdateUser : handleCreateUser}>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">Nombre</label>
                    <input
                      type="text"
                      value={userForm.nombre}
                      onChange={(e) => setUserForm({...userForm, nombre: e.target.value})}
                      className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Apellido</label>
                    <input
                      type="text"
                      value={userForm.apellido}
                      onChange={(e) => setUserForm({...userForm, apellido: e.target.value})}
                      className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Email</label>
                    <input
                      type="email"
                      value={userForm.correo_bdo}
                      onChange={(e) => {
                        setUserForm({...userForm, correo_bdo: e.target.value});
                        // Limpiar error si el usuario empieza a modificar el email
                        if (error && error.includes('email')) {
                          setError('');
                        }
                      }}
                      className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Cargo BDO</label>
                    <input
                      type="text"
                      value={userForm.cargo_bdo}
                      onChange={(e) => setUserForm({...userForm, cargo_bdo: e.target.value})}
                      className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2"
                      placeholder="Ej: Contador Senior, Analista Contable, etc."
                    />
                  </div>
                  
                  {/* Campos de contraseña solo al crear usuario nuevo */}
                  {!editingUser && (
                    <>
                      <div>
                        <label className="block text-sm font-medium mb-1">Contraseña</label>
                        <input
                          type="password"
                          value={userForm.password}
                          onChange={(e) => setUserForm({...userForm, password: e.target.value})}
                          className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2"
                          required
                          minLength="8"
                          placeholder="Mínimo 8 caracteres"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium mb-1">Confirmar Contraseña</label>
                        <input
                          type="password"
                          value={userForm.password_confirm}
                          onChange={(e) => setUserForm({...userForm, password_confirm: e.target.value})}
                          className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2"
                          required
                          minLength="8"
                          placeholder="Repetir contraseña"
                        />
                        {userForm.password && userForm.password_confirm && userForm.password !== userForm.password_confirm && (
                          <p className="text-red-400 text-xs mt-1">Las contraseñas no coinciden</p>
                        )}
                      </div>
                    </>
                  )}
                  
                  <div>
                    <label className="block text-sm font-medium mb-1">Rol</label>
                    <select
                      value={userForm.tipo_usuario}
                      onChange={(e) => setUserForm({...userForm, tipo_usuario: e.target.value})}
                      className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2"
                    >
                      <option value="analista">Analista</option>
                      <option value="supervisor">Supervisor</option>
                      <option value="gerente">Gerente</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Área</label>
                    <select
                      value={userForm.area}
                      onChange={(e) => setUserForm({...userForm, area: e.target.value})}
                      className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2"
                    >
                      <option value="">Seleccionar área</option>
                      {areas.map(area => (
                        <option key={area} value={area}>{area}</option>
                      ))}
                    </select>
                  </div>
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="is_active"
                      checked={userForm.is_active}
                      onChange={(e) => setUserForm({...userForm, is_active: e.target.checked})}
                      className="mr-2"
                    />
                    <label htmlFor="is_active" className="text-sm">Usuario activo</label>
                  </div>
                </div>
                <div className="flex justify-end space-x-3 mt-6">
                  <button
                    type="button"
                    onClick={() => {
                      setShowUserForm(false);
                      setEditingUser(null);
                      setUserForm({
                        nombre: '',
                        apellido: '',
                        correo_bdo: '',
                        password: '',
                        password_confirm: '',
                        tipo_usuario: 'analista',
                        area: '',
                        cargo_bdo: '',
                        is_active: true
                      });
                    }}
                    className="bg-gray-600 hover:bg-gray-700 px-4 py-2 rounded"
                  >
                    Cancelar
                  </button>
                  <button
                    type="submit"
                    className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded"
                  >
                    {editingUser ? 'Actualizar' : 'Crear'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Modal: Formulario Cliente */}
        {showClientForm && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-gray-800 p-6 rounded-lg w-full max-w-md">
              <h3 className="text-lg font-semibold mb-4">
                {editingClient ? 'Editar Cliente' : 'Nuevo Cliente'}
              </h3>
              <form onSubmit={handleCreateClient}>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium mb-1">Nombre *</label>
                    <input
                      type="text"
                      value={clientForm.nombre}
                      onChange={(e) => setClientForm({...clientForm, nombre: e.target.value})}
                      className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">RUT *</label>
                    <input
                      type="text"
                      value={clientForm.rut}
                      onChange={(e) => setClientForm({...clientForm, rut: e.target.value})}
                      className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2"
                      placeholder="12.345.678-9"
                      required
                    />
                  </div>
                  
                  {/* Selección de Áreas */}
                  <div>
                    <label className="block text-sm font-medium mb-1">Áreas *</label>
                    <div className="bg-gray-700 border border-gray-600 rounded px-3 py-2 min-h-[100px]">
                      <div className="grid grid-cols-1 gap-2">
                        {areas.map(area => (
                          <label key={area} className="flex items-center">
                            <input
                              type="checkbox"
                              checked={clientForm.areas.includes(area)}
                              onChange={(e) => {
                                if (e.target.checked) {
                                  setClientForm({
                                    ...clientForm,
                                    areas: [...clientForm.areas, area]
                                  });
                                } else {
                                  setClientForm({
                                    ...clientForm,
                                    areas: clientForm.areas.filter(a => a !== area)
                                  });
                                }
                              }}
                              className="mr-2"
                            />
                            <span className="text-sm text-white">{area}</span>
                          </label>
                        ))}
                      </div>
                      {clientForm.areas.length === 0 && (
                        <p className="text-gray-400 text-sm mt-2">
                          Se asignará automáticamente el área de Contabilidad
                        </p>
                      )}
                    </div>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium mb-1">Industria</label>
                    <select
                      value={clientForm.industria}
                      onChange={(e) => setClientForm({...clientForm, industria: e.target.value})}
                      className="w-full bg-gray-700 border border-gray-600 rounded px-3 py-2"
                    >
                      <option value="">Seleccionar industria</option>
                      {industrias.map(industria => (
                        <option key={industria.id} value={industria.nombre}>{industria.nombre}</option>
                      ))}
                    </select>
                  </div>
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      id="clienteBilingue"
                      checked={clientForm.bilingue}
                      onChange={(e) => setClientForm({...clientForm, bilingue: e.target.checked})}
                      className="mr-2"
                    />
                    <label htmlFor="clienteBilingue" className="text-sm">
                      Cliente bilingüe (requiere informes en inglés y español)
                    </label>
                  </div>
                </div>
                <div className="flex space-x-3 mt-6">
                  <button
                    type="submit"
                    className="flex-1 bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded"
                  >
                    {editingClient ? 'Actualizar' : 'Crear'} Cliente
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setShowClientForm(false);
                      setEditingClient(null);
                      setClientForm({
                        nombre: '',
                        rut: '',
                        bilingue: false,
                        industria: '',
                        areas: ['Contabilidad']
                      });
                    }}
                    className="flex-1 bg-gray-600 hover:bg-gray-700 px-4 py-2 rounded"
                  >
                    Cancelar
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Modal: Confirmación de Eliminación */}
        {showDeleteConfirm && deletingUser && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-gray-800 p-6 rounded-lg w-full max-w-md">
              <h3 className="text-lg font-semibold mb-4 text-red-400">
                Confirmar Eliminación
              </h3>
              <p className="text-gray-300 mb-6">
                ¿Estás seguro de que deseas eliminar al usuario{' '}
                <strong>{deletingUser.nombre} {deletingUser.apellido}</strong>?
              </p>
              <p className="text-sm text-gray-400 mb-6">
                Esta acción no se puede deshacer.
              </p>
              <div className="flex justify-end space-x-3">
                <button
                  onClick={() => {
                    setShowDeleteConfirm(false);
                    setDeletingUser(null);
                  }}
                  className="bg-gray-600 hover:bg-gray-700 px-4 py-2 rounded"
                >
                  Cancelar
                </button>
                <button
                  onClick={confirmDeleteUser}
                  className="bg-red-600 hover:bg-red-700 px-4 py-2 rounded"
                >
                  Eliminar
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Modal: Confirmación de Eliminación Cliente */}
        {showDeleteClientConfirm && deletingClient && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-gray-800 p-6 rounded-lg w-full max-w-md">
              <h3 className="text-lg font-semibold mb-4 text-red-400">
                Confirmar Eliminación de Cliente
              </h3>
              <p className="text-gray-300 mb-6">
                ¿Estás seguro de que deseas eliminar al cliente{' '}
                <strong>{deletingClient.nombre}</strong>?
              </p>
              <p className="text-sm text-gray-400 mb-6">
                Esta acción no se puede deshacer. Se verificará que no tenga asignaciones o cierres activos.
              </p>
              <div className="flex justify-end space-x-3">
                <button
                  onClick={() => {
                    setShowDeleteClientConfirm(false);
                    setDeletingClient(null);
                  }}
                  className="bg-gray-600 hover:bg-gray-700 px-4 py-2 rounded"
                >
                  Cancelar
                </button>
                <button
                  onClick={confirmDeleteClient}
                  className="bg-red-600 hover:bg-red-700 px-4 py-2 rounded"
                >
                  Eliminar Cliente
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Overlay de EN DESARROLLO */}
      {enDesarrollo && (
        <div className="fixed inset-0 bg-black bg-opacity-80 backdrop-blur-sm flex items-center justify-center z-[9999]">
          <div className="bg-gray-900 border-2 border-orange-500 rounded-lg p-8 max-w-md mx-4 text-center shadow-2xl">
            <div className="flex items-center justify-center mb-4">
              <Settings className="w-16 h-16 text-orange-500 animate-spin" />
            </div>
            <h2 className="text-3xl font-bold text-orange-500 mb-2">EN DESARROLLO</h2>
            <p className="text-gray-300 mb-4">
              Esta funcionalidad está actualmente en desarrollo y no está disponible.
            </p>
            <div className="flex items-center justify-center text-sm text-gray-400">
              <Clock className="w-4 h-4 mr-2" />
              Próximamente disponible
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminSistema;
