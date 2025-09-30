import { X } from "lucide-react";

const ModalCorreccionLibro = ({ abierto, onCerrar, children }) => {
  if (!abierto) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/70" onClick={onCerrar} />
      <div className="relative bg-gray-900 border border-gray-700 rounded-xl w-full max-w-3xl mx-4 p-4">
        <button
          aria-label="Cerrar"
          onClick={onCerrar}
          className="absolute top-3 right-3 p-1 rounded hover:bg-gray-800 text-gray-300"
        >
          <X size={18} />
        </button>
        {children}
      </div>
    </div>
  );
};

export default ModalCorreccionLibro;
