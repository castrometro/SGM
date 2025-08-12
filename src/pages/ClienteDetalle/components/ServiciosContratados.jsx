import { formatMoney } from "../../../utils/format";

const ServiciosContratados = ({ servicios, areaActiva }) => {
  // Filtra los servicios que correspondan solo al área activa
  const serviciosFiltrados = areaActiva
    ? servicios.filter(s => s.area_nombre === areaActiva)
    : servicios;

  return (
    <div className="bg-gray-800 p-6 rounded-lg shadow-lg">
      <h2 className="text-xl font-bold mb-4">Servicios Contratados</h2>

      {serviciosFiltrados.length === 0 ? (
        <p className="text-gray-400 italic">
          Este cliente no tiene servicios registrados para tu área.
        </p>
      ) : (
        <ul className="list-disc list-inside space-y-2">
          {serviciosFiltrados.map((s) => (
            <li key={s.id} className="text-white">
              {s.servicio_nombre || "—"} — {formatMoney(s.valor)} {s.moneda}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default ServiciosContratados;
