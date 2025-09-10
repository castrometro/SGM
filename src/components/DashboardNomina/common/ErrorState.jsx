import React from 'react';
import { AlertCircle } from 'lucide-react';

const ErrorState = ({ message='Error al cargar', onBack }) => (
  <div className="min-h-screen bg-gray-900 flex items-center justify-center">
    <div className="text-center">
      <div className="bg-red-600 w-12 h-12 rounded-full flex items-center justify-center mx-auto mb-4">
        <AlertCircle className="text-white" size={24} />
      </div>
      <h3 className="text-xl font-semibold text-white mb-2">Error al cargar</h3>
      <p className="text-gray-400 mb-4">{message}</p>
      {onBack && (
        <button onClick={onBack} className="bg-teal-600 hover:bg-teal-700 text-white px-4 py-2 rounded-lg transition-colors">
          Regresar
        </button>
      )}
    </div>
  </div>
);

export default ErrorState;
