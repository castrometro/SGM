import { useState } from "react";
import { useToolsOptions } from "./hooks/useToolsOptions";
import SectionTabs from "./components/SectionTabs";
import ToolsGrid from "./components/ToolsGrid";
import InfoSection from "./components/InfoSection";

/**
 * Página principal de herramientas
 * Sistema dinámico de pestañas con herramientas personalizadas por usuario y área
 */
const Tools = () => {
  // Obtener usuario del localStorage
  const usuario = JSON.parse(localStorage.getItem("usuario"));
  
  // Usar hook dinámico para obtener herramientas personalizadas
  const { sections } = useToolsOptions(usuario);
  
  // Estado para sección activa (por defecto la primera disponible)
  const [activeSection, setActiveSection] = useState(
    sections.length > 0 ? sections[0].id : "general"
  );

  // Si no hay secciones disponibles, mostrar mensaje
  if (!sections || sections.length === 0) {
    return (
      <div className="text-white space-y-6">
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <h1 className="text-3xl font-bold mb-2">Herramientas</h1>
            <p className="text-gray-400">No hay herramientas disponibles para tu perfil</p>
          </div>
        </div>
        <InfoSection />
      </div>
    );
  }

  return (
    <div className="text-white space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <h1 className="text-3xl font-bold mb-2">Herramientas</h1>
          <p className="text-gray-400">Utilidades y recursos personalizados para tu perfil</p>
          {usuario && (
            <p className="text-sm text-blue-400 mt-1">
              Perfil: {usuario.tipo_usuario} 
              {usuario.areas?.length > 0 && ` • Áreas: ${usuario.areas.map(a => a.nombre).join(', ')}`}
            </p>
          )}
        </div>
      </div>

      {/* Navigation Tabs */}
      <SectionTabs 
        sections={sections}
        activeSection={activeSection}
        onSectionChange={setActiveSection}
      />

      {/* Tools Grid */}
      <ToolsGrid 
        sections={sections}
        activeSection={activeSection}
      />

      {/* Info Section */}
      <InfoSection />
    </div>
  );
};

export default Tools;
