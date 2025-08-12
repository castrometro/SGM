import React from 'react';
import { useClientesData } from './hooks/useClientesData';
import DebugButton from './components/DebugButton';
import ClienteRow from '../../components/ClienteRow';
import { MESSAGES } from './config/clientesConfig';

const Clientes = () => {
  const {
    clientes,
    clientesFiltrados,
    filtro,
    setFiltro,
    usuario,
    areaActiva,
    cargando,
    error
  } = useClientesData();

  if (cargando) {
    return (
      <div className="text-white flex items-center justify-center h-64">
        {MESSAGES.loading}
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
        {MESSAGES.noUser}
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
          <DebugButton
            usuario={usuario}
            areaActiva={areaActiva}
            clientes={clientes}
            clientesFiltrados={clientesFiltrados}
            filtro={filtro}
          />
        </div>
      </div>

      <input
        type="text"
        placeholder={MESSAGES.searchPlaceholder}
        className="mb-4 p-2 rounded bg-gray-700 text-white w-full"
        value={filtro}
        onChange={(e) => setFiltro(e.target.value)}
      />

      <div className="bg-gray-800 p-6 rounded-lg shadow-lg">
        {clientesFiltrados.length === 0 ? (
          <div className="text-center py-8">
            {clientes.length === 0 ? (
              <div>
                <p className="text-gray-300 mb-2">{MESSAGES.noClients} "{areaActiva}".</p>
                <p className="text-gray-500 text-sm">
                  {usuario.tipo_usuario === "analista" 
                    ? MESSAGES.analistaNoClients
                    : MESSAGES.defaultNoClients
                  }
                </p>
              </div>
            ) : (
              <p className="text-gray-300">
                {MESSAGES.noClientsFound} "{filtro}".
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
