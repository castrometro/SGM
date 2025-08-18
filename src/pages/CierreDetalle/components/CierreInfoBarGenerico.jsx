import EstadoBadge from "../../../components/EstadoBadge";
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const CierreInfoBarGenerico = ({ 
  cierre, 
  cliente, 
  onCierreActualizado, 
  tipoModulo, 
  botonesPersonalizados = [], 
  manejarActualizarCustom = null,
  procesandoCustom = false 
}) => {
  const navigate = useNavigate();
  const [actualizandoEstado, setActualizandoEstado] = useState(false);

  const manejarActualizarEstado = async () => {
    // Si hay una función personalizada, usarla
    if (manejarActualizarCustom) {
      return manejarActualizarCustom();
    }

    // Función genérica por defecto
    setActualizandoEstado(true);
    try {
      console.log(`API de ${tipoModulo} aún no implementada`);
      alert(`La funcionalidad de ${tipoModulo} está en desarrollo`);
    } catch (error) {
      console.error(`Error al actualizar estado del cierre ${tipoModulo}:`, error);
      alert('Error al actualizar el estado del cierre');
    } finally {
      setActualizandoEstado(false);
    }
  };

  // Determinar si está procesando (custom o genérico)
  const estaProcesando = procesandoCustom || actualizandoEstado;

  return (
    <div className="bg-gray-800 px-8 py-6 rounded-xl shadow flex flex-wrap items-center gap-6 mb-10 w-full">
      {/* Nombre + bilingüe */}
      <div className="flex items-center gap-2">
        <span className="text-2xl font-bold text-white">{cliente?.nombre || "Cliente desconocido"}</span>
        {cliente?.bilingue && (
          <span className="bg-blue-600 text-white text-xs px-2 py-1 rounded-full shadow font-semibold flex items-center gap-1">
            <svg className="inline-block w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v2m0 4v2m0 4v2m0 4v2m8-10h-2m-4 0H8m-4 0H2m18 0c0 4.418-3.582 8-8 8s-8-3.582-8-8 3.582-8 8-8 8 3.582 8 8z" />
            </svg>
            Bilingüe
          </span>
        )}
      </div>

      {/* RUT */}
      <div className="text-gray-300 text-base">
        <span className="font-bold">RUT:</span> {cliente?.rut}
      </div>

      {/* Industria */}
      <div className="text-gray-300 text-base">
        <span className="font-bold">Industria:</span> {cliente?.industria_nombre || "—"}
      </div>

      {/* Periodo */}
      <div className="text-gray-300 text-base">
        <span className="font-bold">Periodo:</span> <span className="text-white font-bold">{cierre?.periodo || "—"}</span>
      </div>

      {/* Estado */}
      <div className="flex items-center gap-2">
        <span className="font-bold text-gray-300">Estado:</span>
        <EstadoBadge estado={cierre?.estado} size="md" />
      </div>

      {/* Botones de acción */}
      <div className="flex items-center gap-3">
        {/* Botón Actualizar Estado */}
        <button
          onClick={manejarActualizarEstado}
          disabled={estaProcesando}
          className="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white px-4 py-2 rounded-lg font-semibold text-sm transition-colors flex items-center gap-2"
        >
          {estaProcesando ? (
            <>
              <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Actualizando...
            </>
          ) : (
            <>
              <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Actualizar Estado
            </>
          )}
        </button>

        {/* Botones personalizados por área */}
        {botonesPersonalizados.map((boton, index) => (
          <button
            key={index}
            onClick={boton.onClick}
            disabled={boton.disabled}
            className={`px-4 py-2 rounded-lg font-semibold text-sm transition-colors flex items-center gap-2 ${boton.className || 'bg-gray-600 hover:bg-gray-700 text-white'}`}
          >
            {boton.icono && boton.icono}
            {boton.texto}
          </button>
        ))}

        {/* Indicador genérico de procesamiento */}
        {cierre?.estado === 'procesando' && (
          <div className="bg-yellow-600 text-white px-4 py-2 rounded-lg font-semibold text-sm flex items-center gap-2">
            <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Procesando...
          </div>
        )}

        {/* Indicador de finalizado */}
        {cierre?.estado === 'finalizado' && (
          <div className="bg-green-600 text-white px-4 py-2 rounded-lg font-semibold text-sm flex items-center gap-2">
            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Cierre Finalizado
          </div>
        )}
      </div>

      {/* Link ficha cliente */}
      {cliente && (
        <div>
          <a
            href={`/menu/clientes/${cliente.id}`}
            className="!text-white text-base underline font-semibold"
          >
            Ver ficha del cliente
          </a>
        </div>
      )}
    </div>
  );
};

export default CierreInfoBarGenerico;
