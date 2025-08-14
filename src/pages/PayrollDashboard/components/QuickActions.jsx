import React from 'react';
import { Activity, Users, TrendingUp } from 'lucide-react';

const QuickActions = ({ userType, areaActiva }) => {
  const getActionsForUser = () => {
    switch (userType) {
      case 'gerente':
        return [
          {
            title: "Ver Todos los Empleados",
            description: "Gestión completa de empleados",
            icon: Users,
            color: "#10B981",
            action: "employees"
          },
          {
            title: "Procesar Nómina",
            description: "Iniciar procesamiento masivo",
            icon: Activity,
            color: "#3B82F6", 
            action: "process"
          },
          {
            title: "Reportes Ejecutivos",
            description: "Análisis y métricas avanzadas",
            icon: TrendingUp,
            color: "#8B5CF6",
            action: "reports"
          }
        ];
      
      case 'supervisor':
        return [
          {
            title: "Supervisar Nóminas",
            description: "Revisar y aprobar nóminas pendientes",
            icon: Activity,
            color: "#F59E0B",
            action: "supervision"
          },
          {
            title: "Reportes de Área",
            description: "Informes de tu área supervisada",
            icon: TrendingUp,
            color: "#059669",
            action: "area-reports"
          }
        ];
      
      case 'analista':
        return [
          {
            title: "Procesar Nómina",
            description: "Trabajar en nóminas asignadas",
            icon: Activity,
            color: "#3B82F6",
            action: "process-assigned"
          }
        ];
      
      default:
        return [];
    }
  };

  const actions = getActionsForUser();

  const handleActionClick = (action) => {
    // TODO: Implementar navegación según la acción
    console.log(`Acción clicked: ${action} para ${userType} en área ${areaActiva}`);
    
    switch (action) {
      case 'employees':
        // Navegar a gestión de empleados
        break;
      case 'process':
      case 'process-assigned':
        // Navegar a procesamiento de nómina
        break;
      case 'supervision':
        // Navegar a supervisión
        break;
      case 'reports':
      case 'area-reports':
        // Navegar a reportes
        break;
      default:
        break;
    }
  };

  if (actions.length === 0) {
    return null;
  }

  return (
    <div className="bg-gray-800/50 rounded-lg p-6">
      <h3 className="text-white font-semibold text-lg mb-4">
        Acciones Rápidas
      </h3>
      
      <div className="grid gap-4">
        {actions.map((action, index) => {
          const IconComponent = action.icon;
          
          return (
            <button
              key={index}
              onClick={() => handleActionClick(action.action)}
              className="flex items-center gap-4 p-4 bg-gray-700/50 rounded-lg hover:bg-gray-700 transition-colors text-left group"
            >
              <div 
                className="p-2 rounded-lg flex-shrink-0"
                style={{ backgroundColor: `${action.color}20` }}
              >
                <IconComponent 
                  size={20} 
                  style={{ color: action.color }}
                />
              </div>
              
              <div className="flex-1">
                <h4 className="text-white font-medium group-hover:text-blue-400 transition-colors">
                  {action.title}
                </h4>
                <p className="text-gray-400 text-sm">
                  {action.description}
                </p>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
};

export default QuickActions;
