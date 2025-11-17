// src/pages/HerramientasNominaModuleDocs.jsx
import { Link } from 'react-router-dom';
import { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  FiArrowLeft, 
  FiBook,
  FiCode,
  FiLayers,
  FiPackage,
  FiSettings,
  FiFileText
} from 'react-icons/fi';
import { DevModulesButton } from '../modules/shared/auth';

/**
 * Página de documentación del módulo Herramientas de Nómina
 */
const HerramientasNominaModuleDocs = () => {
  const [activeSection, setActiveSection] = useState('overview');

  const sections = [
    { id: 'overview', label: 'Descripción General', icon: FiBook },
    { id: 'structure', label: 'Estructura', icon: FiLayers },
    { id: 'components', label: 'Componentes', icon: FiPackage },
    { id: 'usage', label: 'Uso', icon: FiCode },
    { id: 'tools', label: 'Herramientas', icon: FiSettings },
    { id: 'extension', label: 'Extensión', icon: FiFileText }
  ];

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700 sticky top-0 z-40">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link
                to="/dev/modules"
                className="inline-flex items-center gap-2 px-3 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm font-medium transition-colors"
              >
                <FiArrowLeft size={16} />
                Volver
              </Link>
              <div>
                <h1 className="text-xl font-bold">Módulo Herramientas de Nómina</h1>
                <p className="text-sm text-gray-400">Documentación Técnica</p>
              </div>
            </div>
            <Link
              to="/dev/modules/herramientas-nomina/demo"
              className="px-4 py-2 bg-teal-600 hover:bg-teal-700 rounded-lg text-sm font-medium transition-colors"
            >
              Ver Demo
            </Link>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Sidebar */}
          <div className="lg:col-span-1">
            <nav className="sticky top-24 space-y-1">
              {sections.map((section) => {
                const Icon = section.icon;
                return (
                  <button
                    key={section.id}
                    onClick={() => setActiveSection(section.id)}
                    className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium transition-all ${
                      activeSection === section.id
                        ? 'bg-teal-600 text-white'
                        : 'text-gray-400 hover:text-white hover:bg-gray-800'
                    }`}
                  >
                    <Icon size={18} />
                    {section.label}
                  </button>
                );
              })}
            </nav>
          </div>

          {/* Content */}
          <div className="lg:col-span-3">
            <motion.div
              key={activeSection}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
              className="bg-gray-800 rounded-lg p-8"
            >
              {activeSection === 'overview' && (
                <div className="space-y-6">
                  <h2 className="text-3xl font-bold mb-4">🛠️ Módulo Herramientas de Nómina</h2>
                  <p className="text-gray-300 text-lg">
                    Centro de utilidades y recursos especializados para la gestión integral de nómina.
                  </p>

                  <div className="bg-gray-900 p-6 rounded-lg">
                    <h3 className="text-xl font-semibold mb-3">✨ Características</h3>
                    <ul className="space-y-2 text-gray-300">
                      <li className="flex items-start gap-2">
                        <span className="text-green-400 mt-1">✓</span>
                        <span>Organización por 4 categorías (General, Nómina, Reportes, Integraciones)</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-green-400 mt-1">✓</span>
                        <span>Sistema de estados (Disponible, Beta, Próximamente, Mantenimiento)</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-green-400 mt-1">✓</span>
                        <span>Cards interactivos con animaciones escalonadas</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-green-400 mt-1">✓</span>
                        <span>Estadísticas en tiempo real de herramientas</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-green-400 mt-1">✓</span>
                        <span>Navegación fluida entre categorías con tabs animados</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-green-400 mt-1">✓</span>
                        <span>Responsive y consistente con el sistema</span>
                      </li>
                    </ul>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-teal-900/30 border border-teal-700 p-4 rounded-lg">
                      <div className="text-2xl font-bold text-teal-400">7</div>
                      <div className="text-sm text-gray-400">Archivos</div>
                    </div>
                    <div className="bg-teal-900/30 border border-teal-700 p-4 rounded-lg">
                      <div className="text-2xl font-bold text-teal-400">15</div>
                      <div className="text-sm text-gray-400">Herramientas configuradas</div>
                    </div>
                  </div>
                </div>
              )}

              {activeSection === 'structure' && (
                <div className="space-y-6">
                  <h2 className="text-3xl font-bold mb-4">🏗️ Estructura del Módulo</h2>
                  
                  <div className="bg-gray-900 p-6 rounded-lg font-mono text-sm">
                    <pre className="text-gray-300">
{`nomina/herramientas/
├── components/
│   ├── ToolCard.jsx           # Card de herramienta
│   ├── CategoryTabs.jsx       # Tabs de categorías
│   └── InfoBanner.jsx         # Banner informativo
├── constants/
│   └── herramientas.constants.js  # Constantes
├── pages/
│   └── HerramientasNominaPage.jsx  # Página principal
├── utils/
│   └── toolsConfig.js         # Configuración
├── index.js                   # Exports públicos
└── README.md                  # Documentación`}
                    </pre>
                  </div>
                </div>
              )}

              {activeSection === 'components' && (
                <div className="space-y-6">
                  <h2 className="text-3xl font-bold mb-4">🧩 Componentes</h2>

                  <div className="space-y-6">
                    <div className="bg-gray-900 p-6 rounded-lg">
                      <h3 className="text-xl font-semibold text-teal-400 mb-3">ToolCard</h3>
                      <p className="text-gray-300 mb-4">Card individual para cada herramienta con animaciones</p>
                      
                      <div className="bg-gray-800 p-4 rounded-lg mb-4">
                        <p className="text-sm text-gray-400 mb-2">Props:</p>
                        <ul className="text-sm text-gray-300 space-y-1">
                          <li><code className="text-green-400">title</code>: string</li>
                          <li><code className="text-green-400">description</code>: string</li>
                          <li><code className="text-green-400">icon</code>: Component (Lucide)</li>
                          <li><code className="text-green-400">color</code>: string</li>
                          <li><code className="text-green-400">onClick</code>: Function</li>
                          <li><code className="text-green-400">status</code>: string</li>
                          <li><code className="text-green-400">index</code>: number</li>
                        </ul>
                      </div>
                    </div>

                    <div className="bg-gray-900 p-6 rounded-lg">
                      <h3 className="text-xl font-semibold text-teal-400 mb-3">CategoryTabs</h3>
                      <p className="text-gray-300 mb-4">Navegación con tabs animados</p>
                      
                      <div className="bg-gray-800 p-4 rounded-lg">
                        <p className="text-sm text-gray-400 mb-2">Props:</p>
                        <ul className="text-sm text-gray-300 space-y-1">
                          <li><code className="text-green-400">categories</code>: Array</li>
                          <li><code className="text-green-400">activeCategory</code>: string</li>
                          <li><code className="text-green-400">onCategoryChange</code>: Function</li>
                        </ul>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {activeSection === 'usage' && (
                <div className="space-y-6">
                  <h2 className="text-3xl font-bold mb-4">💡 Uso del Módulo</h2>

                  <div className="bg-gray-900 p-6 rounded-lg">
                    <h3 className="text-xl font-semibold mb-4">1. Importar la página</h3>
                    <pre className="bg-gray-800 p-4 rounded-lg text-green-400 text-sm overflow-x-auto">
{`import { HerramientasNominaPage } from './modules/nomina/herramientas';

<Route path="/menu/nomina/tools" element={<HerramientasNominaPage />} />`}
                    </pre>
                  </div>

                  <div className="bg-gray-900 p-6 rounded-lg">
                    <h3 className="text-xl font-semibold mb-4">2. Usar componentes individuales</h3>
                    <pre className="bg-gray-800 p-4 rounded-lg text-green-400 text-sm overflow-x-auto">
{`import { ToolCard, CategoryTabs } from './modules/nomina/herramientas';

<ToolCard
  title="Mi Herramienta"
  description="Descripción"
  icon={MyIcon}
  color="bg-blue-600"
  status="available"
  onClick={() => navigate('/ruta')}
/>`}
                    </pre>
                  </div>
                </div>
              )}

              {activeSection === 'tools' && (
                <div className="space-y-6">
                  <h2 className="text-3xl font-bold mb-4">🛠️ Herramientas Disponibles</h2>

                  <div className="space-y-4">
                    <div className="bg-gray-900 p-4 rounded-lg">
                      <h4 className="font-semibold text-teal-400 mb-2">Categoría: General</h4>
                      <ul className="text-sm text-gray-300 space-y-1 list-disc list-inside">
                        <li>Captura Masiva de Gastos ✅</li>
                        <li>Exportar Datos (próximamente)</li>
                        <li>Importar Empleados (próximamente)</li>
                      </ul>
                    </div>

                    <div className="bg-gray-900 p-4 rounded-lg">
                      <h4 className="font-semibold text-teal-400 mb-2">Categoría: Nómina</h4>
                      <ul className="text-sm text-gray-300 space-y-1 list-disc list-inside">
                        <li>Libro de Remuneraciones</li>
                        <li>Cálculo de Finiquitos</li>
                        <li>Gestión de Incidencias</li>
                        <li>Calendario Laboral</li>
                      </ul>
                    </div>

                    <div className="bg-gray-900 p-4 rounded-lg">
                      <h4 className="font-semibold text-teal-400 mb-2">Categoría: Reportes</h4>
                      <ul className="text-sm text-gray-300 space-y-1 list-disc list-inside">
                        <li>Dashboard de Nómina (beta)</li>
                        <li>Reportes Personalizados</li>
                        <li>Análisis de Costos</li>
                        <li>Gestión de Analistas</li>
                      </ul>
                    </div>

                    <div className="bg-gray-900 p-4 rounded-lg">
                      <h4 className="font-semibold text-teal-400 mb-2">Categoría: Integraciones</h4>
                      <ul className="text-sm text-gray-300 space-y-1 list-disc list-inside">
                        <li>Integración Previred</li>
                        <li>Integración SII</li>
                      </ul>
                    </div>
                  </div>
                </div>
              )}

              {activeSection === 'extension' && (
                <div className="space-y-6">
                  <h2 className="text-3xl font-bold mb-4">➕ Agregar Nueva Herramienta</h2>

                  <div className="bg-gray-900 p-6 rounded-lg">
                    <h3 className="text-xl font-semibold mb-4">En toolsConfig.js</h3>
                    <pre className="bg-gray-800 p-4 rounded-lg text-green-400 text-sm overflow-x-auto">
{`import { MyIcon } from 'lucide-react';

export const NOMINA_TOOLS = [
  // ... herramientas existentes
  {
    title: "Nueva Herramienta",
    description: "Descripción detallada",
    icon: MyIcon,
    color: TOOL_COLORS.blue,
    path: "/ruta/herramienta",
    status: TOOL_STATUS.AVAILABLE
  }
];`}
                    </pre>
                  </div>

                  <div className="bg-yellow-900/20 border border-yellow-700 p-4 rounded-lg">
                    <h4 className="font-semibold text-yellow-400 mb-2">💡 Tip</h4>
                    <p className="text-sm text-gray-300">
                      Las herramientas se agrupan automáticamente por categoría. Solo agrega el objeto
                      al array correspondiente y aparecerá en la UI.
                    </p>
                  </div>
                </div>
              )}
            </motion.div>
          </div>
        </div>
      </div>

      <DevModulesButton />
    </div>
  );
};

export default HerramientasNominaModuleDocs;
