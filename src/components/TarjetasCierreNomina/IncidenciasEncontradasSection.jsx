import { useState } from "react";
import { AlertOctagon, ChevronDown, ChevronRight } from "lucide-react";
import IncidenciaCard from "./IncidenciasEncontradas/IncidenciaCard";

const IncidenciasEncontradasSection = () => {
  const [expandido, setExpandido] = useState(true);

  const categorias = [
    {
      id: "info-faltante",
      titulo: "Información Faltante",
      descripcion:
        "Comparar la información del archivo Movimientos con los datos de Finiquitos, Incidencias/Ausentismos e Ingresos.",
      items: [],
    },
  ];

  return (
    <section className="space-y-6">
      <div
        className="flex items-center justify-between cursor-pointer hover:bg-gray-800/50 p-3 -m-3 rounded-lg transition-colors"
        onClick={() => setExpandido(!expandido)}
      >
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-10 h-10 bg-red-600 rounded-lg">
            <AlertOctagon size={20} className="text-white" />
          </div>
          <div>
            <h2 className="text-xl font-semibold text-white">Incidencias Encontradas</h2>
            <p className="text-gray-400 text-sm">Categorias de incidencias detectadas</p>
          </div>
        </div>
        {expandido ? (
          <ChevronDown size={20} className="text-gray-400" />
        ) : (
          <ChevronRight size={20} className="text-gray-400" />
        )}
      </div>

      {expandido && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {categorias.map((cat) => (
            <IncidenciaCard
              key={cat.id}
              titulo={cat.titulo}
              descripcion={cat.descripcion}
              items={cat.items}
            />
          ))}
        </div>
      )}
    </section>
  );
};

export default IncidenciasEncontradasSection;
