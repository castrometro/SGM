import React, { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import CierreInfoBar from "../../InfoCards/CierreInfoBar";
import CierreProgresoNomina_v2 from "../components/CierreProgresoNomina_v2";
import { obtenerCierreNominaPorId } from "../../../api/nomina";
import { obtenerCliente } from "../../../api/clientes";

const CierreDetalleNomina_v2 = () => {
  const { cierreId } = useParams();
  const [cierre, setCierre] = useState(null);
  const [cliente, setCliente] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // 🎯 CARGAR DATOS INICIALES
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        console.log('🚀 [CierreDetalle_v2] Cargando cierre:', cierreId);
        
        const cierreData = await obtenerCierreNominaPorId(cierreId);
        setCierre(cierreData);
        
        const clienteData = await obtenerCliente(cierreData.cliente);
        setCliente(clienteData);
        
        console.log('✅ [CierreDetalle_v2] Datos cargados:', { 
          cierre: cierreData.estado, 
          cliente: clienteData.nombre 
        });
        
      } catch (err) {
        console.error('❌ [CierreDetalle_v2] Error:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    if (cierreId) {
      fetchData();
    }
  }, [cierreId]);

  // 🔄 CALLBACK PARA ACTUALIZAR CIERRE
  const handleCierreActualizado = (cierreActualizado) => {
    console.log('🔄 [CierreDetalle_v2] Cierre actualizado:', cierreActualizado.estado);
    setCierre(cierreActualizado);
  };

  // 📱 ESTADOS DE CARGA
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-white text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p>Cargando cierre de nómina...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-red-400 text-center">
          <p className="text-xl mb-2">❌ Error al cargar el cierre</p>
          <p className="text-sm">{error}</p>
        </div>
      </div>
    );
  }

  if (!cierre || !cliente) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-gray-400 text-center">
          <p>No se encontró el cierre de nómina</p>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-6 space-y-6">
      {/* 🎯 HEADER CON BADGE V2 */}
      <div className="bg-gradient-to-r from-purple-600/10 to-blue-600/10 border border-purple-500/30 rounded-lg p-4">
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <h1 className="text-2xl font-bold text-white">Cierre de Nómina</h1>
              <span className="px-3 py-1 bg-purple-600/20 text-purple-400 rounded-full text-sm font-medium border border-purple-500/30">
                V2 - Nuevo Sistema
              </span>
            </div>
            <p className="text-gray-400">
              Cliente: <span className="text-white font-medium">{cliente.nombre}</span> | 
              Período: <span className="text-white font-medium">{cierre.periodo}</span>
            </p>
          </div>
          <div className="text-right">
            <span className={`
              px-4 py-2 rounded-full text-sm font-medium border
              ${cierre.estado === 'finalizado' ? 'bg-green-600/20 text-green-400 border-green-500/30' :
                cierre.estado === 'pendiente' ? 'bg-gray-600/20 text-gray-400 border-gray-500/30' :
                'bg-blue-600/20 text-blue-400 border-blue-500/30'}
            `}>
              {cierre.estado}
            </span>
          </div>
        </div>
      </div>

      {/* 🎯 INFO BAR EXISTENTE (REUTILIZAR) */}
      <CierreInfoBar 
        cierre={cierre} 
        cliente={cliente}
        onCierreActualizado={handleCierreActualizado}
        tipoModulo="nomina"
      />

      {/* 🎯 COMPONENTE PRINCIPAL - PROGRESO V2 */}
      <CierreProgresoNomina_v2
        cierre={cierre}
        cliente={cliente}
      />
    </div>
  );
};

export default CierreDetalleNomina_v2;
