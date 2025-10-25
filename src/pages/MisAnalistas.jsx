import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Users, User, Building2, Calendar, AlertCircle, CheckCircle, Eye, FileText, ShieldCheck, ChevronDown, ChevronRight } from 'lucide-react';
import { obtenerMisAnalistas, obtenerClientesSupervisionados } from '../api/supervisores';

const MisAnalistas = () => {
  const navigate = useNavigate();
  const [supervisorData, setSupervisorData] = useState(null);
  const [clientesSupervisionados, setClientesSupervisionados] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expandedAnalista, setExpandedAnalista] = useState(null);

  useEffect(() => {
    fetchSupervisorData();
    fetchClientesSupervisionados();
  }, []);

  const fetchSupervisorData = async () => {
    try {
      const data = await obtenerMisAnalistas();
      setSupervisorData(data);
    } catch (err) {
      setError(err.message || 'Error al cargar datos del supervisor');
    }
  };

  const fetchClientesSupervisionados = async () => {
    try {
      const data = await obtenerClientesSupervisionados();
      setClientesSupervisionados(data);
    } catch (err) {
      setError(err.message || 'Error al cargar clientes supervisados');
    } finally {
      setLoading(false);
    }
  };

  const toggleExpandAnalista = (analistaId) => {
    setExpandedAnalista(expandedAnalista === analistaId ? null : analistaId);
  };

  const handleVerClientes = (analista) => {
    // Expandir/contraer la sección de clientes del analista
    toggleExpandAnalista(analista.id);
  };

  const handleVerHistorial = (clienteId) => {
    // Navegar al historial de cierres del cliente
    navigate(`/menu/clientes/${clienteId}/cierres`);
  };

  const handleIrValidacion = () => {
    // TODO: Implementar página de validaciones
    // navigate('/menu/validaciones');
    alert('Funcionalidad de validaciones en desarrollo');
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-64 text-white">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-400">Cargando datos del supervisor...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-900/20 border border-red-500/30 rounded-lg p-6">
        <div className="flex items-center">
          <AlertCircle className="h-6 w-6 text-red-400 mr-3" />
          <span className="text-red-300">{error}</span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header inspirado en ClienteDetalle */}
      <div className="bg-gradient-to-br from-gray-800 via-gray-800 to-gray-900 rounded-xl shadow-2xl overflow-hidden border border-gray-700/50">
        {/* Header con gradiente */}
        <div className="bg-gradient-to-r from-indigo-600/20 via-purple-600/20 to-pink-600/20 border-b border-gray-700/50 p-6">
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-3">
                <div className="flex items-center justify-center w-12 h-12 rounded-xl bg-gradient-to-br from-indigo-500/20 to-purple-500/20 border border-indigo-500/30">
                  <Users className="w-6 h-6 text-indigo-400" />
                </div>
                <div>
                  <h1 className="text-2xl font-bold text-white leading-tight">
                    Mis Analistas
                  </h1>
                  <p className="text-sm text-gray-400 mt-0.5">
                    Gestión y supervisión de tu equipo
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Métricas en grid similar a ClienteDetalle */}
        {supervisorData && (
          <div className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Total Analistas */}
              <div className="group bg-gradient-to-br from-gray-700/40 to-gray-800/40 rounded-lg p-5 border border-gray-700/50 hover:border-gray-600 hover:shadow-lg transition-all duration-300 hover:-translate-y-0.5">
                <div className="absolute top-0 left-0 w-1 h-full rounded-l-lg bg-indigo-500" />
                <div className="ml-2">
                  <div className="flex items-center gap-2 mb-2">
                    <User className="w-4 h-4 text-indigo-400" />
                    <span className="text-xs font-medium text-gray-400 uppercase tracking-wider">Total Analistas</span>
                  </div>
                  <p className="text-3xl font-bold text-indigo-300 tabular-nums">
                    {supervisorData.total_analistas}
                  </p>
                </div>
              </div>

              {/* Total Clientes */}
              <div className="group bg-gradient-to-br from-gray-700/40 to-gray-800/40 rounded-lg p-5 border border-gray-700/50 hover:border-gray-600 hover:shadow-lg transition-all duration-300 hover:-translate-y-0.5">
                <div className="absolute top-0 left-0 w-1 h-full rounded-l-lg bg-emerald-500" />
                <div className="ml-2">
                  <div className="flex items-center gap-2 mb-2">
                    <Building2 className="w-4 h-4 text-emerald-400" />
                    <span className="text-xs font-medium text-gray-400 uppercase tracking-wider">Clientes Supervisados</span>
                  </div>
                  <p className="text-3xl font-bold text-emerald-300 tabular-nums">
                    {supervisorData.total_clientes_supervisados}
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Efecto de brillo sutil */}
        <div className="absolute inset-0 rounded-xl opacity-0 hover:opacity-100 transition-opacity duration-500 pointer-events-none">
          <div className="absolute inset-0 rounded-xl bg-gradient-to-br from-white/[0.02] to-transparent" />
        </div>
      </div>

      {/* Contenido principal */}
      {supervisorData && supervisorData.analistas_supervisados && supervisorData.analistas_supervisados.length > 0 ? (
        <div className="space-y-4">
          {/* Header de sección con botón de validaciones */}
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-white flex items-center gap-2">
              <Users className="w-5 h-5 text-indigo-400" />
              Equipo de Analistas
            </h2>
            <button
              onClick={handleIrValidacion}
              className="flex items-center px-4 py-2 bg-gradient-to-r from-yellow-500/20 to-orange-500/20 hover:from-yellow-500/30 hover:to-orange-500/30 text-yellow-300 border border-yellow-500/30 rounded-lg transition-all"
            >
              <ShieldCheck className="h-4 w-4 mr-2" />
              Validaciones
            </button>
          </div>

          {/* Grid de tarjetas de analistas - estilo ClienteDetalle */}
          <div className="space-y-4">
            {supervisorData.analistas_supervisados.map((analista) => (
              <div
                key={analista.id}
                className="bg-gradient-to-br from-gray-800 via-gray-800 to-gray-900 rounded-xl shadow-2xl overflow-hidden border border-gray-700/50 hover:border-gray-600 transition-all duration-300"
              >
                {/* Card Header con info del analista */}
                <div className="bg-gradient-to-r from-blue-600/10 via-indigo-600/10 to-purple-600/10 border-b border-gray-700/50 p-6">
                  <div className="flex items-center justify-between gap-4">
                    {/* Info del analista */}
                    <div className="flex items-center gap-4 flex-1">
                      {/* Avatar con indicador de estado */}
                      <div className="relative">
                        <div className="w-14 h-14 rounded-xl bg-gradient-to-br from-blue-500/20 to-indigo-500/20 border border-blue-500/30 flex items-center justify-center">
                          <User className="w-7 h-7 text-blue-400" />
                        </div>
                        <div className="absolute -bottom-1 -right-1 w-4 h-4 bg-emerald-500 border-2 border-gray-800 rounded-full"></div>
                      </div>
                      
                      {/* Datos del analista */}
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-1">
                          <h3 className="text-xl font-bold text-white">
                            {analista.nombre} {analista.apellido}
                          </h3>
                          {/* Áreas como badges */}
                          {analista.areas.map((area) => (
                            <span
                              key={area.id}
                              className="inline-flex items-center gap-1.5 bg-purple-500/20 text-purple-300 text-xs font-medium px-3 py-1 rounded-full border border-purple-500/30"
                            >
                              <Building2 className="w-3 h-3" />
                              {area.nombre}
                            </span>
                          ))}
                        </div>
                        <p className="text-sm text-gray-400">
                          {analista.correo_bdo}
                        </p>
                        <p className="text-xs text-gray-500 mt-0.5">
                          {analista.cargo_bdo}
                        </p>
                      </div>
                    </div>

                    {/* Métricas y acciones */}
                    <div className="flex items-center gap-4">
                      {/* Badge de clientes */}
                      <div className="bg-gradient-to-br from-gray-700/40 to-gray-800/40 rounded-lg p-4 border border-gray-700/50 text-center min-w-[100px]">
                        <div className="text-3xl font-bold text-indigo-300 tabular-nums">
                          {analista.total_clientes}
                        </div>
                        <div className="text-xs text-gray-400 uppercase tracking-wider mt-1">
                          Cliente{analista.total_clientes !== 1 ? 's' : ''}
                        </div>
                      </div>

                      {/* Botón Ver Clientes */}
                      <button
                        onClick={() => handleVerClientes(analista)}
                        className="flex items-center gap-2 px-4 py-2.5 bg-gradient-to-r from-blue-500/20 to-indigo-500/20 hover:from-blue-500/30 hover:to-indigo-500/30 text-blue-300 border border-blue-500/30 rounded-lg transition-all"
                        title="Ver clientes asignados"
                      >
                        {expandedAnalista === analista.id ? (
                          <ChevronDown className="w-4 h-4" />
                        ) : (
                          <ChevronRight className="w-4 h-4" />
                        )}
                        <Eye className="w-4 h-4" />
                        Ver Clientes
                      </button>
                    </div>
                  </div>
                </div>

                {/* Clientes expandibles con diseño mejorado */}
                {expandedAnalista === analista.id && analista.clientes_asignados && (
                  <div className="p-6 bg-gray-900/30">
                    <h4 className="text-sm font-medium text-gray-300 flex items-center gap-2 mb-4">
                      <Building2 className="w-4 h-4 text-blue-400" />
                      Clientes asignados a {analista.nombre}
                      <span className="text-gray-500">({analista.clientes_asignados.length})</span>
                    </h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
                      {analista.clientes_asignados.map((cliente) => (
                        <div
                          key={cliente.id}
                          className="group bg-gradient-to-br from-gray-700/40 to-gray-800/40 rounded-lg p-4 border border-gray-700/50 hover:border-blue-500/50 transition-all duration-300 hover:-translate-y-0.5 cursor-pointer"
                        >
                          <div className="flex items-start gap-3 mb-3">
                            <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-blue-500/20 border border-blue-500/30 flex-shrink-0">
                              <Building2 className="w-5 h-5 text-blue-400" />
                            </div>
                            <div className="flex-1 min-w-0">
                              <h5 className="font-semibold text-white text-sm group-hover:text-blue-400 transition-colors truncate">
                                {cliente.nombre}
                              </h5>
                              <p className="text-gray-400 text-xs mt-0.5">{cliente.rut}</p>
                            </div>
                          </div>
                          <button
                            onClick={() => handleVerHistorial(cliente.id)}
                            className="w-full flex items-center justify-center gap-2 px-3 py-2 bg-gradient-to-r from-emerald-500/20 to-green-500/20 hover:from-emerald-500/30 hover:to-green-500/30 text-emerald-300 border border-emerald-500/30 rounded-lg transition-all text-xs font-medium"
                          >
                            <FileText className="w-3.5 h-3.5" />
                            Ver Historial
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Efecto de brillo sutil */}
                <div className="absolute inset-0 rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none">
                  <div className="absolute inset-0 rounded-xl bg-gradient-to-br from-white/[0.02] to-transparent" />
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        supervisorData && (
          <div className="bg-gradient-to-br from-gray-800 via-gray-800 to-gray-900 rounded-xl shadow-2xl overflow-hidden border border-gray-700/50 p-12 text-center">
            <div className="max-w-md mx-auto">
              <div className="flex items-center justify-center w-20 h-20 rounded-xl bg-gradient-to-br from-gray-700/40 to-gray-800/40 border border-gray-700/50 mx-auto mb-4">
                <Users className="w-10 h-10 text-gray-500" />
              </div>
              <h3 className="text-xl font-semibold text-white mb-2">
                No tienes analistas asignados
              </h3>
              <p className="text-gray-400">
                Aún no se te han asignado analistas para supervisar. Contacta con tu gerente para más información.
              </p>
            </div>
          </div>
        )
      )}

      {/* Resumen general mejorado con estilo ClienteDetalle */}
      {clientesSupervisionados.length > 0 && (
        <div className="bg-gradient-to-br from-gray-800 via-gray-800 to-gray-900 rounded-xl shadow-2xl overflow-hidden border border-gray-700/50">
          {/* Header con gradiente */}
          <div className="bg-gradient-to-r from-emerald-600/20 via-green-600/20 to-teal-600/20 border-b border-gray-700/50 p-6">
            <div className="flex items-center gap-3">
              <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-gradient-to-br from-emerald-500/20 to-green-500/20 border border-emerald-500/30">
                <CheckCircle className="w-5 h-5 text-emerald-400" />
              </div>
              <div>
                <h2 className="text-xl font-semibold text-white">
                  Todos los Clientes Supervisados
                </h2>
                <p className="text-sm text-gray-400 mt-0.5">
                  Vista consolidada de {clientesSupervisionados.length} clientes bajo tu supervisión
                </p>
              </div>
            </div>
          </div>
          
          {/* Grid de clientes */}
          <div className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {clientesSupervisionados.map((item) => (
                <div
                  key={`${item.cliente.id}-${item.analista.id}`}
                  className="group bg-gradient-to-br from-gray-700/40 to-gray-800/40 rounded-lg p-4 border border-gray-700/50 hover:border-emerald-500/50 transition-all duration-300 hover:-translate-y-0.5 cursor-pointer"
                >
                  {/* Header con cliente */}
                  <div className="flex items-start gap-3 mb-3">
                    <div className="flex items-center justify-center w-10 h-10 rounded-lg bg-emerald-500/20 border border-emerald-500/30 flex-shrink-0">
                      <Building2 className="w-5 h-5 text-emerald-400" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="font-semibold text-white text-sm group-hover:text-emerald-400 transition-colors truncate">
                        {item.cliente.nombre}
                      </h3>
                      <p className="text-xs text-gray-400 mt-0.5">{item.cliente.rut}</p>
                    </div>
                    <CheckCircle className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                  </div>
                  
                  {/* Info del analista y fecha */}
                  <div className="space-y-2 mb-3 pt-3 border-t border-gray-700/50">
                    <div className="flex items-center gap-2 text-xs text-gray-300">
                      <User className="w-3.5 h-3.5 text-blue-400" />
                      <span className="truncate">{item.analista.nombre} {item.analista.apellido}</span>
                    </div>
                    <div className="flex items-center gap-2 text-xs text-gray-400">
                      <Calendar className="w-3.5 h-3.5" />
                      {new Date(item.fecha_asignacion).toLocaleDateString('es-ES', {
                        day: '2-digit',
                        month: 'short',
                        year: 'numeric'
                      })}
                    </div>
                  </div>
                  
                  {/* Botón de acción */}
                  <button
                    onClick={() => handleVerHistorial(item.cliente.id)}
                    className="w-full flex items-center justify-center gap-2 px-3 py-2 bg-gradient-to-r from-emerald-500/20 to-green-500/20 hover:from-emerald-500/30 hover:to-green-500/30 text-emerald-300 border border-emerald-500/30 rounded-lg transition-all text-xs font-medium"
                  >
                    <FileText className="w-3.5 h-3.5" />
                    Ver Historial
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* Efecto de brillo sutil */}
          <div className="absolute inset-0 rounded-xl opacity-0 hover:opacity-100 transition-opacity duration-500 pointer-events-none">
            <div className="absolute inset-0 rounded-xl bg-gradient-to-br from-white/[0.02] to-transparent" />
          </div>
        </div>
      )}
    </div>
  );
};

export default MisAnalistas;
