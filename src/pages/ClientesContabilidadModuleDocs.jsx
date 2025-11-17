// src/pages/ClientesContabilidadModuleDocs.jsx
import { Link } from 'react-router-dom';
import { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  FiArrowLeft, 
  FiBook,
  FiCode,
  FiLayers,
  FiPackage,
  FiDatabase,
  FiShield
} from 'react-icons/fi';
import { DevModulesButton } from '../modules/shared/auth';

/**
 * Página de documentación del módulo Clientes de Contabilidad
 */
const ClientesContabilidadModuleDocs = () => {
  const [activeSection, setActiveSection] = useState('overview');

  const sections = [
    { id: 'overview', label: 'Descripción General', icon: FiBook },
    { id: 'structure', label: 'Estructura', icon: FiLayers },
    { id: 'components', label: 'Componentes', icon: FiPackage },
    { id: 'api', label: 'API', icon: FiDatabase },
    { id: 'security', label: 'Validación de Acceso', icon: FiShield },
    { id: 'usage', label: 'Uso', icon: FiCode }
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
                <h1 className="text-xl font-bold">Módulo Clientes de Contabilidad</h1>
                <p className="text-sm text-gray-400">Documentación Técnica</p>
              </div>
            </div>
            <Link
              to="/dev/modules/clientes-contabilidad/demo"
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
                  <h2 className="text-3xl font-bold mb-4">📊 Módulo Clientes de Contabilidad</h2>
                  <p className="text-gray-300 text-lg">
                    Sistema completo de gestión de clientes con validación de acceso basada en área.
                  </p>

                  <div className="bg-gray-900 p-6 rounded-lg">
                    <h3 className="text-xl font-semibold mb-3">✨ Características</h3>
                    <ul className="space-y-2 text-gray-300">
                      <li className="flex items-start gap-2">
                        <span className="text-green-400 mt-1">✓</span>
                        <span>Validación de acceso al área de Contabilidad</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-green-400 mt-1">✓</span>
                        <span>Lista adaptativa según tipo de usuario (Analista/Supervisor/Gerente)</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-green-400 mt-1">✓</span>
                        <span>Vista responsive: Cards en móvil, Tabla en desktop</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-green-400 mt-1">✓</span>
                        <span>Búsqueda por nombre o RUT</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-green-400 mt-1">✓</span>
                        <span>Estados de cierres con badges de color</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-green-400 mt-1">✓</span>
                        <span>Animaciones con Framer Motion</span>
                      </li>
                    </ul>
                  </div>

                  <div className="grid grid-cols-3 gap-4">
                    <div className="bg-purple-900/30 border border-purple-700 p-4 rounded-lg">
                      <div className="text-2xl font-bold text-purple-400">11</div>
                      <div className="text-sm text-gray-400">Archivos</div>
                    </div>
                    <div className="bg-purple-900/30 border border-purple-700 p-4 rounded-lg">
                      <div className="text-2xl font-bold text-purple-400">6</div>
                      <div className="text-sm text-gray-400">Componentes</div>
                    </div>
                    <div className="bg-purple-900/30 border border-purple-700 p-4 rounded-lg">
                      <div className="text-2xl font-bold text-purple-400">5</div>
                      <div className="text-sm text-gray-400">API Endpoints</div>
                    </div>
                  </div>
                </div>
              )}

              {activeSection === 'structure' && (
                <div className="space-y-6">
                  <h2 className="text-3xl font-bold mb-4">🏗️ Estructura del Módulo</h2>
                  
                  <div className="bg-gray-900 p-6 rounded-lg font-mono text-sm">
                    <pre className="text-gray-300">
{`contabilidad/clientes/
├── api/
│   └── clientes.api.js
├── components/
│   ├── ClienteRow.jsx
│   ├── ClienteActions.jsx
│   ├── ClientesTable.jsx
│   ├── ClientesListHeader.jsx
│   ├── EstadoBadge.jsx
│   └── EmptyState.jsx
├── constants/
│   └── clientes.constants.js
├── pages/
│   └── ClientesContabilidadPage.jsx
├── router/
│   └── ClientesContabilidadRouter.jsx
├── utils/
│   └── clientesHelpers.js
└── index.js`}
                    </pre>
                  </div>
                </div>
              )}

              {activeSection === 'components' && (
                <div className="space-y-6">
                  <h2 className="text-3xl font-bold mb-4">🧩 Componentes</h2>
                  
                  <div className="space-y-4">
                    <div className="bg-gray-900 p-4 rounded-lg">
                      <h4 className="font-semibold text-purple-400 mb-2">ClientesContabilidadPage</h4>
                      <p className="text-sm text-gray-300">Página principal con validación de acceso y carga de clientes según rol</p>
                    </div>
                    
                    <div className="bg-gray-900 p-4 rounded-lg">
                      <h4 className="font-semibold text-purple-400 mb-2">ClienteRow</h4>
                      <p className="text-sm text-gray-300">Renderiza card (móvil) o fila (desktop) con datos del cliente y estado de cierre</p>
                    </div>
                    
                    <div className="bg-gray-900 p-4 rounded-lg">
                      <h4 className="font-semibold text-purple-400 mb-2">ClientesTable</h4>
                      <p className="text-sm text-gray-300">Contenedor que mapea clientes a ClienteRow</p>
                    </div>

                    <div className="bg-gray-900 p-4 rounded-lg">
                      <h4 className="font-semibold text-purple-400 mb-2">EstadoBadge</h4>
                      <p className="text-sm text-gray-300">Badge con color según estado del cierre</p>
                    </div>
                  </div>
                </div>
              )}

              {activeSection === 'api' && (
                <div className="space-y-6">
                  <h2 className="text-3xl font-bold mb-4">📡 API</h2>
                  
                  <div className="space-y-4">
                    <div className="bg-gray-900 p-4 rounded-lg">
                      <code className="text-purple-400">obtenerClientesAsignados()</code>
                      <p className="text-sm text-gray-300 mt-2">GET /clientes/asignados/ - Para Analistas</p>
                    </div>
                    
                    <div className="bg-gray-900 p-4 rounded-lg">
                      <code className="text-purple-400">obtenerClientesPorArea()</code>
                      <p className="text-sm text-gray-300 mt-2">GET /clientes-por-area/ - Para Gerentes y Supervisores</p>
                    </div>
                    
                    <div className="bg-gray-900 p-4 rounded-lg">
                      <code className="text-purple-400">obtenerResumenContabilidad(clienteId)</code>
                      <p className="text-sm text-gray-300 mt-2">GET /cierres/resumen/&#123;clienteId&#125;/ - Resumen de cierres</p>
                    </div>
                  </div>
                </div>
              )}

              {activeSection === 'security' && (
                <div className="space-y-6">
                  <h2 className="text-3xl font-bold mb-4">🔒 Validación de Acceso</h2>
                  
                  <div className="bg-gray-900 p-6 rounded-lg">
                    <h3 className="text-xl font-semibold mb-3 text-purple-400">Flujo de Validación</h3>
                    <ol className="space-y-3 text-gray-300 list-decimal list-inside">
                      <li>Lee usuario de localStorage</li>
                      <li>Valida que usuario.areas contenga 'Contabilidad' (normalizado)</li>
                      <li>Si no tiene acceso → Muestra pantalla "Acceso Denegado"</li>
                      <li>Si tiene acceso → Carga clientes según rol</li>
                    </ol>
                  </div>

                  <pre className="bg-gray-900 p-6 rounded-lg text-green-400 text-sm">
{`const tieneAcceso = validarAccesoContabilidad(userData);
if (!tieneAcceso) {
  // Mostrar mensaje de acceso denegado
  return;
}`}
                  </pre>
                </div>
              )}

              {activeSection === 'usage' && (
                <div className="space-y-6">
                  <h2 className="text-3xl font-bold mb-4">💡 Uso del Módulo</h2>
                  
                  <pre className="bg-gray-900 p-6 rounded-lg text-green-400 text-sm">
{`// En App.jsx
import { ClientesContabilidadRouter } from './modules/contabilidad/clientes';

<Route path="/menu/clientes/*" element={<ClientesContabilidadRouter />} />`}
                  </pre>

                  <div className="bg-yellow-900/30 border border-yellow-700 p-4 rounded-lg">
                    <p className="text-yellow-200 text-sm">
                      <strong>Nota:</strong> El módulo valida automáticamente el acceso. Solo usuarios con área "Contabilidad" pueden ver los clientes.
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

export default ClientesContabilidadModuleDocs;
