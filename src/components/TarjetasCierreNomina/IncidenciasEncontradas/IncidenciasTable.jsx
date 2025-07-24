import React, { useState, useEffect } from "react";
import { AlertTriangle, CheckCircle, Clock, XCircle, Eye, User, Calendar, UserCheck } from "lucide-react";
import { obtenerIncidenciasCierre } from "../../../api/nomina";
import { useAuth } from "../../../hooks/useAuth";
import { obtenerEstadoReal, ESTADOS_INCIDENCIA } from "../../../utils/incidenciaUtils";

const IncidenciasTable = ({ cierreId, filtros = {}, onIncidenciaSeleccionada }) => {
  const [todasLasIncidencias, setTodasLasIncidencias] = useState([]);
  const [incidenciasFiltradas, setIncidenciasFiltradas] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState("");
  const [paginaActual, setPaginaActual] = useState(1);
  const [incidenciasPorPagina] = useState(10);
  const { user } = useAuth();

  useEffect(() => {
    cargarIncidencias();
  }, [cierreId]);

  // Efecto para aplicar filtros localmente
  useEffect(() => {
    aplicarFiltros();
    setPaginaActual(1); // Resetear a primera página cuando cambian los filtros
  }, [filtros, todasLasIncidencias]);

  const cargarIncidencias = async () => {
    if (!cierreId) return;
    
    setCargando(true);
    setError("");
    try {
      const data = await obtenerIncidenciasCierre(cierreId, {
        // Solo traer todas sin filtros para tenerlas localmente
        page_size: 1000 // Traer muchas para tener todas localmente
      });
      const incidencias = Array.isArray(data.results) ? data.results : data;
      setTodasLasIncidencias(incidencias);
    } catch (err) {
      console.error("Error cargando incidencias:", err);
      setError("Error al cargar incidencias");
    } finally {
      setCargando(false);
    }
  };

  const aplicarFiltros = () => {
    let incidenciasFiltradas = [...todasLasIncidencias];
    
    // Debug para verificar filtros
    console.log('Aplicando filtros:', filtros);
    console.log('Total incidencias antes de filtrar:', incidenciasFiltradas.length);

    // Aplicar filtro por estado
    if (filtros.estado && filtros.estado !== '') {
      incidenciasFiltradas = incidenciasFiltradas.filter(
        incidencia => incidencia.estado === filtros.estado
      );
      console.log('Después filtro estado:', incidenciasFiltradas.length);
    }

    // Aplicar filtro por prioridad
    if (filtros.prioridad && filtros.prioridad !== '') {
      incidenciasFiltradas = incidenciasFiltradas.filter(
        incidencia => incidencia.prioridad === filtros.prioridad
      );
      console.log('Después filtro prioridad:', incidenciasFiltradas.length);
    }

    // Aplicar filtro por tipo
    if (filtros.tipo_incidencia && filtros.tipo_incidencia !== '') {
      incidenciasFiltradas = incidenciasFiltradas.filter(
        incidencia => incidencia.tipo_incidencia === filtros.tipo_incidencia
      );
      console.log('Después filtro tipo:', incidenciasFiltradas.length);
    }

    // Aplicar filtro por texto de búsqueda
    if (filtros.busqueda && filtros.busqueda.trim() !== '') {
      const busqueda = filtros.busqueda.toLowerCase().trim();
      incidenciasFiltradas = incidenciasFiltradas.filter(incidencia => 
        incidencia.rut_empleado?.toLowerCase().includes(busqueda) ||
        incidencia.descripcion?.toLowerCase().includes(busqueda) ||
        incidencia.concepto_afectado?.toLowerCase().includes(busqueda) ||
        incidencia.empleado_libro?.nombre?.toLowerCase().includes(busqueda) ||
        incidencia.empleado_novedades?.nombre?.toLowerCase().includes(busqueda)
      );
      console.log('Después filtro búsqueda:', incidenciasFiltradas.length);
    }

    console.log('Incidencias finales filtradas:', incidenciasFiltradas.length);
    setIncidenciasFiltradas(incidenciasFiltradas);
  };

  // Calcular incidencias para la página actual
  const indiceInicio = (paginaActual - 1) * incidenciasPorPagina;
  const indiceFin = indiceInicio + incidenciasPorPagina;
  const incidenciasPagina = incidenciasFiltradas.slice(indiceInicio, indiceFin);
  const totalPaginas = Math.ceil(incidenciasFiltradas.length / incidenciasPorPagina);

  const obtenerIconoEstado = (estadoReal) => {
    switch (estadoReal) {
      case ESTADOS_INCIDENCIA.PENDIENTE:
        return <Clock className="w-4 h-4 text-yellow-500" />;
      case ESTADOS_INCIDENCIA.RESUELTA_ANALISTA:
        return <CheckCircle className="w-4 h-4 text-blue-500" />;
      case ESTADOS_INCIDENCIA.APROBADA_SUPERVISOR:
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case ESTADOS_INCIDENCIA.RECHAZADA_SUPERVISOR:
        return <XCircle className="w-4 h-4 text-red-500" />;
      case ESTADOS_INCIDENCIA.RE_RESUELTA:
        return <CheckCircle className="w-4 h-4 text-purple-500" />;
      default:
        return <AlertTriangle className="w-4 h-4 text-gray-500" />;
    }
  };

  // Función para determinar el turno según la nueva arquitectura
  const obtenerTurnoIncidencia = (incidencia) => {
    const esSupervidor = user?.is_staff || user?.is_superuser;
    const resoluciones = incidencia.resoluciones || [];
    
    if (resoluciones.length === 0) {
      // INICIANDO: Sin mensajes → Turno del Analista
      return {
        esMiTurno: !esSupervidor,
        turno: 'Analista',
        icono: <User className="w-4 h-4 text-blue-500" />
      };
    }

    // Ordenar por fecha y obtener la última resolución
    const ultimaResolucion = resoluciones.sort((a, b) => 
      new Date(b.fecha_resolucion) - new Date(a.fecha_resolucion)
    )[0];

    // APROBADA: Último mensaje es aprobación → Conversación terminada
    if (ultimaResolucion.tipo_resolucion === 'aprobacion') {
      return {
        esMiTurno: false,
        turno: 'Aprobada',
        icono: <CheckCircle className="w-4 h-4 text-green-500" />
      };
    }

    // Determinar turno basado en el último mensaje
    const esDelSupervisor = ['consulta', 'rechazo'].includes(ultimaResolucion.tipo_resolucion);
    
    if (esDelSupervisor) {
      // TURNO_ANALISTA: Último mensaje fue de supervisor → Analista debe responder
      return {
        esMiTurno: !esSupervidor,
        turno: 'Analista',
        icono: <User className="w-4 h-4 text-blue-500" />
      };
    } else {
      // TURNO_SUPERVISOR: Último mensaje fue de analista → Supervisor debe decidir
      return {
        esMiTurno: esSupervidor,
        turno: 'Supervisor',
        icono: <UserCheck className="w-4 h-4 text-purple-500" />
      };
    }
  };

  const obtenerClasePrioridad = (prioridad) => {
    switch (prioridad) {
      case 'critica':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'alta':
        return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'media':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'baja':
        return 'bg-green-100 text-green-800 border-green-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const formatearFecha = (fecha) => {
    return new Date(fecha).toLocaleDateString('es-CL', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const truncarTexto = (texto, maxLength = 50) => {
    if (!texto) return '-';
    return texto.length > maxLength ? `${texto.substring(0, maxLength)}...` : texto;
  };

  if (cargando) {
    return (
      <div className="flex justify-center items-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
        <span className="ml-2 text-gray-300">Cargando incidencias...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-900/20 border border-red-500 rounded-lg p-4">
        <div className="flex items-center text-red-400">
          <AlertTriangle className="w-5 h-5 mr-2" />
          {error}
        </div>
      </div>
    );
  }

  if (!todasLasIncidencias.length) {
    return (
      <div className="text-center py-8 text-gray-400">
        <AlertTriangle className="w-12 h-12 mx-auto mb-3 opacity-50" />
        <p>No se encontraron incidencias</p>
        <p className="text-sm">Las incidencias aparecerán aquí una vez generadas</p>
      </div>
    );
  }

  if (!incidenciasFiltradas.length) {
    return (
      <div className="text-center py-8 text-gray-400">
        <AlertTriangle className="w-12 h-12 mx-auto mb-3 opacity-50" />
        <p>No se encontraron incidencias con los filtros aplicados</p>
        <p className="text-sm">Intenta ajustar los filtros para ver más resultados</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Tabla de incidencias */}
      <div className="overflow-x-auto">
        <table className="min-w-full bg-gray-800 rounded-lg">
          <thead className="bg-gray-700">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                Empleado
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                Tipo
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                Descripción
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                Prioridad
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                Estado
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                Turno
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                Impacto
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                Fecha
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                Acciones
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-700">
            {incidenciasPagina.map((incidencia) => (
              <tr key={incidencia.id} className="hover:bg-gray-700/50">
                <td className="px-4 py-3 whitespace-nowrap text-sm text-white">
                  <div>
                    <div className="font-medium">{incidencia.rut_empleado}</div>
                    {incidencia.empleado_libro?.nombre && (
                      <div className="text-gray-400 text-xs">
                        {incidencia.empleado_libro.nombre}
                      </div>
                    )}
                  </div>
                </td>
                <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-300">
                  {incidencia.get_tipo_incidencia_display || incidencia.tipo_incidencia}
                </td>
                <td className="px-4 py-3 text-sm text-gray-300">
                  <div title={incidencia.descripcion}>
                    {truncarTexto(incidencia.descripcion, 60)}
                  </div>
                  {incidencia.concepto_afectado && (
                    <div className="text-xs text-gray-500 mt-1">
                      {incidencia.concepto_afectado}
                    </div>
                  )}
                </td>
                <td className="px-4 py-3 whitespace-nowrap">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${obtenerClasePrioridad(incidencia.prioridad)}`}>
                    {incidencia.prioridad}
                  </span>
                </td>
                <td className="px-4 py-3 whitespace-nowrap">
                  {(() => {
                    const estadoReal = obtenerEstadoReal(incidencia);
                    return (
                      <div className="flex items-center">
                        {obtenerIconoEstado(estadoReal.estado)}
                        <span className="ml-2 text-sm text-gray-300">
                          {estadoReal.display}
                        </span>
                      </div>
                    );
                  })()}
                </td>
                <td className="px-4 py-3 whitespace-nowrap">
                  {(() => {
                    const turno = obtenerTurnoIncidencia(incidencia);
                    return (
                      <div className="flex items-center">
                        {turno.icono}
                        <span className={`ml-2 text-sm font-medium ${
                          turno.esMiTurno 
                            ? 'text-yellow-400' 
                            : turno.turno === 'Aprobada' 
                              ? 'text-green-400' 
                              : 'text-gray-400'
                        }`}>
                          {turno.turno}
                        </span>
                      </div>
                    );
                  })()}
                </td>
                <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-300">
                  {incidencia.impacto_monetario ? (
                    <span className="font-medium">
                      ${Number(incidencia.impacto_monetario).toLocaleString('es-CL')}
                    </span>
                  ) : (
                    '-'
                  )}
                </td>
                <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-300">
                  <div className="flex items-center">
                    <Calendar className="w-4 h-4 mr-1" />
                    {formatearFecha(incidencia.fecha_detectada)}
                  </div>
                </td>
                <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-300">
                  <div className="flex space-x-2">
                    <button
                      onClick={() => onIncidenciaSeleccionada && onIncidenciaSeleccionada(incidencia)}
                      className="text-blue-400 hover:text-blue-300 p-1 rounded-md hover:bg-blue-500/10 transition-colors"
                      title="Ver detalles"
                    >
                      <Eye className="w-4 h-4" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Paginación mejorada */}
      {totalPaginas > 1 && (
        <div className="flex justify-between items-center mt-4">
          <div className="text-sm text-gray-400">
            Mostrando {indiceInicio + 1}-{Math.min(indiceFin, incidenciasFiltradas.length)} de {incidenciasFiltradas.length} incidencias
          </div>
          <div className="flex space-x-2">
            <button
              onClick={() => setPaginaActual(Math.max(1, paginaActual - 1))}
              disabled={paginaActual === 1}
              className="px-3 py-1 bg-gray-700 text-white rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-600"
            >
              Anterior
            </button>
            <span className="px-3 py-1 text-gray-300 bg-gray-800 rounded">
              Página {paginaActual} de {totalPaginas}
            </span>
            <button
              onClick={() => setPaginaActual(Math.min(totalPaginas, paginaActual + 1))}
              disabled={paginaActual === totalPaginas}
              className="px-3 py-1 bg-gray-700 text-white rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-600"
            >
              Siguiente
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default IncidenciasTable;
