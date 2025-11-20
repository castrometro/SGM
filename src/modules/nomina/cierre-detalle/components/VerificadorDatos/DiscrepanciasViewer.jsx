import { useState, useEffect } from "react";
import { CheckCircle, AlertTriangle, Filter, ShieldCheck } from "lucide-react";
import DiscrepanciasTable from "./DiscrepanciasTable";
import { 
  obtenerDiscrepanciasCierre, 
  obtenerResumenDiscrepancias
} from "../../api/cierreDetalle.api";

const DiscrepanciasViewer = ({ 
  cierreId, 
  estadoDiscrepancias, 
  visible = true 
}) => {
  const [discrepancias, setDiscrepancias] = useState([]);
  const [resumen, setResumen] = useState(null);
  const [cargando, setCargando] = useState(false);
  const [filtros, setFiltros] = useState({});

  useEffect(() => {
    if (cierreId && estadoDiscrepancias?.total_discrepancias > 0 && visible) {
      cargarDatos();
    }
  }, [cierreId, estadoDiscrepancias, visible]);

  const cargarDatos = async () => {
    if (!cierreId) return;
    
    setCargando(true);
    
    try {
      const [discrepanciasData, resumenData] = await Promise.all([
        obtenerDiscrepanciasCierre(cierreId, filtros),
        obtenerResumenDiscrepancias(cierreId)
      ]);
      
      setDiscrepancias(Array.isArray(discrepanciasData.results) ? discrepanciasData.results : discrepanciasData);
      setResumen(resumenData);
    } catch (err) {
      console.error("Error cargando datos de discrepancias:", err);
    } finally {
      setCargando(false);
    }
  };

  const manejarFiltroChange = (nuevosFiltros) => {
    setFiltros({ ...filtros, ...nuevosFiltros });
  };

  // No renderizar nada si no es visible o no hay discrepancias
  if (!visible || !estadoDiscrepancias) {
    return null;
  }

  // Si hay 0 discrepancias, mostrar mensaje de éxito
  if (estadoDiscrepancias.total_discrepancias === 0 && estadoDiscrepancias.verificacion_completada) {
    return (
      <div className="text-center py-8 text-gray-400">
        <CheckCircle className="w-12 h-12 mx-auto mb-3 text-green-500" />
        <p className="text-lg">No se encontraron discrepancias</p>
        <p className="text-sm">
          Los datos están en concordancia entre el Libro de Remuneraciones y las Novedades
        </p>
      </div>
    );
  }

  // Si no hay discrepancias aún, no mostrar nada
  if (estadoDiscrepancias.total_discrepancias === 0) {
    return null;
  }

  return (
    <div className="space-y-6">
      {/* Resumen de discrepancias */}
      {resumen && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Total Discrepancias</p>
                <p className="text-2xl font-bold text-white">{resumen.total}</p>
              </div>
              <AlertTriangle className="w-8 h-8 text-orange-500" />
            </div>
          </div>
          
          <div className="bg-gray-800 rounded-lg p-4 border border-blue-700/50">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Libro vs Novedades</p>
                <p className="text-2xl font-bold text-blue-400">
                  {resumen.total_libro_vs_novedades || 0}
                </p>
              </div>
              <div className="bg-blue-500/20 p-2 rounded-full">
                <ShieldCheck className="w-6 h-6 text-blue-400" />
              </div>
            </div>
            <p className="text-xs text-blue-300 mt-2">Comparación entre fuentes principales</p>
          </div>
          
          <div className="bg-gray-800 rounded-lg p-4 border border-purple-700/50">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Movimientos vs Analista</p>
                <p className="text-2xl font-bold text-purple-400">
                  {resumen.total_movimientos_vs_analista || 0}
                </p>
              </div>
              <div className="bg-purple-500/20 p-2 rounded-full">
                <CheckCircle className="w-6 h-6 text-purple-400" />
              </div>
            </div>
            <p className="text-xs text-purple-300 mt-2">Validación con datos del analista</p>
          </div>
          
          <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-400">Empleados Afectados</p>
                <p className="text-lg font-bold text-white">
                  {resumen.empleados_afectados || 0}
                </p>
              </div>
              <span className="text-yellow-400 text-2xl">👥</span>
            </div>
          </div>
        </div>
      )}

      {/* Filtros */}
      <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
        <div className="flex items-center gap-4 flex-wrap">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-gray-400" />
            <span className="text-sm text-gray-400">Filtros:</span>
          </div>
          
          <select
            value={filtros.tipo_discrepancia || ''}
            onChange={(e) => manejarFiltroChange({ tipo_discrepancia: e.target.value })}
            className="bg-gray-700 border border-gray-600 rounded px-3 py-1 text-sm text-white"
          >
            <option value="">Todos los tipos</option>
            {/* Grupo 1: Libro vs Novedades */}
            <optgroup label="Libro vs Novedades">
              <option value="empleado_solo_libro">Empleado solo en Libro</option>
              <option value="empleado_solo_novedades">Empleado solo en Novedades</option>
              <option value="diff_datos_personales">Diferencia en Datos Personales</option>
              <option value="diff_sueldo_base">Diferencia en Sueldo Base</option>
              <option value="diff_concepto_monto">Diferencia en Monto por Concepto</option>
              <option value="concepto_solo_libro">Concepto solo en Libro</option>
              <option value="concepto_solo_novedades">Concepto solo en Novedades</option>
            </optgroup>
            {/* Grupo 2: MovimientosMes vs Analista */}
            <optgroup label="Movimientos vs Analista">
              <option value="ingreso_no_reportado">Ingreso no reportado</option>
              <option value="finiquito_no_reportado">Finiquito no reportado</option>
              <option value="ausencia_no_reportada">Ausencia no reportada</option>
              <option value="diff_fechas_ausencia">Diferencia en Fechas de Ausencia</option>
              <option value="diff_dias_ausencia">Diferencia en Días de Ausencia</option>
              <option value="diff_tipo_ausencia">Diferencia en Tipo de Ausencia</option>
            </optgroup>
          </select>
          
          <input
            type="text"
            placeholder="Buscar por RUT, descripción, concepto..."
            value={filtros.busqueda || ''}
            onChange={(e) => manejarFiltroChange({ busqueda: e.target.value })}
            className="bg-gray-700 border border-gray-600 rounded px-3 py-1 text-sm text-white placeholder-gray-400"
          />
        </div>
      </div>

      {/* Tabla de discrepancias */}
      <div className="bg-gray-800 rounded-lg border border-gray-700">
        <div className="p-4 border-b border-gray-700">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-medium text-white">
              Lista de Discrepancias
            </h3>
            <div className="flex items-center gap-2 text-sm text-gray-400">
              <span>Solo informativas - No requieren resolución</span>
            </div>
          </div>
        </div>
        <div className="p-4">
          <DiscrepanciasTable
            cierreId={cierreId}
            filtros={filtros}
          />
        </div>
      </div>
    </div>
  );
};

export default DiscrepanciasViewer;
