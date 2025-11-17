// src/pages/AuthModuleDocs.jsx
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
 * Página de documentación del módulo Auth
 */
const AuthModuleDocs = () => {
  const [activeSection, setActiveSection] = useState('overview');

  const sections = [
    { id: 'overview', label: 'Descripción General', icon: FiBook },
    { id: 'structure', label: 'Estructura', icon: FiLayers },
    { id: 'components', label: 'Componentes', icon: FiPackage },
    { id: 'usage', label: 'Uso', icon: FiCode },
    { id: 'context', label: 'Context & Hooks', icon: FiSettings },
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
                <h1 className="text-xl font-bold">Módulo Auth</h1>
                <p className="text-sm text-gray-400">Documentación Técnica</p>
              </div>
            </div>
            <Link
              to="/dev/modules/auth/demo"
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-medium transition-colors"
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
                        ? 'bg-blue-600 text-white'
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
                  <h2 className="text-3xl font-bold mb-4">🔐 Módulo Auth</h2>
                  <p className="text-gray-300 text-lg">
                    Módulo completo de autenticación con JWT, gestión de sesión y protección de rutas.
                  </p>

                  <div className="bg-gray-900 p-6 rounded-lg">
                    <h3 className="text-xl font-semibold mb-3">✨ Características</h3>
                    <ul className="space-y-2 text-gray-300">
                      <li className="flex items-start gap-2">
                        <span className="text-green-400 mt-1">✓</span>
                        <span>Autenticación JWT con refresh tokens</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-green-400 mt-1">✓</span>
                        <span>Context API para estado global de usuario</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-green-400 mt-1">✓</span>
                        <span>PrivateRoute con redirección automática</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-green-400 mt-1">✓</span>
                        <span>Formulario responsive con validación</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-green-400 mt-1">✓</span>
                        <span>Manejo de errores centralizado</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-green-400 mt-1">✓</span>
                        <span>Animaciones con Framer Motion</span>
                      </li>
                    </ul>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-indigo-900/30 border border-indigo-700 p-4 rounded-lg">
                      <div className="text-2xl font-bold text-indigo-400">12</div>
                      <div className="text-sm text-gray-400">Archivos</div>
                    </div>
                    <div className="bg-blue-900/30 border border-blue-700 p-4 rounded-lg">
                      <div className="text-2xl font-bold text-blue-400">~1200</div>
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
{`shared/auth/
├── api/
│   └── auth.api.js            # Cliente API de autenticación
├── components/
│   ├── DevModulesButton.jsx   # Botón dev showcase
│   ├── LoginForm.jsx          # Formulario de login
│   ├── LoginHeader.jsx        # Header del login
│   └── PrivateRoute.jsx       # HOC protección rutas
├── constants/
│   └── auth.constants.js      # Constantes y mensajes
├── contexts/
│   └── AuthContext.jsx        # Context de usuario
├── hooks/
│   └── useAuth.js             # Custom hook de auth
├── pages/
│   └── LoginPage.jsx          # Página principal login
├── router/
│   └── auth.routes.jsx        # Rutas del módulo
├── utils/
│   └── authHelpers.js         # Funciones helper
├── index.js                   # Exports públicos
└── README.md                  # Documentación`}
                    </pre>
                  </div>

                  <div className="space-y-4">
                    <h3 className="text-xl font-semibold">📁 Descripción de Carpetas</h3>
                    <div className="space-y-3">
                      <div className="bg-gray-900 p-4 rounded-lg">
                        <h4 className="font-semibold text-blue-400 mb-2">api/</h4>
                        <p className="text-gray-300 text-sm">
                          Cliente Axios configurado con interceptores para JWT y manejo de errores
                        </p>
                      </div>
                      <div className="bg-gray-900 p-4 rounded-lg">
                        <h4 className="font-semibold text-blue-400 mb-2">contexts/</h4>
                        <p className="text-gray-300 text-sm">
                          AuthContext con Provider para estado global de usuario autenticado
                        </p>
                      </div>
                      <div className="bg-gray-900 p-4 rounded-lg">
                        <h4 className="font-semibold text-blue-400 mb-2">hooks/</h4>
                        <p className="text-gray-300 text-sm">
                          useAuth() - Custom hook para acceder al contexto de autenticación
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
                      <h3 className="text-xl font-semibold text-blue-400 mb-3">LoginPage</h3>
                      <p className="text-gray-300 mb-4">Página principal de autenticación</p>
                      
                      <div className="bg-gray-800 p-4 rounded-lg mb-4">
                        <p className="text-sm text-gray-400 mb-2">Props:</p>
                        <code className="text-green-400 text-sm">Ninguna</code>
                      </div>

                      <div className="bg-gray-800 p-4 rounded-lg">
                        <p className="text-sm text-gray-400 mb-2">Ejemplo de uso:</p>
                        <pre className="text-green-400 text-sm">
{`<Route path="/login" element={<LoginPage />} />`}
                        </pre>
                      </div>
                    </div>

                    <div className="bg-gray-900 p-6 rounded-lg">
                      <h3 className="text-xl font-semibold text-blue-400 mb-3">LoginForm</h3>
                      <p className="text-gray-300 mb-4">Formulario de credenciales con validación</p>
                      
                      <div className="bg-gray-800 p-4 rounded-lg mb-4">
                        <p className="text-sm text-gray-400 mb-2">Props:</p>
                        <ul className="text-sm text-gray-300 space-y-1">
                          <li><code className="text-green-400">onSubmit</code>: (credentials) {'=>'} void</li>
                          <li><code className="text-green-400">loading</code>: boolean</li>
                          <li><code className="text-green-400">error</code>: string | null</li>
                        </ul>
                      </div>
                    </div>

                    <div className="bg-gray-900 p-6 rounded-lg">
                      <h3 className="text-xl font-semibold text-blue-400 mb-3">PrivateRoute</h3>
                      <p className="text-gray-300 mb-4">HOC para proteger rutas privadas</p>
                      
                      <div className="bg-gray-800 p-4 rounded-lg mb-4">
                        <p className="text-sm text-gray-400 mb-2">Props:</p>
                        <ul className="text-sm text-gray-300 space-y-1">
                          <li><code className="text-green-400">children</code>: ReactNode</li>
                          <li><code className="text-green-400">requiredRole</code>?: string (opcional)</li>
                        </ul>
                      </div>

                      <div className="bg-gray-800 p-4 rounded-lg">
                        <p className="text-sm text-gray-400 mb-2">Ejemplo de uso:</p>
                        <pre className="text-green-400 text-sm">
{`<PrivateRoute requiredRole="Gerente">
  <AdminPanel />
</PrivateRoute>`}
                        </pre>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {activeSection === 'usage' && (
                <div className="space-y-6">
                  <h2 className="text-3xl font-bold mb-4">💡 Uso del Módulo</h2>

                  <div className="bg-gray-900 p-6 rounded-lg">
                    <h3 className="text-xl font-semibold mb-4">1. Configurar el Provider</h3>
                    <pre className="bg-gray-800 p-4 rounded-lg text-green-400 text-sm overflow-x-auto">
{`import { AuthProvider } from './modules/shared/auth';

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          {/* rutas */}
        </Routes>
      </Router>
    </AuthProvider>
  );
}`}
                    </pre>
                  </div>

                  <div className="bg-gray-900 p-6 rounded-lg">
                    <h3 className="text-xl font-semibold mb-4">2. Usar el hook useAuth</h3>
                    <pre className="bg-gray-800 p-4 rounded-lg text-green-400 text-sm overflow-x-auto">
{`import { useAuth } from './modules/shared/auth';

function MiComponente() {
  const { user, login, logout, isAuthenticated } = useAuth();

  return (
    <div>
      {isAuthenticated ? (
        <p>Bienvenido {user.nombre}</p>
      ) : (
        <button onClick={login}>Iniciar sesión</button>
      )}
    </div>
  );
}`}
                    </pre>
                  </div>

                  <div className="bg-gray-900 p-6 rounded-lg">
                    <h3 className="text-xl font-semibold mb-4">3. Proteger rutas privadas</h3>
                    <pre className="bg-gray-800 p-4 rounded-lg text-green-400 text-sm overflow-x-auto">
{`import { PrivateRoute } from './modules/shared/auth';

<Route 
  path="/dashboard" 
  element={
    <PrivateRoute>
      <Dashboard />
    </PrivateRoute>
  } 
/>`}
                    </pre>
                  </div>
                </div>
              )}

              {activeSection === 'context' && (
                <div className="space-y-6">
                  <h2 className="text-3xl font-bold mb-4">⚙️ Context & Hooks</h2>

                  <div className="bg-gray-900 p-6 rounded-lg">
                    <h3 className="text-xl font-semibold text-blue-400 mb-3">AuthContext</h3>
                    <p className="text-gray-300 mb-4">Context que provee el estado de autenticación</p>
                    
                    <div className="bg-gray-800 p-4 rounded-lg">
                      <p className="text-sm text-gray-400 mb-2">Estado disponible:</p>
                      <ul className="text-sm text-gray-300 space-y-1">
                        <li><code className="text-green-400">user</code>: Usuario actual o null</li>
                        <li><code className="text-green-400">isAuthenticated</code>: boolean</li>
                        <li><code className="text-green-400">loading</code>: boolean</li>
                        <li><code className="text-green-400">login(credentials)</code>: Promise</li>
                        <li><code className="text-green-400">logout()</code>: void</li>
                      </ul>
                    </div>
                  </div>

                  <div className="bg-gray-900 p-6 rounded-lg">
                    <h3 className="text-xl font-semibold text-blue-400 mb-3">useAuth()</h3>
                    <p className="text-gray-300 mb-4">Hook personalizado para acceder al contexto</p>
                    
                    <div className="bg-gray-800 p-4 rounded-lg">
                      <p className="text-sm text-gray-400 mb-2">Ejemplo completo:</p>
                      <pre className="text-green-400 text-sm">
{`const { user, login, logout } = useAuth();

const handleLogin = async (credentials) => {
  try {
    await login(credentials);
    navigate('/dashboard');
  } catch (error) {
    console.error(error);
  }
};`}
                      </pre>
                    </div>
                  </div>
                </div>
              )}

              {activeSection === 'api' && (
                <div className="space-y-6">
                  <h2 className="text-3xl font-bold mb-4">📡 API Reference</h2>

                  <div className="bg-gray-900 p-6 rounded-lg">
                    <h3 className="text-xl font-semibold text-blue-400 mb-3">auth.api.js</h3>
                    
                    <div className="space-y-4">
                      <div className="bg-gray-800 p-4 rounded-lg">
                        <p className="text-sm font-semibold text-gray-400 mb-2">login(credentials)</p>
                        <p className="text-sm text-gray-300 mb-2">Autentica usuario con email y password</p>
                        <pre className="text-green-400 text-sm">
{`const response = await authApi.login({
  email: 'user@example.com',
  password: 'password123'
});
// Retorna: { token, user, refresh_token }`}
                        </pre>
                      </div>

                      <div className="bg-gray-800 p-4 rounded-lg">
                        <p className="text-sm font-semibold text-gray-400 mb-2">refreshToken()</p>
                        <p className="text-sm text-gray-300 mb-2">Refresca el token JWT expirado</p>
                        <pre className="text-green-400 text-sm">
{`const response = await authApi.refreshToken();
// Retorna: { token }`}
                        </pre>
                      </div>

                      <div className="bg-gray-800 p-4 rounded-lg">
                        <p className="text-sm font-semibold text-gray-400 mb-2">logout()</p>
                        <p className="text-sm text-gray-300 mb-2">Cierra sesión del usuario</p>
                        <pre className="text-green-400 text-sm">
{`await authApi.logout();
// Limpia tokens de localStorage`}
                        </pre>
                      </div>
                    </div>
                  </div>

                  <div className="bg-yellow-900/20 border border-yellow-700 p-4 rounded-lg">
                    <h4 className="font-semibold text-yellow-400 mb-2">⚠️ Nota Importante</h4>
                    <p className="text-sm text-gray-300">
                      El cliente API incluye interceptores automáticos para:
                    </p>
                    <ul className="text-sm text-gray-300 list-disc list-inside mt-2">
                      <li>Agregar el token JWT a cada request</li>
                      <li>Refrescar el token automáticamente si expira</li>
                      <li>Redirigir a /login si el refresh falla</li>
                    </ul>
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

export default AuthModuleDocs;
