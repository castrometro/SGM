// src/pages/HerramientasContabilidadModuleDocs.jsx
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
 * Página de documentación del módulo Herramientas de Contabilidad
 */
const HerramientasContabilidadModuleDocs = () => {
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
                <h1 className="text-xl font-bold">Módulo Herramientas de Contabilidad</h1>
                <p className="text-sm text-gray-400">Documentación Técnica</p>
              </div>
            </div>
            <Link
              to="/dev/modules/herramientas-contabilidad/demo"
              className="px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg text-sm font-medium transition-colors"
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
                        ? 'bg-purple-600 text-white'
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
                  <h2 className="text-3xl font-bold mb-4">🧮 Módulo Herramientas de Contabilidad</h2>
                  <p className="text-gray-300 text-lg">
                    Centro de utilidades y recursos especializados para la gestión integral de contabilidad.
                  </p>

                  <div className="bg-gray-900 p-6 rounded-lg">
                    <h3 className="text-xl font-semibold mb-3">✨ Características</h3>
                    <ul className="space-y-2 text-gray-300">
                      <li className="flex items-start gap-2">
                        <span className="text-green-400 mt-1">✓</span>
                        <span>Organización por 4 categorías (General, Contabilidad, Reportes, Integraciones)</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-green-400 mt-1">✓</span>
                        <span>17 herramientas configuradas especializadas en contabilidad</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-green-400 mt-1">✓</span>
                        <span>Sistema de estados (Disponible, Beta, Próximamente)</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-green-400 mt-1">✓</span>
                        <span>Estadísticas en tiempo real</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-green-400 mt-1">✓</span>
                        <span>Tabs animados con Framer Motion</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-green-400 mt-1">✓</span>
                        <span>Responsive y consistente</span>
                      </li>
                    </ul>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-purple-900/30 border border-purple-700 p-4 rounded-lg">
                      <div className="text-2xl font-bold text-purple-400">7</div>
                      <div className="text-sm text-gray-400">Archivos</div>
                    </div>
                    <div className="bg-purple-900/30 border border-purple-700 p-4 rounded-lg">
                      <div className="text-2xl font-bold text-purple-400">17</div>
                      <div className="text-sm text-gray-400">Herramientas</div>
                    </div>
                  </div>
                </div>
              )}

              {activeSection === 'structure' && (
                <div className="space-y-6">
                  <h2 className="text-3xl font-bold mb-4">🏗️ Estructura del Módulo</h2>
                  
                  <div className="bg-gray-900 p-6 rounded-lg font-mono text-sm">
                    <pre className="text-gray-300">
{`contabilidad/herramientas/
├── components/
│   ├── ToolCard.jsx
│   ├── CategoryTabs.jsx
│   └── InfoBanner.jsx
├── constants/
│   └── herramientas.constants.js
├── pages/
│   └── HerramientasContabilidadPage.jsx
├── utils/
│   └── toolsConfig.js
└── index.js`}
                    </pre>
                  </div>
                </div>
              )}

              {activeSection === 'tools' && (
                <div className="space-y-6">
                  <h2 className="text-3xl font-bold mb-4">🛠️ Herramientas Disponibles</h2>

                  <div className="space-y-4">
                    <div className="bg-gray-900 p-4 rounded-lg">
                      <h4 className="font-semibold text-purple-400 mb-2">Categoría: General (3)</h4>
                      <ul className="text-sm text-gray-300 space-y-1 list-disc list-inside">
                        <li>Captura Masiva de Gastos ✅</li>
                        <li>Exportar Datos Contables</li>
                        <li>Importar Plan de Cuentas</li>
                      </ul>
                    </div>

                    <div className="bg-gray-900 p-4 rounded-lg">
                      <h4 className="font-semibold text-purple-400 mb-2">Categoría: Gestión Contable (5)</h4>
                      <ul className="text-sm text-gray-300 space-y-1 list-disc list-inside">
                        <li>Clasificación de Cuentas</li>
                        <li>Análisis de Libro Mayor</li>
                        <li>Conciliación Bancaria</li>
                        <li>Balance de Comprobación</li>
                        <li>Gestión de Asientos</li>
                      </ul>
                    </div>

                    <div className="bg-gray-900 p-4 rounded-lg">
                      <h4 className="font-semibold text-purple-400 mb-2">Categoría: Reportes (6)</h4>
                      <ul className="text-sm text-gray-300 space-y-1 list-disc list-inside">
                        <li>Dashboard Contable (beta)</li>
                        <li>Estados Financieros</li>
                        <li>Análisis de Variaciones</li>
                        <li>Reportes Personalizados</li>
                        <li>Análisis por Centro de Costo</li>
                        <li>Gestión de Analistas</li>
                      </ul>
                    </div>

                    <div className="bg-gray-900 p-4 rounded-lg">
                      <h4 className="font-semibold text-purple-400 mb-2">Categoría: Integraciones (3)</h4>
                      <ul className="text-sm text-gray-300 space-y-1 list-disc list-inside">
                        <li>Integración SII</li>
                        <li>Integración ERP</li>
                        <li>API Bancaria</li>
                      </ul>
                    </div>
                  </div>
                </div>
              )}

              {activeSection === 'components' && (
                <div className="space-y-6">
                  <h2 className="text-3xl font-bold mb-4">🧩 Componentes</h2>
                  <p className="text-gray-300">
                    Los mismos componentes base que Herramientas de Nómina: ToolCard, CategoryTabs e InfoBanner,
                    pero con tema purple para Contabilidad.
                  </p>
                </div>
              )}

              {activeSection === 'usage' && (
                <div className="space-y-6">
                  <h2 className="text-3xl font-bold mb-4">💡 Uso del Módulo</h2>
                  <pre className="bg-gray-900 p-6 rounded-lg text-green-400 text-sm">
{`import { HerramientasContabilidadPage } from './modules/contabilidad/herramientas';

<Route path="/menu/contabilidad/tools" element={<HerramientasContabilidadPage />} />`}
                  </pre>
                </div>
              )}

              {activeSection === 'extension' && (
                <div className="space-y-6">
                  <h2 className="text-3xl font-bold mb-4">➕ Agregar Nueva Herramienta</h2>
                  <pre className="bg-gray-900 p-6 rounded-lg text-green-400 text-sm">
{`// En toolsConfig.js
export const CONTABILIDAD_TOOLS = [
  // ... existentes
  {
    title: "Nueva Herramienta",
    description: "Descripción",
    icon: MyIcon,
    color: TOOL_COLORS.blue,
    path: "/ruta",
    status: TOOL_STATUS.AVAILABLE
  }
];`}
                  </pre>
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

export default HerramientasContabilidadModuleDocs;
