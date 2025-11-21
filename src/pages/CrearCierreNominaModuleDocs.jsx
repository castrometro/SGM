// src/pages/CrearCierreNominaModuleDocs.jsx
import { Link } from 'react-router-dom';
import { ArrowLeft, FileText, Code, Package, Users } from 'lucide-react';

const CrearCierreNominaModuleDocs = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 p-8">
      <div className="max-w-5xl mx-auto">
        <Link
          to="/dev/modules"
          className="inline-flex items-center gap-2 text-purple-400 hover:text-purple-300 mb-6 transition-colors"
        >
          <ArrowLeft size={20} />
          Volver al Showcase
        </Link>

        <div className="bg-gray-800/50 backdrop-blur-sm rounded-2xl p-8 border border-gray-700/50">
          <div className="flex items-center gap-4 mb-8">
            <div className="p-3 bg-gradient-to-br from-purple-500/20 to-pink-500/20 rounded-xl border border-purple-500/30">
              <FileText size={32} className="text-purple-400" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-white">Crear Cierre de Nómina</h1>
              <p className="text-gray-400">Módulo refactorizado para creación de cierres mensuales con checklist</p>
            </div>
          </div>

          {/* Descripción */}
          <section className="mb-8">
            <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
              <Package size={20} className="text-purple-400" />
              Descripción
            </h2>
            <p className="text-gray-300 leading-relaxed mb-4">
              Módulo completo para crear nuevos cierres mensuales de nómina. Incluye validación de acceso,
              verificación de cierres existentes, formulario con selector de periodo, y gestión de checklist
              de tareas comprometidas para el cierre.
            </p>
          </section>

          {/* Características */}
          <section className="mb-8">
            <h2 className="text-xl font-semibold text-white mb-4">Características Principales</h2>
            <ul className="space-y-2 text-gray-300">
              <li className="flex items-start gap-2">
                <span className="text-purple-400">•</span>
                <span>Validación de acceso al área de Nómina</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-purple-400">•</span>
                <span>Información del cliente con resumen de nómina</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-purple-400">•</span>
                <span>Verificación de cierres existentes antes de crear</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-purple-400">•</span>
                <span>Selector de periodo (mes y año)</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-purple-400">•</span>
                <span>Gestión de checklist de tareas (agregar/eliminar)</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-purple-400">•</span>
                <span>Validación de tareas antes de crear</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-purple-400">•</span>
                <span>Confirmación antes de crear (tareas no editables después)</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-purple-400">•</span>
                <span>Navegación automática al cierre creado</span>
              </li>
            </ul>
          </section>

          {/* Estructura */}
          <section className="mb-8">
            <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
              <Code size={20} className="text-purple-400" />
              Estructura del Módulo
            </h2>
            <div className="bg-gray-900/50 rounded-lg p-4 font-mono text-sm text-gray-300">
              <pre>{`src/modules/nomina/crear-cierre/
├── api/
│   └── crearCierre.api.js           # Endpoints
├── components/
│   ├── ClienteInfoCard.jsx           # Info del cliente
│   ├── FormularioCierre.jsx          # Formulario principal
│   └── ChecklistTareas.jsx           # Gestión de tareas
├── constants/
│   └── crearCierre.constants.js      # Mensajes y labels
├── pages/
│   └── CrearCierreNominaPage.jsx
├── utils/
│   └── crearCierreHelpers.js         # Validaciones
└── index.js                           # Exports`}</pre>
            </div>
          </section>

          {/* API */}
          <section className="mb-8">
            <h2 className="text-xl font-semibold text-white mb-4">Endpoints API</h2>
            <div className="space-y-3">
              <div className="bg-gray-900/50 rounded-lg p-4 border border-gray-700/50">
                <code className="text-green-400">GET /nomina/cierres/?cliente=:id&periodo=:periodo</code>
                <p className="text-gray-400 text-sm mt-2">Verifica si existe cierre para el periodo</p>
              </div>
              <div className="bg-gray-900/50 rounded-lg p-4 border border-gray-700/50">
                <code className="text-blue-400">POST /nomina/cierres/</code>
                <p className="text-gray-400 text-sm mt-2">Crea un nuevo cierre mensual con tareas</p>
                <div className="mt-2 text-xs text-gray-500">
                  Body: <code>{`{ cliente, periodo, tareas: [{descripcion: "..."}] }`}</code>
                </div>
              </div>
              <div className="bg-gray-900/50 rounded-lg p-4 border border-gray-700/50">
                <code className="text-green-400">GET /clientes/:id/</code>
                <p className="text-gray-400 text-sm mt-2">Obtiene información del cliente</p>
              </div>
              <div className="bg-gray-900/50 rounded-lg p-4 border border-gray-700/50">
                <code className="text-green-400">GET /nomina/clientes/:id/resumen/</code>
                <p className="text-gray-400 text-sm mt-2">Obtiene resumen de nómina (opcional)</p>
              </div>
            </div>
          </section>

          {/* Uso */}
          <section className="mb-8">
            <h2 className="text-xl font-semibold text-white mb-4 flex items-center gap-2">
              <Users size={20} className="text-purple-400" />
              Uso
            </h2>
            <div className="bg-gray-900/50 rounded-lg p-4">
              <code className="text-gray-300">
                {`import { CrearCierreNominaPage } from '@/modules/nomina/crear-cierre';

// En App.jsx
<Route path="/clientes/:clienteId/crear-cierre-nomina" 
       element={<CrearCierreNominaPage />} />`}
              </code>
            </div>
          </section>

          {/* Links */}
          <section>
            <h2 className="text-xl font-semibold text-white mb-4">Enlaces</h2>
            <div className="flex gap-4">
              <Link
                to="/dev/modules/crear-cierre-nomina/demo/1"
                className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors"
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

export default CrearCierreNominaModuleDocs;
