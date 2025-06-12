import { useState, useEffect } from 'react';
import { obtenerMetricasAvanzadas } from '../../api/gerente';
import { formatNumber, formatPercentage } from '../../utils/format';

const MetricasAvanzadas = ({ areas }) => {
  const [metricas, setMetricas] = useState(null);
  const [filtros, setFiltros] = useState({
    periodo: 'month',
    area: ''
  });
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    cargarMetricas();
  }, [filtros]);

  const cargarMetricas = async () => {
    setCargando(true);
    setError('');
    try {
      const data = await obtenerMetricasAvanzadas(filtros);
      setMetricas(data);
    } catch (error) {
      console.error('Error cargando métricas:', error);
      setError('Error al cargar las métricas. Por favor intenta nuevamente.');
    } finally {
      setCargando(false);
    }
  };

  if (cargando) {
    return (
      <div className="space-y-6">
        <div className="bg-gray-800 p-6 rounded-lg">
          <div className="animate-pulse space-y-4">
            <div className="h-4 bg-gray-700 rounded w-1/4"></div>
            <div className="grid grid-cols-4 gap-4">
              {[1,2,3,4].map(i => (
                <div key={i} className="h-24 bg-gray-700 rounded"></div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-600 text-white p-4 rounded-lg">
        <h3 className="font-semibold">Error</h3>
        <p>{error}</p>
        <button 
          onClick={cargarMetricas}
          className="mt-2 bg-red-800 hover:bg-red-900 px-4 py-2 rounded"
        >
          Reintentar
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header y Filtros */}
      <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4">
        <h2 className="text-2xl font-bold text-white">Métricas Avanzadas</h2>
        
        <div className="flex gap-4">
          {/* Filtro de período */}
          <select
            value={filtros.periodo}
            onChange={(e) => setFiltros({...filtros, periodo: e.target.value})}
            className="bg-gray-700 text-white p-2 rounded"
          >
            <option value="week">Esta Semana</option>
            <option value="month">Este Mes</option>
            <option value="quarter">Trimestre</option>
            <option value="year">Año</option>
          </select>

          {/* Filtro de área */}
          <select
            value={filtros.area}
            onChange={(e) => setFiltros({...filtros, area: e.target.value})}
            className="bg-gray-700 text-white p-2 rounded"
          >
            <option value="">Todas las áreas</option>
            {areas?.map(area => (
              <option key={area.id} value={area.nombre}>{area.nombre}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Resumen Ejecutivo */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard
          titulo="Clientes Totales"
          valor={metricas?.resumen?.total_clientes || 0}
          cambio={null}
          color="blue"
          icono="👥"
        />
        <KPICard
          titulo="Analistas Activos"
          valor={metricas?.resumen?.total_analistas || 0}
          cambio={null}
          color="green"
          icono="👨‍💼"
        />
        <KPICard
          titulo="Cierres del Período"
          valor={metricas?.resumen?.cierres_periodo || 0}
          cambio={null}
          color="yellow"
          icono="📊"
        />
        <KPICard
          titulo="% Asignación"
          valor={formatPercentage(metricas?.resumen?.porcentaje_asignacion || 0)}
          cambio={null}
          color="purple"
          icono="📈"
        />
      </div>

      {/* KPIs Operacionales */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <KPICard
          titulo="Eficiencia del Equipo"
          valor={formatPercentage(metricas?.kpis?.eficiencia_equipo || 0)}
          color="green"
          descripcion="Productividad general"
        />
        <KPICard
          titulo="Tiempo Promedio Cierre"
          valor={`${metricas?.kpis?.tiempo_promedio_cierre || 0} días`}
          color="blue"
          descripcion="Tiempo de procesamiento"
        />
        <KPICard
          titulo="SLA Cumplimiento"
          valor={formatPercentage(metricas?.kpis?.sla_cumplimiento || 0)}
          color="yellow"
          descripcion="Objetivos alcanzados"
        />
      </div>

      {/* Distribución y Tendencias */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Distribución por Áreas */}
        <div className="bg-gray-800 p-6 rounded-lg">
          <h3 className="text-xl font-semibold text-white mb-4">Distribución por Áreas</h3>
          <div className="space-y-3">
            {metricas?.tendencias?.distribucion_areas?.map((area) => (
              <div key={area.area} className="flex justify-between items-center">
                <span className="text-white">{area.area}</span>
                <div className="flex items-center gap-2">
                  <div className="w-32 bg-gray-700 rounded-full h-2">
                    <div 
                      className="bg-blue-500 h-2 rounded-full"
                      style={{ width: `${area.porcentaje}%` }}
                    ></div>
                  </div>
                  <span className="text-gray-400 text-sm w-12 text-right">
                    {area.clientes}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Tendencia de Cierres */}
        <div className="bg-gray-800 p-6 rounded-lg">
          <h3 className="text-xl font-semibold text-white mb-4">Tendencia de Cierres</h3>
          <div className="space-y-2">
            {metricas?.tendencias?.cierres_mensuales?.map((mes) => (
              <div key={mes.periodo} className="flex justify-between items-center">
                <span className="text-white">{mes.periodo}</span>
                <div className="flex items-center gap-2">
                  <div className="w-24 bg-gray-700 rounded-full h-2">
                    <div 
                      className="bg-green-500 h-2 rounded-full"
                      style={{ width: `${(mes.cierres / 70) * 100}%` }}
                    ></div>
                  </div>
                  <span className="text-gray-400 text-sm w-8 text-right">
                    {mes.cierres}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Alertas y Recomendaciones */}
      <div className="bg-gray-800 p-6 rounded-lg">
        <h3 className="text-xl font-semibold text-white mb-4">Recomendaciones del Sistema</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <RecomendacionCard
            tipo="warning"
            titulo="Sobrecarga Detectada"
            mensaje="2 analistas tienen más de 12 clientes asignados"
            accion="Revisar asignaciones"
          />
          <RecomendacionCard
            tipo="info"
            titulo="Oportunidad de Mejora"
            mensaje="El tiempo promedio de cierre aumentó 0.5 días"
            accion="Analizar procesos"
          />
        </div>
      </div>
    </div>
  );
};

const KPICard = ({ titulo, valor, cambio, color, icono, descripcion }) => {
  const colorClasses = {
    blue: 'text-blue-500',
    green: 'text-green-500',
    yellow: 'text-yellow-500',
    purple: 'text-purple-500',
    red: 'text-red-500'
  };

  return (
    <div className="bg-gray-800 p-6 rounded-lg">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-white font-semibold text-sm">{titulo}</h3>
        {icono && <span className="text-2xl">{icono}</span>}
      </div>
      <p className={`text-3xl font-bold ${colorClasses[color]}`}>{valor}</p>
      {descripcion && (
        <p className="text-gray-400 text-sm mt-1">{descripcion}</p>
      )}
      {cambio && (
        <p className={`text-sm mt-1 ${cambio >= 0 ? 'text-green-400' : 'text-red-400'}`}>
          {cambio >= 0 ? '+' : ''}{cambio}% vs período anterior
        </p>
      )}
    </div>
  );
};

const RecomendacionCard = ({ tipo, titulo, mensaje, accion }) => {
  const tipoStyles = {
    warning: 'border-l-yellow-500 bg-yellow-900/20',
    info: 'border-l-blue-500 bg-blue-900/20',
    success: 'border-l-green-500 bg-green-900/20',
    error: 'border-l-red-500 bg-red-900/20'
  };

  return (
    <div className={`border-l-4 p-4 rounded ${tipoStyles[tipo]}`}>
      <h4 className="text-white font-semibold text-sm mb-1">{titulo}</h4>
      <p className="text-gray-300 text-sm mb-2">{mensaje}</p>
      <button className="text-blue-400 hover:text-blue-300 text-sm font-medium">
        {accion} →
      </button>
    </div>
  );
};

export default MetricasAvanzadas;
