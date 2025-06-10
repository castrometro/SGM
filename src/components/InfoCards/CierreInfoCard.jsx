import EstadoBadge from "../EstadoBadge";

const CierreInfoCard = ({ cierre, cliente }) => {

  return (
    <div className="bg-gray-800 p-6 rounded-lg shadow-lg">
      <div className="flex items-center gap-3 mb-2">
        <h2 className="text-2xl font-bold">{cliente?.nombre || "Cliente desconocido"}</h2>
        {cliente?.bilingue && (
          <span className="ml-2 bg-blue-600 text-white text-xs px-2 py-1 rounded-full shadow font-semibold flex items-center gap-1">
            <svg className="inline-block w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v2m0 4v2m0 4v2m0 4v2m8-10h-2m-4 0H8m-4 0H2m18 0c0 4.418-3.582 8-8 8s-8-3.582-8-8 3.582-8 8-8 8 3.582 8 8z" />
            </svg>
            Bilingüe
          </span>
        )}
      </div>
      <p className="text-gray-300 mb-1">RUT: {cliente?.rut}</p>
      <p className="text-gray-300 mb-1">Industria: {cliente?.industria_nombre || "—"}</p>
      <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="bg-gray-700 p-4 rounded">
          <h3 className="text-sm text-gray-400">Periodo</h3>
          <p className="text-lg font-semibold">{cierre?.periodo || "—"}</p>
        </div>
        <div className="bg-gray-700 p-4 rounded flex flex-col gap-2">
          <h3 className="text-sm text-gray-400">Estado del cierre</h3>
          <EstadoBadge estado={cierre?.estado} />
        </div>
        <div className="bg-gray-700 p-4 rounded">
          <h3 className="text-sm text-gray-400">Creado por</h3>
          <p className="text-lg font-semibold">{cierre?.creado_por || "—"}</p>
          {cierre?.fecha_creacion && (
            <span className="text-xs text-gray-400">
              {new Date(cierre.fecha_creacion).toLocaleString()}
            </span>
          )}
        </div>
        <div className="bg-gray-700 p-4 rounded">
          <h3 className="text-sm text-gray-400">Acceso rápido</h3>
          {cliente && (
            <a
              href={`/menu/clientes/${cliente.id}`}
              className="text-blue-400 text-base underline font-semibold"
            >
              Ver ficha del cliente
            </a>
          )}
        </div>
      </div>
    </div>
  );
};

export default CierreInfoCard;
