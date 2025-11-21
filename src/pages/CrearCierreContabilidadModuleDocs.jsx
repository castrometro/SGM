// src/pages/CrearCierreContabilidadModuleDocs.jsx
import { Link } from 'react-router-dom';
import { ArrowLeft, FileText, Code, Package, Users } from 'lucide-react';

const CrearCierreContabilidadModuleDocs = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 p-8">
      <div className="max-w-5xl mx-auto">
        <Link
          to="/dev/modules"
          className="inline-flex items-center gap-2 text-blue-400 hover:text-blue-300 mb-6 transition-colors"
        >
          <ArrowLeft size={20} />
          Volver al Showcase
        </Link>

        <div className="bg-gray-800/50 backdrop-blur-sm rounded-2xl p-8 border border-gray-700/50">
          <div className="flex items-center gap-4 mb-8">
            <div className="p-3 bg-gradient-to-br from-blue-500/20 to-cyan-500/20 rounded-xl border border-blue-500/30">
              <FileText size={32} className="text-blue-400" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-white">Crear Cierre de Contabilidad</h1>
              <p className="text-gray-400">Módulo refactorizado para creación de cierres mensuales</p>
            </div>
          </div>

          {/* Descripción */}
          <section className="mb-8">
            <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
              <Package size={20} className="text-blue-400" />
              Descripción
            </h2>
            <p className="text-gray-300 leading-relaxed mb-4">
              Módulo completo para crear nuevos cierres mensuales de contabilidad. Incluye validación de acceso,
              verificación de cierres existentes, y formulario intuitivo con validaciones.
            </p>
          </section>

          {/* Características */}
          <section className="mb-8">
            <h2 className="text-xl font-semibold text-white mb-4">Características Principales</h2>
            <ul className="space-y-2 text-gray-300">
              <li className="flex items-start gap-2">
                <span className="text-blue-400">•</span>
                <span>Validación de acceso al área de Contabilidad</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-blue-400">•</span>
                <span>Información del cliente con resumen contable</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-blue-400">•</span>
                <span>Verificación de cierres existentes antes de crear</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-blue-400">•</span>
                <span>Selector de periodo (mes y año)</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-blue-400">•</span>
                <span>Confirmación antes de crear</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-blue-400">•</span>
                <span>Navegación automática al cierre creado</span>
              </li>
            </ul>
          </section>

          {/* Estructura */}
          <section className="mb-8">
            <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
              <Code size={20} className="text-blue-400" />
              Estructura del Módulo
            </h2>
            <div className="bg-gray-900/50 rounded-lg p-4 font-mono text-sm text-gray-300">
              <pre>{`src/modules/contabilidad/crear-cierre/
├── api/
│   └── crearCierre.api.js          # Endpoints
├── components/
│   ├── ClienteInfoCard.jsx          # Info del cliente
│   └── FormularioCierre.jsx         # Formulario principal
├── constants/
│   └── crearCierre.constants.js     # Mensajes y labels
├── pages/
│   └── CrearCierreContabilidadPage.jsx
├── utils/
│   └── crearCierreHelpers.js        # Validaciones
└── index.js                          # Exports`}</pre>
            </div>
          </section>

          {/* API */}
          <section className="mb-8">
            <h2 className="text-xl font-semibold text-white mb-4">Endpoints API</h2>
            <div className="space-y-3">
              <div className="bg-gray-900/50 rounded-lg p-4 border border-gray-700/50">
                <code className="text-green-400">GET /contabilidad/cierres/?cliente=:id&periodo=:periodo</code>
                <p className="text-gray-400 text-sm mt-2">Verifica si existe cierre para el periodo</p>
              </div>
              <div className="bg-gray-900/50 rounded-lg p-4 border border-gray-700/50">
                <code className="text-blue-400">POST /contabilidad/cierres/</code>
                <p className="text-gray-400 text-sm mt-2">Crea un nuevo cierre mensual</p>
              </div>
              <div className="bg-gray-900/50 rounded-lg p-4 border border-gray-700/50">
                <code className="text-green-400">GET /clientes/:id/</code>
                <p className="text-gray-400 text-sm mt-2">Obtiene información del cliente</p>
              </div>
              <div className="bg-gray-900/50 rounded-lg p-4 border border-gray-700/50">
                <code className="text-green-400">GET /contabilidad/clientes/:id/resumen/</code>
                <p className="text-gray-400 text-sm mt-2">Obtiene resumen contable (opcional)</p>
              </div>
            </div>
          </section>

          {/* Uso */}
          <section className="mb-8">
            <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
              <Users size={20} className="text-blue-400" />
              Uso
            </h2>
            <div className="bg-gray-900/50 rounded-lg p-4">
              <code className="text-gray-300">
                {`import { CrearCierreContabilidadPage } from '@/modules/contabilidad/crear-cierre';

// En App.jsx
<Route path="/clientes/:clienteId/crear-cierre" 
       element={<CrearCierreContabilidadPage />} />`}
              </code>
            </div>
          </section>

          {/* Links */}
          <section>
            <h2 className="text-xl font-semibold text-white mb-4">Enlaces</h2>
            <div className="flex gap-4">
              <Link
                to="/dev/modules/crear-cierre-contabilidad/demo/1"
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
              >
                Ver Demo
              </Link>
              <Link
                to="/dev/modules"
                className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors"
              >
                Volver al Showcase
              </Link>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
};

export default CrearCierreContabilidadModuleDocs;
