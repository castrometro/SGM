// src/modules/contabilidad/clientes/components/ClienteActions.jsx

/**
 * 🎯 Componente ClienteActions
 * Botones de acción para ver cliente y cierres
 */
const ClienteActions = ({ onVerCliente, onVerCierres, mobile = false }) => {
  return (
    <div className={`flex items-center ${mobile ? 'flex-col sm:flex-row' : ''} gap-2`}>
      <button
        onClick={onVerCliente}
        className={`${mobile ? 'w-full sm:w-auto' : ''} px-3 py-1.5 rounded-lg text-sm font-medium !text-white bg-blue-600 hover:bg-blue-700 transition-all hover:scale-105 active:scale-95 text-center`}
      >
        Ver Cliente
      </button>
      <button
        onClick={onVerCierres}
        className={`${mobile ? 'w-full sm:w-auto' : ''} px-3 py-1.5 rounded-lg text-sm font-medium text-white bg-gradient-to-r from-purple-500 to-indigo-500 hover:from-purple-600 hover:to-indigo-600 transition-all hover:scale-105 active:scale-95 flex items-center justify-center gap-1.5 shadow-sm`}
        title="Ver Cierres"
      >
        <svg className="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 13h2l2 6 4-14 3 8h6" />
        </svg>
        Ver Cierres
      </button>
    </div>
  );
};

export default ClienteActions;
