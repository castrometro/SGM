import ToolCard from "./ToolCard";

/**
 * Componente que renderiza el grid de herramientas
 * para la sección activa
 */
const ToolsGrid = ({ sections, activeSection }) => {
  const currentSection = sections.find(s => s.id === activeSection);
  
  if (!currentSection) {
    return (
      <div className="text-center text-gray-400 py-8">
        <p>Sección no encontrada.</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {currentSection.tools.map((tool, index) => (
        <ToolCard
          key={index}
          title={tool.title}
          description={tool.description}
          icon={tool.icon}
          color={tool.color}
          onClick={tool.onClick}
          disabled={tool.disabled}
        />
      ))}
    </div>
  );
};

export default ToolsGrid;
