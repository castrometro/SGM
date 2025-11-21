// src/modules/contabilidad/crear-cierre/components/ClienteInfoCard.jsx
import { Building2, Calendar, FileCheck } from 'lucide-react';

/**
 * Tarjeta de información del cliente
 * Muestra datos básicos y resumen contable
 */
const ClienteInfoCard = ({ cliente, resumen }) => {
  return (
    <div className="bg-gray-800 p-6 rounded-lg shadow-lg">
      <div className="flex items-start gap-4">
        <div className="p-3 bg-blue-600 rounded-lg">
          <Building2 size={32} className="text-white" />
        </div>
        
        <div className="flex-1">
          <h2 className="text-2xl font-bold text-white mb-1">
            {cliente.nombre}
          </h2>
          <p className="text-gray-400 text-sm mb-4">
            RUT: {cliente.rut}
          </p>
          
          {resumen && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-green-600 rounded-lg">
                  <FileCheck size={20} className="text-white" />
                </div>
                <div>
                  <p className="text-xs text-gray-500">Cierres Completados</p>
                  <p className="text-lg font-semibold text-white">
                    {resumen.cierres_completados || 0}
                  </p>
                </div>
              </div>
              
              <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-600 rounded-lg">
                  <Calendar size={20} className="text-white" />
                </div>
                <div>
                  <p className="text-xs text-gray-500">Último Cierre</p>
                  <p className="text-lg font-semibold text-white">
                    {resumen.ultimo_periodo || 'N/A'}
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ClienteInfoCard;
