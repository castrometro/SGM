import { useState, useEffect } from "react";
import { AlertTriangle, User, FileText, Eye } from "lucide-react";
import { obtenerDiscrepanciasCierre } from "../../../api/nomina";

const DiscrepanciasTable = ({ cierreId, filtros }) => {
  const [discrepancias, setDiscrepancias] = useState([]);
  const [cargando, setCargando] = useState(false);
  const [paginacion, setPaginacion] = useState({
    pagina: 1,
    porPagina: 20,
    total: 0,
    totalPaginas: 0
  });

  useEffect(() => {
    if (cierreId) {
      cargarDiscrepancias();
    }
  }, [cierreId, filtros, paginacion.pagina]);

  const cargarDiscrepancias = async () => {
    setCargando(true);
    try {
      const params = {
        ...filtros,
        page: paginacion.pagina,
        page_size: paginacion.porPagina
      };
      
      const response = await obtenerDiscrepanciasCierre(cierreId, params);
      
      setDiscrepancias(response.results || response);
      setPaginacion(prev => ({
        ...prev,
        total: response.count || response.length,
        totalPaginas: Math.ceil((response.count || response.length) / prev.porPagina)
      }));
    } catch (error) {
      console.error("Error cargando discrepancias:", error);
    } finally {
      setCargando(false);
    }
  };

  const formatearFecha = (fecha) => {
    if (!fecha) return "-";
    return new Date(fecha).toLocaleDateString('es-CL', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const obtenerIconoTipo = (tipo) => {
    const tiposIconos = {
      'empleado_solo_libro': '📚',
      'empleado_solo_novedades': '📝',
      'diff_datos_personales': '👤',
      'diff_sueldo_base': '💰',
      'diff_concepto_monto': '💲',
      'concepto_solo_libro': '📊',
      'concepto_solo_novedades': '📋',
      'ingreso_no_reportado': '➕',
      'finiquito_no_reportado': '➖',
      'ausencia_no_reportada': '🚫',
      'diff_fechas_ausencia': '📅',
      'diff_dias_ausencia': '🗓️',
      'diff_tipo_ausencia': '🔄'
    };
    return tiposIconos[tipo] || '⚠️';
  };

  const obtenerTextoTipo = (tipo) => {
    const tiposTextos = {
      'empleado_solo_libro': 'Empleado solo en Libro',
      'empleado_solo_novedades': 'Empleado solo en Novedades',
      'diff_datos_personales': 'Diferencia en Datos Personales',
      'diff_sueldo_base': 'Diferencia en Sueldo Base',
      'diff_concepto_monto': 'Diferencia en Monto por Concepto',
      'concepto_solo_libro': 'Concepto solo en Libro',
      'concepto_solo_novedades': 'Concepto solo en Novedades',
      'ingreso_no_reportado': 'Ingreso no reportado',
      'finiquito_no_reportado': 'Finiquito no reportado',
      'ausencia_no_reportada': 'Ausencia no reportada',
      'diff_fechas_ausencia': 'Diferencia en Fechas de Ausencia',
      'diff_dias_ausencia': 'Diferencia en Días de Ausencia',
      'diff_tipo_ausencia': 'Diferencia en Tipo de Ausencia'
    };
    return tiposTextos[tipo] || tipo;
  };

  const obtenerGrupoTipo = (tipo) => {
    const gruposLibroNovedades = [
      'empleado_solo_libro', 'empleado_solo_novedades', 'diff_datos_personales',
      'diff_sueldo_base', 'diff_concepto_monto', 'concepto_solo_libro', 'concepto_solo_novedades'
    ];
    
    return gruposLibroNovedades.includes(tipo) ? 'Libro vs Novedades' : 'Movimientos vs Analista';
  };

  const obtenerColorGrupo = (tipo) => {
    const grupo = obtenerGrupoTipo(tipo);
    return grupo === 'Libro vs Novedades' ? 'text-blue-400' : 'text-green-400';
  };

  const cambiarPagina = (nuevaPagina) => {
    setPaginacion(prev => ({ ...prev, pagina: nuevaPagina }));
  };

  if (cargando) {
    return (
      <div className="flex justify-center items-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-500"></div>
        <span className="ml-2 text-gray-400">Cargando discrepancias...</span>
      </div>
    );
  }

  if (!discrepancias.length) {
    return (
      <div className="text-center py-8 text-gray-400">
        <AlertTriangle className="w-8 h-8 mx-auto mb-2" />
        <p>No hay discrepancias con los filtros aplicados</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Tabla */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-700">
          <thead className="bg-gray-900">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                Tipo
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                Empleado
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">
                Descripción
              </th>
            </tr>
          </thead>
          <tbody className="bg-gray-800 divide-y divide-gray-700">
            {discrepancias.map((discrepancia) => (
              <tr key={discrepancia.id} className="hover:bg-gray-750 transition-colors">
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    <span className="text-lg mr-2">{obtenerIconoTipo(discrepancia.tipo_discrepancia)}</span>
                    <div>
                      <div className="text-sm font-medium text-white">
                        {obtenerTextoTipo(discrepancia.tipo_discrepancia)}
                      </div>
                      <div className={`text-xs ${obtenerColorGrupo(discrepancia.tipo_discrepancia)}`}>
                        {obtenerGrupoTipo(discrepancia.tipo_discrepancia)}
                      </div>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    <User className="w-4 h-4 text-gray-400 mr-2" />
                    <div>
                      <div className="text-sm text-white">
                        {discrepancia.empleado_libro_nombre || discrepancia.empleado_novedades_nombre || 'Sin nombre'}
                      </div>
                      <div className="text-xs text-gray-400">
                        RUT: {discrepancia.rut_empleado || '-'}
                      </div>
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4">
                  <div className="text-sm text-gray-300">
                    {discrepancia.descripcion}
                  </div>
                  
                  {/* Concepto afectado */}
                  {discrepancia.concepto_afectado && (
                    <div className="text-xs text-blue-400 mt-1">
                      <span className="font-medium">Concepto:</span> {discrepancia.concepto_afectado}
                    </div>
                  )}
                  
                  {/* Valores comparados - Para discrepancias Libro vs Novedades */}
                  {(discrepancia.valor_libro || discrepancia.valor_novedades) && (
                    <div className="mt-2 space-y-1">
                      {discrepancia.valor_libro && (
                        <div className="text-xs">
                          <span className="font-medium text-blue-300">📚 Libro:</span> 
                          <span className="text-gray-300 ml-2">{discrepancia.valor_libro}</span>
                        </div>
                      )}
                      {discrepancia.valor_novedades && (
                        <div className="text-xs">
                          <span className="font-medium text-green-300">📝 Novedades:</span>
                          <span className="text-gray-300 ml-2">{discrepancia.valor_novedades}</span>
                        </div>
                      )}
                    </div>
                  )}
                  
                  {/* Valores comparados - Para discrepancias MovimientosMes vs Analista */}
                  {(discrepancia.valor_movimientos || discrepancia.valor_analista) && (
                    <div className="mt-2 space-y-1">
                      {discrepancia.valor_movimientos && (
                        <div className="text-xs">
                          <span className="font-medium text-purple-300">📊 MovimientosMes:</span>
                          <span className="text-gray-300 ml-2">{discrepancia.valor_movimientos}</span>
                        </div>
                      )}
                      {discrepancia.valor_analista && (
                        <div className="text-xs">
                          <span className="font-medium text-yellow-300">👥 Analista:</span>
                          <span className="text-gray-300 ml-2">{discrepancia.valor_analista}</span>
                        </div>
                      )}
                    </div>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Paginación */}
      {paginacion.totalPaginas > 1 && (
        <div className="flex items-center justify-between border-t border-gray-700 px-4 py-3">
          <div className="flex items-center">
            <p className="text-sm text-gray-400">
              Mostrando {((paginacion.pagina - 1) * paginacion.porPagina) + 1} a{' '}
              {Math.min(paginacion.pagina * paginacion.porPagina, paginacion.total)} de{' '}
              {paginacion.total} discrepancias
            </p>
          </div>
          
          <div className="flex items-center space-x-2">
            <button
              onClick={() => cambiarPagina(paginacion.pagina - 1)}
              disabled={paginacion.pagina === 1}
              className="px-3 py-1 text-sm bg-gray-700 text-white rounded hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Anterior
            </button>
            
            <span className="text-sm text-gray-400">
              Página {paginacion.pagina} de {paginacion.totalPaginas}
            </span>
            
            <button
              onClick={() => cambiarPagina(paginacion.pagina + 1)}
              disabled={paginacion.pagina === paginacion.totalPaginas}
              className="px-3 py-1 text-sm bg-gray-700 text-white rounded hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Siguiente
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default DiscrepanciasTable;
