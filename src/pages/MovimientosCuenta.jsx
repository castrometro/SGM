import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import CierreInfoBar from "../components/InfoCards/CierreInfoBar";
import {
  obtenerCierrePorId,
  obtenerMovimientosCuenta,
} from "../api/contabilidad";
import { obtenerCliente } from "../api/clientes";
import { formatMoney } from "../utils/format";

const MovimientosCuenta = () => {
  const { cierreId, cuentaId } = useParams();
  const [cierre, setCierre] = useState(null);
  const [cliente, setCliente] = useState(null);
  const [detalle, setDetalle] = useState(null);
  const [filtros, setFiltros] = useState({ desde: "", hasta: "", texto: "" });
  const [sortField, setSortField] = useState("fecha");
  const [sortOrder, setSortOrder] = useState("asc");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [paginaActual, setPaginaActual] = useState(1);
  const [movimientosPorPagina, setMovimientosPorPagina] = useState(50); // Hacer editable

  useEffect(() => {
    const fetchData = async () => {
      if (!cierreId || !cuentaId) {
        setError("Parámetros de cierre o cuenta faltantes");
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        setError(null);

        console.log(`Cargando datos para cierre ${cierreId} y cuenta ${cuentaId}`);
        
        // Cargar cierre
        const cierreObj = await obtenerCierrePorId(cierreId);
        console.log("Cierre obtenido:", cierreObj);
        setCierre(cierreObj);
        
        // Cargar cliente
        const clienteObj = await obtenerCliente(cierreObj.cliente);
        console.log("Cliente obtenido:", clienteObj);
        setCliente(clienteObj);
        
        // Cargar movimientos de la cuenta - intentar obtener todos
        const data = await obtenerMovimientosCuenta(cierreId, cuentaId, { 
          limit: 10000,  // Solicitar hasta 10,000 movimientos
          page_size: 10000,
          per_page: 10000,
          all: true  // Algunos backends usan este parámetro
        });
        console.log("Movimientos obtenidos:", data);
        setDetalle(data);
      } catch (err) {
        console.error("Error al cargar datos:", err);
        setError(`Error al cargar los datos: ${err.message || "Error desconocido"}`);
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, [cierreId, cuentaId]);

  // Resetear página al cambiar filtros
  useEffect(() => {
    setPaginaActual(1);
  }, [filtros.desde, filtros.hasta, filtros.texto]);

  if (loading) {
    return (
      <div className="text-white text-center mt-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white mx-auto mb-4"></div>
        Cargando movimientos...
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-red-400 text-center mt-8 p-4 bg-red-900/20 rounded-lg">
        <h2 className="text-lg font-semibold mb-2">Error</h2>
        <p>{error}</p>
        <Link 
          to={`/menu/cierres/${cierreId}/libro`} 
          className="inline-block mt-4 text-blue-400 hover:text-blue-300"
        >
          ← Volver al libro mayor
        </Link>
      </div>
    );
  }

  if (!cierre || !cliente || !detalle) {
    return (
      <div className="text-white text-center mt-8">Cargando movimientos...</div>
    );
  }

  const { desde, hasta, texto } = filtros;
  
  // Filtrar movimientos excluyendo totales (registros sin fecha específica o con fecha futura sospechosa)
  const movimientosReales = (detalle.movimientos || []).filter((m) => {
    // Excluir registros que parecen ser totales o resúmenes
    // Pueden ser identificados por tener fechas futuras, o campos específicos
    if (!m.fecha) return false;
    
    // Si la fecha es muy reciente y los valores parecen ser totales, excluir
    const fechaMovimiento = new Date(m.fecha);
    const hoy = new Date();
    const esHoy = fechaMovimiento.toDateString() === hoy.toDateString();
    
    // Si es de hoy, probablemente es un total
    if (esHoy) {
      return false;
    }
    
    // Filtro adicional: si tiene valores muy altos que parecen ser sumas
    const debeAlto = (Number(m.debe) || 0) > 300000;
    const haberAlto = (Number(m.haber) || 0) > 2000000;
    
    if (debeAlto && haberAlto) {
      return false; // Probablemente es una fila de totales
    }
    
    // Filtro por descripción sospechosa (si no tiene descripción específica)
    const descripcionText = typeof m.descripcion === 'object' && m.descripcion 
      ? (m.descripcion.descripcion || m.descripcion.codigo || '') 
      : (m.descripcion || "");
    
    if (!descripcionText || descripcionText.trim() === '') {
      return false;
    }
    
    return true;
  });
  
  const movimientosFiltrados = movimientosReales.filter((m) => {
    if (desde && new Date(m.fecha) < new Date(desde)) return false;
    if (hasta && new Date(m.fecha) > new Date(hasta)) return false;
    if (texto) {
      const descripcionText = typeof m.descripcion === 'object' && m.descripcion 
        ? (m.descripcion.descripcion || m.descripcion.codigo || '') 
        : (m.descripcion || "");
      if (!descripcionText.toLowerCase().includes(texto.toLowerCase())) {
        return false;
      }
    }
    return true;
  });

  const handleSort = (field) => {
    if (sortField === field) {
      setSortOrder((o) => (o === "asc" ? "desc" : "asc"));
    } else {
      setSortField(field);
      setSortOrder("asc");
    }
  };

  const movimientosOrdenados = [...movimientosFiltrados].sort((a, b) => {
    let valA = a[sortField];
    let valB = b[sortField];
    
    // Manejar campos que pueden ser objetos
    if (sortField === "descripcion") {
      valA = typeof valA === 'object' && valA 
        ? (valA.descripcion || valA.codigo || '') 
        : (valA || "");
      valB = typeof valB === 'object' && valB 
        ? (valB.descripcion || valB.codigo || '') 
        : (valB || "");
    } else if (sortField === "tipo_documento") {
      valA = typeof valA === 'object' && valA 
        ? (valA.descripcion || valA.codigo || '') 
        : (valA || "");
      valB = typeof valB === 'object' && valB 
        ? (valB.descripcion || valB.codigo || '') 
        : (valB || "");
    } else if (sortField === "fecha") {
      valA = new Date(valA);
      valB = new Date(valB);
    }
    
    if (valA < valB) return sortOrder === "asc" ? -1 : 1;
    if (valA > valB) return sortOrder === "asc" ? 1 : -1;
    return 0;
  });

  // Lógica de paginación
  const totalPaginas = Math.ceil(movimientosOrdenados.length / movimientosPorPagina);
  const indiceInicio = (paginaActual - 1) * movimientosPorPagina;
  const indiceFin = indiceInicio + movimientosPorPagina;
  const movimientosPaginados = movimientosOrdenados.slice(indiceInicio, indiceFin);

  const irAPagina = (pagina) => {
    setPaginaActual(Math.max(1, Math.min(pagina, totalPaginas)));
  };

  return (
    <div className="space-y-6">
      <CierreInfoBar cierre={cierre} cliente={cliente} />
      <Link to={`/menu/cierres/${cierreId}/libro`} className="text-blue-400">
        ← Volver
      </Link>
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-semibold text-white">
          {detalle.codigo} - {detalle.nombre}
        </h2>
        <div className="text-sm text-gray-400">
          {movimientosOrdenados.length} movimiento{movimientosOrdenados.length !== 1 ? 's' : ''} total
          {(desde || hasta || texto) && ` (filtrado${movimientosOrdenados.length !== 1 ? 's' : ''})`}
          {movimientosOrdenados.length > movimientosPorPagina && (
            <span className="ml-2">
              • Página {paginaActual} de {totalPaginas}
            </span>
          )}
        </div>
      </div>

      <div className="bg-gray-800 p-4 rounded-md">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end">
          <div className="flex flex-col">
            <label className="text-sm text-gray-300" htmlFor="desde">Desde</label>
            <input
              id="desde"
              type="date"
              className="bg-gray-700 text-white rounded px-2 py-1 min-w-[140px]"
              value={desde}
              onChange={(e) =>
                setFiltros((f) => ({ ...f, desde: e.target.value }))
              }
            />
          </div>
          <div className="flex flex-col">
            <label className="text-sm text-gray-300" htmlFor="hasta">Hasta</label>
            <input
              id="hasta"
              type="date"
              className="bg-gray-700 text-white rounded px-2 py-1 min-w-[140px]"
              value={hasta}
              onChange={(e) =>
                setFiltros((f) => ({ ...f, hasta: e.target.value }))
              }
            />
          </div>
          <div className="flex flex-col flex-grow">
            <label className="text-sm text-gray-300" htmlFor="texto">Buscar</label>
            <input
              id="texto"
              type="text"
              placeholder="Descripción..."
              className="bg-gray-700 text-white rounded px-2 py-1"
              value={texto}
              onChange={(e) =>
                setFiltros((f) => ({ ...f, texto: e.target.value }))
              }
            />
          </div>
          <div className="flex flex-col">
            <label className="text-sm text-gray-300" htmlFor="porPagina">Por página</label>
            <select
              id="porPagina"
              className="bg-gray-700 text-white rounded px-2 py-1 min-w-[100px]"
              value={movimientosPorPagina}
              onChange={(e) => {
                setMovimientosPorPagina(Number(e.target.value));
                setPaginaActual(1); // Reset a página 1
              }}
            >
              <option value={20}>20</option>
              <option value={50}>50</option>
              <option value={100}>100</option>
              <option value={200}>200</option>
              <option value={999999}>Todos</option>
            </select>
          </div>
        </div>
        
        {/* Información adicional sobre limitaciones del backend */}
        {detalle.movimientos && detalle.movimientos.length >= 20 && (
          <div className="mt-3 p-3 bg-yellow-900/30 border border-yellow-600/50 rounded">
            <div className="flex items-center justify-between">
              <div className="text-yellow-200 text-xs">
                ⚠️ Posible limitación del backend: Mostrando {detalle.movimientos.length} movimientos. 
                Puede haber más datos disponibles.
              </div>
              <button
                onClick={async () => {
                  try {
                    setLoading(true);
                    // Intentar diferentes parámetros para obtener más datos
                    const dataTodos = await obtenerMovimientosCuenta(cierreId, cuentaId, { 
                      limit: 999999,
                      size: 999999,
                      count: 999999
                    });
                    setDetalle(dataTodos);
                  } catch (err) {
                    console.error("Error al intentar cargar más movimientos:", err);
                  } finally {
                    setLoading(false);
                  }
                }}
                className="ml-3 px-3 py-1 text-xs bg-yellow-600 hover:bg-yellow-700 text-white rounded"
              >
                Intentar cargar todos
              </button>
            </div>
          </div>
        )}
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm border-separate border-spacing-y-1">
          <thead>
            <tr className="bg-gray-700">
              <th
                className="px-4 py-2 cursor-pointer"
                onClick={() => handleSort("fecha")}
              >
                Fecha {sortField === "fecha" && (sortOrder === "asc" ? "▲" : "▼")}
              </th>
              <th
                className="px-4 py-2 cursor-pointer"
                onClick={() => handleSort("tipo_documento")}
              >
                Tipo doc.{" "}
                {sortField === "tipo_documento" &&
                  (sortOrder === "asc" ? "▲" : "▼")}
              </th>
              <th
                className="px-4 py-2 cursor-pointer"
                onClick={() => handleSort("numero_comprobante")}
              >
                N° comprobante {sortField === "numero_comprobante" && (sortOrder === "asc" ? "▲" : "▼")}
              </th>
              <th
                className="px-4 py-2 cursor-pointer"
                onClick={() => handleSort("descripcion")}
              >
                Descripción {sortField === "descripcion" && (sortOrder === "asc" ? "▲" : "▼")}
              </th>
              <th
                className="px-4 py-2 text-right cursor-pointer"
                onClick={() => handleSort("debe")}
              >
                Debe {sortField === "debe" && (sortOrder === "asc" ? "▲" : "▼")}
              </th>
              <th
                className="px-4 py-2 text-right cursor-pointer"
                onClick={() => handleSort("haber")}
              >
                Haber {sortField === "haber" && (sortOrder === "asc" ? "▲" : "▼")}
              </th>
              <th
                className="px-4 py-2 text-right cursor-pointer"
                onClick={() => handleSort("saldo")}
              >
                Saldo {sortField === "saldo" && (sortOrder === "asc" ? "▲" : "▼")}
              </th>
            </tr>
          </thead>
          <tbody>
            <tr className="bg-gray-800 font-semibold">
              <td colSpan={6} className="px-4 py-2 text-right">Saldo inicial</td>
              <td className="px-4 py-2 text-right">{formatMoney(detalle.saldo_inicial || 0)}</td>
            </tr>
            {movimientosPaginados.length === 0 ? (
              <tr className="bg-gray-800">
                <td colSpan={7} className="px-4 py-8 text-center text-gray-400">
                  No se encontraron movimientos{texto || desde || hasta ? " con los filtros aplicados" : ""}
                </td>
              </tr>
            ) : (
              <>
                {movimientosPaginados.map((m) => (
                  <tr key={m.id} className="bg-gray-800">
                    <td className="px-4 py-2">{m.fecha}</td>
                    <td className="px-4 py-2">
                      {typeof m.tipo_documento === 'object' && m.tipo_documento 
                        ? (m.tipo_documento.descripcion || m.tipo_documento.codigo || '') 
                        : (m.tipo_documento || "")
                      }
                    </td>
                    <td className="px-4 py-2">{m.numero_comprobante || ""}</td>
                    <td className="px-4 py-2">
                      {typeof m.descripcion === 'object' && m.descripcion 
                        ? (m.descripcion.descripcion || m.descripcion.codigo || '') 
                        : (m.descripcion || "")
                      }
                    </td>
                    <td className="px-4 py-2 text-right">{formatMoney(m.debe || 0)}</td>
                    <td className="px-4 py-2 text-right">{formatMoney(m.haber || 0)}</td>
                    <td className="px-4 py-2 text-right">{formatMoney(m.saldo || 0)}</td>
                  </tr>
                ))}
                {/* Fila de totales */}
                {movimientosOrdenados.length > 0 && (
                  <tr className="bg-gray-700 font-semibold border-t-2 border-gray-600">
                    <td colSpan={4} className="px-4 py-2 text-right">TOTALES:</td>
                    <td className="px-4 py-2 text-right">
                      {formatMoney(movimientosOrdenados.reduce((sum, m) => sum + (Number(m.debe) || 0), 0))}
                    </td>
                    <td className="px-4 py-2 text-right">
                      {formatMoney(movimientosOrdenados.reduce((sum, m) => sum + (Number(m.haber) || 0), 0))}
                    </td>
                    <td className="px-4 py-2 text-right">
                      {movimientosOrdenados.length > 0 
                        ? formatMoney(movimientosOrdenados[movimientosOrdenados.length - 1].saldo || 0)
                        : formatMoney(detalle.saldo_inicial || 0)
                      }
                    </td>
                  </tr>
                )}
              </>
            )}
          </tbody>
        </table>
      </div>

      {/* Información y controles de paginación */}
      <div className="flex items-center justify-between bg-gray-800 px-4 py-3 rounded-md">
        <div className="flex items-center text-sm text-gray-300">
          <span>
            {movimientosPorPagina >= 999999 
              ? `Mostrando todos los ${movimientosOrdenados.length} movimientos`
              : `Mostrando ${indiceInicio + 1} a ${Math.min(indiceFin, movimientosOrdenados.length)} de ${movimientosOrdenados.length} movimientos`
            }
          </span>
        </div>
        
        {totalPaginas > 1 && (
          <div className="flex items-center space-x-2">
            <button
              onClick={() => irAPagina(paginaActual - 1)}
              disabled={paginaActual === 1}
              className="px-3 py-1 text-sm bg-gray-700 text-white rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-600"
            >
              Anterior
            </button>
            
            <div className="flex space-x-1">
              {[...Array(totalPaginas)].map((_, index) => {
                const pagina = index + 1;
                const mostrarPagina = 
                  pagina === 1 || 
                  pagina === totalPaginas || 
                  (pagina >= paginaActual - 2 && pagina <= paginaActual + 2);
                
                if (!mostrarPagina) {
                  if (pagina === paginaActual - 3 || pagina === paginaActual + 3) {
                    return <span key={pagina} className="px-2 text-gray-500">...</span>;
                  }
                  return null;
                }
                
                return (
                  <button
                    key={pagina}
                    onClick={() => irAPagina(pagina)}
                    className={`px-3 py-1 text-sm rounded ${
                      paginaActual === pagina
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-700 text-white hover:bg-gray-600'
                    }`}
                  >
                    {pagina}
                  </button>
                );
              })}
            </div>
            
            <button
              onClick={() => irAPagina(paginaActual + 1)}
              disabled={paginaActual === totalPaginas}
              className="px-3 py-1 text-sm bg-gray-700 text-white rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-600"
            >
              Siguiente
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default MovimientosCuenta;
