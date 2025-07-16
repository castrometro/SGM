import React, { useState, useEffect } from 'react';
import { obtenerClientesAsignados, obtenerTodosLosClientes } from '../api/clientes';
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

        const data =
          userData.tipo_usuario === "gerente"
            ? await obtenerTodosLosClientes()
            : await obtenerClientesAsignados();
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
      <div className="flex items-center gap-4 mb-4">
        <h1 className="text-3xl font-bold">Lista de Clientes</h1>
        <span className="px-3 py-1 rounded-full bg-blue-600 text-white text-sm font-semibold">
          {areaActiva}
        </span>
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
          <p className="text-gray-300">No se encontraron clientes.</p>
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
