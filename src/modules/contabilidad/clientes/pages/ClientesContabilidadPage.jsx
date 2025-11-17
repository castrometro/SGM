// src/modules/contabilidad/clientes/pages/ClientesContabilidadPage.jsx
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  obtenerClientesAsignados, 
  obtenerClientesPorArea, 
  obtenerUsuario 
} from '../api/clientes.api';
import { 
  determinarAreaActiva, 
  determinarEndpointClientes, 
  filtrarClientes,
  generarInfoDebug,
  validarAccesoContabilidad
} from '../utils/clientesHelpers';
import { MENSAJES } from '../constants/clientes.constants';
import ClientesListHeader from '../components/ClientesListHeader';
import ClientesTable from '../components/ClientesTable';
import EmptyState from '../components/EmptyState';

/**
 * 📄 Página Principal de Clientes de Contabilidad
 * Lista todos los clientes de contabilidad según el tipo de usuario
 * Valida acceso al área de Contabilidad antes de cargar datos
 */
const ClientesContabilidadPage = () => {
  const [clientes, setClientes] = useState([]);
  const [filtro, setFiltro] = useState("");
  const [usuario, setUsuario] = useState(null);
  const [areaActiva, setAreaActiva] = useState(null);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState("");
  const [hasAccess, setHasAccess] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    const cargarDatos = async () => {
      setCargando(true);
      setError("");
      
      try {
        // 1. Obtener datos del usuario
        const userData = await obtenerUsuario();
        setUsuario(userData);

        // 2. Validar acceso a Contabilidad
        const tieneAcceso = validarAccesoContabilidad(userData);
        setHasAccess(tieneAcceso);
        
        if (!tieneAcceso) {
          setError(MENSAJES.SIN_ACCESO);
          setCargando(false);
          return;
        }

        // 3. Determinar área activa
        const area = determinarAreaActiva(userData);
        if (!area) {
          setError(MENSAJES.SIN_AREA);
          setCargando(false);
          return;
        }
        setAreaActiva(area);
        localStorage.setItem("area_activa", area);

        // 4. Obtener clientes según tipo de usuario
        const endpoint = determinarEndpointClientes(userData.tipo_usuario);
        let data;
        
        if (endpoint === 'clientesAsignados') {
          data = await obtenerClientesAsignados();
        } else {
          data = await obtenerClientesPorArea();
        }

        console.log('=== DEBUG: Clientes de Contabilidad cargados ===');
        console.log('Tipo usuario:', userData.tipo_usuario);
        console.log('Área activa:', area);
        console.log('Total clientes:', data.length);
        console.log('Endpoint usado:', endpoint);
        console.log('=========================================');

        setClientes(data);
      } catch (err) {
        setError(MENSAJES.ERROR_CARGA);
        console.error("Error al cargar usuario/clientes de contabilidad:", err);
      }
      
      setCargando(false);
    };

    cargarDatos();
  }, []);

  const clientesFiltrados = filtrarClientes(clientes, filtro);

  const handleDebugClick = () => {
    const debugInfo = generarInfoDebug(
      usuario, 
      areaActiva, 
      clientes, 
      filtro, 
      clientesFiltrados
    );
    alert(debugInfo);
  };

  // Validando acceso
  if (cargando && hasAccess === null) {
    return (
      <div className="text-white flex items-center justify-center h-64">
        Validando acceso...
      </div>
    );
  }

  // Sin acceso
  if (hasAccess === false) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="max-w-md mx-auto text-center p-8">
          <div className="text-red-400 text-5xl mb-4">⚠️</div>
          <h2 className="text-2xl font-bold text-gray-100 mb-2">Acceso Denegado</h2>
          <p className="text-gray-400 mb-6">
            No tienes permisos para acceder a clientes de Contabilidad.
          </p>
          <button
            onClick={() => navigate('/menu')}
            className="px-6 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors"
          >
            Volver al Menú
          </button>
        </div>
      </div>
    );
  }

  // Estados de carga y error
  if (cargando) {
    return (
      <div className="text-white flex items-center justify-center h-64">
        {MENSAJES.CARGANDO}
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-red-400 flex items-center justify-center h-64">
        {error}
      </div>
    );
  }

  if (!usuario || !areaActiva) {
    return (
      <div className="text-white flex items-center justify-center h-64">
        No se pudo determinar tu área activa.
      </div>
    );
  }

  return (
    <div className="text-white px-4 sm:px-0">
      {/* Header con título y badge */}
      <ClientesListHeader 
        areaActiva={areaActiva}
        totalClientes={clientes.length}
        onDebugClick={handleDebugClick}
      />

      {/* Buscador */}
      <input
        type="text"
        placeholder="Buscar por nombre o RUT..."
        className="mb-4 p-2.5 sm:p-3 rounded-lg bg-gray-700 text-white w-full text-sm sm:text-base focus:outline-none focus:ring-2 focus:ring-purple-500 transition-all"
        value={filtro}
        onChange={(e) => setFiltro(e.target.value)}
      />

      {/* Contenedor de tabla/cards */}
      <div className="bg-gray-800 p-4 sm:p-6 rounded-lg shadow-lg">
        {clientesFiltrados.length === 0 ? (
          <EmptyState 
            totalClientes={clientes.length}
            filtro={filtro}
            areaActiva={areaActiva}
            tipoUsuario={usuario.tipo_usuario}
          />
        ) : (
          <ClientesTable 
            clientes={clientesFiltrados}
            areaActiva={areaActiva}
          />
        )}
      </div>
    </div>
  );
};

export default ClientesContabilidadPage;
