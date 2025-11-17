import { Wrench } from "lucide-react";
import { motion } from "framer-motion";

/**
 * InfoBanner - Banner informativo para la sección de herramientas
 */
const InfoBanner = () => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.3 }}
      className="bg-purple-900/20 border border-purple-500/30 rounded-lg p-6"
    >
      <div className="flex items-start">
        <div className="p-2 bg-purple-600 rounded-lg mr-4 flex-shrink-0">
          <Wrench className="w-5 h-5 text-white" />
        </div>
        <div>
          <h3 className="font-semibold text-purple-400 mb-2">
            Centro de Herramientas de Contabilidad
          </h3>
          <p className="text-gray-300 text-sm leading-relaxed mb-2">
            Accede a utilidades especializadas para la gestión contable, análisis de cuentas, 
            clasificaciones y reportes financieros.
          </p>
          <p className="text-gray-400 text-xs">
            Las herramientas marcadas como "Próximamente" se habilitarán conforme se completen 
            las pruebas de funcionalidad y seguridad.
          </p>
        </div>
      </div>
    </motion.div>
  );
};

export default InfoBanner;
