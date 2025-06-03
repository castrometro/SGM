import { useState } from "react";

const ModalTabla = ({ abierto, 
  onClose, titulo, columnas, 
  datos, editable = false, 
  onEliminarTodos, eliminando = false, 
  errorEliminando = '' 
}) => {
  const [confirmando, setConfirmando] = useState(false);

  if (!abierto) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black bg-opacity-40 flex items-center justify-center">
      <div className="bg-gray-800 rounded-xl shadow-lg p-6 w-full max-w-lg relative text-white">
        <h2 className="text-xl font-semibold mb-4">{titulo}</h2>
        <button
          className="absolute top-3 right-3 text-gray-400 hover:text-red-500"
          onClick={onClose}
        >✕</button>
        <div className="overflow-y-auto" style={{ maxHeight: "380px" }}>
          <table className="w-full text-left">
            <thead>
              <tr>
                {columnas.map((col, i) => (
                  <th key={i} className="px-2 py-2 border-b font-semibold">{col.label}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {datos.length === 0 ? (
                <tr>
                  <td colSpan={columnas.length} className="text-center py-10 text-gray-400">
                    No hay tipos de documento cargados.
                  </td>
                </tr>
              ) : (
                datos.map((fila, idx) => (
                  <tr key={idx} className="hover:bg-gray-700">
                    {columnas.map((col, i) => (
                      <td key={i} className="px-2 py-2 border-b">{fila[col.key]}</td>
                    ))}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        {/* Botón Eliminar */}
        {editable && (
          <div className="mt-5 flex justify-end">
            {confirmando ? (
              <div className="flex gap-2 items-center">
                <span>¿Confirmar eliminación?</span>
                <button
                  className="bg-red-600 hover:bg-red-700 px-3 py-1 rounded font-bold flex items-center gap-2"
                  onClick={onEliminarTodos}
                  disabled={eliminando}
                >
                  {eliminando && (
                    <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none"/>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"/>
                    </svg>
                  )}
                  Sí, eliminar
                </button>
                <button
                  className="bg-gray-600 hover:bg-gray-500 px-3 py-1 rounded"
                  onClick={() => setConfirmando(false)}
                  disabled={eliminando}
                >Cancelar</button>
              </div>
            ) : (
              <button
                className="bg-red-600 hover:bg-red-700 px-4 py-2 rounded font-bold"
                onClick={() => setConfirmando(true)}
              >Eliminar todos</button>
            )}
          </div>
        )}
        {errorEliminando && (
          <div className="mt-2 text-red-400 text-xs text-right">{errorEliminando}</div>
        )}
      </div>
    </div>
  );
};

export default ModalTabla;
