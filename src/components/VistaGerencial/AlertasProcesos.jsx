import { 
  AlertTriangle, 
  Clock, 
  XCircle, 
  Zap,
  Bell,
  Eye,
  RefreshCw,
  UserCheck
} from "lucide-react";
import { Link } from "react-router-dom";
import EstadoBadge from "../EstadoBadge";

const AlertasProcesos = ({ cierres }) => {
  const hoy = new Date();

  // Detectar procesos detenidos o con problemas
  const procesosConAlertas = cierres.filter(cierre => {
    const fechaCreacion = new Date(cierre.fecha_creacion);
    const diasTranscurridos = (hoy - fechaCreacion) / (1000 * 60 * 60 * 24);
    
    // Alertas por tiempo excesivo
    const detenidoPorTiempo = diasTranscurridos > 5 && 
      !['completado', 'sin_incidencias'].includes(cierre.estado);
    
    // Alertas por incidencias abiertas
    const conIncidencias = cierre.estado === 'incidencias_abiertas';
    
    // Alertas por estado sin avance
    const sinAvance = cierre.estado === 'pendiente' && diasTranscurridos > 2;
    
    return detenidoPorTiempo || conIncidencias || sinAvance;
  });

  // Clasificar alertas por tipo
  const alertas = procesosConAlertas.map(cierre => {
    const fechaCreacion = new Date(cierre.fecha_creacion);
    const diasTranscurridos = Math.floor((hoy - fechaCreacion) / (1000 * 60 * 60 * 24));
    
    let tipo = "";
    let prioridad = "";
    let icono = AlertTriangle;
    let color = "text-yellow-400";
    let mensaje = "";
    
    if (cierre.estado === 'incidencias_abiertas') {
      tipo = "incidencias";
      prioridad = "alta";
      icono = XCircle;
      color = "text-red-400";
      mensaje = "Proceso con incidencias que requieren supervisión";
    } else if (diasTranscurridos > 7) {
      tipo = "critico";
      prioridad = "critica";
      icono = Zap;
      color = "text-red-500";
      mensaje = `Proceso detenido por ${diasTranscurridos} días - Intervención crítica`;
    } else if (diasTranscurridos > 5) {
      tipo = "atraso";
      prioridad = "alta";
      icono = Clock;
      color = "text-orange-400";
      mensaje = `Posible atraso - ${diasTranscurridos} días sin completar`;
    } else if (cierre.estado === 'pendiente' && diasTranscurridos > 2) {
      tipo = "sin_avance";
      prioridad = "media";
      icono = AlertTriangle;
      color = "text-yellow-400";
      mensaje = "Sin avance por más de 2 días - Verificar asignación";
    }
    
    return {
      ...cierre,
      alertaTipo: tipo,
      alertaPrioridad: prioridad,
      alertaIcono: icono,
      alertaColor: color,
      alertaMensaje: mensaje,
      diasTranscurridos
    };
  });

  // Ordenar por prioridad
  const alertasOrdenadas = alertas.sort((a, b) => {
    const prioridades = { critica: 3, alta: 2, media: 1 };
    return prioridades[b.alertaPrioridad] - prioridades[a.alertaPrioridad];
  });

  const estadisticasAlertas = {
    total: alertas.length,
    criticas: alertas.filter(a => a.alertaPrioridad === 'critica').length,
    altas: alertas.filter(a => a.alertaPrioridad === 'alta').length,
    medias: alertas.filter(a => a.alertaPrioridad === 'media').length
  };

  return (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
      <div className="flex items-center gap-3 mb-6">
        <div className="flex items-center justify-center w-10 h-10 bg-red-600 rounded-lg">
          <Bell size={20} className="text-white" />
        </div>
        <div>
          <h2 className="text-xl font-semibold text-white">
            Alertas y Procesos Críticos
          </h2>
          <p className="text-gray-400 text-sm">
            Procesos que requieren intervención inmediata
          </p>
        </div>
      </div>

      {/* Resumen de alertas */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-gray-700 p-3 rounded-lg text-center">
          <div className="text-lg font-bold text-white">{estadisticasAlertas.total}</div>
          <div className="text-xs text-gray-400">Total Alertas</div>
        </div>
        <div className="bg-red-600 p-3 rounded-lg text-center">
          <div className="text-lg font-bold text-white">{estadisticasAlertas.criticas}</div>
          <div className="text-xs text-red-100">Críticas</div>
        </div>
        <div className="bg-orange-600 p-3 rounded-lg text-center">
          <div className="text-lg font-bold text-white">{estadisticasAlertas.altas}</div>
          <div className="text-xs text-orange-100">Altas</div>
        </div>
        <div className="bg-yellow-600 p-3 rounded-lg text-center">
          <div className="text-lg font-bold text-white">{estadisticasAlertas.medias}</div>
          <div className="text-xs text-yellow-100">Medias</div>
        </div>
      </div>

      {/* Lista de alertas */}
      <div className="space-y-3 max-h-96 overflow-y-auto">
        {alertasOrdenadas.length === 0 ? (
          <div className="text-center py-8">
            <div className="w-16 h-16 bg-green-600 rounded-full flex items-center justify-center mx-auto mb-4">
              <UserCheck size={24} className="text-white" />
            </div>
            <h3 className="text-green-400 font-medium mb-2">¡Todo bajo control!</h3>
            <p className="text-gray-400 text-sm">
              No hay procesos que requieran intervención inmediata
            </p>
          </div>
        ) : (
          alertasOrdenadas.map((alerta, index) => {
            const IconoAlerta = alerta.alertaIcono;
            
            return (
              <div 
                key={alerta.id} 
                className="bg-gray-700 rounded-lg p-4 border-l-4 border-l-red-500 hover:bg-gray-650 transition-colors"
              >
                <div className="flex items-start gap-3">
                  <div className={`mt-1 ${alerta.alertaColor}`}>
                    <IconoAlerta size={20} />
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h4 className="text-white font-medium truncate">
                        {alerta.cliente_nombre}
                      </h4>
                      <span className="text-gray-400 text-sm">•</span>
                      <span className="text-gray-300 text-sm">{alerta.periodo}</span>
                      <div className="ml-auto">
                        <EstadoBadge estado={alerta.estado} size="xs" />
                      </div>
                    </div>
                    
                    <p className="text-sm text-gray-300 mb-2">
                      {alerta.alertaMensaje}
                    </p>
                    
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4 text-xs text-gray-400">
                        <span>Analista: {alerta.usuario_analista || "Sin asignar"}</span>
                        <span>Días: {alerta.diasTranscurridos}</span>
                        <span className={`px-2 py-1 rounded ${
                          alerta.alertaPrioridad === 'critica' ? 'bg-red-600 text-white' :
                          alerta.alertaPrioridad === 'alta' ? 'bg-orange-600 text-white' :
                          'bg-yellow-600 text-white'
                        }`}>
                          {alerta.alertaPrioridad.toUpperCase()}
                        </span>
                      </div>
                      
                      <div className="flex gap-2">
                        <Link
                          to={`/menu/nomina/cierres/${alerta.id}`}
                          className="flex items-center gap-1 px-3 py-1 bg-blue-600 text-white rounded text-xs hover:bg-blue-700 transition-colors"
                        >
                          <Eye size={12} />
                          Revisar
                        </Link>
                        <button className="flex items-center gap-1 px-3 py-1 bg-orange-600 text-white rounded text-xs hover:bg-orange-700 transition-colors">
                          <RefreshCw size={12} />
                          Reasignar
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Acciones rápidas */}
      {alertasOrdenadas.length > 0 && (
        <div className="mt-6 flex gap-3">
          <button className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors text-sm">
            <Zap size={16} />
            Intervenir Críticos
          </button>
          <button className="flex items-center gap-2 px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors text-sm">
            <UserCheck size={16} />
            Reasignar Masivo
          </button>
          <button className="flex items-center gap-2 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors text-sm">
            <RefreshCw size={16} />
            Actualizar Todo
          </button>
        </div>
      )}
    </div>
  );
};

export default AlertasProcesos;
