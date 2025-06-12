import React from "react";

const IncidenciaDetalleModal = ({ abierta, incidencia = {}, onClose }) => {
  if (!abierta) return null;

  const { titulo, descripcion, detalle, items = [] } = incidencia;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-60 z-50 flex justify-center items-center">
      <div className="bg-gray-900 rounded-lg shadow-lg p-6 w-full max-w-lg relative text-white">
        <button
          onClick={onClose}
          className="absolute top-3 right-3 text-gray-400 hover:text-white text-xl"
        >
          &times;
        </button>
        <h2 className="text-xl font-semibold mb-4">{titulo}</h2>
        {descripcion && <p className="text-gray-300 mb-4">{descripcion}</p>}
        {detalle && (
          <div className="mb-4 max-h-60 overflow-y-auto whitespace-pre-wrap text-sm bg-gray-800 p-3 rounded">
            {detalle}
          </div>
        )}
        {items.length > 0 && (
          <ul className="list-disc list-inside text-gray-300 text-sm space-y-1">
            {items.map((item, idx) => (
              <li key={idx}>{item}</li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
};

export default IncidenciaDetalleModal;
