import OpcionMenu from "../components/OpcionMenu";
import {
  FolderKanban,
  Wrench,
  ShieldCheck,
  UserCog,
  FileText,
  BarChart3,
  Activity,
  Users,
  Settings,
  Database,
  Monitor
} from "lucide-react";

const MenuUsuario = () => {
  const usuario = JSON.parse(localStorage.getItem("usuario"));

  const opciones = [];

  if (usuario.tipo_usuario === "analista") {
    opciones.push(
      { label: "Clientes", descripcion: "Ver y trabajar con tus clientes asignados", icon: FolderKanban, color: "#4F46E5", path: "/menu/clientes" },
      { label: "Herramientas", descripcion: "Acceso a recursos y utilidades", icon: Wrench, color: "#10B981", path: "/menu/tools" }
    );
  }

  if (usuario.tipo_usuario === "supervisor") {
    opciones.push(
      { label: "Mis Analistas", descripcion: "Gestión y supervisión de analistas asignados", icon: Users, color: "#EC4899", path: "/menu/mis-analistas" },
      { label: "Clientes", descripcion: "Ver y validar clientes asignados", icon: FolderKanban, color: "#4F46E5", path: "/menu/clientes" },
      { label: "Validaciones", descripcion: "Revisar y aprobar cierres", icon: ShieldCheck, color: "#F59E0B", path: "/menu/validaciones" }
    );
  }

  if (usuario.tipo_usuario === "gerente") {
    // Obtener las áreas del gerente para mostrar opciones relevantes
    const areas = usuario.areas || [];
    const tieneContabilidad = areas.some(area => area.nombre === "Contabilidad");
    const tieneNomina = areas.some(area => area.nombre === "Nomina");
    
    opciones.push(
      { label: "Clientes", descripcion: "Visión general de todos los clientes", icon: FolderKanban, color: "#4F46E5", path: "/menu/clientes" }
    );
    
    // Dashboard del Gerente - Nuevo
    opciones.push({
      label: "Dashboard Gerencial", 
      descripcion: "Dashboard avanzado con métricas, alertas y reportes", 
      icon: Activity, 
      color: "#EF4444", 
      path: "/menu/dashboard-gerente"
    });
    
    // Analytics específicos por área
    if (tieneContabilidad || tieneNomina) {
      let descripcionAnalytics = "KPIs y métricas de ";
      if (tieneContabilidad && tieneNomina) {
        descripcionAnalytics += "contabilidad y nómina";
      } else if (tieneContabilidad) {
        descripcionAnalytics += "contabilidad y cierres";
      } else if (tieneNomina) {
        descripcionAnalytics += "nómina y remuneraciones";
      }
      
      opciones.push({
        label: "Analytics de Performance", 
        descripcion: descripcionAnalytics, 
        icon: BarChart3, 
        color: "#8B5CF6", 
        path: "/menu/analytics"
      });
    }
    
    // Funcionalidades específicas de Contabilidad para Gerentes
    if (tieneContabilidad) {
      opciones.push(
        { label: "Logs y Actividad", descripcion: "Auditoría y logs de actividades de usuarios", icon: FileText, color: "#F97316", path: "/menu/gerente/logs-actividad" },
        { label: "Estados de Cierres", descripcion: "Monitoreo en tiempo real de estados de cierres", icon: Monitor, color: "#06B6D4", path: "/menu/gerente/estados-cierres" },
        { label: "Cache Redis", descripcion: "Estado y gestión del cache Redis de cierres", icon: Database, color: "#10B981", path: "/menu/gerente/cache-redis" }
      );
    }
    
    opciones.push(
      { label: "Gestión de Analistas", descripcion: "Gestión de analistas y asignaciones", icon: UserCog, color: "#EC4899", path: "/menu/analistas" },
      { label: "Herramientas", descripcion: "Utilidades del sistema", icon: Wrench, color: "#10B981", path: "/menu/tools" }
    );

    // Herramientas avanzadas de sistema para contabilidad
    if (tieneContabilidad) {
      opciones.push({
        label: "Admin Sistema", 
        descripcion: "Creación de usuarios, clientes y herramientas avanzadas", 
        icon: Settings, 
        color: "#DC2626", 
        path: "/menu/gerente/admin-sistema"
      });
    }
  }

  // Variable para controlar la transparencia de las tarjetas
  const cardOpacity = 0.9; // Cambia este valor entre 0.1 y 1.0

  return (
    <div className="text-white">
      <h1 className="text-3xl font-bold mb-6 animate-fade-in">Menú Principal</h1>
      
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {opciones.map((op, index) => (
          <div
            key={op.label}
            className="animate-slide-up"
            style={{
              animationDelay: `${index * 100}ms`,
              opacity: cardOpacity,
              transition: 'opacity 0.2s ease'
            }}
            onMouseEnter={(e) => e.currentTarget.style.opacity = '1'}
            onMouseLeave={(e) => e.currentTarget.style.opacity = cardOpacity}
          >
            <OpcionMenu {...op} />
          </div>
        ))}
      </div>
      
      <style>
        {`
          @keyframes fade-in {
            from {
              opacity: 0;
              transform: translateY(-10px);
            }
            to {
              opacity: 1;
              transform: translateY(0);
            }
          }
          
          @keyframes slide-up {
            from {
              opacity: 0;
              transform: translateY(20px);
            }
            to {
              opacity: 1;
              transform: translateY(0);
            }
          }
          
          .animate-fade-in {
            animation: fade-in 0.8s ease-out;
          }
          
          .animate-slide-up {
            animation: slide-up 0.6s ease-out both;
          }
        `}
      </style>
    </div>
  );
};

export default MenuUsuario;
