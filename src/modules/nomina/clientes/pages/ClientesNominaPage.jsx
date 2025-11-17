// src/modules/nomina/clientes/pages/ClientesNominaPage.jsx
import { useState, useEffect } from 'react';
import { 
  obtenerClientesAsignados, 
  obtenerClientesPorArea, 
  obtenerUsuario 
} from '../api/clientes.api';
import { 
  determinarAreaActiva, 
  determinarEndpointClientes, 
  filtrarClientes,
  generarInfoDebug 
} from '../utils/clientesHelpers';
import { MENSAJES } from '../constants/clientes.constants';
import ClientesListHeader from '../components/ClientesListHeader';
import ClientesTable from '../components/ClientesTable';
import EmptyState from '../components/EmptyState';

/**
 * 📄 Página Principal de Clientes de Nómina
 * Lista todos los clientes de nómina según el tipo de usuario
 */
const ClientesNominaPage = () => {
  const [clientes, setClientes] = useState([]);
  const [filtro, setFiltro] = useState("");
  const [usuario, setUsuario] = useState(null);
  const [areaActiva, setAreaActiva] = useState(null);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const cargarDatos = async () => {
      setCargando(true);
      setError("");
      
      try {
        // 1. Obtener datos del usuario
        const userData = await obtenerUsuario();
        setUsuario(userData);

        // 2. Determinar área activa
        const area = determinarAreaActiva(userData);
        if (!area) {
          setError(MENSAJES.SIN_AREA);
          setCargando(false);
          return;
        }
        setAreaActiva(area);
        localStorage.setItem("area_activa", area);

        // 3. Obtener clientes según tipo de usuario
        const endpoint = determinarEndpointClientes(userData.tipo_usuario);
        let data;
        
        if (endpoint === 'clientesAsignados') {
          data = await obtenerClientesAsignados();
        } else {
          data = await obtenerClientesPorArea();
        }

        console.log('=== DEBUG: Clientes de Nómina cargados ===');
        console.log('Tipo usuario:', userData.tipo_usuario);
        console.log('Área activa:', area);
        console.log('Total clientes:', data.length);
        console.log('Endpoint usado:', endpoint);
        console.log('=========================================');

        setClientes(data);
      } catch (err) {
        setError(MENSAJES.ERROR_CARGA);
        console.error("Error al cargar usuario/clientes de nómina:", err);
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
        className="mb-4 p-2.5 sm:p-3 rounded-lg bg-gray-700 text-white w-full text-sm sm:text-base focus:outline-none focus:ring-2 focus:ring-teal-500 transition-all"
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

export default ClientesNominaPage;
