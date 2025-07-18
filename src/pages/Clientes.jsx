import React, { useState, useEffect } from 'react';
import { obtenerClientesAsignados, obtenerTodosLosClientes, obtenerClientesPorArea } from '../api/clientes';
import { obtenerUsuario } from '../api/auth';
import ClienteRow from '../components/ClienteRow';

const Clientes = () => {
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
        const userData = await obtenerUsuario();

        setUsuario(userData);
        

        // ¿Cómo es tu array de áreas? (ajusta si es array de objetos)
        let area = null;
        if (userData.area_activa) {
          area = userData.area_activa;
        } else if (userData.areas && userData.areas.length > 0) {
          // Si es array de objetos: area = userData.areas[0].nombre || userData.areas[0]
          area = userData.areas[0].nombre || userData.areas[0];
        } else {
          setError("No tienes un área activa asignada. Contacta a tu administrador.");
          setCargando(false);
          return;
        }
        setAreaActiva(area);
        localStorage.setItem("area_activa", area);

        let data;
        if (userData.tipo_usuario === "gerente") {
          // Gerentes ven todos los clientes de sus áreas asignadas
          data = await obtenerClientesPorArea();
        } else if (userData.tipo_usuario === "analista") {
          // Analistas ven solo los clientes que tienen asignados
          data = await obtenerClientesAsignados();
        } else if (userData.tipo_usuario === "supervisor") {
          // Supervisores ven clientes del área que supervisan
          data = await obtenerClientesPorArea();
        } else {
          // Por defecto, usar clientes por área
          data = await obtenerClientesPorArea();
        }
        
        console.log('=== DEBUG: Clientes cargados ===');
        console.log('Tipo usuario:', userData.tipo_usuario);
        console.log('Área activa:', area);
        console.log('Total clientes:', data.length);
        console.log('Clientes:', data);
        console.log('===============================');
        
        setClientes(data);
      } catch (err) {
        setError("No se pudo cargar el usuario o los clientes. Intenta más tarde.");
        console.error("Error al cargar usuario/clientes:", err);
      }
      setCargando(false);
    };

    cargarDatos();
  }, []);

  const clientesFiltrados = clientes.filter((cliente) =>
    cliente.nombre.toLowerCase().includes(filtro.toLowerCase()) ||
    cliente.rut.toLowerCase().includes(filtro.toLowerCase())
  );

  if (cargando) {
    return (
      <div className="text-white flex items-center justify-center h-64">
        Cargando clientes...
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
    <div className="text-white">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-4">
          <h1 className="text-3xl font-bold">Lista de Clientes</h1>
          <span className="px-3 py-1 rounded-full bg-blue-600 text-white text-sm font-semibold">
            {areaActiva}
          </span>
        </div>
        <div className="text-gray-400 text-sm">
          {clientes.length} cliente{clientes.length !== 1 ? 's' : ''} en tu área
          <button
            onClick={() => {
              const debugInfo = `
=== DEBUG: Carga de Clientes por Área ===
Usuario: ${usuario?.nombre} ${usuario?.apellido}
Tipo: ${usuario?.tipo_usuario}
Área Activa: ${areaActiva}
Áreas del Usuario: ${usuario?.areas?.map(a => a.nombre || a).join(', ') || 'N/A'}

Total Clientes Cargados: ${clientes.length}
Clientes Después del Filtro: ${clientesFiltrados.length}
Filtro Actual: "${filtro}"

ENDPOINT USADO:
${usuario?.tipo_usuario === "gerente" ? "📊 /clientes-por-area/ (Gerente - clientes de sus áreas)" :
  usuario?.tipo_usuario === "analista" ? "👤 /clientes/asignados/ (Analista - solo asignados)" :
  usuario?.tipo_usuario === "supervisor" ? "👁️ /clientes-por-area/ (Supervisor - área supervisada)" :
  "🔧 /clientes-por-area/ (Por defecto)"
}

CLIENTES ENCONTRADOS:
${clientes.slice(0, 5).map((c, i) => 
  `${i + 1}. ${c.nombre} (${c.rut}) - Áreas: ${c.areas_efectivas?.map(a => a.nombre).join(', ') || 'Sin áreas'}`
).join('\n')}
${clientes.length > 5 ? `... y ${clientes.length - 5} más` : ''}
=====================================`;
              alert(debugInfo);
            }}
            className="ml-2 text-xs text-blue-400 hover:text-blue-300 underline"
          >
            🔍 Debug
          </button>
        </div>
      </div>

      <input
        type="text"
        placeholder="Buscar por nombre o RUT..."
        className="mb-4 p-2 rounded bg-gray-700 text-white w-full"
        value={filtro}
        onChange={(e) => setFiltro(e.target.value)}
      />

      <div className="bg-gray-800 p-6 rounded-lg shadow-lg">
        {clientesFiltrados.length === 0 ? (
          <div className="text-center py-8">
            {clientes.length === 0 ? (
              <div>
                <p className="text-gray-300 mb-2">No hay clientes en tu área "{areaActiva}".</p>
                <p className="text-gray-500 text-sm">
                  {usuario.tipo_usuario === "analista" 
                    ? "No tienes clientes asignados. Contacta a tu supervisor."
                    : "No hay clientes registrados para esta área."
                  }
                </p>
              </div>
            ) : (
              <p className="text-gray-300">
                No se encontraron clientes que coincidan con "{filtro}".
              </p>
            )}
          </div>
        ) : (
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-gray-700">
                <th className="p-2">Cliente</th>
                <th className="p-2">RUT</th>
                <th className="p-2 text-center">Último Cierre</th>
                <th className="p-2 text-center">Estado Actual</th>
                <th className="p-2 text-center">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {clientesFiltrados.map((cliente) => (
                <ClienteRow
                  key={cliente.id}
                  cliente={cliente}
                  areaActiva={areaActiva}
                />
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

export default Clientes;
