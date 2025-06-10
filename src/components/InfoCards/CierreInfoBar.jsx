import EstadoBadge from "../EstadoBadge";

const CierreInfoBar = ({ cierre, cliente }) => {

  return (
    <div className="bg-gray-800 px-8 py-6 rounded-xl shadow flex flex-wrap items-center gap-6 mb-10 w-full">
      {/* Nombre + bilingüe */}
      <div className="flex items-center gap-2">
        <span className="text-2xl font-bold text-white">{cliente?.nombre || "Cliente desconocido"}</span>
        {cliente?.bilingue && (
          <span className="bg-blue-600 text-white text-xs px-2 py-1 rounded-full shadow font-semibold flex items-center gap-1">
            <svg className="inline-block w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v2m0 4v2m0 4v2m0 4v2m8-10h-2m-4 0H8m-4 0H2m18 0c0 4.418-3.582 8-8 8s-8-3.582-8-8 3.582-8 8-8 8 3.582 8 8z" />
            </svg>
            Bilingüe
          </span>
        )}
      </div>
      {/* RUT */}
      <div className="text-gray-300 text-base">
        <span className="font-bold">RUT:</span> {cliente?.rut}
      </div>
      {/* Industria */}
      <div className="text-gray-300 text-base">
        <span className="font-bold">Industria:</span> {cliente?.industria_nombre || "—"}
      </div>
      {/* Periodo */}
      <div className="text-gray-300 text-base">
        <span className="font-bold">Periodo:</span> <span className="text-white font-bold">{cierre?.periodo || "—"}</span>
      </div>
      {/* Estado */}
      <div className="flex items-center gap-2">
        <span className="font-bold text-gray-300">Estado:</span>
        <EstadoBadge estado={cierre?.estado} size="md" />
      </div>
      {/* Link ficha cliente */}
      {cliente && (
        <div>
          <a
            href={`/menu/clientes/${cliente.id}`}
            className="!text-white text-base underline font-semibold"
          >
            Ver ficha del cliente
          </a>
        </div>
      )}
    </div>
  );
};

export default CierreInfoBar;
