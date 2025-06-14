import { useEffect } from "react";
import { CheckCircle, XCircle, X } from "lucide-react";

const Notificacion = ({ tipo, mensaje, visible, onClose, duracion = 3000 }) => {
  useEffect(() => {
    if (visible && duracion > 0) {
      const timer = setTimeout(() => {
        onClose();
      }, duracion);
      return () => clearTimeout(timer);
    }
  }, [visible, duracion, onClose]);

  if (!visible) return null;

  const esExito = tipo === "exito";
  const iconColor = esExito ? "text-green-400" : "text-red-400";
  const bgColor = esExito ? "bg-green-600/20 border-green-600" : "bg-red-600/20 border-red-600";
  const textColor = esExito ? "text-green-400" : "text-red-400";

  return (
    <div className={`fixed top-4 right-4 z-[60] ${bgColor} border rounded-lg px-4 py-3 shadow-lg max-w-sm`}>
      <div className="flex items-center gap-3">
        {esExito ? (
          <CheckCircle size={20} className={iconColor} />
        ) : (
          <XCircle size={20} className={iconColor} />
        )}
        <span className={`${textColor} text-sm flex-1`}>{mensaje}</span>
        <button
          onClick={onClose}
          className={`${iconColor} hover:opacity-70 transition-opacity`}
        >
          <X size={16} />
        </button>
      </div>
    </div>
  );
};

export default Notificacion;
