import { useState } from "react";
import { 
  UserCog, 
  Users, 
  ArrowRight, 
  Plus,
  Search,
  Settings,
  Shield,
  CheckCircle,
  AlertCircle
} from "lucide-react";

const GestionAsignaciones = () => {
  const [vistaActiva, setVistaActiva] = useState("reasignar");

  // Datos simulados para diseño (en producción vendrían de API)
  const analistas = [
    {
      id: 1,
      nombre: "María González",
      carga: 5,
      capacidad: 8,
      especialidad: "Nóminas Complejas",
      disponible: true
    },
    {
      id: 2,
      nombre: "Juan Pérez", 
      carga: 7,
      capacidad: 8,
      especialidad: "Proceso Estándar",
      disponible: true
    },
    {
      id: 3,
      nombre: "Ana López",
      carga: 3,
      capacidad: 6,
      especialidad: "Análisis Variaciones",
      disponible: false
    },
    {
      id: 4,
      nombre: "Carlos Silva",
      carga: 8,
      capacidad: 8,
      especialidad: "Incidencias",
      disponible: true
    }
  ];

  const supervisores = [
    {
      id: 1,
      nombre: "Patricia Morales",
      analistas: 3,
      carga: "Alta",
      area: "Nómina Principal"
    },
    {
      id: 2,
      nombre: "Roberto Chen",
      analistas: 2,
      carga: "Media",
      area: "Nómina Especial"
    }
  ];

  const obtenerColorCarga = (carga, capacidad) => {
    const porcentaje = (carga / capacidad) * 100;
    if (porcentaje >= 90) return "text-red-400";
    if (porcentaje >= 70) return "text-yellow-400";
    return "text-green-400";
  };

  return (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
      <div className="flex items-center gap-3 mb-6">
        <div className="flex items-center justify-center w-10 h-10 bg-purple-600 rounded-lg">
          <UserCog size={20} className="text-white" />
        </div>
        <div>
          <h2 className="text-xl font-semibold text-white">
            Gestión de Asignaciones
          </h2>
          <p className="text-gray-400 text-sm">
            Reasignar tareas para mantener operación fluida
          </p>
        </div>
      </div>

      {/* Tabs de navegación */}
      <div className="flex border-b border-gray-700 mb-6">
        <button
          onClick={() => setVistaActiva("reasignar")}
          className={`px-4 py-2 text-sm font-medium transition-colors ${
            vistaActiva === "reasignar"
              ? "text-white border-b-2 border-purple-500"
              : "text-gray-400 hover:text-white"
          }`}
        >
          Reasignar Tareas
        </button>
        <button
          onClick={() => setVistaActiva("analistas")}
          className={`px-4 py-2 text-sm font-medium transition-colors ${
            vistaActiva === "analistas"
              ? "text-white border-b-2 border-purple-500"
              : "text-gray-400 hover:text-white"
          }`}
        >
          Estado Analistas
        </button>
        <button
          onClick={() => setVistaActiva("supervisores")}
          className={`px-4 py-2 text-sm font-medium transition-colors ${
            vistaActiva === "supervisores"
              ? "text-white border-b-2 border-purple-500"
              : "text-gray-400 hover:text-white"
          }`}
        >
          Supervisores
        </button>
      </div>

      {/* Vista: Reasignar Tareas */}
      {vistaActiva === "reasignar" && (
        <div className="space-y-4">
          <div className="bg-orange-900/20 border border-orange-500/30 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-3">
              <AlertCircle className="w-5 h-5 text-orange-400" />
              <h3 className="text-orange-400 font-medium">Tareas Pendientes de Reasignación</h3>
            </div>
            
            {/* Simulación de tareas para reasignar */}
            <div className="space-y-3">
              <div className="bg-gray-700 rounded-lg p-3">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-white font-medium">Cliente ABC S.A. - Período 2025-06</div>
                    <div className="text-gray-400 text-sm">Analista actual: Sin asignar</div>
                  </div>
                  <div className="flex items-center gap-2">
                    <select className="bg-gray-600 border border-gray-500 rounded px-3 py-1 text-white text-sm">
                      <option>Seleccionar analista...</option>
                      {analistas.filter(a => a.disponible).map(analista => (
                        <option key={analista.id} value={analista.id}>
                          {analista.nombre} ({analista.carga}/{analista.capacidad})
                        </option>
                      ))}
                    </select>
                    <button className="flex items-center gap-1 px-3 py-1 bg-green-600 text-white rounded text-sm hover:bg-green-700">
                      <ArrowRight size={14} />
                      Asignar
                    </button>
                  </div>
                </div>
              </div>

              <div className="bg-gray-700 rounded-lg p-3">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-white font-medium">Empresa XYZ Ltda. - Período 2025-06</div>
                    <div className="text-gray-400 text-sm">Analista actual: Carlos Silva (sobrecargado)</div>
                  </div>
                  <div className="flex items-center gap-2">
                    <select className="bg-gray-600 border border-gray-500 rounded px-3 py-1 text-white text-sm">
                      <option>Reasignar a...</option>
                      {analistas.filter(a => a.disponible && a.carga < a.capacidad).map(analista => (
                        <option key={analista.id} value={analista.id}>
                          {analista.nombre} ({analista.carga}/{analista.capacidad})
                        </option>
                      ))}
                    </select>
                    <button className="flex items-center gap-1 px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700">
                      <ArrowRight size={14} />
                      Reasignar
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="flex gap-3">
            <button className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors text-sm">
              <Plus size={16} />
              Asignación Masiva
            </button>
            <button className="flex items-center gap-2 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors text-sm">
              <Settings size={16} />
              Configurar Reglas
            </button>
          </div>
        </div>
      )}

      {/* Vista: Estado de Analistas */}
      {vistaActiva === "analistas" && (
        <div className="space-y-4">
          {analistas.map(analista => {
            const porcentajeCarga = (analista.carga / analista.capacidad) * 100;
            
            return (
              <div key={analista.id} className="bg-gray-700 rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <div className={`w-3 h-3 rounded-full ${
                      analista.disponible ? 'bg-green-400' : 'bg-red-400'
                    }`}></div>
                    <div>
                      <h3 className="text-white font-medium">{analista.nombre}</h3>
                      <p className="text-gray-400 text-sm">{analista.especialidad}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className={`text-lg font-bold ${obtenerColorCarga(analista.carga, analista.capacidad)}`}>
                      {analista.carga}/{analista.capacidad}
                    </div>
                    <div className="text-gray-400 text-sm">Carga actual</div>
                  </div>
                </div>
                
                <div className="mb-3">
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-400">Capacidad utilizada</span>
                    <span className="text-white">{porcentajeCarga.toFixed(0)}%</span>
                  </div>
                  <div className="w-full bg-gray-600 rounded-full h-2">
                    <div 
                      className={`h-2 rounded-full transition-all duration-300 ${
                        porcentajeCarga >= 90 ? 'bg-red-500' :
                        porcentajeCarga >= 70 ? 'bg-yellow-500' : 'bg-green-500'
                      }`}
                      style={{ width: `${Math.min(porcentajeCarga, 100)}%` }}
                    ></div>
                  </div>
                </div>
                
                <div className="flex justify-between items-center">
                  <span className={`text-sm px-2 py-1 rounded ${
                    analista.disponible 
                      ? 'bg-green-600 text-green-100' 
                      : 'bg-red-600 text-red-100'
                  }`}>
                    {analista.disponible ? 'Disponible' : 'No disponible'}
                  </span>
                  <button className="text-blue-400 hover:text-blue-300 text-sm">
                    Ver detalles →
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Vista: Supervisores */}
      {vistaActiva === "supervisores" && (
        <div className="space-y-4">
          {supervisores.map(supervisor => (
            <div key={supervisor.id} className="bg-gray-700 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="flex items-center justify-center w-8 h-8 bg-blue-600 rounded-lg">
                    <Shield size={16} className="text-white" />
                  </div>
                  <div>
                    <h3 className="text-white font-medium">{supervisor.nombre}</h3>
                    <p className="text-gray-400 text-sm">{supervisor.area}</p>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-white font-medium">{supervisor.analistas} analistas</div>
                  <div className={`text-sm ${
                    supervisor.carga === 'Alta' ? 'text-red-400' :
                    supervisor.carga === 'Media' ? 'text-yellow-400' : 'text-green-400'
                  }`}>
                    Carga: {supervisor.carga}
                  </div>
                </div>
              </div>
            </div>
          ))}
          
          <div className="bg-blue-900/20 border border-blue-500/30 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-2">
              <CheckCircle className="w-4 h-4 text-blue-400" />
              <span className="text-blue-300 font-medium">Funcionalidad en Desarrollo</span>
            </div>
            <p className="text-blue-200 text-sm">
              La gestión avanzada de supervisores y redistribución automática de cargas estará disponible próximamente.
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default GestionAsignaciones;
