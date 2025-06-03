import React, { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import CierreInfoBar from "../components/InfoCards/CierreInfoBar"; // Puedes crear uno especial para nómina después
import { obtenerCierreNominaPorId } from "../api/nomina";
import { obtenerCliente } from "../api/clientes";
import CierreProgresoNomina from "../components/TarjetasCierreNomina/CierreProgresoNomina"; // Asegúrate de crear este componente

const CierreDetalleNomina = () => {
  const { cierreId } = useParams();
  const [cierre, setCierre] = useState(null);
  const [cliente, setCliente] = useState(null);



  useEffect(() => {
    const fetchData = async () => {
      if (cierreId) {
        const cierreObj = await obtenerCierreNominaPorId(cierreId);
        setCierre(cierreObj);
        const clienteObj = await obtenerCliente(cierreObj.cliente);
        setCliente(clienteObj);
      }
    };
    fetchData();
  }, [cierreId]);

  if (!cierre || !cliente) {
    return <div className="text-white text-center mt-8">Cargando cierre...</div>;
  }

  return (
    <>
      <div className="mb-6">
        <CierreInfoBar cierre={cierre} cliente={cliente} />
      </div>
      <CierreProgresoNomina
        cierre={cierre}
        cliente={cliente}
        className="grid grid-cols-1 md:grid-cols-3 gap-4"
      />
    </>

  );
};

export default CierreDetalleNomina;
