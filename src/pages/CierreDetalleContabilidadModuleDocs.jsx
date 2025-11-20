// src/pages/CierreDetalleContabilidadModuleDocs.jsx
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

const CierreDetalleContabilidadModuleDocs = () => {
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
      <header className="bg-gray-800 border-b border-gray-700 sticky top-0 z-40">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link to="/dev/modules" className="inline-flex items-center gap-2 px-3 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm font-medium transition-colors">
                <FiArrowLeft size={16} />
                Volver
              </Link>
              <div>
                <h1 className="text-xl font-bold">Módulo Cierre Detalle de Contabilidad</h1>
                <p className="text-sm text-gray-400">Documentación Técnica</p>
              </div>
            </div>
            <Link to="/dev/modules/cierre-detalle-contabilidad/demo" className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-medium transition-colors">
              Ver Demo
            </Link>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          <div className="lg:col-span-1">
            <nav className="sticky top-24 space-y-1">
              {sections.map((section) => {
                const Icon = section.icon;
                return (
                  <button key={section.id} onClick={() => setActiveSection(section.id)} className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium transition-all ${activeSection === section.id ? 'bg-blue-600 text-white' : 'text-gray-400 hover:text-white hover:bg-gray-800'}`}>
                    <Icon size={18} />
                    {section.label}
                  </button>
                );
              })}
            </nav>
          </div>

          <div className="lg:col-span-3">
            <motion.div key={activeSection} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }} className="bg-gray-800 rounded-lg p-8">
              {activeSection === 'overview' && (
                <div className="space-y-6">
                  <h2 className="text-3xl font-bold mb-4">📊 Módulo Cierre Detalle de Contabilidad</h2>
                  <p className="text-gray-300 text-lg">Vista completa del progreso de un cierre contable con todas sus etapas y procesos.</p>
                  <div className="bg-gray-900 p-6 rounded-lg">
                    <h3 className="text-xl font-semibold mb-3">✨ Características</h3>
                    <ul className="space-y-2 text-gray-300">
                      <li className="flex items-start gap-2"><span className="text-green-400 mt-1">✓</span><span>Validación de acceso a Contabilidad</span></li>
                      <li className="flex items-start gap-2"><span className="text-green-400 mt-1">✓</span><span>CierreInfoBar con información del cierre</span></li>
                      <li className="flex items-start gap-2"><span className="text-green-400 mt-1">✓</span><span>CierreProgresoContabilidad con 4 etapas principales</span></li>
                      <li className="flex items-start gap-2"><span className="text-green-400 mt-1">✓</span><span>Paso 1: Tipos de Documento</span></li>
                      <li className="flex items-start gap-2"><span className="text-green-400 mt-1">✓</span><span>Paso 2: Clasificación de Cuentas (bulk)</span></li>
                      <li className="flex items-start gap-2"><span className="text-green-400 mt-1">✓</span><span>Paso 3: Nombres en Inglés (clientes bilingües)</span></li>
                      <li className="flex items-start gap-2"><span className="text-green-400 mt-1">✓</span><span>Paso 4: Libro Mayor (procesamiento final)</span></li>
                      <li className="flex items-start gap-2"><span className="text-green-400 mt-1">✓</span><span>Gestión de incidencias consolidadas</span></li>
                      <li className="flex items-start gap-2"><span className="text-green-400 mt-1">✓</span><span>Reprocesamiento con excepciones</span></li>
                    </ul>
                  </div>
                  <div className="grid grid-cols-3 gap-4">
                    <div className="bg-blue-900/30 border border-blue-700 p-4 rounded-lg">
                      <div className="text-2xl font-bold text-blue-400">12+</div>
                      <div className="text-sm text-gray-400">Componentes</div>
                    </div>
                    <div className="bg-blue-900/30 border border-blue-700 p-4 rounded-lg">
                      <div className="text-2xl font-bold text-blue-400">30+</div>
                      <div className="text-sm text-gray-400">API Functions</div>
                    </div>
                    <div className="bg-blue-900/30 border border-blue-700 p-4 rounded-lg">
                      <div className="text-2xl font-bold text-blue-400">800+</div>
                      <div className="text-sm text-gray-400">Líneas de código</div>
                    </div>
                  </div>
                </div>
              )}

              {activeSection === 'structure' && (
                <div className="space-y-6">
                  <h2 className="text-3xl font-bold mb-4">🏗️ Estructura del Módulo</h2>
                  <div className="bg-gray-900 p-6 rounded-lg font-mono text-sm">
                    <pre className="text-gray-300 overflow-x-auto">
{`src/modules/contabilidad/cierre-detalle/
├── api/
│   └── cierreDetalle.api.js       # API functions
├── components/
│   ├── CierreInfoBar.jsx          # Barra de información
│   ├── CierreProgresoContabilidad.jsx  # Componente principal
│   ├── TipoDocumentoCard.jsx      # Paso 1: Tipos de documento
│   ├── ClasificacionBulkCard.jsx  # Paso 2: Clasificación
│   ├── NombresEnInglesCard.jsx    # Paso 3: Traducción
│   ├── LibroMayorCard.jsx         # Paso 4: Libro Mayor
│   └── Modal*.jsx                  # Modales auxiliares
├── pages/
│   └── CierreDetalleContabilidadPage.jsx
├── router/
│   └── CierreDetalleContabilidadRouter.jsx
├── utils/
│   └── cierreDetalleHelpers.js    # Helpers y validaciones
└── index.js                        # Exports del módulo`}
                    </pre>
                  </div>
                </div>
              )}

              {activeSection === 'components' && (
                <div className="space-y-6">
                  <h2 className="text-3xl font-bold mb-4">📦 Componentes Principales</h2>
                  
                  <div className="space-y-4">
                    <div className="bg-gray-900 p-4 rounded-lg border border-gray-700">
                      <h3 className="text-lg font-semibold text-blue-400 mb-2">CierreDetalleContabilidadPage</h3>
                      <p className="text-gray-300 text-sm mb-2">Página principal del módulo</p>
                      <code className="text-xs bg-gray-800 p-2 rounded block">
                        {`import { CierreDetalleContabilidadPage } from '../modules/contabilidad/cierre-detalle';`}
                      </code>
                    </div>

                    <div className="bg-gray-900 p-4 rounded-lg border border-gray-700">
                      <h3 className="text-lg font-semibold text-blue-400 mb-2">CierreInfoBar</h3>
                      <p className="text-gray-300 text-sm mb-2">Muestra información del cliente, período y estado del cierre</p>
                      <code className="text-xs bg-gray-800 p-2 rounded block">
                        {`<CierreInfoBar cierre={cierre} cliente={cliente} tipoModulo="contabilidad" />`}
                      </code>
                    </div>

                    <div className="bg-gray-900 p-4 rounded-lg border border-gray-700">
                      <h3 className="text-lg font-semibold text-blue-400 mb-2">CierreProgresoContabilidad</h3>
                      <p className="text-gray-300 text-sm mb-2">Componente con las 4 tarjetas del proceso contable</p>
                      <code className="text-xs bg-gray-800 p-2 rounded block">
                        {`<CierreProgresoContabilidad cierre={cierre} cliente={cliente} />`}
                      </code>
                    </div>

                    <div className="bg-gray-900 p-4 rounded-lg border border-gray-700">
                      <h3 className="text-lg font-semibold text-blue-400 mb-2">TipoDocumentoCard</h3>
                      <p className="text-gray-300 text-sm">Gestión de tipos de documento para el cliente</p>
                    </div>

                    <div className="bg-gray-900 p-4 rounded-lg border border-gray-700">
                      <h3 className="text-lg font-semibold text-blue-400 mb-2">ClasificacionBulkCard</h3>
                      <p className="text-gray-300 text-sm">Clasificación masiva de cuentas contables</p>
                    </div>

                    <div className="bg-gray-900 p-4 rounded-lg border border-gray-700">
                      <h3 className="text-lg font-semibold text-blue-400 mb-2">NombresEnInglesCard</h3>
                      <p className="text-gray-300 text-sm">Traducción de nombres de cuentas (solo clientes bilingües)</p>
                    </div>

                    <div className="bg-gray-900 p-4 rounded-lg border border-gray-700">
                      <h3 className="text-lg font-semibold text-blue-400 mb-2">LibroMayorCard</h3>
                      <p className="text-gray-300 text-sm">Procesamiento del Libro Mayor con gestión de incidencias</p>
                    </div>
                  </div>
                </div>
              )}

              {activeSection === 'api' && (
                <div className="space-y-6">
                  <h2 className="text-3xl font-bold mb-4">🔌 API Functions</h2>
                  
                  <div className="space-y-4">
                    <div className="bg-gray-900 p-4 rounded-lg">
                      <h3 className="text-lg font-semibold text-blue-400 mb-3">Funciones de Cierres</h3>
                      <ul className="space-y-2 text-sm font-mono text-gray-300">
                        <li>• obtenerCierrePorId(cierreId)</li>
                        <li>• obtenerCierresCliente(clienteId)</li>
                        <li>• crearCierreMensual(clienteId, periodo)</li>
                        <li>• finalizarCierre(cierreId)</li>
                        <li>• actualizarEstadoCierre(cierreId)</li>
                      </ul>
                    </div>

                    <div className="bg-gray-900 p-4 rounded-lg">
                      <h3 className="text-lg font-semibold text-blue-400 mb-3">Funciones de Tipo de Documento</h3>
                      <ul className="space-y-2 text-sm font-mono text-gray-300">
                        <li>• obtenerEstadoTipoDocumento(clienteId)</li>
                        <li>• subirTipoDocumento(formData)</li>
                        <li>• obtenerTiposDocumentoCliente(clienteId)</li>
                      </ul>
                    </div>

                    <div className="bg-gray-900 p-4 rounded-lg">
                      <h3 className="text-lg font-semibold text-blue-400 mb-3">Funciones de Libro Mayor</h3>
                      <ul className="space-y-2 text-sm font-mono text-gray-300">
                        <li>• subirLibroMayor(clienteId, archivo, cierreId)</li>
                        <li>• obtenerLibrosMayor(cierreId)</li>
                        <li>• obtenerMovimientosIncompletos(cierreId)</li>
                        <li>• reprocesarConExcepciones(cierreId)</li>
                      </ul>
                    </div>

                    <div className="bg-gray-900 p-4 rounded-lg">
                      <h3 className="text-lg font-semibold text-blue-400 mb-3">Funciones de Clasificación</h3>
                      <ul className="space-y-2 text-sm font-mono text-gray-300">
                        <li>• obtenerProgresoClasificacionTodosLosSets(cierreId)</li>
                        <li>• obtenerProgresoClasificacionPorSet(cierreId, setId)</li>
                        <li>• obtenerCuentasPendientes(cierreId)</li>
                      </ul>
                    </div>
                  </div>
                </div>
              )}

              {activeSection === 'security' && (
                <div className="space-y-6">
                  <h2 className="text-3xl font-bold mb-4">🔒 Validación de Acceso</h2>
                  
                  <div className="bg-gray-900 p-6 rounded-lg">
                    <h3 className="text-lg font-semibold mb-3">Función de Validación</h3>
                    <code className="text-sm bg-gray-800 p-4 rounded block text-gray-300">
{`export const validarAccesoContabilidad = (userData) => {
  if (!userData || !userData.areas) return false;
  
  return userData.areas.some(area => {
    const areaNombre = typeof area === 'string' ? area : area.nombre;
    return normalizar(areaNombre) === 'contabilidad';
  });
};`}
                    </code>
                  </div>

                  <div className="bg-gray-900 p-6 rounded-lg">
                    <h3 className="text-lg font-semibold mb-3">Uso en la Página</h3>
                    <code className="text-sm bg-gray-800 p-4 rounded block text-gray-300">
{`useEffect(() => {
  const usuario = JSON.parse(localStorage.getItem("usuario"));
  if (!validarAccesoContabilidad(usuario)) {
    setTieneAcceso(false);
    setCargandoInicial(false);
  }
}, []);`}
                    </code>
                  </div>

                  <div className="bg-yellow-900/20 border border-yellow-700 p-4 rounded-lg">
                    <p className="text-yellow-300 text-sm">
                      ⚠️ <strong>Importante:</strong> Esta validación se ejecuta en el frontend. El backend también debe validar permisos para garantizar la seguridad.
                    </p>
                  </div>
                </div>
              )}

              {activeSection === 'usage' && (
                <div className="space-y-6">
                  <h2 className="text-3xl font-bold mb-4">💻 Cómo Usar el Módulo</h2>
                  
                  <div className="space-y-4">
                    <div className="bg-gray-900 p-6 rounded-lg">
                      <h3 className="text-lg font-semibold mb-3">1. Importar el Router</h3>
                      <code className="text-sm bg-gray-800 p-4 rounded block text-gray-300">
{`import { CierreDetalleContabilidadRouter } from './modules/contabilidad/cierre-detalle';

// En App.jsx
<Route 
  path="/menu/cierres-contabilidad/:cierreId/*" 
  element={<CierreDetalleContabilidadRouter />} 
/>`}
                      </code>
                    </div>

                    <div className="bg-gray-900 p-6 rounded-lg">
                      <h3 className="text-lg font-semibold mb-3">2. Usar la Página Directamente</h3>
                      <code className="text-sm bg-gray-800 p-4 rounded block text-gray-300">
{`import { CierreDetalleContabilidadPage } from './modules/contabilidad/cierre-detalle';

// Usar en cualquier parte de tu aplicación
<CierreDetalleContabilidadPage />`}
                      </code>
                    </div>

                    <div className="bg-gray-900 p-6 rounded-lg">
                      <h3 className="text-lg font-semibold mb-3">3. Navegar al Detalle</h3>
                      <code className="text-sm bg-gray-800 p-4 rounded block text-gray-300">
{`import { useNavigate } from 'react-router-dom';

const navigate = useNavigate();
navigate(\`/menu/cierres-contabilidad/\${cierreId}\`);`}
                      </code>
                    </div>

                    <div className="bg-blue-900/20 border border-blue-700 p-4 rounded-lg">
                      <p className="text-blue-300 text-sm">
                        💡 <strong>Tip:</strong> El cierreId se obtiene automáticamente de la URL mediante useParams() dentro del componente.
                      </p>
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

export default CierreDetalleContabilidadModuleDocs;
