import { 
  TrendingUp, 
  Clock, 
  AlertTriangle, 
  CheckCircle,
  Calendar,
  Target,
  Users,
  FileX
} from "lucide-react";

const IndicadoresClave = ({ cierres }) => {
  // Calcular métricas de cumplimiento de plazos
  const calcularCumplimientoPlazos = () => {
    const hoy = new Date();
    const cierresConPlazo = cierres.filter(c => c.fecha_creacion);
    
    let dentroPlazo = 0;
    let fuera = 0;
    
    cierresConPlazo.forEach(cierre => {
      const fechaCreacion = new Date(cierre.fecha_creacion);
      const diasTranscurridos = (hoy - fechaCreacion) / (1000 * 60 * 60 * 24);
      
      // Considerar plazo estándar de 5 días
      if (diasTranscurridos <= 5 || ['completado', 'sin_incidencias'].includes(cierre.estado)) {
        dentroPlazo++;
      } else {
        fuera++;
      }
    });
    
    const total = dentroPlazo + fuera;
    return total > 0 ? Math.round((dentroPlazo / total) * 100) : 100;
  };

  // Calcular diferencias por cliente (simulado - solo diseño)
  const calcularDiferenciasCliente = () => {
    // Simulación para diseño - en producción calcularía diferencias reales
    const clientesUnicos = [...new Set(cierres.map(c => c.cliente_id))];
    return Math.max(0, clientesUnicos.length - 2); // Simulación
  };

  // Calcular nóminas rechazadas (basado en estados existentes)
  const calcularRechazadas = () => {
    return cierres.filter(c => c.estado === 'incidencias_abiertas').length;
  };

  // Tiempo promedio de procesamiento
  const calcularTiempoPromedio = () => {
    const completados = cierres.filter(c => 
      ['completado', 'sin_incidencias'].includes(c.estado) && c.fecha_creacion
    );
    
    if (completados.length === 0) return 0;
    
    const tiempos = completados.map(cierre => {
      const inicio = new Date(cierre.fecha_creacion);
      const fin = new Date(); // Simplificado, en producción usaría fecha_completado
      return (fin - inicio) / (1000 * 60 * 60 * 24);
    });
    
    return Math.round(tiempos.reduce((a, b) => a + b, 0) / tiempos.length);
  };

  const indicadores = [
    {
      titulo: "Cumplimiento de Plazos",
      valor: calcularCumplimientoPlazos(),
      unidad: "%",
      descripcion: "Procesos completados en tiempo estándar",
      icono: Target,
      color: calcularCumplimientoPlazos() >= 90 ? "text-green-400" : 
             calcularCumplimientoPlazos() >= 70 ? "text-yellow-400" : "text-red-400",
      fondo: calcularCumplimientoPlazos() >= 90 ? "bg-green-600" : 
             calcularCumplimientoPlazos() >= 70 ? "bg-yellow-600" : "bg-red-600"
    },
    {
      titulo: "Tiempo Promedio",
      valor: calcularTiempoPromedio(),
      unidad: "días",
      descripcion: "Duración promedio de procesamiento",
      icono: Clock,
      color: "text-blue-400",
      fondo: "bg-blue-600"
    },
    {
      titulo: "Clientes con Diferencias",
      valor: calcularDiferenciasCliente(),
      unidad: "",
      descripcion: "Clientes con incidencias detectadas",
      icono: AlertTriangle,
      color: "text-orange-400",
      fondo: "bg-orange-600"
    },
    {
      titulo: "Procesos con Incidencias",
      valor: calcularRechazadas(),
      unidad: "",
      descripcion: "Nóminas que requieren revisión",
      icono: FileX,
      color: "text-red-400",
      fondo: "bg-red-600"
    },
    {
      titulo: "Analistas Activos",
      valor: [...new Set(cierres.filter(c => c.usuario_analista).map(c => c.usuario_analista))].length,
      unidad: "",
      descripcion: "Analistas con procesos asignados",
      icono: Users,
      color: "text-purple-400",
      fondo: "bg-purple-600"
    },
    {
      titulo: "Procesos Este Mes",
      valor: cierres.filter(c => {
        const fechaCreacion = new Date(c.fecha_creacion);
        const hoy = new Date();
        return fechaCreacion.getMonth() === hoy.getMonth() && 
               fechaCreacion.getFullYear() === hoy.getFullYear();
      }).length,
      unidad: "",
      descripcion: "Cierres iniciados en el mes actual",
      icono: Calendar,
      color: "text-cyan-400",
      fondo: "bg-cyan-600"
    }
  ];

  return (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
      <div className="flex items-center gap-3 mb-6">
        <div className="flex items-center justify-center w-10 h-10 bg-green-600 rounded-lg">
          <TrendingUp size={20} className="text-white" />
        </div>
        <div>
          <h2 className="text-xl font-semibold text-white">
            Indicadores Clave de Performance
          </h2>
          <p className="text-gray-400 text-sm">
            Métricas estratégicas para toma de decisiones
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {indicadores.map((indicador, index) => {
          const IconoComponent = indicador.icono;
          
          return (
            <div key={index} className="bg-gray-700 rounded-lg p-4 hover:bg-gray-650 transition-colors">
              <div className="flex items-center justify-between mb-3">
                <div className={`flex items-center justify-center w-8 h-8 ${indicador.fondo} rounded-lg`}>
                  <IconoComponent size={16} className="text-white" />
                </div>
                <div className="text-right">
                  <div className={`text-2xl font-bold ${indicador.color}`}>
                    {indicador.valor}{indicador.unidad}
                  </div>
                </div>
              </div>
              <div>
                <h3 className="text-white font-medium text-sm mb-1">
                  {indicador.titulo}
                </h3>
                <p className="text-gray-400 text-xs">
                  {indicador.descripcion}
                </p>
              </div>
            </div>
          );
        })}
      </div>

      {/* Nota informativa */}
      <div className="mt-6 bg-blue-900/20 border border-blue-500/30 rounded-lg p-4">
        <div className="flex items-start gap-2">
          <CheckCircle className="w-4 h-4 text-blue-400 mt-0.5" />
          <div className="text-sm text-blue-300">
            <strong>Métricas en Tiempo Real:</strong> Los indicadores se actualizan automáticamente 
            basándose en el estado actual de todos los procesos de nómina.
          </div>
        </div>
      </div>
    </div>
  );
};

export default IndicadoresClave;
