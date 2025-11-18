// src/pages/ClienteDetalleContabilidadModuleDocs.jsx
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
 * Página de documentación del módulo Detalle de Cliente de Contabilidad
 */
const ClienteDetalleContabilidadModuleDocs = () => {
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
                <h1 className="text-xl font-bold">Módulo Detalle de Cliente de Contabilidad</h1>
                <p className="text-sm text-gray-400">Documentación Técnica</p>
              </div>
            </div>
            <Link
              to="/dev/modules/cliente-detalle-contabilidad/demo"
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
                  <h2 className="text-3xl font-bold mb-4">📚 Módulo Detalle de Cliente de Contabilidad</h2>
                  <p className="text-gray-300 text-lg">
                    Vista completa de cliente con KPIs contables, información básica y acciones rápidas.
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
                        <span>Información del cliente con badges (bilingüe, fuente de datos)</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-green-400 mt-1">✓</span>
                        <span>KPIs del último cierre (movimientos, debe, haber, diferencia)</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-green-400 mt-1">✓</span>
                        <span>Indicador de balance contable (balanceado/descuadre)</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-green-400 mt-1">✓</span>
                        <span>Botones de acción rápida (Dashboard, Cierres, Libros)</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-green-400 mt-1">✓</span>
                        <span>Carga optimizada con caché Redis</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-green-400 mt-1">✓</span>
                        <span>Fallback a datos básicos si no hay KPIs</span>
                      </li>
                    </ul>
                  </div>

                  <div className="grid grid-cols-3 gap-4">
                    <div className="bg-purple-900/30 border border-purple-700 p-4 rounded-lg">
                      <div className="text-2xl font-bold text-purple-400">9</div>
                      <div className="text-sm text-gray-400">Archivos</div>
                    </div>
                    <div className="bg-purple-900/30 border border-purple-700 p-4 rounded-lg">
                      <div className="text-2xl font-bold text-purple-400">3</div>
                      <div className="text-sm text-gray-400">Componentes</div>
                    </div>
                    <div className="bg-purple-900/30 border border-purple-700 p-4 rounded-lg">
                      <div className="text-2xl font-bold text-purple-400">4</div>
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
{`contabilidad/cliente-detalle/
├── api/
│   └── clienteDetalle.api.js
├── components/
│   ├── ClienteInfoCard.jsx
│   ├── KpiResumenContabilidad.jsx
│   └── ClienteActionButtons.jsx
├── pages/
│   └── ClienteDetalleContabilidadPage.jsx
├── router/
│   └── ClienteDetalleContabilidadRouter.jsx
├── utils/
│   └── clienteDetalleHelpers.js
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
                      <h4 className="font-semibold text-purple-400 mb-2">ClienteDetalleContabilidadPage</h4>
                      <p className="text-sm text-gray-300">Página principal con validación de acceso y carga de datos con fallback</p>
                    </div>
                    
                    <div className="bg-gray-900 p-4 rounded-lg">
                      <h4 className="font-semibold text-purple-400 mb-2">ClienteInfoCard</h4>
                      <p className="text-sm text-gray-300">Card con información básica: nombre, RUT, industria, último cierre, estado (tema purple)</p>
                    </div>
                    
                    <div className="bg-gray-900 p-4 rounded-lg">
                      <h4 className="font-semibold text-purple-400 mb-2">KpiResumenContabilidad</h4>
                      <p className="text-sm text-gray-300">Grid de KPIs: total movimientos, debe, haber, diferencia + indicador de balance</p>
                    </div>

                    <div className="bg-gray-900 p-4 rounded-lg">
                      <h4 className="font-semibold text-purple-400 mb-2">ClienteActionButtons</h4>
                      <p className="text-sm text-gray-300">5 botones de acción: Dashboard, Crear Cierre, Historial, Libros, Herramientas</p>
                    </div>
                  </div>
                </div>
              )}

              {activeSection === 'api' && (
                <div className="space-y-6">
                  <h2 className="text-3xl font-bold mb-4">📡 API</h2>
                  
                  <div className="space-y-4">
                    <div className="bg-gray-900 p-4 rounded-lg">
                      <code className="text-purple-400">obtenerCliente(id)</code>
                      <p className="text-sm text-gray-300 mt-2">GET /clientes/&#123;id&#125;/ - Datos del cliente</p>
                    </div>
                    
                    <div className="bg-gray-900 p-4 rounded-lg">
                      <code className="text-purple-400">obtenerKpisContabilidadCliente(clienteId)</code>
                      <p className="text-sm text-gray-300 mt-2">GET /contabilidad/cierres/ + /informe/ - KPIs agregados del último cierre</p>
                    </div>
                    
                    <div className="bg-gray-900 p-4 rounded-lg">
                      <code className="text-purple-400">obtenerResumenContabilidad(clienteId)</code>
                      <p className="text-sm text-gray-300 mt-2">GET /contabilidad/cierres/resumen/&#123;clienteId&#125;/ - Resumen básico (fallback)</p>
                    </div>

                    <div className="bg-gray-900 p-4 rounded-lg">
                      <code className="text-purple-400">obtenerUsuario()</code>
                      <p className="text-sm text-gray-300 mt-2">GET /usuarios/me/ - Usuario actual para validación</p>
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
                      <li>Obtiene usuario con obtenerUsuario()</li>
                      <li>Valida que usuario.areas contenga 'Contabilidad' (normalizado)</li>
                      <li>Si no tiene acceso → Pantalla "Acceso Denegado"</li>
                      <li>Si tiene acceso → Carga datos del cliente y KPIs</li>
                      <li>Si falla KPIs → Fallback a resumen básico</li>
                    </ol>
                  </div>

                  <pre className="bg-gray-900 p-6 rounded-lg text-green-400 text-sm">
{`const tieneAcceso = validarAccesoContabilidad(userData);
if (!tieneAcceso) {
  // Mostrar acceso denegado
  return;
}
// Cargar datos...`}
                  </pre>
                </div>
              )}

              {activeSection === 'usage' && (
                <div className="space-y-6">
                  <h2 className="text-3xl font-bold mb-4">💡 Uso del Módulo</h2>
                  
                  <pre className="bg-gray-900 p-6 rounded-lg text-green-400 text-sm">
{`// En App.jsx
import { ClienteDetalleContabilidadRouter } from './modules/contabilidad/cliente-detalle';

<Route path="/menu/contabilidad/clientes/:id/*" 
       element={<ClienteDetalleContabilidadRouter />} />`}
                  </pre>

                  <div className="bg-yellow-900/30 border border-yellow-700 p-4 rounded-lg">
                    <p className="text-yellow-200 text-sm">
                      <strong>Nota:</strong> El módulo valida automáticamente el acceso y muestra indicador de balance contable (debe vs haber).
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

export default ClienteDetalleContabilidadModuleDocs;
