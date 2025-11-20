// src/modules/contabilidad/historial-cierres/pages/HistorialCierresContabilidadPage.jsx
import { useEffect, useState, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  FileCheck,
  RefreshCw,
  ArrowLeft
} from "lucide-react";
import { obtenerCierresContabilidadCliente, obtenerCliente, obtenerUsuario } from "../api/historialCierres.api";
import { validarAccesoContabilidad, filtrarCierresPorEstado, calcularEstadisticas } from "../utils/historialCierresHelpers";
import EstadisticasCierres from "../components/EstadisticasCierres";
import FiltrosCierres from "../components/FiltrosCierres";
import TablaCierres from "../components/TablaCierres";

/**
 * Página de historial de cierres de contabilidad
 * Muestra todos los cierres de un cliente con filtros y estadísticas
 */
const HistorialCierresContabilidadPage = () => {
  const { clienteId } = useParams();
  const navigate = useNavigate();
  
  const [cliente, setCliente] = useState(null);
  const [cierres, setCierres] = useState([]);
  const [filtroEstado, setFiltroEstado] = useState("todos");
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [hasAccess, setHasAccess] = useState(null);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState("");

  const fetchCierres = useCallback(async (showRefresh = false) => {
    if (showRefresh) setIsRefreshing(true);
    
    try {
      const res = await obtenerCierresContabilidadCliente(clienteId);
      setCierres(res);
    } catch (error) {
      console.error("Error obteniendo cierres:", error);
      setError("Error al cargar los cierres");
    }
    
    if (showRefresh) {
      setTimeout(() => setIsRefreshing(false), 500);
    }
  }, [clienteId]);

  useEffect(() => {
    const cargarDatos = async () => {
      setCargando(true);
      setError("");
      
      try {
        // 1. Validar acceso
        const userData = await obtenerUsuario();
        const tieneAcceso = validarAccesoContabilidad(userData);
        setHasAccess(tieneAcceso);
        
        if (!tieneAcceso) {
          setCargando(false);
          return;
        }

        // 2. Cargar cliente
        const clienteData = await obtenerCliente(clienteId);
        setCliente(clienteData);

        // 3. Cargar cierres
        await fetchCierres();
      } catch (err) {
        console.error("Error cargando datos:", err);
        if (err.response?.status === 404) {
          setError(`No se encontró el cliente con ID ${clienteId}`);
        } else if (err.response?.status === 403) {
          setError("No tienes permisos para ver este cliente");
        } else {
          setError("Error al cargar los datos");
        }
      }
      
      setCargando(false);
    };

    if (clienteId) {
      cargarDatos();
    }
  }, [clienteId, fetchCierres]);

  // Auto-refresh para cierres en proceso
  useEffect(() => {
    const cierresEnProceso = cierres.filter(cierre => 
      cierre.estado === 'generando_reportes' || cierre.estado === 'procesando'
    );
    
    if (cierresEnProceso.length > 0) {
      const interval = setInterval(() => fetchCierres(), 30000);
      return () => clearInterval(interval);
    }
  }, [cierres, fetchCierres]);

  // Validando acceso
  if (cargando && hasAccess === null) {
    return (
      <div className="text-white flex items-center justify-center h-64">
        <div className="flex flex-col items-center gap-3">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500"></div>
          <p>Validando acceso...</p>
        </div>
      </div>
    );
  }

  // Sin acceso
  if (hasAccess === false) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="max-w-md mx-auto text-center p-8">
          <div className="text-red-400 text-5xl mb-4">⚠️</div>
          <h2 className="text-2xl font-bold text-gray-100 mb-2">Acceso Denegado</h2>
          <p className="text-gray-400 mb-6">
            No tienes permisos para acceder al historial de cierres de Contabilidad.
          </p>
          <button
            onClick={() => navigate('/menu')}
            className="px-6 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors"
          >
            Volver al Menú
          </button>
        </div>
      </div>
    );
  }

  // Cargando
  if (cargando) {
    return (
      <div className="text-white flex items-center justify-center h-64">
        <div className="flex flex-col items-center gap-3">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-500"></div>
          <p>Cargando historial...</p>
        </div>
      </div>
    );
  }

  // Error
  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="max-w-md mx-auto text-center p-8">
          <div className="text-red-400 text-5xl mb-4">❌</div>
          <h2 className="text-2xl font-bold text-gray-100 mb-2">Error</h2>
          <p className="text-gray-400 mb-6">{error}</p>
          <button
            onClick={() => navigate('/menu/clientes')}
            className="px-6 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors"
          >
            Volver a Clientes
          </button>
        </div>
      </div>
    );
  }

  const cierresFiltrados = filtrarCierresPorEstado(cierres, filtroEstado);
  const stats = calcularEstadisticas(cierres);

  // Sin cierres
  if (cierres.length === 0) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4 mb-4">
          <button
            onClick={() => navigate('/menu/clientes')}
            className="p-2 hover:bg-gray-700 rounded-lg transition-colors text-white"
          >
            <ArrowLeft size={20} />
          </button>
          <h1 className="text-2xl font-bold text-white">Historial de Cierres - Contabilidad</h1>
        </div>

        <div className="flex flex-col items-center justify-center py-16 px-4">
          <div className="bg-gradient-to-br from-gray-800/50 to-gray-900/50 backdrop-blur-sm rounded-2xl p-8 border border-gray-700/50 max-w-md text-center">
            <FileCheck size={48} className="text-gray-500 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-white mb-2">Sin cierres registrados</h3>
            <p className="text-sm text-gray-400">
              No hay cierres contables para {cliente?.nombre || 'este cliente'} aún.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 text-white">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/menu/clientes')}
            className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
          >
            <ArrowLeft size={20} />
          </button>
          <div>
            <h2 className="text-2xl font-bold flex items-center gap-3">
              <div className="p-2 bg-gradient-to-br from-purple-500/20 to-indigo-500/20 rounded-lg border border-purple-500/30">
                <FileCheck size={24} className="text-purple-400" />
              </div>
              Historial de Cierres
              <span className="px-3 py-1 rounded-full bg-purple-600 text-white text-sm font-semibold">
                Contabilidad
              </span>
            </h2>
            <p className="text-sm text-gray-400 mt-1">
              {cliente?.nombre} • {cierresFiltrados.length} de {cierres.length} cierres mostrados
            </p>
          </div>
        </div>

        <button
          onClick={() => fetchCierres(true)}
          disabled={isRefreshing}
          className="flex items-center gap-2 px-4 py-2 bg-gray-800/80 hover:bg-gray-700/80 border border-gray-600/50 rounded-lg text-sm text-gray-300 transition-all duration-200 disabled:opacity-50"
        >
          <RefreshCw size={16} className={isRefreshing ? "animate-spin" : ""} />
          Actualizar
        </button>
      </div>

      {/* Estadísticas */}
      <EstadisticasCierres stats={stats} />

      {/* Filtros */}
      <FiltrosCierres 
        filtroActivo={filtroEstado}
        stats={stats}
        onCambiarFiltro={setFiltroEstado}
      />

      {/* Tabla */}
      <TablaCierres cierres={cierresFiltrados} />
    </div>
  );
};

export default HistorialCierresContabilidadPage;
