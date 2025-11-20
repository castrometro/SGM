// src/pages/ModulesShowcase.jsx
import { Link } from 'react-router-dom';
import { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  FiPackage, 
  FiCheckCircle, 
  FiClock, 
  FiArrowRight,
  FiFileText,
  FiCode,
  FiLayers
} from 'react-icons/fi';
import { DevModulesButton } from '../modules/shared/auth';

/**
 * Página de showcase para módulos refactorizados
 * Accesible en desarrollo para probar nuevos módulos
 */
const ModulesShowcase = () => {
  const modules = [
    {
      id: 'auth',
      name: 'Autenticación (Login)',
      status: 'completed',
      description: 'Módulo completo de autenticación con JWT, validaciones y gestión de sesión',
      route: '/dev/modules/auth/demo',
      docsRoute: '/dev/modules/auth/docs',
      features: [
        'LoginPage refactorizada',
        'Utilidades de storage',
        'Validadores reutilizables',
        'Constantes centralizadas',
        'API mejorada con parseError'
      ],
      stats: {
        files: 11,
        lines: '~1,100',
        utils: 15,
        constants: '25+'
      }
    },
    {
      id: 'menu',
      name: 'Menú Principal',
      status: 'completed',
      description: 'Módulo de menú principal con opciones dinámicas por rol y área',
      route: '/dev/modules/menu/demo',
      docsRoute: '/dev/modules/menu/docs',
      features: [
        'MenuUsuarioPage refactorizada',
        'MenuCard componente reutilizable',
        'Configuración dinámica por roles',
        'Utilidades de menú (getUserMenuOptions, hasArea)',
        'Constantes centralizadas'
      ],
      stats: {
        files: 7,
        lines: '~600',
        utils: 2,
        constants: '6 grupos'
      }
    },
    {
      id: 'clientes',
      name: 'Gestión de Clientes',
      status: 'pending',
      description: 'Módulo para gestión completa de clientes (próximo)',
      route: null,
      features: [
        'Lista de clientes',
        'Detalle de cliente',
        'Crear/Editar cliente',
        'Asignación de analistas',
        'Historial de actividades'
      ]
    },
    {
      id: 'clientes-nomina',
      name: 'Clientes de Nómina',
      status: 'completed',
      description: 'Módulo de gestión de clientes del área de Nómina con dashboard integrado',
      route: '/dev/modules/clientes-nomina/demo',
      docsRoute: '/dev/modules/clientes-nomina/docs',
      features: [
        'ClientesNominaPage refactorizada',
        'Vista responsiva: Cards + Tabla',
        'Filtrado por tipo de usuario',
        'Estados de cierre con badges',
        'Integración con Dashboard Nómina',
        'Modo debug integrado'
      ],
      stats: {
        files: 11,
        lines: '~800',
        components: 7,
        constants: '5 grupos'
      }
    },
    {
      id: 'clientes-contabilidad',
      name: 'Clientes de Contabilidad',
      status: 'completed',
      description: 'Gestión de clientes con validación de acceso al área de Contabilidad',
      route: '/dev/modules/clientes-contabilidad/demo',
      docsRoute: '/dev/modules/clientes-contabilidad/docs',
      features: [
        'Validación de área Contabilidad',
        'Vista adaptativa (Card/Tabla)',
        'Estados de cierres con badges',
        'Búsqueda por nombre/RUT',
        'API diferenciada por rol'
      ],
      stats: {
        files: 11,
        lines: '~900',
        components: 6,
        endpoints: 5
      }
    },
    {
      id: 'herramientas-nomina',
      name: 'Herramientas de Nómina',
      status: 'completed',
      description: 'Centro de utilidades y recursos para gestión integral de nómina',
      route: '/dev/modules/herramientas-nomina/demo',
      docsRoute: '/dev/modules/herramientas-nomina/docs',
      features: [
        '4 categorías de herramientas',
        '15 herramientas configuradas',
        'Sistema de estados',
        'Estadísticas en tiempo real',
        'Tabs animados'
      ],
      stats: {
        files: 7,
        lines: '~800',
        tools: 15,
        categories: 4
      }
    },
    {
      id: 'herramientas-contabilidad',
      name: 'Herramientas de Contabilidad',
      status: 'completed',
      description: 'Centro de utilidades y recursos para gestión integral de contabilidad',
      route: '/dev/modules/herramientas-contabilidad/demo',
      docsRoute: '/dev/modules/herramientas-contabilidad/docs',
      features: [
        '4 categorías de herramientas',
        '17 herramientas configuradas',
        'Sistema de estados',
        'Estadísticas en tiempo real',
        'Tabs animados'
      ],
      stats: {
        files: 7,
        lines: '~850',
        tools: 17,
        categories: 4
      }
    },
    {
      id: 'cliente-detalle-nomina',
      name: 'Detalle de Cliente de Nómina',
      status: 'completed',
      description: 'Vista completa de cliente con KPIs del último cierre y acciones rápidas',
      route: '/dev/modules/cliente-detalle-nomina/demo',
      docsRoute: '/dev/modules/cliente-detalle-nomina/docs',
      features: [
        'Validación de acceso al área',
        'KPIs del último cierre',
        'Información del cliente con badges',
        '5 botones de acción rápida',
        'Fallback a datos básicos'
      ],
      stats: {
        files: 9,
        lines: '~650',
        components: 3,
        endpoints: 4
      }
    },
    {
      id: 'cliente-detalle-contabilidad',
      name: 'Detalle de Cliente de Contabilidad',
      status: 'completed',
      description: 'Vista completa de cliente con KPIs contables y análisis de balance',
      route: '/dev/modules/cliente-detalle-contabilidad/demo',
      docsRoute: '/dev/modules/cliente-detalle-contabilidad/docs',
      features: [
        'Validación de acceso a Contabilidad',
        'KPIs del último cierre contable',
        'Indicador de balance (debe/haber)',
        '5 botones de acción rápida',
        'Fallback a datos básicos'
      ],
      stats: {
        files: 9,
        lines: '~650',
        components: 3,
        endpoints: 4
      }
    },
    {
      id: 'historial-cierres-nomina',
      name: 'Historial de Cierres de Nómina',
      status: 'completed',
      description: 'Lista completa de cierres de nómina con filtros, estadísticas y auto-refresh',
      route: '/dev/modules/historial-cierres-nomina/demo',
      docsRoute: '/dev/modules/historial-cierres-nomina/docs',
      features: [
        'Auto-refresh cada 30s para cierres en proceso',
        'Filtros por estado (todos, finalizado, procesando, incidencias)',
        '4 estadísticas (Total, Finalizados, En Proceso, Con Incidencias)',
        'Navegación a detalle y libro de remuneraciones',
        'Validación de acceso a Nómina'
      ],
      stats: {
        files: 9,
        lines: '~750',
        components: 3,
        endpoints: 3
      }
    },
    {
      id: 'historial-cierres-contabilidad',
      name: 'Historial de Cierres de Contabilidad',
      status: 'completed',
      description: 'Lista completa de cierres contables con cuentas nuevas y estado de proceso',
      route: '/dev/modules/historial-cierres-contabilidad/demo',
      docsRoute: '/dev/modules/historial-cierres-contabilidad/docs',
      features: [
        'Tabla extendida con Cuentas Nuevas y Estado Proceso',
        'Badges de estado: Listo para finalizar, Generando reportes, Reportes disponibles',
        'Auto-refresh cada 30s',
        'Filtros por estado con contadores dinámicos',
        'Navegación a detalle y libro mayor'
      ],
      stats: {
        files: 9,
        lines: '~800',
        components: 3,
        endpoints: 3
      }
    },
    {
      id: 'cierre-detalle-nomina',
      name: 'Detalle de Cierre de Nómina',
      status: 'completed',
      description: 'Vista completa del progreso de un cierre de nómina con todas sus etapas, archivos y verificaciones',
      route: '/dev/modules/cierre-detalle-nomina/demo',
      docsRoute: '/dev/modules/cierre-detalle-nomina/docs',
      features: [
        '8+ secciones: Talana, Analista, Verificador, Incidencias, Resumen',
        '6+ tarjetas: Libro, Movimientos, Ingresos, Finiquitos, Ausentismos, Novedades',
        'Verificador de datos automático',
        'Gestión completa de incidencias',
        'Auto-actualización del estado'
      ],
      stats: {
        files: '28+',
        lines: '~1,200',
        components: '28+',
        endpoints: '50+'
      }
    },
    {
      id: 'captura-gastos',
      name: 'Captura Masiva de Gastos',
      status: 'completed',
      description: 'Herramienta para procesar gastos desde Excel de forma masiva, exclusiva para Contabilidad',
      route: '/dev/modules/captura-gastos/demo',
      docsRoute: '/dev/modules/captura-gastos/docs',
      features: [
        'Validación de acceso a Contabilidad',
        'Carga masiva desde Excel',
        'Validación de cuentas contables',
        'Mapeo de centros de costo',
        'Descarga de plantilla y resultados'
      ],
      stats: {
        files: 8,
        lines: '~700',
        hooks: 1,
        endpoints: 4
      }
    },
    {
      id: 'contabilidad',
      name: 'Contabilidad',
      status: 'pending',
      description: 'Módulo de cierres contables y clasificaciones',
      route: null,
      features: [
        'Historial de cierres',
        'Detalle de cierre',
        'Clasificación de cuentas',
        'Análisis de libro mayor',
        'Reportes contables'
      ]
    },
    {
      id: 'nomina',
      name: 'Nómina',
      status: 'pending',
      description: 'Módulo de procesamiento de nómina y remuneraciones',
      route: null,
      features: [
        'Libro de remuneraciones',
        'Movimientos del mes',
        'Gestión de incidencias',
        'Dashboard de nómina',
        'Reportes de variaciones'
      ]
    }
  ];

  const getStatusBadge = (status) => {
    const configs = {
      completed: {
        icon: FiCheckCircle,
        text: 'Completado',
        className: 'bg-green-100 text-green-800 border-green-200'
      },
      pending: {
        icon: FiClock,
        text: 'Pendiente',
        className: 'bg-yellow-100 text-yellow-800 border-yellow-200'
      }
    };

    const config = configs[status];
    const Icon = config.icon;

    return (
      <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium border ${config.className}`}>
        <Icon size={14} />
        {config.text}
      </span>
    );
  };

  /**
   * Componente especial para módulos que necesitan parámetros
   */
  const ModuleCardWithInput = ({ module }) => {
    const [clienteId, setClienteId] = useState('1');

    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden hover:shadow-md transition-shadow"
      >
        {/* Header */}
        <div className="p-6 border-b border-gray-100">
          <div className="flex items-start justify-between mb-3">
            <h3 className="text-lg font-semibold text-gray-900">{module.name}</h3>
            {getStatusBadge(module.status)}
          </div>
          <p className="text-sm text-gray-600 leading-relaxed">{module.description}</p>
        </div>

        {/* Features */}
        <div className="px-6 py-4 bg-gray-50">
          <h4 className="text-xs font-semibold text-gray-500 uppercase mb-2">Características</h4>
          <ul className="space-y-1">
            {module.features.map((feature, idx) => (
              <li key={idx} className="flex items-start gap-2 text-sm text-gray-700">
                <FiCheckCircle size={16} className="text-green-500 flex-shrink-0 mt-0.5" />
                <span>{feature}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Stats */}
        {module.stats && (
          <div className="px-6 py-4 border-t border-gray-100">
            <div className="grid grid-cols-2 gap-3">
              {Object.entries(module.stats).map(([key, value]) => (
                <div key={key} className="text-center p-2 bg-white rounded-lg border border-gray-200">
                  <div className="text-xl font-bold text-gray-900">{value}</div>
                  <div className="text-xs text-gray-500 capitalize">{key}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Actions con Input */}
        <div className="p-6 bg-gray-50 border-t border-gray-200">
          <div className="mb-3">
            <label htmlFor={`clienteId-${module.id}`} className="block text-sm font-medium text-gray-700 mb-2">
              🔢 ID del Cliente para Demo:
            </label>
            <input
              type="number"
              id={`clienteId-${module.id}`}
              value={clienteId}
              onChange={(e) => setClienteId(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
              min="1"
              placeholder="Ingrese ID del cliente"
            />
          </div>
          <div className="flex gap-2">
            <Link
              to={`${module.route}/${clienteId}`}
              className="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2 bg-gradient-to-r from-teal-600 to-teal-700 text-white rounded-lg text-sm font-medium hover:from-teal-700 hover:to-teal-800 transition-all"
            >
              Ver Demo (Cliente {clienteId})
              <FiArrowRight size={14} />
            </Link>
            {module.docsRoute && (
              <Link
                to={module.docsRoute}
                className="px-4 py-2 bg-white hover:bg-gray-100 text-gray-700 rounded-lg text-sm font-medium transition-colors border border-gray-300"
              >
                <FiFileText size={16} />
              </Link>
            )}
          </div>
        </div>
      </motion.div>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-red-600 to-red-700 rounded-lg flex items-center justify-center">
                <FiLayers className="text-white" size={20} />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">Módulos Refactorizados</h1>
                <p className="text-sm text-gray-500">Showcase de arquitectura modular SGM</p>
              </div>
            </div>
            
            <div className="flex items-center gap-3">
              <span className="px-3 py-1.5 bg-yellow-100 text-yellow-800 rounded-full text-xs font-medium border border-yellow-200">
                🚧 Desarrollo
              </span>
              <Link 
                to="/menu" 
                className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg text-sm font-medium transition-colors"
              >
                Volver al Sistema
              </Link>
            </div>
          </div>
        </div>
      </header>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Intro */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-blue-50 border border-blue-200 rounded-xl p-6 mb-8"
        >
          <div className="flex items-start gap-4">
            <div className="w-12 h-12 bg-blue-600 rounded-lg flex items-center justify-center flex-shrink-0">
              <FiPackage className="text-white" size={24} />
            </div>
            <div className="flex-1">
              <h2 className="text-lg font-semibold text-blue-900 mb-2">
                🎯 Objetivo de la Refactorización
              </h2>
              <p className="text-blue-800 text-sm leading-relaxed mb-3">
                Esta página muestra todos los módulos que están siendo refactorizados siguiendo 
                el nuevo patrón de arquitectura modular. Cada módulo es autocontenido, 
                documentado y reutilizable.
              </p>
              <div className="flex flex-wrap gap-2">
                <Link 
                  to="/dev/modules/docs" 
                  className="inline-flex items-center gap-2 px-3 py-1.5 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
                >
                  <FiFileText size={14} />
                  Ver Documentación
                </Link>
                <a 
                  href="https://github.com/castrometro/SGM" 
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 px-3 py-1.5 bg-white border border-blue-200 text-blue-600 rounded-lg text-sm font-medium hover:bg-blue-50 transition-colors"
                >
                  <FiCode size={14} />
                  Ver Código en GitHub
                </a>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Modules Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {modules.map((module, index) => {
            // Usar componente especial para módulos con input de ID
            if (module.id === 'cliente-detalle-nomina' || 
                module.id === 'cliente-detalle-contabilidad' ||
                module.id === 'historial-cierres-nomina' ||
                module.id === 'historial-cierres-contabilidad' ||
                module.id === 'cierre-detalle-nomina') {
              return (
                <ModuleCardWithInput 
                  key={module.id} 
                  module={module} 
                />
              );
            }

            // Componente normal para otros módulos
            return (
              <motion.div
                key={module.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className="bg-white rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-shadow"
              >
                {/* Header */}
                <div className="p-6 border-b border-gray-100">
                  <div className="flex items-start justify-between mb-3">
                    <h3 className="text-lg font-semibold text-gray-900">{module.name}</h3>
                    {getStatusBadge(module.status)}
                  </div>
                  <p className="text-sm text-gray-600 leading-relaxed">
                    {module.description}
                  </p>
                </div>

              {/* Features */}
              <div className="p-6 border-b border-gray-100">
                <h4 className="text-sm font-medium text-gray-700 mb-3">Características:</h4>
                <ul className="space-y-2">
                  {module.features.map((feature, idx) => (
                    <li key={idx} className="flex items-start gap-2 text-sm text-gray-600">
                      <FiCheckCircle className="text-green-500 flex-shrink-0 mt-0.5" size={16} />
                      <span>{feature}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Stats (solo para módulos completados) */}
              {module.stats && (
                <div className="p-6 bg-gray-50 border-b border-gray-100">
                  <h4 className="text-sm font-medium text-gray-700 mb-3">Estadísticas:</h4>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="text-center p-2 bg-white rounded-lg border border-gray-200">
                      <div className="text-xl font-bold text-gray-900">{module.stats.files}</div>
                      <div className="text-xs text-gray-500">Archivos</div>
                    </div>
                    <div className="text-center p-2 bg-white rounded-lg border border-gray-200">
                      <div className="text-xl font-bold text-gray-900">{module.stats.lines}</div>
                      <div className="text-xs text-gray-500">Líneas</div>
                    </div>
                    <div className="text-center p-2 bg-white rounded-lg border border-gray-200">
                      <div className="text-xl font-bold text-gray-900">{module.stats.utils}</div>
                      <div className="text-xs text-gray-500">Utilidades</div>
                    </div>
                    <div className="text-center p-2 bg-white rounded-lg border border-gray-200">
                      <div className="text-xl font-bold text-gray-900">{module.stats.constants}</div>
                      <div className="text-xs text-gray-500">Constantes</div>
                    </div>
                  </div>
                </div>
              )}

              {/* Actions */}
              <div className="p-6">
                <div className="flex gap-2">
                  {module.route ? (
                    <>
                      <Link
                        to={module.route}
                        className="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2 bg-gradient-to-r from-red-600 to-red-700 text-white rounded-lg text-sm font-medium hover:from-red-700 hover:to-red-800 transition-all"
                      >
                        Ver Demo
                        <FiArrowRight size={14} />
                      </Link>
                      {module.docsRoute && (
                        <Link
                          to={module.docsRoute}
                          className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg text-sm font-medium transition-colors"
                        >
                          <FiFileText size={16} />
                        </Link>
                      )}
                    </>
                  ) : (
                    <button
                      disabled
                      className="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2 bg-gray-100 text-gray-400 rounded-lg text-sm font-medium cursor-not-allowed"
                    >
                      Próximamente
                      <FiClock size={14} />
                    </button>
                  )}
                </div>
              </div>
            </motion.div>
            );
          })}
        </div>

        {/* Footer Info */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
          className="mt-8 bg-white rounded-xl border border-gray-200 p-6"
        >
          <h3 className="text-lg font-semibold text-gray-900 mb-4">📚 Documentación del Proyecto</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Link
              to="/dev/modules/docs?doc=estado-actual"
              className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <h4 className="font-medium text-gray-900 mb-1">Estado Actual</h4>
              <p className="text-sm text-gray-600">Análisis del sistema antes de refactorizar</p>
            </Link>
            <Link
              to="/dev/modules/docs?doc=propuesta"
              className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <h4 className="font-medium text-gray-900 mb-1">Propuesta</h4>
              <p className="text-sm text-gray-600">Arquitectura y patrón de diseño modular</p>
            </Link>
            <Link
              to="/dev/modules/docs?doc=guia-rapida"
              className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <h4 className="font-medium text-gray-900 mb-1">Guía Rápida</h4>
              <p className="text-sm text-gray-600">Implementación y uso de módulos</p>
            </Link>
          </div>
        </motion.div>
      </div>

      {/* Botón flotante de desarrollo */}
      <DevModulesButton />
    </div>
  );
};

export default ModulesShowcase;
