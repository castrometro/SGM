import React, { useState, useEffect, useCallback } from "react";
import { useParams } from "react-router-dom";
import CierreInfoBar from "../components/InfoCards/CierreInfoBar"; // Puedes crear uno especial para nómina después
import { obtenerCierreNominaPorId } from "../api/nomina";
import { obtenerCliente } from "../api/clientes";
import CierreProgresoNomina from "../components/TarjetasCierreNomina/CierreProgresoNomina"; // Asegúrate de crear este componente
import CierreProgresoNomina_v2 from "../components/TarjetasCierreNomina/CierreProgresoNomina_v2";
const CierreDetalleNomina = () => {
  const { cierreId } = useParams();
  const [cierre, setCierre] = useState(null);
  const [cliente, setCliente] = useState(null);
  const [cargandoInicial, setCargandoInicial] = useState(true);

  // Función para refrescar datos del cierre
  const refrescarCierre = useCallback(async () => {
    if (cierreId) {
      try {
        const cierreActualizado = await obtenerCierreNominaPorId(cierreId);
        setCierre(cierreActualizado);
        console.log('🔄 [CierreDetalleNomina] Cierre actualizado:', cierreActualizado.estado);
      } catch (error) {
        console.error('❌ Error refrescando cierre:', error);
      }
    }
  }, [cierreId]);

  useEffect(() => {
    const fetchData = async () => {
      if (cierreId) {
        setCargandoInicial(true);
        try {
          const cierreObj = await obtenerCierreNominaPorId(cierreId);
          setCierre(cierreObj);
          const clienteObj = await obtenerCliente(cierreObj.cliente);
          setCliente(clienteObj);
          console.log('✅ [CierreDetalleNomina] Datos iniciales cargados', { cierre: cierreObj, cliente: clienteObj });
        } catch (error) {
          console.error('❌ Error cargando datos iniciales:', error);
        } finally {
          setCargandoInicial(false);
        }
      }
    };
    fetchData();
  }, [cierreId]);

  if (cargandoInicial || !cierre || !cliente) {
    return <div className="text-white text-center mt-8">Cargando cierre...</div>;
  }

  return (
    <>
      <div className="mb-6">
        <CierreInfoBar 
          cierre={cierre} 
          cliente={cliente}
          onCierreActualizado={setCierre}
          tipoModulo="nomina"
        />
      </div>


       <CierreProgresoNomina
        cierre={cierre}
        cliente={cliente}
        onCierreActualizado={refrescarCierre}
        className="grid grid-cols-1 md:grid-cols-3 gap-4"
      /> 

      
    </>

  );
};

export default CierreDetalleNomina;
