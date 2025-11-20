// src/pages/HistorialCierresNominaModuleDocs.jsx
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
 * Página de documentación del módulo Historial de Cierres de Nómina
 */
const HistorialCierresNominaModuleDocs = () => {
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
                <h1 className="text-xl font-bold">Módulo Historial de Cierres de Nómina</h1>
                <p className="text-sm text-gray-400">Documentación Técnica</p>
              </div>
            </div>
            <Link
              to="/dev/modules/historial-cierres-nomina/demo"
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
                    className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium transition-all ${ activeSection === section.id
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
                  <h2 className="text-3xl font-bold mb-4">📚 Módulo Historial de Cierres de Nómina</h2>
                  <p className="text-gray-300 text-lg">
                    Lista completa de cierres con filtros, estadísticas y auto-refresh para procesos activos.
                  </p>

                  <div className="bg-gray-900 p-6 rounded-lg">
                    <h3 className="text-xl font-semibold mb-3">✨ Características</h3>
                    <ul className="space-y-2 text-gray-300">
                      <li className="flex items-start gap-2">
                        <span className="text-green-400 mt-1">✓</span>
                        <span>Validación de acceso al área de Nómina</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-green-400 mt-1">✓</span>
                        <span>Tabla completa con periodo, estado y fecha</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-green-400 mt-1">✓</span>
                        <span>Estadísticas: Total, Finalizados, En Proceso, Con Incidencias</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-green-400 mt-1">✓</span>
                        <span>Filtros por estado (todos, finalizado, procesando, con incidencias)</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-green-400 mt-1">✓</span>
                        <span>Auto-refresh cada 30s para cierres en proceso</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-green-400 mt-1">✓</span>
                        <span>Botón manual de refresh</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-green-400 mt-1">✓</span>
                        <span>Navegación a detalle y libro de remuneraciones</span>
                      </li>
                    </ul>
                  </div>

                  <div className="grid grid-cols-3 gap-4">
                    <div className="bg-teal-900/30 border border-teal-700 p-4 rounded-lg">
                      <div className="text-2xl font-bold text-teal-400">9</div>
                      <div className="text-sm text-gray-400">Archivos</div>
                    </div>
                    <div className="bg-teal-900/30 border border-teal-700 p-4 rounded-lg">
                      <div className="text-2xl font-bold text-teal-400">3</div>
                      <div className="text-sm text-gray-400">Componentes</div>
                    </div>
                    <div className="bg-teal-900/30 border border-teal-700 p-4 rounded-lg">
                      <div className="text-2xl font-bold text-teal-400">3</div>
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
{`nomina/historial-cierres/
├── api/
│   └── historialCierres.api.js
├── components/
│   ├── EstadisticasCierres.jsx
│   ├── FiltrosCierres.jsx
│   └── TablaCierres.jsx
├── pages/
│   └── HistorialCierresNominaPage.jsx
├── router/
│   └── HistorialCierresNominaRouter.jsx
├── utils/
│   └── historialCierresHelpers.js
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
                      <h4 className="font-semibold text-teal-400 mb-2">HistorialCierresNominaPage</h4>
                      <p className="text-sm text-gray-300">Página principal con validación, carga de datos, filtros y auto-refresh</p>
                    </div>
                    
                    <div className="bg-gray-900 p-4 rounded-lg">
                      <h4 className="font-semibold text-teal-400 mb-2">EstadisticasCierres</h4>
                      <p className="text-sm text-gray-300">Grid de 4 cards: Total, Finalizados, En Proceso, Con Incidencias</p>
                    </div>
                    
                    <div className="bg-gray-900 p-4 rounded-lg">
                      <h4 className="font-semibold text-teal-400 mb-2">FiltrosCierres</h4>
                      <p className="text-sm text-gray-300">Botones de filtro por estado con conteo dinámico</p>
                    </div>

                    <div className="bg-gray-900 p-4 rounded-lg">
                      <h4 className="font-semibold text-teal-400 mb-2">TablaCierres</h4>
                      <p className="text-sm text-gray-300">Tabla con columnas: Periodo, Estado, Fecha, Acciones (Ver detalle, Ver libro)</p>
                    </div>
                  </div>
                </div>
              )}

              {activeSection === 'api' && (
                <div className="space-y-6">
                  <h2 className="text-3xl font-bold mb-4">📡 API</h2>
                  
                  <div className="space-y-4">
                    <div className="bg-gray-900 p-4 rounded-lg">
                      <code className="text-teal-400">obtenerCierresNominaCliente(clienteId)</code>
                      <p className="text-sm text-gray-300 mt-2">GET /nomina/cierres/?cliente=&#123;clienteId&#125;</p>
                    </div>
                    
                    <div className="bg-gray-900 p-4 rounded-lg">
                      <code className="text-teal-400">obtenerCliente(id)</code>
                      <p className="text-sm text-gray-300 mt-2">GET /clientes/&#123;id&#125;/ - Datos del cliente</p>
                    </div>

                    <div className="bg-gray-900 p-4 rounded-lg">
                      <code className="text-teal-400">obtenerUsuario()</code>
                      <p className="text-sm text-gray-300 mt-2">GET /usuarios/me/ - Usuario actual para validación</p>
                    </div>
                  </div>
                </div>
              )}

              {activeSection === 'security' && (
                <div className="space-y-6">
                  <h2 className="text-3xl font-bold mb-4">🔒 Validación de Acceso</h2>
                  
                  <div className="bg-gray-900 p-6 rounded-lg">
                    <h3 className="text-xl font-semibold mb-3 text-teal-400">Flujo de Validación</h3>
                    <ol className="space-y-3 text-gray-300 list-decimal list-inside">
                      <li>Obtiene usuario con obtenerUsuario()</li>
                      <li>Valida que usuario.areas contenga 'Nomina' (normalizado)</li>
                      <li>Si no tiene acceso → Pantalla "Acceso Denegado"</li>
                      <li>Si tiene acceso → Carga cliente y cierres</li>
                      <li>Activa auto-refresh si hay cierres en proceso</li>
                    </ol>
                  </div>

                  <pre className="bg-gray-900 p-6 rounded-lg text-green-400 text-sm">
{`const tieneAcceso = validarAccesoNomina(userData);
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
{`// En App.jsx (solo /dev)
import { HistorialCierresNominaRouter } from './modules/nomina/historial-cierres';

// Ruta demo
<Route path="/dev/modules/historial-cierres-nomina/demo/:clienteId" 
       element={<HistorialCierresNominaModuleDemo />} />`}
                  </pre>

                  <div className="bg-yellow-900/30 border border-yellow-700 p-4 rounded-lg">
                    <p className="text-yellow-200 text-sm">
                      <strong>Nota:</strong> Auto-refresh activo cada 30 segundos si hay cierres en proceso o generando reportes.
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

export default HistorialCierresNominaModuleDocs;
