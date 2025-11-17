import { motion } from "framer-motion";

/**
 * CategoryTabs - Pestañas para navegar entre categorías de herramientas
 * 
 * @param {Array} categories - Array de categorías {id, name}
 * @param {string} activeCategory - ID de la categoría activa
 * @param {Function} onCategoryChange - Callback al cambiar de categoría
 */
const CategoryTabs = ({ categories, activeCategory, onCategoryChange }) => {
  return (
    <div className="flex space-x-4 border-b border-gray-700 overflow-x-auto pb-px">
      {categories.map((category) => (
        <button
          key={category.id}
          onClick={() => onCategoryChange(category.id)}
          className="relative pb-4 px-2 font-medium transition-colors whitespace-nowrap"
        >
          <span className={`${
            activeCategory === category.id
              ? 'text-teal-400'
              : 'text-gray-400 hover:text-white'
          }`}>
            {category.name}
          </span>
          
          {activeCategory === category.id && (
            <motion.div
              layoutId="activeTab"
              className="absolute bottom-0 left-0 right-0 h-0.5 bg-teal-400"
              transition={{ type: "spring", stiffness: 380, damping: 30 }}
            />
          )}
        </button>
      ))}
    </div>
  );
};

export default CategoryTabs;
