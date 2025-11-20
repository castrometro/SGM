// src/modules/contabilidad/cierre-detalle/pages/CierreDetalleContabilidadPage.jsx
import { useState, useEffect, useCallback } from "react";
import { useParams } from "react-router-dom";
import { obtenerCierrePorId, obtenerCliente } from "../api/cierreDetalle.api";
import { validarAccesoContabilidad } from "../utils/cierreDetalleHelpers";
import CierreInfoBar from "../components/CierreInfoBar";
import CierreProgresoContabilidad from "../components/CierreProgresoContabilidad";

/**
 * Página de detalle de cierre de contabilidad
 * Muestra toda la información y progreso del cierre
 */
const CierreDetalleContabilidadPage = () => {
  const { cierreId } = useParams();
  const [cierre, setCierre] = useState(null);
  const [cliente, setCliente] = useState(null);
  const [cargandoInicial, setCargandoInicial] = useState(true);
  const [error, setError] = useState(null);
  const [tieneAcceso, setTieneAcceso] = useState(true);

  // Validar acceso al área de Contabilidad
  useEffect(() => {
    const usuario = JSON.parse(localStorage.getItem("usuario"));
    if (!validarAccesoContabilidad(usuario)) {
      setTieneAcceso(false);
      setCargandoInicial(false);
    }
  }, []);

  // Función para refrescar datos del cierre
  const refrescarCierre = useCallback(async () => {
    if (cierreId) {
      try {
        const cierreActualizado = await obtenerCierrePorId(cierreId);
        setCierre(cierreActualizado);
        console.log('🔄 [CierreDetalleContabilidadPage] Cierre actualizado:', cierreActualizado.estado);
      } catch (error) {
        console.error('❌ Error refrescando cierre:', error);
      }
    }
  }, [cierreId]);

  // Carga inicial de datos
  useEffect(() => {
    const fetchData = async () => {
      if (!cierreId || !tieneAcceso) return;
      
      setCargandoInicial(true);
      setError(null);
      
      try {
        const cierreObj = await obtenerCierrePorId(cierreId);
        setCierre(cierreObj);
        
        const clienteObj = await obtenerCliente(cierreObj.cliente);
        setCliente(clienteObj);
        
        console.log('✅ [CierreDetalleContabilidadPage] Datos iniciales cargados', { 
          cierre: cierreObj, 
          cliente: clienteObj 
        });
      } catch (error) {
        console.error('❌ Error cargando datos iniciales:', error);
        setError(error.message || 'Error al cargar el cierre');
      } finally {
        setCargandoInicial(false);
      }
    };
    
    fetchData();
  }, [cierreId, tieneAcceso]);

  // Pantalla de acceso denegado
  if (!tieneAcceso) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="bg-red-900/20 border border-red-700 rounded-lg p-8 max-w-md text-center">
          <div className="text-red-400 text-5xl mb-4">🚫</div>
          <h2 className="text-2xl font-bold text-white mb-2">Acceso Denegado</h2>
          <p className="text-gray-300">No tienes permisos para acceder al área de Contabilidad.</p>
        </div>
      </div>
    );
  }

  // Pantalla de carga
  if (cargandoInicial) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-white text-lg">Cargando cierre...</p>
        </div>
      </div>
    );
  }

  // Pantalla de error
  if (error) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="bg-red-900/20 border border-red-700 rounded-lg p-8 max-w-md text-center">
          <div className="text-red-400 text-5xl mb-4">⚠️</div>
          <h2 className="text-2xl font-bold text-white mb-2">Error</h2>
          <p className="text-gray-300">{error}</p>
          <button 
            onClick={() => window.location.reload()}
            className="mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
          >
            Reintentar
          </button>
        </div>
      </div>
    );
  }

  // Validación de datos cargados
  if (!cierre || !cliente) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-white text-center">
          <p className="text-lg">No se pudo cargar la información del cierre.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Barra de información del cierre */}
        <CierreInfoBar 
          cierre={cierre} 
          cliente={cliente}
          onCierreActualizado={setCierre}
          tipoModulo="contabilidad"
        />

        {/* Progreso del cierre con todas las secciones */}
        <CierreProgresoContabilidad
          cierre={cierre}
          cliente={cliente}
          onCierreActualizado={refrescarCierre}
        />
      </div>
    </div>
  );
};

export default CierreDetalleContabilidadPage;
