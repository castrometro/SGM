import { AlertTriangle } from "lucide-react";

const IncidenciaCard = ({ titulo, descripcion, items = [] }) => {
  return (
    <div className="bg-gray-800 p-4 rounded-lg shadow flex flex-col gap-2">
      <div className="flex items-center gap-2 mb-2">
        <AlertTriangle size={18} className="text-yellow-400" />
        <h4 className="font-semibold text-white">{titulo}</h4>
      </div>
      {descripcion && <p className="text-gray-300 text-xs mb-2">{descripcion}</p>}
      {items.length > 0 && (
        <ul className="list-disc list-inside text-gray-300 text-xs space-y-1">
          {items.map((item, idx) => (
            <li key={idx}>{item}</li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default IncidenciaCard;
