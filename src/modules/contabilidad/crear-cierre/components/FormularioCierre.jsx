// src/modules/contabilidad/crear-cierre/components/FormularioCierre.jsx
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { MENSAJES, LABELS } from '../constants/crearCierre.constants';
import { validarFormulario, formatearPeriodoConfirmacion } from '../utils/crearCierreHelpers';
import { obtenerCierreMensual, crearCierreMensual } from '../api/crearCierre.api';

/**
 * Formulario para crear cierre de contabilidad
 */
const FormularioCierre = ({ clienteId }) => {
  const [periodo, setPeriodo] = useState('');
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    // Validar formulario
    const validacion = validarFormulario(periodo);
    if (!validacion.valido) {
      setError(validacion.error);
      return;
    }

    // Confirmar creación
    const periodoFormateado = formatearPeriodoConfirmacion(periodo);
    if (!window.confirm(MENSAJES.CONFIRMAR_CREACION.replace('{periodo}', periodoFormateado))) {
      return;
    }

    setLoading(true);
    try {
      // Verificar si ya existe cierre
      const cierreExistente = await obtenerCierreMensual(clienteId, periodo);
      
      if (cierreExistente) {
        setError(MENSAJES.ERROR_CIERRE_EXISTENTE);
        setLoading(false);
        return;
      }

      // Crear cierre
      const cierre = await crearCierreMensual(clienteId, periodo);
      
      // Navegar al detalle del cierre
      navigate(`/menu/cierres/${cierre.id}`);
    } catch (err) {
      console.error('Error creando cierre:', err);
      setError(MENSAJES.ERROR_CREANDO);
    }
    
    setLoading(false);
  };

  return (
    <div className="bg-gray-800 p-6 rounded-lg shadow-lg mt-4">
      <h2 className="text-xl font-bold text-white mb-4">
        {MENSAJES.TITULO}
      </h2>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Campo Periodo */}
        <div>
          <label className="block text-gray-300 font-semibold mb-1">
            {LABELS.PERIODO}
          </label>
          <input
            type="month"
            value={periodo}
            onChange={(e) => setPeriodo(e.target.value)}
            className="w-full border rounded p-2 bg-gray-900 text-white"
            required
          />
        </div>

        {/* Error */}
        {error && (
          <div className="text-red-400">
            {error}
          </div>
        )}

        {/* Botón Submit */}
        <button
          type="submit"
          disabled={loading}
          className="bg-blue-600 text-white px-4 py-2 rounded-xl shadow hover:bg-blue-800 transition disabled:opacity-50"
        >
          {loading ? MENSAJES.CREANDO : MENSAJES.CREAR}
        </button>
      </form>
    </div>
  );
};

export default FormularioCierre;
