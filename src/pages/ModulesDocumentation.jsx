// src/pages/ModulesDocumentation.jsx
import { Link, useNavigate } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { 
  FiChevronRight,
  FiCopy,
  FiCheck,
  FiBook,
  FiLayers,
  FiFileText,
  FiGitBranch,
  FiArrowLeft
} from 'react-icons/fi';
import { DevModulesButton } from '../modules/shared/auth';

// Componente simple para renderizar markdown
const DocsViewer = ({ markdown }) => {
  return (
    <div className="prose prose-invert max-w-none">
      <pre className="whitespace-pre-wrap text-gray-300 text-sm font-mono p-4 bg-gray-900 rounded-lg">
        {markdown}
      </pre>
    </div>
  );
};/**
 * Página de documentación de módulos refactorizados
 * Muestra enlaces a todos los documentos MD generados
 */
const ModulesDocumentation = () => {
  const navigate = useNavigate();

  // Documentos disponibles con path relativo interno y raw import dinámico
  const documents = [
    {
      id: 'index',
      title: 'Índice General',
      description: 'Navegación completa de toda la documentación de refactorización',
      file: 'README.md',
      icon: FiBook,
      color: 'blue',
      path: '/docs/refactorizacion/README.md'
    },
    {
      id: 'principio-colocacion',
      title: '06 - Principio de Colocación',
      description: 'Reglas de oro para mantener módulos autocontenidos con casos prácticos',
      file: '06_PRINCIPIO_COLOCACION.md',
      icon: FiLayers,
      color: 'indigo',
      path: '/docs/refactorizacion/06_PRINCIPIO_COLOCACION.md',
      stats: '500+ líneas'
    },
    {
      id: 'correccion-colocacion',
      title: 'Corrección: Principio de Colocación',
      description: 'Bitácora de la corrección aplicada al componente DevModulesButton',
      file: 'CORRECCION_PRINCIPIO_COLOCACION.md',
      icon: FiFileText,
      color: 'purple',
      path: '/docs/refactorizacion/CORRECCION_PRINCIPIO_COLOCACION.md',
      stats: 'Resumen'
    },
    {
      id: 'estado-actual',
      title: '01 - Estado Actual del Login',
      description: 'Análisis exhaustivo de la implementación actual del módulo de autenticación',
      file: '01_LOGIN_ESTADO_ACTUAL.md',
      icon: FiFileText,
      color: 'purple',
      path: '/docs/refactorizacion/01_LOGIN_ESTADO_ACTUAL.md',
      stats: '650 líneas'
    },
    {
      id: 'propuesta',
      title: '02 - Propuesta de Estructura Modular',
      description: 'Diseño arquitectónico y patrón reproducible para todos los módulos',
      file: '02_PROPUESTA_ESTRUCTURA_MODULAR.md',
      icon: FiLayers,
      color: 'green',
      path: '/docs/refactorizacion/02_PROPUESTA_ESTRUCTURA_MODULAR.md',
      stats: '800 líneas'
    },
    {
      id: 'resumen',
      title: '03 - Resumen de Refactorización',
      description: 'Resumen ejecutivo, comparaciones y beneficios logrados',
      file: '03_RESUMEN_REFACTORIZACION.md',
      icon: FiFileText,
      color: 'yellow',
      path: '/docs/refactorizacion/03_RESUMEN_REFACTORIZACION.md',
      stats: '900 líneas'
    },
    {
      id: 'arbol',
      title: '04 - Árbol de Estructura Auth',
      description: 'Visualización detallada del árbol de archivos y dependencias',
      file: '04_ARBOL_ESTRUCTURA_AUTH.md',
      icon: FiGitBranch,
      color: 'indigo',
      path: '/docs/refactorizacion/04_ARBOL_ESTRUCTURA_AUTH.md',
      stats: '400 líneas'
    },
    {
      id: 'guia-rapida',
      title: '05 - Guía Rápida de Implementación',
      description: 'Guía práctica paso a paso para usar y aplicar el patrón',
      file: '05_GUIA_RAPIDA_IMPLEMENTACION.md',
      icon: FiFileText,
      color: 'red',
      path: '/docs/refactorizacion/05_GUIA_RAPIDA_IMPLEMENTACION.md',
      stats: '500 líneas'
    },
    {
      id: 'auth-readme',
      title: 'README - Módulo Auth',
      description: 'Documentación completa del módulo de autenticación refactorizado',
      file: 'shared/auth/README.md',
      icon: FiBook,
      color: 'pink',
      path: '/src/modules/shared/auth/README.md',
      stats: '850 líneas'
    }
  ];

  const getColorClasses = (color) => {
    const colors = {
      blue: 'from-blue-500 to-blue-600 border-blue-200 bg-blue-50',
      purple: 'from-purple-500 to-purple-600 border-purple-200 bg-purple-50',
      green: 'from-green-500 to-green-600 border-green-200 bg-green-50',
      yellow: 'from-yellow-500 to-yellow-600 border-yellow-200 bg-yellow-50',
      indigo: 'from-indigo-500 to-indigo-600 border-indigo-200 bg-indigo-50',
      red: 'from-red-500 to-red-600 border-red-200 bg-red-50',
      pink: 'from-pink-500 to-pink-600 border-pink-200 bg-pink-50'
    };
    return colors[color] || colors.blue;
  };

  const openInVSCode = (path) => {
    // Esta funcionalidad abre el archivo en VS Code
    // En un ambiente real, esto podría usar vscode:// protocol
    console.log('Abrir en VS Code:', path);
    alert(`Archivo: ${path}\n\nEn VS Code, abre: /root/SGM${path}`);
  };

  // Determinar documento seleccionado via query (?doc=ID)
  const params = new URLSearchParams(window.location.search);
  const selectedId = params.get('doc');
  const selected = documents.find(d => d.id === selectedId);

  // Estado y efecto para cargar markdown seleccionado
  const [markdownContent, setMarkdownContent] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    const load = async () => {
      if (!selected) {
        setMarkdownContent('');
        setError('');
        return;
      }
      setLoading(true);
      setError('');
      try {
        const rawMap = {
          'index': () => import('../../docs/refactorizacion/README.md?raw'),
          'estado-actual': () => import('../../docs/refactorizacion/01_LOGIN_ESTADO_ACTUAL.md?raw'),
          'propuesta': () => import('../../docs/refactorizacion/02_PROPUESTA_ESTRUCTURA_MODULAR.md?raw'),
          'resumen': () => import('../../docs/refactorizacion/03_RESUMEN_REFACTORIZACION.md?raw'),
          'arbol': () => import('../../docs/refactorizacion/04_ARBOL_ESTRUCTURA_AUTH.md?raw'),
          'guia-rapida': () => import('../../docs/refactorizacion/05_GUIA_RAPIDA_IMPLEMENTACION.md?raw'),
          'principio-colocacion': () => import('../../docs/refactorizacion/06_PRINCIPIO_COLOCACION.md?raw'),
          'correccion-colocacion': () => import('../../docs/refactorizacion/CORRECCION_PRINCIPIO_COLOCACION.md?raw'),
          'auth-readme': () => import('../modules/shared/auth/README.md?raw'),
        };
        const loader = rawMap[selected.id];
        if (!loader) {
          setMarkdownContent('# No disponible');
        } else {
          const mod = await loader();
          setMarkdownContent(mod.default || String(mod));
        }
      } catch (e) {
        setError(String(e));
      } finally {
        setLoading(false);
      }
    };
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedId]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <button
                onClick={() => navigate('/dev/modules')}
                className="w-10 h-10 bg-gray-100 hover:bg-gray-200 rounded-lg flex items-center justify-center transition-colors"
              >
                <FiArrowLeft size={20} />
              </button>
              <div>
                <h1 className="text-xl font-bold text-gray-900">Documentación de Módulos</h1>
                <p className="text-sm text-gray-500">Toda la documentación generada</p>
              </div>
            </div>
            
            <Link 
              to="/menu" 
              className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg text-sm font-medium transition-colors"
            >
              Volver al Sistema
            </Link>
          </div>
        </div>
      </header>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8"
        >
          <div className="bg-white rounded-lg border border-gray-200 p-6 text-center">
            <div className="text-3xl font-bold text-gray-900 mb-1">9</div>
            <div className="text-sm text-gray-600">Documentos</div>
          </div>
          <div className="bg-white rounded-lg border border-gray-200 p-6 text-center">
            <div className="text-3xl font-bold text-gray-900 mb-1">~3,500</div>
            <div className="text-sm text-gray-600">Líneas escritas</div>
          </div>
          <div className="bg-white rounded-lg border border-gray-200 p-6 text-center">
            <div className="text-3xl font-bold text-gray-900 mb-1">1</div>
            <div className="text-sm text-gray-600">Módulo completado</div>
          </div>
          <div className="bg-white rounded-lg border border-gray-200 p-6 text-center">
            <div className="text-3xl font-bold text-gray-900 mb-1">100%</div>
            <div className="text-sm text-gray-600">Documentado</div>
          </div>
        </motion.div>

        {/* Layout dividido: lista + visor */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Lista de documentos */}
          <div className="lg:col-span-5 space-y-6">
            <div className="bg-white rounded-xl border border-gray-200 p-4">
              <h2 className="text-lg font-semibold text-gray-900 mb-2 flex items-center gap-2">
                <FiFileText /> Documentos
              </h2>
              <p className="text-sm text-gray-600 mb-4">Selecciona un documento para visualizarlo. Uso de query ?doc=ID</p>
              <div className="space-y-3">
                {documents.map((doc) => {
                  const Icon = doc.icon;
                  const active = doc.id === selectedId;
                  return (
                    <Link
                      key={doc.id}
                      to={`?doc=${doc.id}`}
                      className={`flex items-start gap-3 px-3 py-3 rounded-lg border transition-all ${active ? 'bg-gray-900 border-gray-800 text-white shadow' : 'bg-gray-50 border-gray-200 hover:bg-gray-100'}`}
                    >
                      <div className={`w-10 h-10 rounded-md flex items-center justify-center ${active ? 'bg-gray-800' : 'bg-white border border-gray-200'}`}>
                        <Icon size={20} className={active ? 'text-white' : 'text-gray-700'} />
                      </div>
                      <div className="flex-1">
                        <div className={`text-sm font-semibold mb-0.5 ${active ? 'text-white' : 'text-gray-900'}`}>{doc.title}</div>
                        <div className={`text-xs leading-relaxed ${active ? 'text-gray-300' : 'text-gray-600'}`}>{doc.description}</div>
                        {doc.stats && (
                          <span className={`inline-block mt-1 px-2 py-0.5 text-[10px] rounded ${active ? 'bg-gray-800 text-gray-200' : 'bg-white border border-gray-200 text-gray-600'}`}>{doc.stats}</span>
                        )}
                      </div>
                    </Link>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Visor de documentación */}
          <div className="lg:col-span-7">
            <div className="bg-[#0d1117] rounded-xl border border-gray-800 p-0 shadow-inner min-h-[480px] overflow-hidden">
              {selected ? (
                <>
                  <div className="mb-4 flex items-center justify-between">
                    <h2 className="text-xl font-bold text-white flex items-center gap-2">
                      <FiBook /> {selected.title}
                    </h2>
                    <div className="flex gap-2">
                      <a
                        href={`https://github.com/castrometro/SGM/blob/main${selected.path}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="px-3 py-1.5 text-xs rounded bg-indigo-600 hover:bg-indigo-700 text-white font-medium"
                      >
                        GitHub
                      </a>
                    </div>
                  </div>
                  {/* Render del contenido */}
                  <div className="h-[400px] overflow-y-auto custom-scrollbar pr-2">
                    {loading ? (
                      <div className="text-sm text-gray-300 italic p-4">Cargando documento...</div>
                    ) : error ? (
                      <div className="text-sm text-red-300 p-4">Error: {error}</div>
                    ) : markdownContent ? (
                      <DocsViewer markdown={markdownContent} />
                    ) : (
                      <div className="text-sm text-gray-400 p-4">Sin contenido disponible.</div>
                    )}
                  </div>
                </>
              ) : (
                <div className="h-full flex items-center justify-center text-gray-400 text-sm">
                  Selecciona un documento a la izquierda.
                </div>
              )}
            </div>
          </div>
        </div>
        

  {/* Info Box */}
  <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4 }}
          className="mt-8 bg-blue-50 border border-blue-200 rounded-xl p-6"
        >
          <h3 className="text-lg font-semibold text-blue-900 mb-2">
            📂 Ubicación de los Archivos
          </h3>
          <p className="text-blue-800 text-sm mb-4">
            Todos los documentos se encuentran en el directorio raíz del proyecto:
          </p>
          <div className="bg-white rounded-lg border border-blue-200 p-4">
            <code className="text-sm text-gray-700 font-mono">
              /root/SGM/docs/refactorizacion/<br />
              /root/SGM/src/modules/shared/auth/README.md
            </code>
          </div>
        </motion.div>
      </div>

      {/* Botón flotante de desarrollo */}
      <DevModulesButton />
    </div>
  );
};

export default ModulesDocumentation;
