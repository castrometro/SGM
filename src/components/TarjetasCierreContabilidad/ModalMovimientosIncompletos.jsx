import React from "react";

const ModalMovimientosIncompletos = ({ abierto, onClose, movimientos = [] }) => {
  if (!abierto) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black bg-opacity-60 flex items-center justify-center">
      <div className="bg-gray-800 rounded-xl shadow-lg p-6 w-full max-w-3xl text-white relative">
        <button onClick={onClose} className="absolute top-3 right-3 text-gray-400 hover:text-white text-xl">
          &times;
        </button>
        <h2 className="text-xl font-semibold mb-4">Movimientos con Incidencias</h2>
        {movimientos.length === 0 ? (
          <p className="text-gray-300">No hay movimientos con incidencias.</p>
        ) : (
          <div className="max-h-80 overflow-y-auto">
            <table className="min-w-full text-sm">
              <thead>
                <tr className="bg-gray-700 text-gray-200">
                  <th className="px-3 py-2 text-left">ID</th>
                  <th className="px-3 py-2 text-left">Cuenta</th>
                  <th className="px-3 py-2 text-left">Incidencias</th>
                </tr>
              </thead>
              <tbody>
                {movimientos.map((mov) => (
                  <tr key={mov.id} className="border-t border-gray-700">
                    <td className="px-3 py-2 whitespace-nowrap">{mov.id}</td>
                    <td className="px-3 py-2 whitespace-nowrap">
                      {mov.cuenta_codigo} - {mov.cuenta_nombre}
                    </td>
                    <td className="px-3 py-2">
                      <ul className="list-disc list-inside space-y-1">
                        {mov.incidencias.map((inc, idx) => (
                          <li key={idx}>{inc}</li>
                        ))}
                      </ul>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default ModalMovimientosIncompletos;
