const PasoTarjeta = ({ titulo, contenido, estado, accesoLabel, accesoAction, accesoHabilitado = false }) => {
  return (
    <div className="bg-gray-800 p-4 rounded-lg shadow hover:shadow-lg transition-all flex flex-col justify-between h-full">
      <h3 className="text-lg font-semibold mb-3">{titulo}</h3>

      <div className="flex flex-col gap-2 text-sm text-gray-300 mb-4">
        {contenido}
      </div>

      <div className="flex justify-between items-center mt-auto pt-2 border-t border-gray-700">
        <span className="text-xs text-gray-400">Estado: <strong>{estado}</strong></span>
        <button
          disabled={!accesoHabilitado}
          onClick={accesoAction}
          className={`px-3 py-1 rounded text-sm font-medium transition ${
            accesoHabilitado
              ? "bg-blue-600 text-white hover:bg-blue-500"
              : "bg-gray-700 text-gray-400 cursor-not-allowed"
          }`}
        >
          {accesoLabel}
        </button>
      </div>
    </div>
  );
};

export default PasoTarjeta;
