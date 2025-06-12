import { useEffect, useState } from "react";
import { 
  BarChart3, 
  Users, 
  Building2, 
  TrendingUp, 
  Clock, 
  CheckCircle, 
  AlertCircle,
  DollarSign,
  Calendar,
  Target,
  PieChart,
  Activity
} from "lucide-react";
import { obtenerDashboardData } from "../api/analistas";
import AreaIndicator from "../components/AreaIndicator";

const KpiCard = ({ title, value, subtitle, icon: Icon, color, trend }) => (
  <div className="bg-gray-800 p-6 rounded-lg border border-gray-700 hover:border-gray-600 transition-colors">
    <div className="flex items-center justify-between">
      <div>
        <p className="text-gray-400 text-sm">{title}</p>
        <p className="text-2xl font-bold text-white mt-1">{value}</p>
        {subtitle && <p className="text-gray-400 text-xs mt-1">{subtitle}</p>}
        {trend && (
          <div className={`flex items-center mt-2 text-sm ${trend.positive ? 'text-green-400' : 'text-red-400'}`}>
            <TrendingUp className="w-4 h-4 mr-1" />
            {trend.value}
          </div>
        )}
      </div>
      <div className={`p-3 rounded-lg ${color}`}>
        <Icon className="w-6 h-6 text-white" />
      </div>
    </div>
  </div>
);

const ChartCard = ({ title, children, className = "" }) => (
  <div className={`bg-gray-800 p-6 rounded-lg border border-gray-700 ${className}`}>
    <h3 className="text-lg font-semibold text-white mb-4">{title}</h3>
    {children}
  </div>
);

const Dashboard = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedPeriod, setSelectedPeriod] = useState("current_month");

  useEffect(() => {
    const cargarDatos = async () => {
      try {
        setLoading(true);
        const data = await obtenerDashboardData(selectedPeriod);
        setDashboardData(data);
      } catch (err) {
        console.error("Error al cargar dashboard:", err);
      } finally {
        setLoading(false);
      }
    };
    cargarDatos();
  }, [selectedPeriod]);

  if (loading) {
    return (
      <div className="text-white flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white"></div>
        <span className="ml-2">Cargando dashboard...</span>
      </div>
    );
  }

  if (!dashboardData) {
    return <div className="text-white">Error al cargar los datos del dashboard</div>;
  }

  const {
    areas_gerente,
    kpis,
    analistas_performance,
    cierres_por_estado,
    clientes_por_industria,
    ingresos_por_servicio,
    tendencia_cierres,
    alerta_cierres_retrasados
  } = dashboardData;

  const { tiene_contabilidad, tiene_nomina } = areas_gerente || {};
  
  // Obtener usuario para mostrar sus áreas
  const usuario = JSON.parse(localStorage.getItem("usuario"));

  return (
    <div className="text-white space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <h1 className="text-3xl font-bold mb-2">Analytics de Performance</h1>
          <p className="text-gray-400">
            KPIs y métricas de {
              tiene_contabilidad && tiene_nomina ? 'contabilidad y nómina' :
              tiene_contabilidad ? 'contabilidad y cierres' :
              tiene_nomina ? 'nómina y remuneraciones' :
              'operaciones'
            }
          </p>
        </div>
        <div className="flex items-center space-x-4">
          <select 
            value={selectedPeriod}
            onChange={(e) => setSelectedPeriod(e.target.value)}
            className="bg-gray-800 border border-gray-600 rounded-lg px-4 py-2 text-white"
          >
            <option value="current_month">Mes Actual</option>
            <option value="last_month">Mes Anterior</option>
            <option value="quarter">Último Trimestre</option>
            <option value="year">Año Actual</option>
          </select>
        </div>
      </div>

      {/* Indicador de Área */}
      <AreaIndicator areas={areas_gerente} className="mt-4" />

      {/* Alertas */}
      {alerta_cierres_retrasados && alerta_cierres_retrasados.count > 0 && (
        <div className="bg-red-900/20 border border-red-500 rounded-lg p-4">
          <div className="flex items-center">
            <AlertCircle className="w-5 h-5 text-red-400 mr-2" />
            <span className="text-red-400 font-medium">
              {alerta_cierres_retrasados.count} cierres retrasados requieren atención
            </span>
          </div>
        </div>
      )}

      {/* KPIs Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <KpiCard
          title="Total Analistas"
          value={kpis.total_analistas}
          subtitle="Activos en el sistema"
          icon={Users}
          color="bg-blue-600"
        />
        <KpiCard
          title="Clientes Activos"
          value={kpis.clientes_activos}
          subtitle="Con contratos vigentes"
          icon={Building2}
          color="bg-green-600"
        />
        
        {/* KPIs específicos por área */}
        {tiene_contabilidad && (
          <KpiCard
            title="Cierres Contabilidad"
            value={kpis.cierres_contabilidad || 0}
            subtitle="Completados en el período"
            icon={CheckCircle}
            color="bg-purple-600"
          />
        )}
        
        {tiene_nomina && (
          <KpiCard
            title="Cierres Nómina"
            value={kpis.cierres_nomina || 0}
            subtitle="Completados en el período"
            icon={CheckCircle}
            color="bg-indigo-600"
          />
        )}
        
        {/* Si tiene ambas áreas, mostrar total */}
        {tiene_contabilidad && tiene_nomina && (
          <KpiCard
            title="Total Cierres"
            value={kpis.cierres_completados}
            subtitle="Ambas áreas combinadas"
            icon={Target}
            color="bg-orange-600"
          />
        )}
        
        {/* Si solo tiene una área, mostrar eficiencia en lugar de total */}
        {(tiene_contabilidad || tiene_nomina) && !(tiene_contabilidad && tiene_nomina) && (
          <KpiCard
            title="Eficiencia Promedio"
            value={`${kpis.eficiencia_promedio}%`}
            subtitle={`Área de ${tiene_contabilidad ? 'Contabilidad' : 'Nómina'}`}
            icon={Target}
            color="bg-orange-600"
          />
        )}
        
        {/* Si tiene ambas áreas, mostrar eficiencia en una quinta tarjeta */}
        {tiene_contabilidad && tiene_nomina && (
          <KpiCard
            title="Eficiencia Promedio"
            value={`${kpis.eficiencia_promedio}%`}
            subtitle="Ambas áreas"
            icon={Target}
            color="bg-orange-600"
          />
        )}
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Performance de Analistas */}
        <ChartCard title="Performance de Analistas">
          <div className="space-y-4">
            {analistas_performance.slice(0, 5).map((analista, index) => (
              <div key={analista.id} className="flex items-center justify-between">
                <div className="flex items-center">
                  <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-sm font-bold mr-3">
                    {index + 1}
                  </div>
                  <div>
                    <p className="font-medium">{analista.nombre} {analista.apellido}</p>
                    <p className="text-gray-400 text-sm">{analista.clientes_asignados} clientes</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="font-medium">{analista.cierres_completados}</p>
                  <p className="text-gray-400 text-sm">cierres</p>
                </div>
              </div>
            ))}
          </div>
        </ChartCard>

        {/* Estado de Cierres */}
        <ChartCard title="Estado de Cierres">
          <div className="space-y-3">
            {Object.entries(cierres_por_estado).map(([estado, count]) => {
              const getStateColor = (estado) => {
                switch (estado) {
                  case 'completado': return 'bg-green-600';
                  case 'en_proceso': return 'bg-yellow-600';
                  case 'pendiente': return 'bg-gray-600';
                  case 'retrasado': return 'bg-red-600';
                  default: return 'bg-blue-600';
                }
              };
              
              const percentage = (count / Object.values(cierres_por_estado).reduce((a, b) => a + b, 0)) * 100;
              
              return (
                <div key={estado} className="flex items-center justify-between">
                  <div className="flex items-center">
                    <div className={`w-3 h-3 rounded-full ${getStateColor(estado)} mr-3`}></div>
                    <span className="capitalize">{estado.replace('_', ' ')}</span>
                  </div>
                  <div className="flex items-center">
                    <span className="mr-2">{count}</span>
                    <div className="w-20 h-2 bg-gray-700 rounded-full">
                      <div 
                        className={`h-2 rounded-full ${getStateColor(estado)}`}
                        style={{ width: `${percentage}%` }}
                      ></div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </ChartCard>

        {/* Distribución por Industria */}
        <ChartCard title="Clientes por Industria">
          <div className="space-y-3">
            {clientes_por_industria.map((industria, index) => (
              <div key={industria.nombre} className="flex items-center justify-between">
                <div className="flex items-center">
                  <div 
                    className="w-3 h-3 rounded-full mr-3"
                    style={{ backgroundColor: `hsl(${index * 60}, 70%, 50%)` }}
                  ></div>
                  <span>{industria.nombre}</span>
                </div>
                <div className="flex items-center">
                  <span className="mr-2">{industria.count}</span>
                  <span className="text-gray-400 text-sm">clientes</span>
                </div>
              </div>
            ))}
          </div>
        </ChartCard>

        {/* Ingresos por Servicio */}
        <ChartCard title="Ingresos por Tipo de Servicio">
          <div className="space-y-3">
            {ingresos_por_servicio.map((servicio, index) => (
              <div key={servicio.area} className="flex items-center justify-between">
                <div className="flex items-center">
                  <DollarSign className="w-4 h-4 text-green-400 mr-2" />
                  <span>{servicio.area}</span>
                </div>
                <div className="text-right">
                  <p className="font-medium">${servicio.total_ingresos.toLocaleString()}</p>
                  <p className="text-gray-400 text-sm">{servicio.clientes} clientes</p>
                </div>
              </div>
            ))}
          </div>
        </ChartCard>
      </div>

      {/* Tendencia de Cierres */}
      <ChartCard title="Tendencia de Cierres - Últimos 6 Meses" className="col-span-full">
        <div className="grid grid-cols-6 gap-4 h-40">
          {tendencia_cierres.map((mes, index) => {
            const maxValue = Math.max(...tendencia_cierres.map(m => m.total));
            const height = (mes.total / maxValue) * 100;
            
            return (
              <div key={mes.periodo} className="flex flex-col items-center">
                <div className="flex-1 flex items-end">
                  <div 
                    className="bg-blue-600 w-8 rounded-t transition-all hover:bg-blue-500"
                    style={{ height: `${height}%` }}
                  ></div>
                </div>
                <div className="mt-2 text-center">
                  <p className="text-sm font-medium">{mes.total}</p>
                  <p className="text-xs text-gray-400">{mes.periodo}</p>
                </div>
              </div>
            );
          })}
        </div>
      </ChartCard>
    </div>
  );
};

export default Dashboard;
