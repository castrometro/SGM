// src/pages/ClientesNominaModuleDocs.jsx
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
  FiFileText,
  FiZap
} from 'react-icons/fi';
import { DevModulesButton } from '../modules/shared/auth';

/**
 * Página de documentación del módulo Clientes de Nómina
 */
const ClientesNominaModuleDocs = () => {
  const [activeSection, setActiveSection] = useState('overview');

  const sections = [
    { id: 'overview', label: 'Descripción General', icon: FiBook },
    { id: 'structure', label: 'Estructura', icon: FiLayers },
    { id: 'components', label: 'Componentes', icon: FiPackage },
    { id: 'usage', label: 'Uso', icon: FiCode },
    { id: 'api', label: 'API', icon: FiFileText },
    { id: 'features', label: 'Características', icon: FiZap }
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
                <h1 className="text-xl font-bold">Módulo Clientes de Nómina</h1>
                <p className="text-sm text-gray-400">Documentación Técnica</p>
              </div>
            </div>
            <Link
              to="/dev/modules/clientes-nomina/demo"
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
                  <h2 className="text-3xl font-bold mb-4">👥 Módulo Clientes de Nómina</h2>
                  <p className="text-gray-300 text-lg">
                    Gestión completa de clientes del área de Nómina con vista responsiva y filtrado por tipo de usuario.
                  </p>

                  <div className="bg-gray-900 p-6 rounded-lg">
                    <h3 className="text-xl font-semibold mb-3">✨ Características Principales</h3>
                    <ul className="space-y-2 text-gray-300">
                      <li className="flex items-start gap-2">
                        <span className="text-teal-400 mt-1">✓</span>
                        <span>Vista responsiva: Cards en móvil/tablet, tabla en desktop</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-teal-400 mt-1">✓</span>
                        <span>Filtrado por tipo de usuario (Analista/Supervisor/Gerente)</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-teal-400 mt-1">✓</span>
                        <span>Búsqueda en tiempo real por nombre o RUT</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-teal-400 mt-1">✓</span>
                        <span>Estados de cierre con badges de colores</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-teal-400 mt-1">✓</span>
                        <span>Integración con Dashboard de Nómina</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-teal-400 mt-1">✓</span>
                        <span>Modo debug para troubleshooting</span>
                      </li>
                    </ul>
                  </div>

                  <div className="grid grid-cols-3 gap-4">
                    <div className="bg-teal-900/30 border border-teal-700 p-4 rounded-lg">
                      <div className="text-2xl font-bold text-teal-400">11</div>
                      <div className="text-sm text-gray-400">Archivos</div>
                    </div>
                    <div className="bg-emerald-900/30 border border-emerald-700 p-4 rounded-lg">
                      <div className="text-2xl font-bold text-emerald-400">~800</div>
                      <div className="text-sm text-gray-400">Líneas</div>
                    </div>
                    <div className="bg-cyan-900/30 border border-cyan-700 p-4 rounded-lg">
                      <div className="text-2xl font-bold text-cyan-400">7</div>
                      <div className="text-sm text-gray-400">Componentes</div>
                    </div>
                  </div>
                </div>
              )}

              {activeSection === 'structure' && (
                <div className="space-y-6">
                  <h2 className="text-3xl font-bold mb-4">🏗️ Estructura del Módulo</h2>
                  
                  <div className="bg-gray-900 p-6 rounded-lg font-mono text-sm">
                    <pre className="text-gray-300">
{`nomina/clientes/
├── api/
│   └── clientes.api.js         # Llamadas al backend
├── components/
│   ├── ClienteRow.jsx          # Fila/Card de cliente
│   ├── EstadoBadge.jsx         # Badge de estado
│   ├── ClienteActions.jsx      # Botones de acción
│   ├── ClientesListHeader.jsx  # Header con área
│   ├── ClientesTable.jsx       # Tabla responsive
│   └── EmptyState.jsx          # Estado vacío
├── constants/
│   └── clientes.constants.js   # Estados, mensajes, config
├── pages/
│   └── ClientesNominaPage.jsx  # Página principal
├── utils/
│   └── clientesHelpers.js      # Funciones auxiliares
├── index.js                    # Exports públicos
└── README.md                   # Documentación`}
                    </pre>
                  </div>

                  <div className="space-y-4">
                    <h3 className="text-xl font-semibold">📁 Descripción de Carpetas</h3>
                    <div className="space-y-3">
                      <div className="bg-gray-900 p-4 rounded-lg">
                        <h4 className="font-semibold text-teal-400 mb-2">api/</h4>
                        <p className="text-gray-300 text-sm">
                          Funciones para comunicarse con el backend (obtenerClientes, obtenerResumen, etc.)
                        </p>
                      </div>
                      <div className="bg-gray-900 p-4 rounded-lg">
                        <h4 className="font-semibold text-teal-400 mb-2">components/</h4>
                        <p className="text-gray-300 text-sm">
                          7 componentes reutilizables (ClienteRow, EstadoBadge, ClienteActions, etc.)
                        </p>
                      </div>
                      <div className="bg-gray-900 p-4 rounded-lg">
                        <h4 className="font-semibold text-teal-400 mb-2">utils/</h4>
                        <p className="text-gray-300 text-sm">
                          Helpers: determinarAreaActiva(), filtrarClientes(), generarInfoDebug()
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
                      <h3 className="text-xl font-semibold text-teal-400 mb-3">ClientesNominaPage</h3>
                      <p className="text-gray-300 mb-4">Página principal que orquesta carga y visualización</p>
                      
                      <div className="bg-gray-800 p-4 rounded-lg space-y-2 text-sm">
                        <div><span className="text-gray-400">Estado:</span> clientes, filtro, usuario, areaActiva, cargando, error</div>
                        <div><span className="text-gray-400">Props:</span> Ninguna</div>
                      </div>
                    </div>

                    <div className="bg-gray-900 p-6 rounded-lg">
                      <h3 className="text-xl font-semibold text-teal-400 mb-3">ClienteRow</h3>
                      <p className="text-gray-300 mb-4">Fila/Card de cliente con vista adaptativa</p>
                      
                      <div className="bg-gray-800 p-4 rounded-lg font-mono text-sm space-y-1">
                        <div><span className="text-blue-400">cliente</span>: <span className="text-green-400">Object</span></div>
                        <div><span className="text-blue-400">areaActiva</span>: <span className="text-green-400">string</span></div>
                        <div><span className="text-blue-400">index</span>: <span className="text-green-400">number</span> - Para animación</div>
                      </div>
                    </div>

                    <div className="bg-gray-900 p-6 rounded-lg">
                      <h3 className="text-xl font-semibold text-teal-400 mb-3">EstadoBadge</h3>
                      <p className="text-gray-300 mb-4">Badge con colores semánticos</p>
                      
                      <div className="bg-gray-800 p-4 rounded-lg font-mono text-sm">
                        <div><span className="text-blue-400">estado</span>: <span className="text-green-400">string</span> - abierto | validado | finalizado | en_proceso | pendiente</div>
                      </div>
                    </div>

                    <div className="bg-gray-900 p-6 rounded-lg">
                      <h3 className="text-xl font-semibold text-teal-400 mb-3">ClienteActions</h3>
                      <p className="text-gray-300 mb-4">Botones: Ver Cliente y Dashboard</p>
                      
                      <div className="bg-gray-800 p-4 rounded-lg font-mono text-sm space-y-1">
                        <div><span className="text-blue-400">onVerCliente</span>: <span className="text-green-400">Function</span></div>
                        <div><span className="text-blue-400">onVerDashboard</span>: <span className="text-green-400">Function</span></div>
                        <div><span className="text-blue-400">mobile</span>: <span className="text-green-400">boolean</span></div>
                      </div>
                    </div>

                    <div className="bg-gray-900 p-6 rounded-lg">
                      <h3 className="text-xl font-semibold text-teal-400 mb-3">ClientesTable</h3>
                      <p className="text-gray-300 mb-4">Tabla que renderiza ClienteRow para cada cliente</p>
                      
                      <div className="bg-gray-800 p-4 rounded-lg font-mono text-sm space-y-1">
                        <div><span className="text-blue-400">clientes</span>: <span className="text-green-400">Array</span></div>
                        <div><span className="text-blue-400">areaActiva</span>: <span className="text-green-400">string</span></div>
                      </div>
                    </div>

                    <div className="bg-gray-900 p-6 rounded-lg">
                      <h3 className="text-xl font-semibold text-teal-400 mb-3">EmptyState</h3>
                      <p className="text-gray-300 mb-4">Mensajes cuando no hay datos</p>
                      
                      <div className="bg-gray-800 p-4 rounded-lg font-mono text-sm space-y-1">
                        <div><span className="text-blue-400">totalClientes</span>: <span className="text-green-400">number</span></div>
                        <div><span className="text-blue-400">filtro</span>: <span className="text-green-400">string</span></div>
                        <div><span className="text-blue-400">areaActiva</span>: <span className="text-green-400">string</span></div>
                        <div><span className="text-blue-400">tipoUsuario</span>: <span className="text-green-400">string</span></div>
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
{`import { ClientesNominaPage } from '@/modules/nomina/clientes';`}
                        </pre>
                      </div>
                    </div>

                    <div>
                      <h3 className="text-xl font-semibold mb-3">En el Router</h3>
                      <div className="bg-gray-900 p-4 rounded-lg">
                        <pre className="text-sm text-gray-300 font-mono">
{`<Route 
  path="/menu/clientes" 
  element={<ClientesNominaPage />} 
/>`}
                        </pre>
                      </div>
                    </div>

                    <div>
                      <h3 className="text-xl font-semibold mb-3">Importar Componentes Individuales</h3>
                      <div className="bg-gray-900 p-4 rounded-lg">
                        <pre className="text-sm text-gray-300 font-mono">
{`import { 
  ClienteRow,
  EstadoBadge,
  ClienteActions,
  filtrarClientes
} from '@/modules/nomina/clientes';`}
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
                      <h3 className="text-xl font-semibold text-teal-400 mb-3">obtenerClientesAsignados()</h3>
                      <p className="text-gray-300 mb-2">Obtiene clientes asignados (Analistas)</p>
                      <div className="bg-gray-800 p-3 rounded text-sm font-mono">
                        <span className="text-green-400">Promise&lt;Array&gt;</span> - Array de clientes
                      </div>
                    </div>

                    <div className="bg-gray-900 p-6 rounded-lg">
                      <h3 className="text-xl font-semibold text-teal-400 mb-3">obtenerClientesPorArea()</h3>
                      <p className="text-gray-300 mb-2">Obtiene clientes del área (Gerentes/Supervisores)</p>
                      <div className="bg-gray-800 p-3 rounded text-sm font-mono">
                        <span className="text-green-400">Promise&lt;Array&gt;</span> - Array de clientes
                      </div>
                    </div>

                    <div className="bg-gray-900 p-6 rounded-lg">
                      <h3 className="text-xl font-semibold text-teal-400 mb-3">obtenerResumenNomina(clienteId)</h3>
                      <p className="text-gray-300 mb-4">Obtiene resumen del último cierre</p>
                      <div className="space-y-2">
                        <div className="bg-gray-800 p-3 rounded text-sm font-mono">
                          <span className="text-blue-400">clienteId</span>: <span className="text-green-400">number</span>
                        </div>
                        <div className="bg-gray-800 p-3 rounded text-sm font-mono">
                          <span className="text-gray-400">Retorna:</span> <span className="text-green-400">Promise&lt;Object&gt;</span> - ultimo_cierre, estado_cierre_actual, usuario_cierre
                        </div>
                      </div>
                    </div>

                    <div className="bg-gray-900 p-6 rounded-lg">
                      <h3 className="text-xl font-semibold text-teal-400 mb-3">filtrarClientes(clientes, filtro)</h3>
                      <p className="text-gray-300 mb-4">Filtra por nombre o RUT</p>
                      <div className="space-y-2">
                        <div className="bg-gray-800 p-3 rounded text-sm font-mono space-y-1">
                          <div><span className="text-blue-400">clientes</span>: <span className="text-green-400">Array</span></div>
                          <div><span className="text-blue-400">filtro</span>: <span className="text-green-400">string</span></div>
                        </div>
                        <div className="bg-gray-800 p-3 rounded text-sm font-mono">
                          <span className="text-gray-400">Retorna:</span> <span className="text-green-400">Array</span> - Clientes filtrados
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {activeSection === 'features' && (
                <div className="space-y-6">
                  <h2 className="text-3xl font-bold mb-4">⚡ Características Avanzadas</h2>

                  <div className="space-y-6">
                    <div className="bg-gray-900 p-6 rounded-lg">
                      <h3 className="text-xl font-semibold text-teal-400 mb-3">🎯 Filtrado por Usuario</h3>
                      <div className="space-y-3 text-sm">
                        <div className="bg-gray-800 p-3 rounded">
                          <span className="text-yellow-400 font-semibold">Analista:</span> Solo ve clientes asignados directamente
                        </div>
                        <div className="bg-gray-800 p-3 rounded">
                          <span className="text-blue-400 font-semibold">Supervisor:</span> Ve clientes del área que supervisa
                        </div>
                        <div className="bg-gray-800 p-3 rounded">
                          <span className="text-purple-400 font-semibold">Gerente:</span> Ve todos los clientes de sus áreas asignadas
                        </div>
                      </div>
                    </div>

                    <div className="bg-gray-900 p-6 rounded-lg">
                      <h3 className="text-xl font-semibold text-teal-400 mb-3">📱 Vista Responsiva</h3>
                      <p className="text-gray-300 mb-3">Adaptación automática según breakpoints:</p>
                      <div className="space-y-2 text-sm">
                        <div className="flex items-center gap-3">
                          <span className="bg-gray-800 px-3 py-1 rounded">&lt; 1024px</span>
                          <span className="text-gray-300">Cards verticales con información compacta</span>
                        </div>
                        <div className="flex items-center gap-3">
                          <span className="bg-gray-800 px-3 py-1 rounded">≥ 1024px</span>
                          <span className="text-gray-300">Tabla completa con todas las columnas</span>
                        </div>
                      </div>
                    </div>

                    <div className="bg-gray-900 p-6 rounded-lg">
                      <h3 className="text-xl font-semibold text-teal-400 mb-3">🎨 Estados de Cierre</h3>
                      <div className="space-y-2">
                        <div className="flex items-center gap-3">
                          <span className="px-3 py-1 rounded-full text-xs font-medium bg-yellow-500 text-white">Abierto</span>
                          <span className="text-gray-300 text-sm">Cierre en curso</span>
                        </div>
                        <div className="flex items-center gap-3">
                          <span className="px-3 py-1 rounded-full text-xs font-medium bg-blue-500 text-white">Validado</span>
                          <span className="text-gray-300 text-sm">Esperando finalización</span>
                        </div>
                        <div className="flex items-center gap-3">
                          <span className="px-3 py-1 rounded-full text-xs font-medium bg-green-500 text-white">Finalizado</span>
                          <span className="text-gray-300 text-sm">Cierre completado</span>
                        </div>
                      </div>
                    </div>

                    <div className="bg-gray-900 p-6 rounded-lg">
                      <h3 className="text-xl font-semibold text-teal-400 mb-3">🔍 Modo Debug</h3>
                      <p className="text-gray-300 mb-3">Clic en "🔍 Debug" muestra:</p>
                      <ul className="text-sm text-gray-300 space-y-1 list-disc list-inside">
                        <li>Tipo de usuario y área activa</li>
                        <li>Endpoint utilizado</li>
                        <li>Total de clientes cargados</li>
                        <li>Filtro actual</li>
                        <li>Primeros 5 clientes con detalles</li>
                      </ul>
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

export default ClientesNominaModuleDocs;
