/**
 * Componente para las pestañas de navegación entre secciones
 */
const SectionTabs = ({ sections, activeSection, onSectionChange }) => {
  return (
    <div className="flex space-x-4 border-b border-gray-700">
      {sections.map((section) => (
        <button
          key={section.id}
          onClick={() => onSectionChange(section.id)}
          className={`pb-4 px-2 font-medium transition-colors ${
            activeSection === section.id
              ? 'text-blue-400 border-b-2 border-blue-400'
              : 'text-gray-400 hover:text-white'
          }`}
        >
          {section.name}
        </button>
      ))}
    </div>
  );
};

export default SectionTabs;
