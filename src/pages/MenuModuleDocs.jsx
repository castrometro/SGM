// src/pages/MenuModuleDocs.jsx
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
 * Página de documentación del módulo Menu
 */
const MenuModuleDocs = () => {
  const [activeSection, setActiveSection] = useState('overview');

  const sections = [
    { id: 'overview', label: 'Descripción General', icon: FiBook },
    { id: 'structure', label: 'Estructura', icon: FiLayers },
    { id: 'components', label: 'Componentes', icon: FiPackage },
    { id: 'usage', label: 'Uso', icon: FiCode },
    { id: 'configuration', label: 'Configuración', icon: FiSettings },
    { id: 'api', label: 'API', icon: FiFileText }
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
                <h1 className="text-xl font-bold">Módulo Menu</h1>
                <p className="text-sm text-gray-400">Documentación Técnica</p>
              </div>
            </div>
            <Link
              to="/dev/modules/menu/demo"
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
                  <h2 className="text-3xl font-bold mb-4">📋 Módulo Menu</h2>
                  <p className="text-gray-300 text-lg">
                    Módulo completo de menú principal con opciones dinámicas según rol y área de negocio.
                  </p>

                  <div className="bg-gray-900 p-6 rounded-lg">
                    <h3 className="text-xl font-semibold mb-3">✨ Características</h3>
                    <ul className="space-y-2 text-gray-300">
                      <li className="flex items-start gap-2">
                        <span className="text-green-400 mt-1">✓</span>
                        <span>Opciones dinámicas por tipo de usuario (Analista, Supervisor, Gerente)</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-green-400 mt-1">✓</span>
                        <span>Separación por áreas de negocio (Contabilidad/Nómina)</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-green-400 mt-1">✓</span>
                        <span>Animaciones escalonadas con Framer Motion</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-green-400 mt-1">✓</span>
                        <span>Vista responsive con grid adaptativo</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-green-400 mt-1">✓</span>
                        <span>Configuración centralizada y mantenible</span>
                      </li>
                    </ul>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-indigo-900/30 border border-indigo-700 p-4 rounded-lg">
                      <div className="text-2xl font-bold text-indigo-400">7</div>
                      <div className="text-sm text-gray-400">Archivos</div>
                    </div>
                    <div className="bg-purple-900/30 border border-purple-700 p-4 rounded-lg">
                      <div className="text-2xl font-bold text-purple-400">~600</div>
                      <div className="text-sm text-gray-400">Líneas de código</div>
                    </div>
                  </div>
                </div>
              )}

              {activeSection === 'structure' && (
                <div className="space-y-6">
                  <h2 className="text-3xl font-bold mb-4">🏗️ Estructura del Módulo</h2>
                  
                  <div className="bg-gray-900 p-6 rounded-lg font-mono text-sm">
                    <pre className="text-gray-300">
{`nomina/menu/  (o contabilidad/menu/)
├── components/
│   └── MenuCard.jsx           # Card individual de opción
├── constants/
│   └── menu.constants.js      # Constantes y configuración
├── pages/
│   └── MenuUsuarioPage.jsx    # Página principal
├── router/
│   └── menu.routes.jsx        # Rutas del módulo
├── utils/
│   └── menuConfig.js          # Lógica de opciones
├── index.js                   # Exports públicos
└── README.md                  # Documentación`}
                    </pre>
                  </div>

                  <div className="space-y-4">
                    <h3 className="text-xl font-semibold">📁 Descripción de Carpetas</h3>
                    <div className="space-y-3">
                      <div className="bg-gray-900 p-4 rounded-lg">
                        <h4 className="font-semibold text-purple-400 mb-2">components/</h4>
                        <p className="text-gray-300 text-sm">
                          Componentes React reutilizables del menú (MenuCard para cada opción)
                        </p>
                      </div>
                      <div className="bg-gray-900 p-4 rounded-lg">
                        <h4 className="font-semibold text-purple-400 mb-2">constants/</h4>
                        <p className="text-gray-300 text-sm">
                          Constantes: tipos de usuario, áreas, colores, configuración de animaciones
                        </p>
                      </div>
                      <div className="bg-gray-900 p-4 rounded-lg">
                        <h4 className="font-semibold text-purple-400 mb-2">utils/</h4>
                        <p className="text-gray-300 text-sm">
                          getUserMenuOptions(), hasArea() - Lógica de configuración de opciones
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {activeSection === 'components' && (
                <div className="space-y-6">
                  <h2 className="text-3xl font-bold mb-4">🧩 Componentes</h2>

                  <div className="space-y-6">
                    <div className="bg-gray-900 p-6 rounded-lg">
                      <h3 className="text-xl font-semibold text-purple-400 mb-3">MenuUsuarioPage</h3>
                      <p className="text-gray-300 mb-4">Página principal que renderiza el grid de opciones</p>
                      
                      <div className="bg-gray-800 p-4 rounded-lg">
                        <p className="text-sm text-gray-400 mb-2">Props:</p>
                        <code className="text-green-400 text-sm">Ninguna (obtiene usuario del contexto)</code>
                      </div>
                    </div>

                    <div className="bg-gray-900 p-6 rounded-lg">
                      <h3 className="text-xl font-semibold text-purple-400 mb-3">MenuCard</h3>
                      <p className="text-gray-300 mb-4">Card individual de opción con animaciones</p>
                      
                      <div className="bg-gray-800 p-4 rounded-lg space-y-2">
                        <p className="text-sm text-gray-400">Props:</p>
                        <div className="font-mono text-sm space-y-1">
                          <div><span className="text-blue-400">label</span>: <span className="text-green-400">string</span> - Título de la opción</div>
                          <div><span className="text-blue-400">descripcion</span>: <span className="text-green-400">string</span> - Descripción</div>
                          <div><span className="text-blue-400">icon</span>: <span className="text-green-400">LucideIcon</span> - Icono</div>
                          <div><span className="text-blue-400">color</span>: <span className="text-green-400">string</span> - Color hex</div>
                          <div><span className="text-blue-400">path</span>: <span className="text-green-400">string</span> - Ruta de navegación</div>
                          <div><span className="text-blue-400">index</span>: <span className="text-green-400">number</span> - Para animación</div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {activeSection === 'usage' && (
                <div className="space-y-6">
                  <h2 className="text-3xl font-bold mb-4">💻 Uso</h2>

                  <div className="space-y-6">
                    <div>
                      <h3 className="text-xl font-semibold mb-3">Importación Básica</h3>
                      <div className="bg-gray-900 p-4 rounded-lg">
                        <pre className="text-sm text-gray-300 font-mono">
{`import { MenuUsuarioPage } from '@/modules/contabilidad/menu';
// o
import { MenuUsuarioPage } from '@/modules/nomina/menu';`}
                        </pre>
                      </div>
                    </div>

                    <div>
                      <h3 className="text-xl font-semibold mb-3">En el Router</h3>
                      <div className="bg-gray-900 p-4 rounded-lg">
                        <pre className="text-sm text-gray-300 font-mono">
{`<Route 
  path="/contabilidad/menu" 
  element={<MenuUsuarioPage />} 
/>`}
                        </pre>
                      </div>
                    </div>

                    <div>
                      <h3 className="text-xl font-semibold mb-3">Importar Componentes Individuales</h3>
                      <div className="bg-gray-900 p-4 rounded-lg">
                        <pre className="text-sm text-gray-300 font-mono">
{`import { 
  MenuCard,
  getUserMenuOptions,
  hasArea
} from '@/modules/contabilidad/menu';`}
                        </pre>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {activeSection === 'configuration' && (
                <div className="space-y-6">
                  <h2 className="text-3xl font-bold mb-4">⚙️ Configuración</h2>

                  <div className="space-y-6">
                    <div className="bg-gray-900 p-6 rounded-lg">
                      <h3 className="text-xl font-semibold text-purple-400 mb-3">Opciones por Tipo de Usuario</h3>
                      <p className="text-gray-300 mb-4">
                        Las opciones se configuran en <code className="bg-gray-800 px-2 py-1 rounded text-sm">utils/menuConfig.js</code>
                      </p>
                      
                      <div className="space-y-3 text-sm">
                        <div className="bg-gray-800 p-3 rounded">
                          <span className="text-yellow-400 font-semibold">Analista:</span> Clientes, Herramientas
                        </div>
                        <div className="bg-gray-800 p-3 rounded">
                          <span className="text-blue-400 font-semibold">Supervisor:</span> Mis Analistas, Clientes, Validaciones
                        </div>
                        <div className="bg-gray-800 p-3 rounded">
                          <span className="text-purple-400 font-semibold">Gerente:</span> Todas las anteriores + Logs, Dashboards, Admin
                        </div>
                      </div>
                    </div>

                    <div className="bg-gray-900 p-6 rounded-lg">
                      <h3 className="text-xl font-semibold text-purple-400 mb-3">Constantes</h3>
                      <div className="bg-gray-800 p-4 rounded-lg">
                        <pre className="text-sm text-gray-300 font-mono">
{`// constants/menu.constants.js
USER_TYPES = {
  ANALISTA: 'analista',
  SUPERVISOR: 'supervisor',
  GERENTE: 'gerente'
}

BUSINESS_AREAS = {
  CONTABILIDAD: 'Contabilidad',
  NOMINA: 'Nomina'
}`}
                        </pre>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {activeSection === 'api' && (
                <div className="space-y-6">
                  <h2 className="text-3xl font-bold mb-4">📚 API Reference</h2>

                  <div className="space-y-6">
                    <div className="bg-gray-900 p-6 rounded-lg">
                      <h3 className="text-xl font-semibold text-purple-400 mb-3">getUserMenuOptions(usuario)</h3>
                      <p className="text-gray-300 mb-4">Retorna las opciones de menú según el usuario</p>
                      
                      <div className="space-y-3">
                        <div>
                          <p className="text-sm text-gray-400 mb-2">Parámetros:</p>
                          <div className="bg-gray-800 p-3 rounded-lg text-sm font-mono">
                            <span className="text-blue-400">usuario</span>: <span className="text-green-400">Object</span> - Objeto con tipo_usuario y areas
                          </div>
                        </div>
                        <div>
                          <p className="text-sm text-gray-400 mb-2">Retorna:</p>
                          <div className="bg-gray-800 p-3 rounded-lg text-sm font-mono">
                            <span className="text-green-400">Array</span> - Array de opciones de menú
                          </div>
                        </div>
                      </div>
                    </div>

                    <div className="bg-gray-900 p-6 rounded-lg">
                      <h3 className="text-xl font-semibold text-purple-400 mb-3">hasArea(usuario, areaNombre)</h3>
                      <p className="text-gray-300 mb-4">Verifica si un usuario tiene un área específica</p>
                      
                      <div className="space-y-3">
                        <div>
                          <p className="text-sm text-gray-400 mb-2">Parámetros:</p>
                          <div className="bg-gray-800 p-3 rounded-lg text-sm font-mono space-y-1">
                            <div><span className="text-blue-400">usuario</span>: <span className="text-green-400">Object</span> - Objeto de usuario</div>
                            <div><span className="text-blue-400">areaNombre</span>: <span className="text-green-400">string</span> - Nombre del área</div>
                          </div>
                        </div>
                        <div>
                          <p className="text-sm text-gray-400 mb-2">Retorna:</p>
                          <div className="bg-gray-800 p-3 rounded-lg text-sm font-mono">
                            <span className="text-green-400">boolean</span>
                          </div>
                        </div>
                      </div>
                    </div>
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

export default MenuModuleDocs;
