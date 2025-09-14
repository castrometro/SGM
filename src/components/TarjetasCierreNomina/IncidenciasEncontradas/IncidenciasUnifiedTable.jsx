import React, { useMemo, useState } from "react";
import { Eye, BarChart3, LayoutList, CornerDownRight, ChevronsUpDown, ChevronUp, ChevronDown, TrendingUp, TrendingDown } from "lucide-react";
import { formatearMonedaChilena } from "../../../utils/formatters";
import { useAuth } from "../../../hooks/useAuth";
import { obtenerEstadoReal } from "../../../utils/incidenciaUtils";

// Tabla unificada que muestra SOLO incidencias de los tipos requeridos:
// - individual (por empleado por ítem)
// - suma_total (agregado por ítem del mes vs mes anterior)
// Excluye: legacy y agregados por categoría (cuando vienen como 'categoria' en datos_adicionales)
export default function IncidenciasUnifiedTable({ incidencias = [], onIncidenciaSeleccionada }) {
  const { user } = useAuth();
  const [sortKey, setSortKey] = useState("variacion_porcentual");
  const [sortDir, setSortDir] = useState("desc");
  const [viewChip, setViewChip] = useState("todos"); // todos | topVar | topImpact
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [dense, setDense] = useState(true);
  const [expanded, setExpanded] = useState(() => new Set()); // grupos expandidos

  // Construcción de grupos: (tipo_concepto, concepto) => {resumen, indiv[]}
  const groups = useMemo(() => {
    const PERMITIDAS_INDIV = ["haber_imponible", "haber_no_imponible", "otro_descuento"]; // seguridad extra
    const ESPECIALES = new Set(["finiquito_no_aplicado", "ingreso_no_informado"]);
    const permitidaSuma = (i) => i.tipo_comparacion === 'suma_total' && !i?.datos_adicionales?.categoria;
    const permitidaIndiv = (i) => {
      if (i.tipo_comparacion !== 'individual') return false;
      // Permitir siempre incidencias especiales, aunque no tengan tipo_concepto
      if (ESPECIALES.has(i.tipo_incidencia)) return true;
      const tc = i?.datos_adicionales?.tipo_concepto || i?.tipo_concepto;
      return PERMITIDAS_INDIV.includes(tc);
    };

    let filtradas = (Array.isArray(incidencias) ? incidencias : [])
      .filter(i => permitidaSuma(i) || permitidaIndiv(i));

    // Vistas rápidas
    if (viewChip === 'topVar') {
      filtradas = [...filtradas]
        // Excluir ingresos informativos del Top N
        .filter(i => i.tipo_incidencia !== 'ingreso_empleado')
        .sort((a, b) => Math.abs((b.datos_adicionales?.variacion_porcentual ?? 0)) - Math.abs((a.datos_adicionales?.variacion_porcentual ?? 0)))
        .slice(0, 50);
    } else if (viewChip === 'topImpact') {
      filtradas = [...filtradas]
        // Excluir ingresos informativos del Top N
        .filter(i => i.tipo_incidencia !== 'ingreso_empleado')
        .sort((a, b) => Math.abs(Number(b.impacto_monetario ?? 0)) - Math.abs(Number(a.impacto_monetario ?? 0)))
        .slice(0, 50);
    }
    // Agrupar por concepto/tipo_concepto
    const byKey = new Map();
    for (const i of filtradas) {
      const da = i.datos_adicionales || {};
      const isEspecial = ESPECIALES.has(i.tipo_incidencia);
      const concepto = isEspecial ? 'Estado del empleado' : (da.concepto || i.concepto_afectado || '-');
      const tipo_concepto = isEspecial ? 'meta' : (da.tipo_concepto || i.tipo_concepto || '-');
      const key = `${tipo_concepto}||${concepto}`;
      if (!byKey.has(key)) byKey.set(key, { key, concepto, tipo_concepto, resumen: null, indiv: [] });
      const g = byKey.get(key);
      if (i.tipo_comparacion === 'suma_total') {
        const anterior = da.suma_anterior != null ? Number(da.suma_anterior) : null;
        const actual = da.suma_actual != null ? Number(da.suma_actual) : null;
        const variacion = da.variacion_porcentual != null ? Number(da.variacion_porcentual) : null;
        g.resumen = {
          anterior, actual, variacion_porcentual: variacion,
          prioridad: i.prioridad || 'baja',
          impacto_monetario: Math.abs(Number(i.impacto_monetario ?? 0)),
          fecha: i.fecha_detectada,
          raw: i,
        };
      } else if (i.tipo_comparacion === 'individual') {
        const especialBadge = i.tipo_incidencia === 'ingreso_empleado' ? 'ingreso_empleado' : (isEspecial ? i.tipo_incidencia : null);
        g.indiv.push({
          id: i.id,
          empleado_rut: i.rut_empleado || null,
          empleado_nombre: i.empleado_nombre || i.empleado_libro?.nombre || null,
          anterior: da.monto_anterior != null ? Number(da.monto_anterior) : null,
          actual: da.monto_actual != null ? Number(da.monto_actual) : null,
          variacion_porcentual: da.variacion_porcentual != null ? Number(da.variacion_porcentual) : null,
          prioridad: i.prioridad || 'baja',
          estadoReal: obtenerEstadoReal(i),
          fecha: i.fecha_detectada,
          raw: i,
          especial: especialBadge,
        });
      }
    }

    // Completar resumen si no vino suma_total
    const groupsArr = Array.from(byKey.values()).map(g => {
      if (!g.resumen) {
        const sumAnt = g.indiv.reduce((acc, r) => acc + (r.anterior ?? 0), 0);
        const sumAct = g.indiv.reduce((acc, r) => acc + (r.actual ?? 0), 0);
        const variacion = sumAnt === 0 ? (sumAct > 0 ? 100 : 0) : ((sumAct - sumAnt) / sumAnt) * 100;
        const absVar = Math.abs(variacion || 0);
        const prioridad = absVar >= 75 ? 'critica' : absVar >= 50 ? 'alta' : absVar >= 30 ? 'media' : 'baja';
        g.resumen = {
          anterior: sumAnt,
          actual: sumAct,
          variacion_porcentual: variacion,
          prioridad,
          impacto_monetario: Math.abs(sumAct - sumAnt),
          fecha: g.indiv[0]?.fecha || null,
          raw: null,
        };
      }
      return g;
    });

    // Ordenamiento por clave seleccionada (sobre resumen)
    const val = (g) => {
      switch (sortKey) {
        case 'variacion_porcentual': return g.resumen.variacion_porcentual ?? -Infinity;
        case 'anterior': return g.resumen.anterior ?? -Infinity;
        case 'actual': return g.resumen.actual ?? -Infinity;
        case 'concepto': return g.concepto || '';
        case 'fecha': return g.resumen.fecha ? new Date(g.resumen.fecha).getTime() : 0;
        default: return 0;
      }
    };
    groupsArr.sort((a, b) => {
      const va = val(a), vb = val(b);
      if (va === vb) return 0;
      const cmp = va > vb ? 1 : -1;
      return sortDir === 'asc' ? cmp : -cmp;
    });

    return groupsArr;
  }, [incidencias, sortKey, sortDir, viewChip]);

  const onSort = (key) => {
    if (sortKey === key) {
      setSortDir(sortDir === 'asc' ? 'desc' : 'asc');
    } else {
      setSortKey(key);
      setSortDir('desc');
    }
  };

  const labelTipoConcepto = (tc) => {
    if (!tc) return '-';
    const map = {
      haber_imponible: 'Haberes Imponibles',
      haber_no_imponible: 'Haberes No Imponibles',
      otro_descuento: 'Otros Descuentos',
      meta: '—',
    };
    if (map[tc]) return map[tc];
    // Fallback: snake_case -> Title Case
    try {
      return tc
        .toString()
        .replace(/_/g, ' ')
        .replace(/\b\w/g, (c) => c.toUpperCase());
    } catch {
      return tc;
    }
  };

  const badgeTipo = (tipo) => {
    const cls = tipo === 'individual'
      ? 'bg-blue-900/50 text-blue-300 ring-1 ring-blue-700/40'
      : 'bg-indigo-900/50 text-indigo-300 ring-1 ring-indigo-700/40';
    const label = tipo === 'individual' ? 'Individual' : 'Suma Total';
    return <span className={`px-2 py-0.5 rounded text-xs ${cls}`}>{label}</span>;
  };

  const badgePrioridad = (p) => {
    const cls = p === 'critica'
      ? 'bg-rose-900/50 text-rose-300 ring-1 ring-rose-700/40'
      : p === 'alta'
        ? 'bg-orange-900/50 text-orange-300 ring-1 ring-orange-700/40'
        : p === 'media'
          ? 'bg-amber-900/50 text-amber-300 ring-1 ring-amber-700/40'
          : 'bg-emerald-900/50 text-emerald-300 ring-1 ring-emerald-700/40';
    return <span className={`px-2 py-0.5 rounded text-xs ${cls}`}>{p}</span>;
  };

  const SortHeader = ({ label, sortKeyLocal }) => {
    const isActive = sortKey === sortKeyLocal;
    const icon = !isActive ? (
      <ChevronsUpDown className="w-3.5 h-3.5 text-gray-500" />
    ) : sortDir === 'asc' ? (
      <ChevronUp className="w-3.5 h-3.5 text-blue-400" />
    ) : (
      <ChevronDown className="w-3.5 h-3.5 text-blue-400" />
    );
    return (
      <div className="flex items-center gap-1 select-none">
        <span>{label}</span>
        {icon}
      </div>
    );
  };

  const badgeEspecial = (tipo) => {
    if (tipo === 'finiquito_no_aplicado') {
      return <span className="ml-2 px-2 py-0.5 rounded text-xs bg-rose-900/50 text-rose-300 ring-1 ring-rose-700/40">Finiquito no aplicado</span>;
    }
    if (tipo === 'ingreso_no_informado') {
      return <span className="ml-2 px-2 py-0.5 rounded text-xs bg-amber-900/50 text-amber-300 ring-1 ring-amber-700/40">Ingreso no informado</span>;
    }
    if (tipo === 'ingreso_empleado') {
      return <span className="ml-2 px-2 py-0.5 rounded text-xs bg-emerald-900/50 text-emerald-300 ring-1 ring-emerald-700/40">Ingreso</span>;
    }
    return null;
  };

  // Paginación por grupos
  const totalRows = groups.length;
  const totalPages = Math.max(1, Math.ceil(totalRows / pageSize));
  const currentPage = Math.min(page, totalPages);
  const startIdx = (currentPage - 1) * pageSize;
  const pageGroups = groups.slice(startIdx, startIdx + pageSize);

  const tdPad = dense ? 'px-3 py-2' : 'px-4 py-3';
  const thPad = dense ? 'px-3 py-2' : 'px-4 py-3';

  return (
    <div className="bg-gray-900/60 rounded-xl p-4 border border-gray-800">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <BarChart3 size={16} className="text-gray-400" />
          <h4 className="text-sm font-medium text-gray-300">Incidencias (Individual + Suma Total)</h4>
        </div>
        <div className="flex items-center gap-2">
          {/* Chips de vista */}
          <div className="flex items-center gap-1 bg-gray-800/70 rounded-lg p-1 border border-gray-700">
            {[
              { key: 'todos', label: 'Todos' },
              { key: 'topVar', label: 'Top 50 Var%' },
              { key: 'topImpact', label: 'Top 50 Impacto' },
            ].map(ch => (
              <button
                key={ch.key}
                onClick={() => { setViewChip(ch.key); setPage(1); }}
                className={`text-xs px-2 py-1 rounded-md transition-colors ${viewChip === ch.key ? 'bg-blue-600 text-white' : 'text-gray-300 hover:bg-gray-700'}`}
              >{ch.label}</button>
            ))}
          </div>
          {/* Densidad */}
          <button
            onClick={() => setDense(!dense)}
            className="flex items-center gap-1 text-xs px-2 py-1 rounded-md border border-gray-700 text-gray-300 hover:bg-gray-800"
            title={dense ? 'Vista amplia' : 'Vista compacta'}
          >
            <LayoutList className="w-3.5 h-3.5" /> {dense ? 'Compacto' : 'Amplio'}
          </button>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full bg-gray-800 rounded-lg">
          <thead className="bg-gray-800/90 backdrop-blur sticky top-0 z-10 border-b border-gray-700">
            <tr>
              <th onClick={() => onSort('concepto')} className={`${thPad} text-left text-xs font-medium text-gray-300 uppercase tracking-wider cursor-pointer`}>
                <SortHeader label="Concepto / Ítem" sortKeyLocal="concepto" />
              </th>
              <th className={`${thPad} text-left text-xs font-medium text-gray-300 uppercase tracking-wider`}>Empleado / Detalle</th>
              <th onClick={() => onSort('variacion_porcentual')} className={`${thPad} text-right text-xs font-medium text-gray-300 uppercase tracking-wider cursor-pointer`}>
                <SortHeader label="Variación %" sortKeyLocal="variacion_porcentual" />
              </th>
              <th onClick={() => onSort('anterior')} className={`${thPad} text-right text-xs font-medium text-gray-300 uppercase tracking-wider cursor-pointer`}>
                <SortHeader label="Anterior" sortKeyLocal="anterior" />
              </th>
              <th onClick={() => onSort('actual')} className={`${thPad} text-right text-xs font-medium text-gray-300 uppercase tracking-wider cursor-pointer`}>
                <SortHeader label="Actual" sortKeyLocal="actual" />
              </th>
              <th className={`${thPad} text-left text-xs font-medium text-gray-300 uppercase tracking-wider`}>Prioridad</th>
              <th className={`${thPad} text-left text-xs font-medium text-gray-300 uppercase tracking-wider`}>Estado</th>
              <th className={`${thPad} text-left text-xs font-medium text-gray-300 uppercase tracking-wider`}>Turno</th>
              <th className={`${thPad} text-left text-xs font-medium text-gray-300 uppercase tracking-wider`}>Acciones</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-700">
            {pageGroups.map((g) => {
              const isOpen = expanded.has(g.key);
              const isExpandable = g.indiv.length > 0;
              const varCls = (g.resumen.variacion_porcentual ?? 0) >= 0 ? 'text-green-400' : 'text-red-400';
              return (
                <React.Fragment key={g.key}>
                  <tr className={`hover:bg-gray-700/50 ${isOpen ? 'bg-gray-800/30' : ''}`}>
                    <td className={`${tdPad} text-sm text-gray-300`}>
                      <div className="flex items-center gap-2">
                        {isExpandable && (
                          <button
                            onClick={() => {
                              const ns = new Set(expanded);
                              if (ns.has(g.key)) ns.delete(g.key); else ns.add(g.key);
                              setExpanded(ns);
                            }}
                            className="text-xs px-2 py-0.5 rounded-md border border-gray-700 text-gray-300 hover:bg-gray-800"
                            title={isOpen ? 'Contraer' : 'Expandir'}
                          >{isOpen ? '−' : '+'}</button>
                        )}
                        <div>
                          <div className="font-medium text-white">{g.concepto}</div>
                          <div className="text-xs text-gray-500 mt-1">{labelTipoConcepto(g.tipo_concepto)}</div>
                        </div>
                      </div>
                    </td>
                    <td className={`${tdPad} whitespace-nowrap text-sm text-gray-300`}>
                      {g.indiv.length > 0 ? (<span className="text-gray-300">{g.indiv.length} individuales</span>) : (<span className="text-gray-500">—</span>)}
                    </td>
                    <td className={`${tdPad} whitespace-nowrap text-sm font-medium ${varCls} text-right`}>
                      {g.resumen.variacion_porcentual != null ? (
                        <span className="inline-flex items-center gap-1 justify-end w-full">
                          {g.resumen.variacion_porcentual >= 0 ? <TrendingUp className="w-3.5 h-3.5" /> : <TrendingDown className="w-3.5 h-3.5" />}
                          <span>{`${g.resumen.variacion_porcentual >= 0 ? '+' : ''}${g.resumen.variacion_porcentual.toFixed(2)}%`}</span>
                        </span>
                      ) : '—'}
                    </td>
                    <td className={`${tdPad} whitespace-nowrap text-sm text-gray-300 text-right`}>
                      {g.resumen.anterior != null ? formatearMonedaChilena(g.resumen.anterior) : '—'}
                    </td>
                    <td className={`${tdPad} whitespace-nowrap text-sm text-gray-300 text-right`}>
                      {g.resumen.actual != null ? formatearMonedaChilena(g.resumen.actual) : '—'}
                    </td>
                    <td className={`${tdPad} whitespace-nowrap`}>{badgePrioridad(g.resumen.prioridad)}</td>
                    <td className={`${tdPad} whitespace-nowrap`}>
                      {isExpandable ? '—' : (
                        (() => {
                          const estado = g.resumen?.raw ? obtenerEstadoReal(g.resumen.raw) : null;
                          return estado ? <span className="text-sm text-gray-300">{estado.display}</span> : '—';
                        })()
                      )}
                    </td>
                    <td className={`${tdPad} whitespace-nowrap`}>
                      {isExpandable ? '—' : (
                        (() => {
                          const esSupervisor = user?.is_staff || user?.is_superuser;
                          const resoluciones = g.resumen?.raw?.resoluciones || [];
                          if (!resoluciones.length) {
                            return <span className={`text-sm font-medium ${!esSupervisor ? 'text-yellow-400' : 'text-gray-400'}`}>Analista</span>;
                          }
                          const ultima = [...resoluciones].sort((a,b) => new Date(b.fecha_resolucion) - new Date(a.fecha_resolucion))[0];
                          if (ultima.tipo_resolucion === 'aprobacion') {
                            return <span className="text-sm font-medium text-green-400">Aprobada</span>;
                          }
                          const esDelSupervisor = ['consulta', 'rechazo'].includes(ultima.tipo_resolucion);
                          const turno = esDelSupervisor ? 'Analista' : 'Supervisor';
                          const color = turno === 'Analista' ? 'text-yellow-400' : 'text-gray-400';
                          return <span className={`text-sm font-medium ${color}`}>{turno}</span>;
                        })()
                      )}
                    </td>
                    <td className={`${tdPad} whitespace-nowrap text-sm text-gray-300`}>
                      {g.resumen?.raw && (
                        <button
                          onClick={() => onIncidenciaSeleccionada && onIncidenciaSeleccionada(g.resumen.raw)}
                          className="text-blue-400 hover:text-blue-300 p-1 rounded-md hover:bg-blue-500/10 transition-colors"
                          title="Ver detalle agregado"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                      )}
                    </td>
                  </tr>
                  {isOpen && g.indiv.map((r, idx) => (
                    <tr key={`${g.key}::${r.id}`} className="bg-gray-800/60">
                      <td className={`${tdPad} text-sm text-gray-300 border-l-2 border-blue-700/40`}
                      >
                        <div className="pl-3 flex items-start gap-2">
                          <CornerDownRight className="w-4 h-4 text-blue-400 mt-0.5" />
                          <div>
                            <div className="font-medium text-white">{g.concepto}</div>
                            <div className="text-xs text-gray-500 mt-1">{labelTipoConcepto(g.tipo_concepto)}</div>
                          </div>
                        </div>
                      </td>
                      <td className={`${tdPad} whitespace-nowrap text-sm text-gray-300`}>
                        <div>
                          <div className="text-white font-medium flex items-center">
                            <span>{r.empleado_rut || '-'}</span>
                            {r.especial && badgeEspecial(r.especial)}
                          </div>
                          {r.empleado_nombre && <div className="text-xs text-gray-400">{r.empleado_nombre}</div>}
                        </div>
                      </td>
                      <td className={`${tdPad} whitespace-nowrap text-sm font-medium ${ (r.variacion_porcentual ?? 0) >= 0 ? 'text-green-400' : 'text-red-400' } text-right`}>
                        {r.variacion_porcentual != null ? (
                          <span className="inline-flex items-center gap-1 justify-end w-full">
                            {r.variacion_porcentual >= 0 ? <TrendingUp className="w-3.5 h-3.5" /> : <TrendingDown className="w-3.5 h-3.5" />}
                            <span>{`${r.variacion_porcentual >= 0 ? '+' : ''}${r.variacion_porcentual.toFixed(2)}%`}</span>
                          </span>
                        ) : '—'}
                      </td>
                      <td className={`${tdPad} whitespace-nowrap text-sm text-gray-300 text-right`}>{r.anterior != null ? formatearMonedaChilena(r.anterior) : '—'}</td>
                      <td className={`${tdPad} whitespace-nowrap text-sm text-gray-300 text-right`}>{r.actual != null ? formatearMonedaChilena(r.actual) : '—'}</td>
                      <td className={`${tdPad} whitespace-nowrap`}>
                        {r.especial === 'ingreso_empleado' ? (
                          <span className="px-2 py-0.5 rounded text-xs bg-emerald-900/50 text-emerald-300 ring-1 ring-emerald-700/40">Informativo</span>
                        ) : (
                          badgePrioridad(r.prioridad)
                        )}
                      </td>
                      <td className={`${tdPad} whitespace-nowrap`}>
                        <div className="flex items-center">
                          {r.especial === 'ingreso_empleado' ? (
                            <span className="text-sm text-emerald-300 font-medium">Informativo</span>
                          ) : (
                            <span className="text-sm text-gray-300">{r.estadoReal.display}</span>
                          )}
                        </div>
                      </td>
                      <td className={`${tdPad} whitespace-nowrap`}>
                        {r.especial === 'ingreso_empleado' ? (
                          <span className="text-sm font-medium text-emerald-300">Informativo</span>
                        ) : (
                          (() => {
                            const esSupervisor = user?.is_staff || user?.is_superuser;
                            const resoluciones = r.raw?.resoluciones || [];
                            if (!resoluciones.length) {
                              return <span className={`text-sm font-medium ${!esSupervisor ? 'text-yellow-400' : 'text-gray-400'}`}>{!esSupervisor ? 'Analista' : 'Analista'}</span>;
                            }
                            const ultima = [...resoluciones].sort((a,b) => new Date(b.fecha_resolucion) - new Date(a.fecha_resolucion))[0];
                            if (ultima.tipo_resolucion === 'aprobacion') {
                              return <span className="text-sm font-medium text-green-400">Aprobada</span>;
                            }
                            const esDelSupervisor = ['consulta', 'rechazo'].includes(ultima.tipo_resolucion);
                            const turno = esDelSupervisor ? 'Analista' : 'Supervisor';
                            const color = turno === 'Analista' ? 'text-yellow-400' : 'text-gray-400';
                            return <span className={`text-sm font-medium ${color}`}>{turno}</span>;
                          })()
                        )}
                      </td>
                      <td className={`${tdPad} whitespace-nowrap text-sm text-gray-300`}>
                        {r.especial === 'ingreso_empleado' ? null : (
                          <button
                            onClick={() => onIncidenciaSeleccionada && onIncidenciaSeleccionada(r.raw)}
                            className="text-blue-400 hover:text-blue-300 p-1 rounded-md hover:bg-blue-500/10 transition-colors"
                            title="Ver detalles"
                          >
                            <Eye className="w-4 h-4" />
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </React.Fragment>
              );
            })}
          </tbody>
        </table>
      </div>
      {/* Paginación */}
      <div className="flex items-center justify-between mt-3 text-xs text-gray-400">
        <div className="flex items-center gap-2">
          <span>Resultados: {totalRows}</span>
          <span className="hidden sm:inline">|</span>
          <label className="hidden sm:flex items-center gap-1">
            Tamaño de página:
            <select
              className="bg-gray-800 border border-gray-700 rounded px-2 py-1 text-gray-200"
              value={pageSize}
              onChange={(e) => { setPageSize(Number(e.target.value)); setPage(1); }}
            >
              {[10, 25, 50, 100, 200].map(n => <option key={n} value={n}>{n}</option>)}
            </select>
          </label>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setPage(1)}
            disabled={currentPage === 1}
            className={`px-2 py-1 rounded border border-gray-700 ${currentPage===1?'text-gray-600':'text-gray-200 hover:bg-gray-800'}`}
          >«</button>
          <button
            onClick={() => setPage(Math.max(1, currentPage - 1))}
            disabled={currentPage === 1}
            className={`px-2 py-1 rounded border border-gray-700 ${currentPage===1?'text-gray-600':'text-gray-200 hover:bg-gray-800'}`}
          >‹</button>
          <span>Página {currentPage} de {totalPages}</span>
          <button
            onClick={() => setPage(Math.min(totalPages, currentPage + 1))}
            disabled={currentPage === totalPages}
            className={`px-2 py-1 rounded border border-gray-700 ${currentPage===totalPages?'text-gray-600':'text-gray-200 hover:bg-gray-800'}`}
          >›</button>
          <button
            onClick={() => setPage(totalPages)}
            disabled={currentPage === totalPages}
            className={`px-2 py-1 rounded border border-gray-700 ${currentPage===totalPages?'text-gray-600':'text-gray-200 hover:bg-gray-800'}`}
          >»</button>
        </div>
      </div>
    </div>
  );
}
