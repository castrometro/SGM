import { useEffect, useState } from "react";
import { obtenerAnalistasPerformance } from "../api/analistas";

const InformesAnalistas = () => {
  const [analistas, setAnalistas] = useState([]);

  useEffect(() => {
    const cargar = async () => {
      try {
        const data = await obtenerAnalistasPerformance();
        setAnalistas(data);
      } catch (err) {
        console.error("Error al cargar analistas", err);
      }
    };
    cargar();
  }, []);

  return (
    <div className="text-white">
      <h1 className="text-3xl font-bold mb-6">Informes de Analistas</h1>
      <div className="bg-gray-800 p-6 rounded-lg">
        <table className="w-full text-left">
          <thead>
            <tr className="border-b border-gray-700">
              <th className="p-2">Analista</th>
              <th className="p-2">Clientes asignados</th>
              <th className="p-2">Cierres Contabilidad</th>
              <th className="p-2">Cierres Nómina</th>
            </tr>
          </thead>
          <tbody>
            {analistas.map((a) => (
              <tr key={a.id} className="border-b border-gray-700">
                <td className="p-2">{a.nombre} {a.apellido}</td>
                <td className="p-2 text-center">{a.clientes_asignados}</td>
                <td className="p-2 text-center">{a.cierres_contabilidad}</td>
                <td className="p-2 text-center">{a.cierres_nomina}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default InformesAnalistas;
