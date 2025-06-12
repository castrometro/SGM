import OpcionMenu from "../components/OpcionMenu";
import {
  FolderKanban,
  Wrench,
  ShieldCheck,
  UserCog,
  FileText,
  BarChart3
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

  if (usuario.tipo_usuario === "senior") {
    opciones.push(
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
    
    opciones.push(
      { label: "Gestión de Analistas", descripcion: "Gestión de analistas y asignaciones", icon: UserCog, color: "#EC4899", path: "/menu/analistas" },
      { label: "Herramientas", descripcion: "Utilidades del sistema", icon: Wrench, color: "#10B981", path: "/menu/tools" }
    );
  }

  return (
    <div className="text-white">
      <h1 className="text-3xl font-bold mb-6">Menú Principal</h1>
      
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {opciones.map((op) => (
          <OpcionMenu key={op.label} {...op} />
        ))}
      </div>
    </div>
  );
};

export default MenuUsuario;
