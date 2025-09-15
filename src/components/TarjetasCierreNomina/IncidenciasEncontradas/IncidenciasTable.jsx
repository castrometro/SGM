import React, { useState, useEffect } from "react";
import { AlertTriangle, CheckCircle, Clock, XCircle, Eye, User, Calendar, UserCheck, BarChart3 } from "lucide-react";
import { obtenerIncidenciasCierre, obtenerResumenNominaConsolidada, obtenerCierresCliente } from "../../../api/nomina";
import { formatearMonedaChilena } from "../../../utils/formatters";
import { useAuth } from "../../../hooks/useAuth";
import { obtenerEstadoReal, ESTADOS_INCIDENCIA } from "../../../utils/incidenciaUtils";

const IncidenciasTable = ({ cierreId, cierre = null, filtros = {}, onIncidenciaSeleccionada }) => {
  const [todasLasIncidencias, setTodasLasIncidencias] = useState([]);
  const [incidenciasFiltradas, setIncidenciasFiltradas] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState("");
  const [paginaActual, setPaginaActual] = useState(1);
  const [incidenciasPorPagina] = useState(10);
  const { user } = useAuth();
  const [resumenActual, setResumenActual] = useState(null);
  const [resumenAnterior, setResumenAnterior] = useState(null);
  const [periodoAnterior, setPeriodoAnterior] = useState(null);

  useEffect(() => {
    cargarIncidencias();
    // Cargar resúmenes de nómina consolidada (actual y previo) para mostrar todas las categorías
    cargarResumenes();
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

  const cargarResumenes = async () => {
    try {
      if (!cierreId) return;
      // Resumen período actual
  const actual = await obtenerResumenNominaConsolidada(cierreId);
  setResumenActual(actual?.resumen || null);
  setResumenAnterior(actual?.resumen_anterior || null);
  setPeriodoAnterior(actual?.periodo_anterior || null);
      // Fallback: si no vino "resumen_anterior", buscar el cierre anterior del cliente
      const clienteId = cierre?.cliente_id || cierre?.cliente?.id || cierre?.cliente;
      if (!actual?.resumen_anterior && clienteId && cierre?.periodo) {
        try {
          const cierres = await obtenerCierresCliente(clienteId);
          // Buscar el cierre anterior por periodo (< actual) y tomar el más reciente
          const periodoActual = String(cierre.periodo);
          const anteriores = (Array.isArray(cierres) ? cierres : []).filter(c => String(c.periodo) < periodoActual);
          if (anteriores.length) {
            // Ordenar descendente por periodo y tomar el primero
            anteriores.sort((a, b) => String(b.periodo).localeCompare(String(a.periodo)));
            const prev = anteriores[0];
            if (prev?.id) {
              const resumenPrev = await obtenerResumenNominaConsolidada(prev.id);
              setResumenAnterior(resumenPrev?.resumen || null);
              setPeriodoAnterior(resumenPrev?.cierre?.periodo || prev.periodo || null);
            }
          }
        } catch (e2) {
          console.warn('No se pudo cargar el resumen del cierre anterior por fallback:', e2?.message || e2);
        }
      }
    } catch (e) {
      // Silencioso para no romper la tabla si falla
      console.warn('No se pudo cargar el resumen de nómina consolidada:', e?.message || e);
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

    // Aplicar filtro por tipo de comparación (individual / suma_total / legacy)
    if (filtros.tipo_comparacion && filtros.tipo_comparacion !== '') {
      incidenciasFiltradas = incidenciasFiltradas.filter(
        incidencia => (incidencia.tipo_comparacion || 'legacy') === filtros.tipo_comparacion
      );
      console.log('Después filtro tipo_comparacion:', incidenciasFiltradas.length);
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

  const renderComparacionBadge = (incidencia) => {
    const tipo = incidencia.tipo_comparacion || 'legacy';
    const label = incidencia.tipo_comparacion_display || (
      tipo === 'individual' ? 'Individual' : tipo === 'suma_total' ? 'Suma Total' : 'Legacy'
    );
    const cls =
      tipo === 'individual'
        ? 'bg-blue-900/50 text-blue-300 ring-1 ring-blue-700/40'
        : tipo === 'suma_total'
          ? 'bg-indigo-900/50 text-indigo-300 ring-1 ring-indigo-700/40'
          : 'bg-gray-800 text-gray-300 ring-1 ring-gray-700/40';
    return (
      <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ml-2 ${cls}`}>
        {label}
      </span>
    );
  };

  const renderDetallesComparacion = (incidencia) => {
    const da = incidencia.datos_adicionales || {};
    const tipo = incidencia.tipo_comparacion;
    if (tipo === 'individual') {
      const montoActual = da.monto_actual ?? null;
      const montoAnterior = da.monto_anterior ?? null;
      const variacion = da.variacion_porcentual ?? null;
      if (montoActual != null || montoAnterior != null || variacion != null) {
        return (
          <div className="mt-1 text-xs text-gray-400 space-x-2">
            {montoAnterior != null && (
              <span>Ant: <span className="text-gray-300 font-medium">{formatearMonedaChilena(montoAnterior)}</span></span>
            )}
            {montoActual != null && (
              <span>Act: <span className="text-gray-300 font-medium">{formatearMonedaChilena(montoActual)}</span></span>
            )}
            {variacion != null && (
              <span>Var: <span className={`font-medium ${Number(variacion) >= 0 ? 'text-green-400' : 'text-red-400'}`}>{Number(variacion).toFixed(2)}%</span></span>
            )}
          </div>
        );
      }
    } else if (tipo === 'suma_total') {
      const sumaActual = da.suma_actual ?? null;
      const sumaAnterior = da.suma_anterior ?? null;
      const variacion = da.variacion_porcentual ?? null;
      if (sumaActual != null || sumaAnterior != null || variacion != null) {
        return (
          <div className="mt-1 text-xs text-gray-400 space-x-2">
            {sumaAnterior != null && (
              <span>Σ Ant: <span className="text-gray-300 font-medium">{formatearMonedaChilena(sumaAnterior)}</span></span>
            )}
            {sumaActual != null && (
              <span>Σ Act: <span className="text-gray-300 font-medium">{formatearMonedaChilena(sumaActual)}</span></span>
            )}
            {variacion != null && (
              <span>Var: <span className={`font-medium ${Number(variacion) >= 0 ? 'text-green-400' : 'text-red-400'}`}>{Number(variacion).toFixed(2)}%</span></span>
            )}
          </div>
        );
      }
    }
    return null;
  };

  // Función para determinar el turno según la nueva arquitectura
  const obtenerTurnoIncidencia = (incidencia) => {
    const esSupervidor = user?.is_staff || user?.is_superuser;
    const resoluciones = incidencia.resoluciones || [];

    // INICIANDO: Sin mensajes → Turno del Analista
    if (resoluciones.length === 0) {
      return {
        esMiTurno: !esSupervidor,
        turno: 'Analista',
        icono: <User className="w-4 h-4 text-blue-500" />
      };
    }

    // Ordenar por fecha y obtener la última resolución
    const ultimaResolucion = resoluciones
      .slice()
      .sort((a, b) => new Date(b.fecha_resolucion) - new Date(a.fecha_resolucion))[0];

    // APROBADA: Último mensaje es aprobación → Conversación terminada
    if (ultimaResolucion?.tipo_resolucion === 'aprobacion') {
      return {
        esMiTurno: false,
        turno: 'Aprobada',
        icono: <CheckCircle className="w-4 h-4 text-green-500" />
      };
    }

    // Determinar turno basado en el último mensaje
    const esDelSupervisor = ['consulta', 'rechazo'].includes(ultimaResolucion?.tipo_resolucion);

    if (esDelSupervisor) {
      // TURNO_ANALISTA: Último mensaje fue de supervisor → Analista debe responder
      return {
        esMiTurno: !esSupervidor,
        turno: 'Analista',
        icono: <User className="w-4 h-4 text-blue-500" />
      };
    }

    // TURNO_SUPERVISOR: Último mensaje fue de analista → Supervisor debe decidir
    return {
      esMiTurno: esSupervidor,
      turno: 'Supervisor',
      icono: <UserCheck className="w-4 h-4 text-purple-500" />
    };
  };

  const obtenerClasePrioridad = (prioridad) => {
    switch (prioridad) {
      case 'critica':
        return 'bg-rose-900/50 text-rose-300 ring-1 ring-rose-700/40';
      case 'alta':
        return 'bg-orange-900/50 text-orange-300 ring-1 ring-orange-700/40';
      case 'media':
        return 'bg-amber-900/50 text-amber-300 ring-1 ring-amber-700/40';
      case 'baja':
        return 'bg-emerald-900/50 text-emerald-300 ring-1 ring-emerald-700/40';
      default:
        return 'bg-gray-800 text-gray-300 ring-1 ring-gray-700/40';
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
      <div className="bg-gray-900/60 rounded-xl p-6 border border-gray-800 text-center">
        <AlertTriangle className="w-12 h-12 mx-auto mb-3 text-gray-400" />
        <p className="text-gray-300">No se encontraron incidencias</p>
        <p className="text-sm text-gray-400">Las incidencias aparecerán aquí una vez generadas</p>
      </div>
    );
  }

  if (!incidenciasFiltradas.length) {
    return (
      <div className="bg-gray-900/60 rounded-xl p-6 border border-gray-800 text-center text-gray-400">
        <AlertTriangle className="w-12 h-12 mx-auto mb-3 opacity-50" />
  <p className="text-gray-300">No se encontraron incidencias con los filtros aplicados</p>
  <p className="text-sm text-gray-400">Intenta ajustar los filtros para ver más resultados</p>
      </div>
    );
  }

  // Vista agrupada por tipo de comparación cuando no se filtra específicamente
  const usarVistaAgrupada = !filtros.tipo_comparacion || filtros.tipo_comparacion === '';
  const PERMITIDAS_INDIV = ['haber_imponible', 'haber_no_imponible', 'otro_descuento'];
  const incidenciasIndividuales = incidenciasFiltradas.filter(
    i => i.tipo_comparacion === 'individual'
  );
  // Solo individuales de categorías permitidas (item por empleado)
  const incidenciasIndividualesPermitidas = incidenciasIndividuales.filter((i) => {
    const tc = i?.datos_adicionales?.tipo_concepto || i?.tipo_concepto;
    return PERMITIDAS_INDIV.includes(tc);
  });
  // Solo categorías en suma_total (variaciones agregadas por categoría)
  const incidenciasSumaTotalCategorias = incidenciasFiltradas.filter(
    i => i.tipo_comparacion === 'suma_total' && (i?.datos_adicionales?.categoria)
  );
  const incidenciasLegacy = incidenciasFiltradas.filter(i => !i.tipo_comparacion || i.tipo_comparacion === 'legacy');

  const categoriasOrden = [
    { key: 'total_haberes_imponibles', label: 'Haberes Imponibles', tipo: 'haber_imponible' },
    { key: 'total_haberes_no_imponibles', label: 'Haberes No Imponibles', tipo: 'haber_no_imponible' },
    { key: 'total_dctos_legales', label: 'Descuentos Legales', tipo: 'descuento_legal' },
    { key: 'total_otros_dctos', label: 'Otros Descuentos', tipo: 'otro_descuento' },
    { key: 'total_impuestos', label: 'Impuestos', tipo: 'impuesto' },
    { key: 'total_aportes_patronales', label: 'Aportes Patronales', tipo: 'aporte_patronal' },
    { key: 'liquido_total', label: 'Total Líquido', tipo: 'total_liquido' },
  ];

  const mapIncidenciaPorCategoria = new Map();
  incidenciasSumaTotalCategorias.forEach((i) => {
    const cat = i?.datos_adicionales?.categoria;
    if (cat) mapIncidenciaPorCategoria.set(cat, i);
  });

  const renderResumenCategorias = () => {
    if (!resumenActual) return null;
    return (
      <div className="bg-gray-900/60 rounded-xl p-4 border border-gray-800 transition-transform duration-200 hover:scale-[1.005] hover:border-gray-700">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <BarChart3 size={16} className="text-gray-400" />
            <h4 className="text-sm font-medium text-gray-300">Resumen por categoría (vs. mes anterior)</h4>
          </div>
          <span className="text-xs text-gray-500">Muestra montos aunque no haya incidencia{periodoAnterior ? ` · vs ${periodoAnterior}` : ''}</span>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full bg-gray-800 rounded-lg">
            <thead className="bg-gray-800/80 border-b border-gray-700">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Categoría</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Σ Actual</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Σ Anterior</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Variación</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Incidencia</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-700">
              {categoriasOrden.map(({ key, label, tipo }) => {
                const sumaActual = resumenActual?.[key] ?? null;
                const sumaAnteriorResumen = resumenAnterior?.[key] ?? null;
                const inc = mapIncidenciaPorCategoria.get(tipo);
                // Preferir resumen anterior, y usar incidencia si no hay
                const sumaAnterior = (sumaAnteriorResumen != null) ? sumaAnteriorResumen : (inc?.datos_adicionales?.suma_anterior ?? null);
                let variacion = null;
                if (sumaAnterior != null && sumaActual != null) {
                  const denom = Math.abs(Number(sumaAnterior)) || 0;
                  variacion = denom ? ((Number(sumaActual) - Number(sumaAnterior)) / denom) * 100 : null;
                } else if (inc?.datos_adicionales?.variacion_porcentual != null) {
                  variacion = inc.datos_adicionales.variacion_porcentual;
                }
                const varPct = variacion != null ? Number(variacion) : null;
                return (
                  <tr key={key} className="hover:bg-gray-700/50">
                    <td className="px-4 py-3 text-sm text-white">
                      <div className="font-medium flex items-center gap-2">
                        <span>{label}</span>
                        {inc && (
                          <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-teal-900/40 text-teal-300 ring-1 ring-teal-700/40">Incidencia</span>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-300">{sumaActual != null ? formatearMonedaChilena(sumaActual) : '-'}</td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-300">{sumaAnterior != null ? formatearMonedaChilena(sumaAnterior) : '-'}</td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm">
                      {varPct != null ? (
                        <span className={`font-medium ${varPct >= 0 ? 'text-green-400' : 'text-red-400'}`}>{varPct >= 0 ? '+' : ''}{varPct.toFixed(2)}%</span>
                      ) : (
                        <span className="text-gray-400">—</span>
                      )}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-300">
                      {inc ? (
                        <button
                          onClick={() => onIncidenciaSeleccionada && onIncidenciaSeleccionada(inc)}
                          className="text-blue-400 hover:text-blue-300 p-1 rounded-md hover:bg-blue-500/10 transition-colors"
                          title="Ver incidencia"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                      ) : (
                        <span className="text-gray-500">Sin incidencia</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    );
  };

  const renderTablaSumaTotal = (lista) => (
    <div className="bg-gray-900/60 rounded-xl p-4 border border-gray-800 transition-transform duration-200 hover:scale-[1.005] hover:border-gray-700">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <BarChart3 size={16} className="text-gray-400" />
          <h4 className="text-sm font-medium text-gray-300">Variaciones agregadas (Suma Total)</h4>
        </div>
        <span className="text-xs text-gray-500">{lista.length} incidencias</span>
      </div>
      <div className="overflow-x-auto">
      <table className="min-w-full bg-gray-800 rounded-lg">
    <thead className="bg-gray-800/80 border-b border-gray-700">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Concepto</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Variación</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Σ Anterior</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Σ Actual</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Prioridad</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Estado</th>
      <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Turno</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Fecha</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Acciones</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-700">
          {lista.map((incidencia) => {
            const da = incidencia.datos_adicionales || {};
            const varPct = Number(da.variacion_porcentual ?? 0);
            return (
              <tr key={incidencia.id} className="hover:bg-gray-700/50">
                <td className="px-4 py-3 text-sm text-gray-300">
                  <div className="font-medium text-white flex items-center gap-2">
                    <span>{da.concepto || incidencia.concepto_afectado || '-'}</span>
                    {da.categoria && (
                      <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-teal-900/40 text-teal-300 ring-1 ring-teal-700/40">Categoría</span>
                    )}
                  </div>
                  {!da.categoria && da.tipo_concepto && (
                    <div className="text-xs text-gray-500 mt-1">{da.tipo_concepto}</div>
                  )}
                </td>
                <td className="px-4 py-3 whitespace-nowrap text-sm">
                  <span className={`font-medium ${varPct >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                    {varPct >= 0 ? '+' : ''}{varPct.toFixed(2)}%
                  </span>
                </td>
                <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-300">{da.suma_anterior != null ? formatearMonedaChilena(da.suma_anterior) : '-'}</td>
                <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-300">{da.suma_actual != null ? formatearMonedaChilena(da.suma_actual) : '-'}</td>
                <td className="px-4 py-3 whitespace-nowrap">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${obtenerClasePrioridad(incidencia.prioridad)}`}>
                    {incidencia.prioridad}
                  </span>
                </td>
                <td className="px-4 py-3 whitespace-nowrap">
                  {(() => {
                    const estadoReal = obtenerEstadoReal(incidencia);
                    return (
                      <div className="flex items-center">
                        {obtenerIconoEstado(estadoReal.estado)}
                        <span className="ml-2 text-sm text-gray-300">{estadoReal.display}</span>
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
                <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-300">{formatearFecha(incidencia.fecha_detectada)}</td>
                <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-300">
                  <div className="flex space-x-2">
                    {(() => {
                      const turno = obtenerTurnoIncidencia(incidencia);
                      return turno.esMiTurno && turno.turno !== 'Aprobada' ? (
                        <button
                          onClick={() => onIncidenciaSeleccionada && onIncidenciaSeleccionada(incidencia)}
                          className="text-yellow-300 hover:text-yellow-200 p-1 rounded-md hover:bg-yellow-500/10 transition-colors"
                          title="Atender (mi turno)"
                        >
                          Atender
                        </button>
                      ) : null;
                    })()}
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
            );
          })}
        </tbody>
  </table>
  </div>
    </div>
  );

  const renderTablaIndividual = (lista, titulo = 'Variaciones por empleado (Individual)') => (
    <div className="bg-gray-900/60 rounded-xl p-4 border border-gray-800 transition-transform duration-200 hover:scale-[1.005] hover:border-gray-700">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <BarChart3 size={16} className="text-gray-400" />
          <h4 className="text-sm font-medium text-gray-300">{titulo}</h4>
        </div>
        <span className="text-xs text-gray-500">{lista.length} incidencias</span>
      </div>
      <div className="overflow-x-auto">
      <table className="min-w-full bg-gray-800 rounded-lg">
    <thead className="bg-gray-800/80 border-b border-gray-700">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Empleado</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Concepto</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Variación</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Ant</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Act</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Prioridad</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Estado</th>
      <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Turno</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Fecha</th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">Acciones</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-700">
          {lista.map((incidencia) => {
            const da = incidencia.datos_adicionales || {};
            const varPct = Number(da.variacion_porcentual ?? 0);
            return (
              <tr key={incidencia.id} className="hover:bg-gray-700/50">
                <td className="px-4 py-3 whitespace-nowrap text-sm text-white">
                  <div>
                    <div className="font-medium">{incidencia.rut_empleado}</div>
                    {(incidencia.empleado_nombre || incidencia.empleado_libro?.nombre) && (
                      <div className="text-gray-400 text-xs">{incidencia.empleado_nombre || incidencia.empleado_libro?.nombre}</div>
                    )}
                  </div>
                </td>
                <td className="px-4 py-3 text-sm text-gray-300">
                  <div className="font-medium text-white">{da.concepto || incidencia.concepto_afectado || '-'}</div>
                  {da.tipo_concepto && (
                    <div className="text-xs text-gray-500 mt-1">{da.tipo_concepto}</div>
                  )}
                </td>
                <td className="px-4 py-3 whitespace-nowrap text-sm">
                  <span className={`font-medium ${varPct >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                    {varPct >= 0 ? '+' : ''}{varPct.toFixed(2)}%
                  </span>
                </td>
                <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-300">{da.monto_anterior != null ? formatearMonedaChilena(da.monto_anterior) : '-'}</td>
                <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-300">{da.monto_actual != null ? formatearMonedaChilena(da.monto_actual) : '-'}</td>
                <td className="px-4 py-3 whitespace-nowrap">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${obtenerClasePrioridad(incidencia.prioridad)}`}>
                    {incidencia.prioridad}
                  </span>
                </td>
                <td className="px-4 py-3 whitespace-nowrap">
                  {(() => {
                    const estadoReal = obtenerEstadoReal(incidencia);
                    return (
                      <div className="flex items-center">
                        {obtenerIconoEstado(estadoReal.estado)}
                        <span className="ml-2 text-sm text-gray-300">{estadoReal.display}</span>
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
                <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-300">{formatearFecha(incidencia.fecha_detectada)}</td>
                <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-300">
                  <div className="flex space-x-2">
                    {(() => {
                      const turno = obtenerTurnoIncidencia(incidencia);
                      return turno.esMiTurno && turno.turno !== 'Aprobada' ? (
                        <button
                          onClick={() => onIncidenciaSeleccionada && onIncidenciaSeleccionada(incidencia)}
                          className="text-yellow-300 hover:text-yellow-200 p-1 rounded-md hover:bg-yellow-500/10 transition-colors"
                          title="Atender (mi turno)"
                        >
                          Atender
                        </button>
                      ) : null;
                    })()}
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
            );
          })}
        </tbody>
  </table>
  </div>
    </div>
  );

  if (usarVistaAgrupada) {
    return (
      <div className="space-y-6">
  {renderResumenCategorias()}
  {incidenciasSumaTotalCategorias.length > 0 && renderTablaSumaTotal(incidenciasSumaTotalCategorias)}
  {incidenciasIndividualesPermitidas.length > 0 && renderTablaIndividual(incidenciasIndividualesPermitidas)}
  {incidenciasLegacy.length > 0 && renderTablaIndividual(incidenciasLegacy, 'Legacy')}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Tabla de incidencias */}
      <div className="bg-gray-900/60 rounded-xl p-4 border border-gray-800">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <BarChart3 size={16} className="text-gray-400" />
            <h4 className="text-sm font-medium text-gray-300">Incidencias</h4>
          </div>
          <span className="text-xs text-gray-500">{incidenciasFiltradas.length} resultados</span>
        </div>
  <div className="overflow-x-auto">
  <table className="w-full min-w-[1300px] md:min-w-[1400px] lg:min-w-[1600px] bg-gray-800 rounded-lg">
          <thead className="bg-gray-800/80 border-b border-gray-700">
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
                    {(incidencia.empleado_nombre || incidencia.empleado_libro?.nombre) && (
                      <div className="text-gray-400 text-xs">
                        {incidencia.empleado_nombre || incidencia.empleado_libro?.nombre}
                      </div>
                    )}
                  </div>
                </td>
                <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-300">
                  {incidencia.get_tipo_incidencia_display || incidencia.tipo_incidencia}
                  {renderComparacionBadge(incidencia)}
                </td>
                <td className="px-4 py-3 text-sm text-gray-300">
                  <div title={incidencia.descripcion}>
                    {truncarTexto(incidencia.descripcion, 60)}
                  </div>
          {(incidencia.concepto_afectado || incidencia.datos_adicionales?.concepto) && (
                    <div className="text-xs text-gray-500 mt-1">
            {incidencia.concepto_afectado || incidencia.datos_adicionales?.concepto}
                    </div>
                  )}
                  {renderDetallesComparacion(incidencia)}
                </td>
                <td className="px-4 py-3 whitespace-nowrap">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${obtenerClasePrioridad(incidencia.prioridad)}`}>
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
                      {formatearMonedaChilena(incidencia.impacto_monetario)}
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
      </div>

      {/* Paginación mejorada */}
  {totalPaginas > 1 && !usarVistaAgrupada && (
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
