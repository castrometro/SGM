import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import CierreInfoBar from "../components/InfoCards/CierreInfoBar";
import {
  obtenerCierrePorId,
  obtenerMovimientosResumen,
  obtenerSetsClasificacion,
  obtenerOpcionesClasificacion,
} from "../api/contabilidad";
import { obtenerCliente } from "../api/clientes";
import { formatMoney } from "../utils/format";

const AnalisisLibro = () => {
  const { cierreId } = useParams();
  const navigate = useNavigate();
  const [cierre, setCierre] = useState(null);
  const [cliente, setCliente] = useState(null);
  const [resumen, setResumen] = useState(null);
  const [filtros, setFiltros] = useState({ texto: "" });
  const [sets, setSets] = useState([]);
  const [opciones, setOpciones] = useState([]);
  const [selectedSet, setSelectedSet] = useState("");
  const [selectedOpcion, setSelectedOpcion] = useState("");

  useEffect(() => {
    const fetchData = async () => {
      if (!cierreId) return;
      const cierreObj = await obtenerCierrePorId(cierreId);
      setCierre(cierreObj);
      const clienteObj = await obtenerCliente(cierreObj.cliente);
      setCliente(clienteObj);
      const setsData = await obtenerSetsClasificacion(clienteObj.id);
      setSets(setsData);
      if (setsData.length > 0) setSelectedSet(setsData[0].id.toString());
    };
    fetchData();
  }, [cierreId]);

  useEffect(() => {
    if (!selectedSet) {
      setOpciones([]);
      return;
    }
    const loadOpts = async () => {
      const opts = await obtenerOpcionesClasificacion(selectedSet);
      setOpciones(opts);
    };
    loadOpts();
  }, [selectedSet]);

  useEffect(() => {
    const fetchResumen = async () => {
      if (!cierreId) return;
      try {
        const params = {
          // No enviamos filtros de clasificación al backend
          // setId: selectedSet || undefined,
          // opcionId: selectedOpcion || undefined,
        };
        const movResumen = await obtenerMovimientosResumen(cierreId, params);
        
        // Se eliminan logs de debug tras confirmación de formato correcto
        setResumen(movResumen);
      } catch (error) {
        if (error.response && error.response.status === 403) {
          // El backend ya validó que el estado no es permitido
          // El componente mostrará el mensaje de acceso restringido
          console.log('Acceso restringido por estado del cierre:', error.response.data);
          setResumen([]); // Set empty array to trigger access restriction UI
        } else {
          console.error('Error al obtener movimientos resumen:', error);
          setResumen(null);
        }
      }
    };
    fetchResumen();
  }, [cierreId]); // Solo depende del cierreId, no de los filtros

  if (!cierre || !cliente || !resumen) {
    return (
      <div className="text-white text-center mt-8">Cargando análisis de libro...</div>
    );
  }

  // Validar acceso al libro según el estado del cierre
  const estadosPermitidos = ['sin_incidencias','listo_para_entrega', 'entregado', 'completado','finalizado'];
  const accesoPermitido = estadosPermitidos.includes(cierre.estado);

  if (!accesoPermitido || (resumen && Array.isArray(resumen) && resumen.length === 0 && cierre.estado)) {
    return (
      <div className="space-y-6">
        <CierreInfoBar cierre={cierre} cliente={cliente} />
        <div className="bg-red-600 border border-red-700 rounded-lg p-6 text-center">
          <div className="flex items-center justify-center mb-4">
            <svg className="h-12 w-12 text-red-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-white mb-2">Acceso Restringido al Libro</h2>
          <p className="text-red-100 mb-4">
            El libro del cierre solo está disponible cuando el estado es <strong>"Sin Incidencias"</strong> o posterior.
          </p>
          <div className="bg-red-700 rounded-lg p-4 mb-4">
            <p className="text-red-100 text-sm">
              <strong>Estado actual:</strong> <span className="font-mono bg-red-800 px-2 py-1 rounded">{cierre.estado}</span>
            </p>
            <p className="text-red-100 text-sm mt-2">
              <strong>Estados requeridos:</strong> listo_para_entrega, entregado, completado
            </p>
          </div>
          <p className="text-red-100 text-sm">
            Por favor, resuelve las incidencias pendientes para acceder al análisis del libro.
          </p>
          <div className="mt-6">
            <button
              onClick={() => navigate(`/menu/cierres/${cierreId}`)}
              className="bg-white text-red-600 px-6 py-2 rounded-lg font-semibold hover:bg-gray-100 transition-colors"
            >
              Volver al Detalle del Cierre
            </button>
          </div>
        </div>
      </div>
    );
  }

  const { texto } = filtros;
  
  // Filtrado local por texto, set y opción
  const resumenFiltrado = resumen.filter((r) => {
    // Filtro por texto
    const matchesText = `${r.codigo} ${r.nombre}`.toLowerCase().includes(texto.toLowerCase());
    
    // Filtro por set de clasificación
    let matchesSet = true;
    if (selectedSet) {
      matchesSet = r.clasificaciones && r.clasificaciones[selectedSet];
    }
    
    // Filtro por opción específica
    let matchesOpcion = true;
    if (selectedSet && selectedOpcion) {
      const clasificacion = r.clasificaciones && r.clasificaciones[selectedSet];
      matchesOpcion = clasificacion && clasificacion.opcion_id == selectedOpcion;
    }
    
    return matchesText && matchesSet && matchesOpcion;
  });

  // Calcular totales dinámicos de los registros filtrados
  const totales = resumenFiltrado.reduce(
    (acc, r) => ({
      saldo_anterior: acc.saldo_anterior + (r.saldo_anterior || 0),
      total_debe: acc.total_debe + (r.total_debe || 0),
      total_haber: acc.total_haber + (r.total_haber || 0),
      saldo_final: acc.saldo_final + (r.saldo_final || 0),
    }),
    { saldo_anterior: 0, total_debe: 0, total_haber: 0, saldo_final: 0 }
  );

  

  return (
    <div className="space-y-6">
      <CierreInfoBar cierre={cierre} cliente={cliente} />
      <div className="bg-gray-800 p-4 rounded-md flex flex-col gap-4 md:flex-row md:items-end">
        <div className="flex flex-col flex-grow">
          <label className="text-sm text-gray-300" htmlFor="texto">Buscar</label>
          <input
            id="texto"
            type="text"
            placeholder="Cuenta..."
            className="bg-gray-700 text-white rounded px-2 py-1"
            value={texto}
            onChange={(e) =>
              setFiltros((f) => ({ ...f, texto: e.target.value }))
            }
          />
        </div>
        <div className="flex flex-col">
          <label className="text-sm text-gray-300" htmlFor="set">Set</label>
          <select
            id="set"
            className="bg-gray-700 text-white rounded px-2 py-1"
            value={selectedSet}
            onChange={(e) => {
              setSelectedSet(e.target.value);
              setSelectedOpcion("");
            }}
          >
            <option value="">Todos</option>
            {sets.map((s) => (
              <option key={s.id} value={s.id}>
                {s.nombre}
              </option>
            ))}
          </select>
        </div>
        <div className="flex flex-col">
          <label className="text-sm text-gray-300" htmlFor="opcion">Opción</label>
          <select
            id="opcion"
            className="bg-gray-700 text-white rounded px-2 py-1"
            value={selectedOpcion}
            onChange={(e) => setSelectedOpcion(e.target.value)}
            disabled={!selectedSet}
          >
            <option value="">Todas</option>
            {opciones.map((o) => (
              <option key={o.id} value={o.id}>
                {o.valor}
              </option>
            ))}
          </select>
        </div>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm border-separate border-spacing-y-1">
          <thead>
            <tr className="bg-gray-700">
              <th className="px-4 py-2 text-left">Cuenta</th>
              <th className="px-4 py-2 text-right">Saldo anterior</th>
              <th className="px-4 py-2 text-right">Total debe</th>
              <th className="px-4 py-2 text-right">Total haber</th>
              <th className="px-4 py-2 text-right">Saldo final</th>
              {selectedSet && (
                <th className="px-4 py-2 text-left">Clasificación</th>
              )}
            </tr>
            {/* Fila de totales */}
            <tr className="bg-blue-600 font-bold text-white">
              <td className="px-4 py-2">
                TOTALES ({resumenFiltrado.length} cuentas)
              </td>
              <td className="px-4 py-2 text-right">{formatMoney(totales.saldo_anterior)}</td>
              <td className="px-4 py-2 text-right">{formatMoney(totales.total_debe)}</td>
              <td className="px-4 py-2 text-right">{formatMoney(totales.total_haber)}</td>
              <td className="px-4 py-2 text-right">{formatMoney(totales.saldo_final)}</td>
              {selectedSet && (
                <td className="px-4 py-2">-</td>
              )}
            </tr>
          </thead>
          <tbody>
            {resumenFiltrado.map((r) => (
              <tr
                key={r.cuenta_id}
                className="bg-gray-800 hover:bg-gray-700 cursor-pointer"
                onClick={() =>
                  navigate(`/menu/cierres/${cierreId}/cuentas/${r.cuenta_id}`)
                }
              >
                <td className="px-4 py-2">
                  {r.codigo} - {r.nombre}
                </td>
                <td className="px-4 py-2 text-right">{formatMoney(r.saldo_anterior)}</td>
                <td className="px-4 py-2 text-right">{formatMoney(r.total_debe)}</td>
                <td className="px-4 py-2 text-right">{formatMoney(r.total_haber)}</td>
                <td className="px-4 py-2 text-right">{formatMoney(r.saldo_final)}</td>
                {selectedSet && (
                  <td className="px-4 py-2">
                    {r.clasificaciones && r.clasificaciones[selectedSet] 
                      ? r.clasificaciones[selectedSet].opcion_valor 
                      : ""
                    }
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default AnalisisLibro;
