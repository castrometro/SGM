// src/modules/contabilidad/crear-cierre/pages/CrearCierreContabilidadPage.jsx
import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import { obtenerCliente, obtenerResumenContable } from '../api/crearCierre.api';
import { validarAccesoContabilidad } from '../utils/crearCierreHelpers';
import { getUsuario } from '../../../shared/auth/utils/storage';
import { MENSAJES } from '../constants/crearCierre.constants';
import ClienteInfoCard from '../components/ClienteInfoCard';
import FormularioCierre from '../components/FormularioCierre';

/**
 * Página para crear un nuevo cierre de contabilidad
 */
const CrearCierreContabilidadPage = () => {
  const { clienteId } = useParams();
  const navigate = useNavigate();
  
  const [cliente, setCliente] = useState(null);
  const [resumen, setResumen] = useState(null);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState('');
  const [hasAccess, setHasAccess] = useState(null);

  useEffect(() => {
    const cargarDatos = async () => {
      setCargando(true);
      setError('');
      
      try {
        // 1. Validar acceso desde localStorage
        const userData = getUsuario();
        const tieneAcceso = validarAccesoContabilidad(userData);
        setHasAccess(tieneAcceso);
        
        if (!tieneAcceso) {
          setError(MENSAJES.SIN_ACCESO);
          setCargando(false);
          return;
        }

        // 2. Cargar cliente
        const clienteData = await obtenerCliente(clienteId);
        setCliente(clienteData);

        // 3. Cargar resumen (opcional)
        try {
          const resumenData = await obtenerResumenContable(clienteId);
          setResumen(resumenData);
        } catch (err) {
          console.warn('No se pudo cargar resumen:', err);
          // Continuamos sin resumen
        }
      } catch (err) {
        console.error('Error cargando datos:', err);
        if (err.response?.status === 404) {
          setError(`No se encontró el cliente con ID ${clienteId}`);
        } else if (err.response?.status === 403) {
          setError('No tienes permisos para ver este cliente');
        } else {
          setError('Error al cargar los datos del cliente');
        }
      }
      
      setCargando(false);
    };

    if (clienteId) {
      cargarDatos();
    }
  }, [clienteId]);

  // Validando acceso
  if (cargando && hasAccess === null) {
    return (
      <div className="text-white flex items-center justify-center h-64">
        <div className="flex flex-col items-center gap-3">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
          <p>Validando acceso...</p>
        </div>
      </div>
    );
  }

  // Sin acceso
  if (hasAccess === false) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="max-w-md mx-auto text-center p-8">
          <div className="text-red-400 text-5xl mb-4">⚠️</div>
          <h2 className="text-2xl font-bold text-gray-100 mb-2">Acceso Denegado</h2>
          <p className="text-gray-400 mb-6">{error}</p>
          <button
            onClick={() => navigate('/menu')}
            className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
          >
            Volver al Menú
          </button>
        </div>
      </div>
    );
  }

  // Cargando
  if (cargando) {
    return (
      <div className="text-white flex items-center justify-center h-64">
        <div className="flex flex-col items-center gap-3">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
          <p>{MENSAJES.CARGANDO_CLIENTE}</p>
        </div>
      </div>
    );
  }

  // Error
  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="max-w-md mx-auto text-center p-8">
          <div className="text-red-400 text-5xl mb-4">❌</div>
          <h2 className="text-2xl font-bold text-gray-100 mb-2">Error</h2>
          <p className="text-gray-400 mb-6">{error}</p>
          <button
            onClick={() => navigate('/menu/clientes')}
            className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
          >
            Volver a Clientes
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Header con botón volver */}
      <div className="flex items-center gap-4">
        <button
          onClick={() => navigate(`/menu/clientes/${clienteId}/cierres`)}
          className="p-2 hover:bg-gray-700 rounded-lg transition-colors text-white"
        >
          <ArrowLeft size={20} />
        </button>
        <h1 className="text-2xl font-bold text-white">Crear Nuevo Cierre</h1>
      </div>

      {/* Información del Cliente */}
      <ClienteInfoCard cliente={cliente} resumen={resumen} />

      {/* Formulario de Creación */}
      <FormularioCierre clienteId={clienteId} />
    </div>
  );
};

export default CrearCierreContabilidadPage;
