// src/modules/contabilidad/cliente-detalle/pages/ClienteDetalleContabilidadPage.jsx
import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { 
  obtenerCliente, 
  obtenerKpisContabilidadCliente, 
  obtenerResumenContabilidad,
  obtenerUsuario 
} from "../api/clienteDetalle.api";
import { 
  validarAccesoContabilidad, 
  procesarDatosResumen 
} from "../utils/clienteDetalleHelpers";
import ClienteInfoCard from "../components/ClienteInfoCard";
import KpiResumenContabilidad from "../components/KpiResumenContabilidad";
import ClienteActionButtons from "../components/ClienteActionButtons";

/**
 * 📄 Página de Detalle de Cliente de Contabilidad
 * Muestra información completa del cliente y sus KPIs
 * Valida acceso al área de Contabilidad antes de cargar datos
 */
const ClienteDetalleContabilidadPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  
  const [cliente, setCliente] = useState(null);
  const [resumen, setResumen] = useState(null);
  const [hasAccess, setHasAccess] = useState(null);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const cargarDatos = async () => {
      setCargando(true);
      setError("");
      
      try {
        // 1. Validar acceso del usuario
        const userData = await obtenerUsuario();
        const tieneAcceso = validarAccesoContabilidad(userData);
        setHasAccess(tieneAcceso);
        
        if (!tieneAcceso) {
          setCargando(false);
          return;
        }

        // 2. Cargar cliente
        console.log('🔍 ClienteDetalleContabilidad - Cargando cliente:', id);
        const clienteData = await obtenerCliente(id);
        setCliente(clienteData);

        // 3. Cargar KPIs de contabilidad
        let resumenData = null;
        try {
          console.log('🔍 ClienteDetalleContabilidad - Obteniendo KPIs...');
          const kpisData = await obtenerKpisContabilidadCliente(id);
          console.log('🔍 ClienteDetalleContabilidad - KPIs obtenidos:', kpisData);
          
          if (kpisData?.tieneCierre) {
            resumenData = procesarDatosResumen(kpisData);
            console.log('🔍 ClienteDetalleContabilidad - Datos procesados:', resumenData);
          }
        } catch (e) {
          console.warn('⚠️ ClienteDetalleContabilidad - Fallo KPIs, usando fallback:', e);
        }

        // Fallback a resumen básico si no hay KPIs
        if (!resumenData) {
          console.log('🔍 ClienteDetalleContabilidad - Usando resumen básico...');
          resumenData = await obtenerResumenContabilidad(id);
          console.log('🔍 ClienteDetalleContabilidad - Resumen básico:', resumenData);
        }

        setResumen(resumenData);
      } catch (err) {
        console.error("❌ ClienteDetalleContabilidad - Error:", err);
        
        // Manejar diferentes tipos de errores
        if (err.response?.status === 404) {
          setError(`No se encontró el cliente con ID ${id}. Verifica que el cliente exista y esté activo.`);
        } else if (err.response?.status === 403) {
          setError("No tienes permisos para ver este cliente.");
        } else if (err.message?.includes('Network Error')) {
          setError("Error de conexión. Verifica tu conexión a internet.");
        } else {
          setError("No se pudo cargar los datos del cliente. Intenta más tarde.");
        }
      }
      
      setCargando(false);
    };

    if (id) {
      cargarDatos();
    } else {
      setError("No se proporcionó un ID de cliente válido.");
      setCargando(false);
    }
  }, [id]);

  // Validando acceso
  if (cargando && hasAccess === null) {
    return (
      <div className="text-white flex items-center justify-center h-64">
        <div className="flex flex-col items-center gap-3">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500"></div>
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
          <p className="text-gray-400 mb-6">
            No tienes permisos para acceder a detalles de clientes de Contabilidad.
          </p>
          <button
            onClick={() => navigate('/menu')}
            className="px-6 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors"
          >
            Volver al Menú
          </button>
        </div>
      </div>
    );
  }

  // Cargando datos
  if (cargando) {
    return (
      <div className="text-white flex items-center justify-center h-64">
        <div className="flex flex-col items-center gap-3">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500"></div>
          <p>Cargando datos del cliente...</p>
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
          <h2 className="text-2xl font-bold text-gray-100 mb-2">Error al cargar cliente</h2>
          <p className="text-gray-400 mb-2">{error}</p>
          {id && (
            <p className="text-gray-500 text-sm mb-6">Cliente ID: {id}</p>
          )}
          <div className="flex gap-3 justify-center">
            <button
              onClick={() => navigate('/menu/clientes')}
              className="px-6 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors"
            >
              Ver Clientes
            </button>
            <button
              onClick={() => window.location.reload()}
              className="px-6 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors"
            >
              Reintentar
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Sin datos
  if (!cliente) {
    return (
      <div className="text-white flex items-center justify-center h-64">
        <p>No se encontró el cliente</p>
      </div>
    );
  }

  return (
    <div className="text-white space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4 mb-4">
        <button
          onClick={() => navigate('/menu/clientes')}
          className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
          title="Volver a Clientes"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 19l-7-7 7-7" />
          </svg>
        </button>
        <h1 className="text-2xl font-bold">Detalle de Cliente</h1>
        <span className="px-3 py-1 rounded-full bg-purple-600 text-white text-sm font-semibold">
          Contabilidad
        </span>
      </div>

      {/* Card de información del cliente */}
      <ClienteInfoCard cliente={cliente} resumen={resumen} />
      
      {/* KPIs del cierre */}
      {resumen && <KpiResumenContabilidad resumen={resumen} />}
      
      {/* Botones de acción */}
      <ClienteActionButtons clienteId={cliente.id} />
    </div>
  );
};

export default ClienteDetalleContabilidadPage;
