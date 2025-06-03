import React, { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import CierreInfoBar from "../components/InfoCards/CierreInfoBar";
import CierreProgreso from "../components/TarjetasCierreContabilidad/CierreProgreso"; // <--- tu nuevo componente
import { obtenerCierrePorId } from "../api/contabilidad";
import { obtenerCliente } from "../api/clientes";

const CierreDetalle = () => {
  const { cierreId } = useParams();
  const [cierre, setCierre] = useState(null);
  const [cliente, setCliente] = useState(null);

  // Estados de control para los pasos
  const [tipoDocumentoReady, setTipoDocumentoReady] = useState(false);
  const [libroMayorReady, setLibroMayorReady] = useState(false);
  const [clasificacionReady, setClasificacionReady] = useState(false);
  const [nombresEnInglesReady, setNombresEnInglesReady] = useState(false);
  const [obtenerProgresoClasificacionTodosLosSets, setObtenerProgresoClasificacionTodosLosSets] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      if (cierreId) {
        const cierreObj = await obtenerCierrePorId(cierreId);
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
      <CierreProgreso
        cierre={cierre}
        cliente={cliente}
        tipoDocumentoReady={tipoDocumentoReady}
        setTipoDocumentoReady={setTipoDocumentoReady}
        libroMayorReady={libroMayorReady}
        setLibroMayorReady={setLibroMayorReady}
        clasificacionReady={clasificacionReady}
        setClasificacionReady={setClasificacionReady}
      />
      {/* Aquí puedes seguir con incidencias, timeline, etc. */}
    </>
  );
};

export default CierreDetalle;
