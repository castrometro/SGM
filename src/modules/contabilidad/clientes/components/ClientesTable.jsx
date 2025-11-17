// src/modules/contabilidad/clientes/components/ClientesTable.jsx
import ClienteRow from './ClienteRow';

/**
 * 📊 Componente ClientesTable
 * Tabla responsive de clientes con vista de cards en móvil
 */
const ClientesTable = ({ clientes, areaActiva }) => {
  return (
    <>
      {/* Vista Cards - Móvil/Tablet */}
      <div className="lg:hidden space-y-3">
        {clientes.map((cliente, idx) => (
          <ClienteRow
            key={cliente.id}
            cliente={cliente}
            areaActiva={areaActiva}
            index={idx}
          />
        ))}
      </div>

      {/* Vista Tabla - Desktop */}
      <div className="hidden lg:block overflow-x-auto">
        <table className="w-full text-left">
          <thead>
            <tr className="border-b border-gray-700">
              <th className="p-2 text-gray-300">Cliente</th>
              <th className="p-2 text-gray-300">RUT</th>
              <th className="p-2 text-center text-gray-300">Último Cierre</th>
              <th className="p-2 text-center text-gray-300">Estado Actual</th>
              <th className="p-2 text-center text-gray-300">Usuario Responsable</th>
              <th className="p-2 text-center text-gray-300">Acciones</th>
            </tr>
          </thead>
          <tbody>
            {clientes.map((cliente, idx) => (
              <ClienteRow
                key={cliente.id}
                cliente={cliente}
                areaActiva={areaActiva}
                index={idx}
              />
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
};

export default ClientesTable;
