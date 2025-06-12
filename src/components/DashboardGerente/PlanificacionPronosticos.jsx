import { useState, useEffect } from 'react';
import { obtenerPlanificacion, guardarPlanificacion } from '../../api/gerente';
import { formatMoney } from '../../utils/format';

const PlanificacionPronosticos = ({ areas }) => {
  const [planificacion, setPlanificacion] = useState(null);
  const [periodoSeleccionado, setPeriodoSeleccionado] = useState('2025');
  const [editando, setEditando] = useState(false);
  const [metasEditadas, setMetasEditadas] = useState({});

  useEffect(() => {
    cargarPlanificacion();
  }, [periodoSeleccionado]);

  const cargarPlanificacion = async () => {
    try {
      const data = await obtenerPlanificacion(periodoSeleccionado);
      setPlanificacion(data);
      setMetasEditadas(data.metas || {});
    } catch (error) {
      console.error('Error cargando planificación:', error);
    }
  };

  const guardarMetas = async () => {
    try {
      await guardarPlanificacion(periodoSeleccionado, metasEditadas);
      await cargarPlanificacion();
      setEditando(false);
    } catch (error) {
      console.error('Error guardando metas:', error);
    }
  };

  if (!planificacion) {
    return <div className="text-white">Cargando planificación...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-white">Planificación & Pronósticos</h2>
        <div className="flex gap-4">
          <select
            value={periodoSeleccionado}
            onChange={(e) => setPeriodoSeleccionado(e.target.value)}
            className="bg-gray-700 text-white p-2 rounded"
          >
            <option value="2025">2025</option>
            <option value="2026">2026</option>
            <option value="Q1-2025">Q1 2025</option>
            <option value="Q2-2025">Q2 2025</option>
            <option value="Q3-2025">Q3 2025</option>
            <option value="Q4-2025">Q4 2025</option>
          </select>
          
          {editando ? (
            <div className="flex gap-2">
              <button
                onClick={guardarMetas}
                className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded"
              >
                💾 Guardar
              </button>
              <button
                onClick={() => setEditando(false)}
                className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded"
              >
                Cancelar
              </button>
            </div>
          ) : (
            <button
              onClick={() => setEditando(true)}
              className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded"
            >
              ✏️ Editar Metas
            </button>
          )}
        </div>
      </div>

      {/* Resumen de Pronósticos */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-gray-800 p-6 rounded-lg">
          <h3 className="text-white font-semibold mb-2">Ingresos Proyectados</h3>
          <p className="text-3xl font-bold text-green-500">
            {formatMoney(planificacion.ingresos_proyectados)} CLP
          </p>
          <p className="text-sm text-gray-400">
            {planificacion.crecimiento_proyectado > 0 ? '+' : ''}{planificacion.crecimiento_proyectado}% vs período anterior
          </p>
        </div>

        <div className="bg-gray-800 p-6 rounded-lg">
          <h3 className="text-white font-semibold mb-2">Nuevos Clientes</h3>
          <p className="text-3xl font-bold text-blue-500">{planificacion.nuevos_clientes_objetivo}</p>
          <p className="text-sm text-gray-400">Meta para {periodoSeleccionado}</p>
        </div>

        <div className="bg-gray-800 p-6 rounded-lg">
          <h3 className="text-white font-semibold mb-2">Retención Esperada</h3>
          <p className="text-3xl font-bold text-yellow-500">{planificacion.retencion_esperada}%</p>
          <p className="text-sm text-gray-400">Basado en histórico</p>
        </div>

        <div className="bg-gray-800 p-6 rounded-lg">
          <h3 className="text-white font-semibold mb-2">Capacidad Equipo</h3>
          <p className="text-3xl font-bold text-purple-500">{planificacion.capacidad_maxima}</p>
          <p className="text-sm text-gray-400">Clientes máximos</p>
        </div>
      </div>

      {/* Metas por Área */}
      <div className="bg-gray-800 p-6 rounded-lg">
        <h3 className="text-xl font-semibold text-white mb-4">Metas por Área - {periodoSeleccionado}</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {areas.map(area => (
            <div key={area.id} className="bg-gray-700 p-4 rounded-lg">
              <h4 className="font-semibold text-white mb-3">{area.nombre}</h4>
              
              <div className="space-y-3">
                <div>
                  <label className="block text-gray-300 text-sm mb-1">Ingresos Objetivo</label>
                  {editando ? (
                    <input
                      type="number"
                      value={metasEditadas[`${area.id}_ingresos`] || ''}
                      onChange={(e) => setMetasEditadas({
                        ...metasEditadas,
                        [`${area.id}_ingresos`]: e.target.value
                      })}
                      className="w-full p-2 bg-gray-600 text-white rounded"
                    />
                  ) : (
                    <div className="text-green-400 font-semibold">
                      {formatMoney(planificacion.metas?.[`${area.id}_ingresos`] || 0)} CLP
                    </div>
                  )}
                </div>

                <div>
                  <label className="block text-gray-300 text-sm mb-1">Clientes Objetivo</label>
                  {editando ? (
                    <input
                      type="number"
                      value={metasEditadas[`${area.id}_clientes`] || ''}
                      onChange={(e) => setMetasEditadas({
                        ...metasEditadas,
                        [`${area.id}_clientes`]: e.target.value
                      })}
                      className="w-full p-2 bg-gray-600 text-white rounded"
                    />
                  ) : (
                    <div className="text-blue-400 font-semibold">
                      {planificacion.metas?.[`${area.id}_clientes`] || 0} clientes
                    </div>
                  )}
                </div>

                <div>
                  <label className="block text-gray-300 text-sm mb-1">SLA Objetivo</label>
                  {editando ? (
                    <input
                      type="number"
                      max="100"
                      value={metasEditadas[`${area.id}_sla`] || ''}
                      onChange={(e) => setMetasEditadas({
                        ...metasEditadas,
                        [`${area.id}_sla`]: e.target.value
                      })}
                      className="w-full p-2 bg-gray-600 text-white rounded"
                    />
                  ) : (
                    <div className="text-yellow-400 font-semibold">
                      {planificacion.metas?.[`${area.id}_sla`] || 0}%
                    </div>
                  )}
                </div>
              </div>
              
              {/* Progreso actual */}
              <div className="mt-4 pt-3 border-t border-gray-600">
                <div className="text-sm text-gray-400">Progreso Actual:</div>
                <div className="grid grid-cols-3 gap-2 mt-2">
                  <div className="text-center">
                    <div className="text-lg font-bold text-green-400">
                      {Math.round((planificacion.progreso_actual?.[`${area.id}_ingresos`] || 0) / 
                      (planificacion.metas?.[`${area.id}_ingresos`] || 1) * 100)}%
                    </div>
                    <div className="text-xs text-gray-500">Ingresos</div>
                  </div>
                  <div className="text-center">
                    <div className="text-lg font-bold text-blue-400">
                      {Math.round((planificacion.progreso_actual?.[`${area.id}_clientes`] || 0) / 
                      (planificacion.metas?.[`${area.id}_clientes`] || 1) * 100)}%
                    </div>
                    <div className="text-xs text-gray-500">Clientes</div>
                  </div>
                  <div className="text-center">
                    <div className="text-lg font-bold text-yellow-400">
                      {planificacion.progreso_actual?.[`${area.id}_sla`] || 0}%
                    </div>
                    <div className="text-xs text-gray-500">SLA</div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Análisis de Capacidad */}
      <div className="bg-gray-800 p-6 rounded-lg">
        <h3 className="text-xl font-semibold text-white mb-4">Análisis de Capacidad del Equipo</h3>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Carga Actual vs Proyectada */}
          <div>
            <h4 className="font-semibold text-gray-300 mb-3">Carga de Trabajo Proyectada</h4>
            <div className="space-y-3">
              {planificacion.analisis_capacidad?.map(analista => (
                <div key={analista.id} className="bg-gray-700 p-3 rounded">
                  <div className="flex justify-between items-center">
                    <span className="text-white">{analista.nombre}</span>
                    <div className="flex items-center gap-2">
                      <div className="w-24 bg-gray-600 rounded-full h-2">
                        <div 
                          className={`h-2 rounded-full ${
                            analista.carga_proyectada > 100 ? 'bg-red-500' :
                            analista.carga_proyectada > 80 ? 'bg-yellow-500' : 'bg-green-500'
                          }`}
                          style={{ width: `${Math.min(analista.carga_proyectada, 100)}%` }}
                        />
                      </div>
                      <span className={`text-sm font-semibold ${
                        analista.carga_proyectada > 100 ? 'text-red-400' :
                        analista.carga_proyectada > 80 ? 'text-yellow-400' : 'text-green-400'
                      }`}>
                        {analista.carga_proyectada}%
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Recomendaciones */}
          <div>
            <h4 className="font-semibold text-gray-300 mb-3">Recomendaciones</h4>
            <div className="space-y-3">
              {planificacion.recomendaciones?.map((recomendacion, index) => (
                <div key={index} className="bg-blue-900 p-3 rounded border-l-4 border-blue-500">
                  <div className="text-blue-200 font-semibold">{recomendacion.tipo}</div>
                  <div className="text-blue-100 text-sm">{recomendacion.descripcion}</div>
                  <div className="text-blue-300 text-xs mt-1">
                    Impacto: {recomendacion.impacto} • Prioridad: {recomendacion.prioridad}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Escenarios de Crecimiento */}
      <div className="bg-gray-800 p-6 rounded-lg">
        <h3 className="text-xl font-semibold text-white mb-4">Escenarios de Crecimiento</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {planificacion.escenarios?.map(escenario => (
            <div key={escenario.tipo} className="bg-gray-700 p-4 rounded-lg">
              <h4 className="font-semibold text-white mb-3">
                {escenario.tipo === 'conservador' && '🐌 Conservador'}
                {escenario.tipo === 'optimista' && '🚀 Optimista'}
                {escenario.tipo === 'pesimista' && '⚠️ Pesimista'}
              </h4>
              
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-300">Crecimiento:</span>
                  <span className="text-white">{escenario.crecimiento}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-300">Ingresos:</span>
                  <span className="text-green-400">{formatMoney(escenario.ingresos)} CLP</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-300">Nuevos clientes:</span>
                  <span className="text-blue-400">{escenario.nuevos_clientes}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-300">Equipo requerido:</span>
                  <span className="text-yellow-400">{escenario.equipo_requerido}</span>
                </div>
              </div>
              
              <div className="mt-3 text-xs text-gray-400">
                Probabilidad: {escenario.probabilidad}%
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default PlanificacionPronosticos;
