import { useEffect } from "react";
import { CheckCircle, XCircle, X, AlertTriangle, Info } from "lucide-react";

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

  // Normalizar tipos
  const tipoNormalizado = tipo === "exito" ? "success" : tipo;
  
  // Configuraciones de colores y iconos por tipo
  const configuraciones = {
    success: {
      icon: CheckCircle,
      iconColor: "text-green-400",
      bgColor: "bg-green-600/20 border-green-600",
      textColor: "text-green-400"
    },
    error: {
      icon: XCircle,
      iconColor: "text-red-400",
      bgColor: "bg-red-600/20 border-red-600",
      textColor: "text-red-400"
    },
    warning: {
      icon: AlertTriangle,
      iconColor: "text-yellow-400",
      bgColor: "bg-yellow-600/20 border-yellow-600",
      textColor: "text-yellow-400"
    },
    info: {
      icon: Info,
      iconColor: "text-blue-400",
      bgColor: "bg-blue-600/20 border-blue-600",
      textColor: "text-blue-400"
    }
  };

  const config = configuraciones[tipoNormalizado] || configuraciones.error;
  const Icon = config.icon;

  return (
    <div className={`fixed bottom-50 right-4 z-[60] ${config.bgColor} border rounded-lg px-4 py-3 shadow-lg max-w-sm`}>
      <div className="flex items-center gap-3">
        <Icon size={20} className={config.iconColor} />
        <span className={`${config.textColor} text-sm flex-1`}>{mensaje}</span>
        <button
          onClick={onClose}
          className={`${config.iconColor} hover:opacity-70 transition-opacity`}
        >
          <X size={16} />
        </button>
      </div>
    </div>
  );
};

export default Notificacion;
