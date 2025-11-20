// src/pages/CierreDetalleNominaModuleDocs.jsx
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

const CierreDetalleNominaModuleDocs = () => {
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
                <h1 className="text-xl font-bold">Módulo Cierre Detalle de Nómina</h1>
                <p className="text-sm text-gray-400">Documentación Técnica</p>
              </div>
            </div>
            <Link to="/dev/modules/cierre-detalle-nomina/demo" className="px-4 py-2 bg-teal-600 hover:bg-teal-700 rounded-lg text-sm font-medium transition-colors">
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
                  <button key={section.id} onClick={() => setActiveSection(section.id)} className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium transition-all ${activeSection === section.id ? 'bg-teal-600 text-white' : 'text-gray-400 hover:text-white hover:bg-gray-800'}`}>
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
                  <h2 className="text-3xl font-bold mb-4">📊 Módulo Cierre Detalle de Nómina</h2>
                  <p className="text-gray-300 text-lg">Vista completa del progreso de un cierre de nómina con todas sus etapas, archivos y verificaciones.</p>
                  <div className="bg-gray-900 p-6 rounded-lg">
                    <h3 className="text-xl font-semibold mb-3">✨ Características</h3>
                    <ul className="space-y-2 text-gray-300">
                      <li className="flex items-start gap-2"><span className="text-green-400 mt-1">✓</span><span>Validación de acceso a Nómina</span></li>
                      <li className="flex items-start gap-2"><span className="text-green-400 mt-1">✓</span><span>CierreInfoBar con información del cierre</span></li>
                      <li className="flex items-start gap-2"><span className="text-green-400 mt-1">✓</span><span>CierreProgresoNomina con 8+ secciones</span></li>
                      <li className="flex items-start gap-2"><span className="text-green-400 mt-1">✓</span><span>Archivos Talana: Libro + Movimientos</span></li>
                      <li className="flex items-start gap-2"><span className="text-green-400 mt-1">✓</span><span>Archivos Analista: Ingresos, Finiquitos, Ausentismos, Novedades</span></li>
                      <li className="flex items-start gap-2"><span className="text-green-400 mt-1">✓</span><span>Verificador de datos automático</span></li>
                      <li className="flex items-start gap-2"><span className="text-green-400 mt-1">✓</span><span>Gestión de incidencias con resolución</span></li>
                      <li className="flex items-start gap-2"><span className="text-green-400 mt-1">✓</span><span>Resumen del cierre con totales y KPIs</span></li>
                    </ul>
                  </div>
                  <div className="grid grid-cols-3 gap-4">
                    <div className="bg-teal-900/30 border border-teal-700 p-4 rounded-lg">
                      <div className="text-2xl font-bold text-teal-400">28+</div>
                      <div className="text-sm text-gray-400">Componentes</div>
                    </div>
                    <div className="bg-teal-900/30 border border-teal-700 p-4 rounded-lg">
                      <div className="text-2xl font-bold text-teal-400">50+</div>
                      <div className="text-sm text-gray-400">API Functions</div>
                    </div>
                    <div className="bg-teal-900/30 border border-teal-700 p-4 rounded-lg">
                      <div className="text-2xl font-bold text-teal-400">1,200+</div>
                      <div className="text-sm text-gray-400">Líneas de código</div>
                    </div>
                  </div>
                </div>
              )}

              {activeSection === 'structure' && (
                <div className="space-y-6">
                  <h2 className="text-3xl font-bold mb-4">🏗️ Estructura del Módulo</h2>
                  <div className="bg-gray-900 p-6 rounded-lg font-mono text-sm">
                    <pre className="text-gray-300">{`nomina/cierre-detalle/
├── api/
│   └── cierreDetalle.api.js          ← 1,200+ líneas (copia completa de nomina.js)
├── components/
│   ├── CierreInfoBar.jsx             ← Barra de información
│   ├── CierreProgresoNomina.jsx      ← Componente principal (1,025 líneas)
│   ├── ArchivosTalanaSection.jsx     ← Sección Talana
│   ├── ArchivosAnalistaSection.jsx   ← Sección Analista
│   ├── VerificadorDatosSection.jsx   ← Verificador automático
│   ├── IncidenciasEncontradasSection.jsx ← Gestión incidencias
│   ├── ResumenCierreSection.jsx      ← Resumen y totales
│   ├── LibroRemuneracionesCard.jsx   ← Card Libro
│   ├── MovimientosMesCard.jsx        ← Card Movimientos
│   ├── IngresosCard.jsx              ← Card Ingresos
│   ├── FiniquitosCard.jsx            ← Card Finiquitos
│   ├── AusentismosCard.jsx           ← Card Ausentismos
│   ├── NovedadesCard.jsx             ← Card Novedades
│   ├── ModalClasificacionHeaders.jsx ← Modal clasificación
│   ├── ModalMapeoNovedades.jsx       ← Modal mapeo
│   └── [subdirectorios]/             ← Más componentes auxiliares
├── pages/
│   └── CierreDetalleNominaPage.jsx   ← Página principal
├── router/
│   └── CierreDetalleNominaRouter.jsx ← Router
├── utils/
│   └── cierreDetalleHelpers.js       ← Helpers y validación
└── index.js                           ← Exports públicos`}</pre>
                  </div>
                </div>
              )}

              {activeSection === 'components' && (
                <div className="space-y-6">
                  <h2 className="text-3xl font-bold mb-4">🧩 Componentes Principales</h2>
                  <div className="space-y-4">
                    <div className="bg-gray-900 p-4 rounded-lg">
                      <h4 className="font-semibold text-teal-400 mb-2">CierreDetalleNominaPage</h4>
                      <p className="text-sm text-gray-300">Página principal con validación, carga y gestión del estado del cierre</p>
                    </div>
                    <div className="bg-gray-900 p-4 rounded-lg">
                      <h4 className="font-semibold text-teal-400 mb-2">CierreInfoBar</h4>
                      <p className="text-sm text-gray-300">Barra superior con información del cliente, período y estado del cierre</p>
                    </div>
                    <div className="bg-gray-900 p-4 rounded-lg">
                      <h4 className="font-semibold text-teal-400 mb-2">CierreProgresoNomina</h4>
                      <p className="text-sm text-gray-300">Componente principal (1,025 líneas) que orquesta todas las secciones y cards</p>
                    </div>
                    <div className="bg-gray-900 p-4 rounded-lg">
                      <h4 className="font-semibold text-teal-400 mb-2">Secciones (4)</h4>
                      <p className="text-sm text-gray-300">ArchivosTalana, ArchivosAnalista, VerificadorDatos, IncidenciasEncontradas, ResumenCierre</p>
                    </div>
                    <div className="bg-gray-900 p-4 rounded-lg">
                      <h4 className="font-semibold text-teal-400 mb-2">Cards (6+)</h4>
                      <p className="text-sm text-gray-300">LibroRemuneraciones, MovimientosMes, Ingresos, Finiquitos, Ausentismos, Novedades</p>
                    </div>
                  </div>
                </div>
              )}

              {activeSection === 'api' && (
                <div className="space-y-6">
                  <h2 className="text-3xl font-bold mb-4">📡 API</h2>
                  <p className="text-gray-300 mb-4">El módulo incluye una copia completa de la API de nómina con 50+ funciones:</p>
                  <div className="space-y-4">
                    <div className="bg-gray-900 p-4 rounded-lg">
                      <h4 className="font-semibold text-teal-400 mb-2">Cierres</h4>
                      <code className="text-sm text-gray-300">obtenerCierreNominaPorId, obtenerInformeCierre, actualizarEstadoCierreNomina</code>
                    </div>
                    <div className="bg-gray-900 p-4 rounded-lg">
                      <h4 className="font-semibold text-teal-400 mb-2">Libro de Remuneraciones</h4>
                      <code className="text-sm text-gray-300">obtenerEstadoLibroRemuneraciones, subirLibroRemuneraciones, procesarLibroRemuneraciones</code>
                    </div>
                    <div className="bg-gray-900 p-4 rounded-lg">
                      <h4 className="font-semibold text-teal-400 mb-2">Movimientos del Mes</h4>
                      <code className="text-sm text-gray-300">obtenerEstadoMovimientosMes, subirMovimientosMes, eliminarMovimientosMes</code>
                    </div>
                    <div className="bg-gray-900 p-4 rounded-lg">
                      <h4 className="font-semibold text-teal-400 mb-2">Archivos Analista</h4>
                      <code className="text-sm text-gray-300">obtenerEstadoIngresos, obtenerEstadoFiniquitos, obtenerEstadoAusentismos, obtenerEstadoArchivoNovedades</code>
                    </div>
                    <div className="bg-gray-900 p-4 rounded-lg">
                      <h4 className="font-semibold text-teal-400 mb-2">Incidencias</h4>
                      <code className="text-sm text-gray-300">obtenerIncidenciasCierre, obtenerResumenIncidencias, resolverIncidencia</code>
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
                      <li>Obtiene usuario desde localStorage</li>
                      <li>Valida que usuario.areas contenga 'Nómina'</li>
                      <li>Si no tiene acceso → Pantalla "Acceso Denegado"</li>
                      <li>Si tiene acceso → Carga cierre y cliente</li>
                      <li>Renderiza CierreInfoBar + CierreProgresoNomina</li>
                    </ol>
                  </div>
                  <div className="bg-yellow-900/30 border border-yellow-700 p-4 rounded-lg">
                    <p className="text-yellow-200 text-sm"><strong>Nota:</strong> La validación se realiza en el componente Page antes de cargar datos.</p>
                  </div>
                </div>
              )}

              {activeSection === 'usage' && (
                <div className="space-y-6">
                  <h2 className="text-3xl font-bold mb-4">💡 Uso del Módulo</h2>
                  <pre className="bg-gray-900 p-6 rounded-lg text-green-400 text-sm">{`// En App.jsx (solo /dev)
import CierreDetalleNominaModuleDemo from './pages/CierreDetalleNominaModuleDemo';

<Route path="/dev/modules/cierre-detalle-nomina/demo/:cierreId" 
       element={<CierreDetalleNominaModuleDemo />} />

// Uso directo del módulo
import { CierreDetalleNominaPage } from './modules/nomina/cierre-detalle';

<Route path="/cierre-nomina/:cierreId" 
       element={<CierreDetalleNominaPage />} />`}</pre>
                  <div className="bg-blue-900/30 border border-blue-700 p-4 rounded-lg">
                    <p className="text-blue-200 text-sm"><strong>Importante:</strong> Este módulo contiene TODOS los componentes copiados. No usa wrappers. Es completamente autocontenido.</p>
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

export default CierreDetalleNominaModuleDocs;
