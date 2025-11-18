// src/pages/CapturaGastosModuleDocs.jsx
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
 * Página de documentación del módulo Captura Masiva de Gastos
 */
const CapturaGastosModuleDocs = () => {
  const [activeSection, setActiveSection] = useState('overview');

  const sections = [
    { id: 'overview', label: 'Descripción General', icon: FiBook },
    { id: 'structure', label: 'Estructura', icon: FiLayers },
    { id: 'components', label: 'Componentes', icon: FiPackage },
    { id: 'api', label: 'API', icon: FiDatabase },
    { id: 'backend', label: 'Backend (814 líneas)', icon: FiCode },
    { id: 'flujo', label: 'Flujo de Procesamiento', icon: FiLayers },
    { id: 'problemas', label: 'Problemas Detectados', icon: FiShield },
    { id: 'mejoras', label: 'Mejoras Sugeridas', icon: FiPackage },
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
                <h1 className="text-xl font-bold">Módulo Captura Masiva de Gastos</h1>
                <p className="text-sm text-gray-400">Documentación Técnica</p>
              </div>
            </div>
            <Link
              to="/dev/modules/captura-gastos/demo"
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
                  <h2 className="text-3xl font-bold mb-4">💰 Módulo Captura Masiva de Gastos</h2>
                  <p className="text-gray-300 text-lg">
                    Herramienta para procesar gastos desde archivos Excel de forma masiva, exclusiva para Contabilidad.
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
                        <span>Carga masiva desde archivos Excel (.xlsx, .xls)</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-green-400 mt-1">✓</span>
                        <span>Validación de cuentas contables</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-green-400 mt-1">✓</span>
                        <span>Mapeo de centros de costo</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-green-400 mt-1">✓</span>
                        <span>Descarga de plantilla y resultados</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <span className="text-green-400 mt-1">✓</span>
                        <span>Procesamiento asíncrono con feedback en tiempo real</span>
                      </li>
                    </ul>
                  </div>

                  <div className="grid grid-cols-3 gap-4">
                    <div className="bg-purple-900/30 border border-purple-700 p-4 rounded-lg">
                      <div className="text-2xl font-bold text-purple-400">8</div>
                      <div className="text-sm text-gray-400">Archivos</div>
                    </div>
                    <div className="bg-purple-900/30 border border-purple-700 p-4 rounded-lg">
                      <div className="text-2xl font-bold text-purple-400">1</div>
                      <div className="text-sm text-gray-400">Hook Custom</div>
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
{`contabilidad/captura-gastos/
├── api/
│   └── capturaGastos.api.js
├── constants/
│   └── capturaGastos.constants.js
├── hooks/
│   └── useCapturaGastos.js
├── pages/
│   └── CapturaGastosPage.jsx
├── router/
│   └── CapturaGastosRouter.jsx
├── utils/
│   └── capturaGastosHelpers.js
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
                      <h4 className="font-semibold text-purple-400 mb-2">CapturaGastosPage</h4>
                      <p className="text-sm text-gray-300">Página principal con validación de acceso, formulario de carga y procesamiento de gastos</p>
                    </div>
                    
                    <div className="bg-gray-900 p-4 rounded-lg">
                      <h4 className="font-semibold text-purple-400 mb-2">useCapturaGastos (Hook)</h4>
                      <p className="text-sm text-gray-300">Maneja toda la lógica de carga, procesamiento y descarga de archivos</p>
                    </div>
                  </div>
                </div>
              )}

              {activeSection === 'api' && (
                <div className="space-y-6">
                  <h2 className="text-3xl font-bold mb-4">📡 API</h2>
                  
                  <div className="space-y-4">
                    <div className="bg-gray-900 p-4 rounded-lg">
                      <code className="text-purple-400">leerHeadersExcel(archivo)</code>
                      <p className="text-sm text-gray-300 mt-2">POST /contabilidad/rindegastos/leer-headers/ - Lee headers del Excel y detecta centros de costo</p>
                    </div>
                    
                    <div className="bg-gray-900 p-4 rounded-lg">
                      <code className="text-purple-400">iniciarProcesamiento(archivo, mapeoCC, parametrosContables)</code>
                      <p className="text-sm text-gray-300 mt-2">POST /contabilidad/rindegastos/step1/iniciar/ - Inicia procesamiento asíncrono, retorna task_id</p>
                    </div>
                    
                    <div className="bg-gray-900 p-4 rounded-lg">
                      <code className="text-purple-400">consultarEstado(taskId)</code>
                      <p className="text-sm text-gray-300 mt-2">GET /contabilidad/rindegastos/step1/estado/{'{taskId}'}/ - Consulta estado del procesamiento</p>
                    </div>

                    <div className="bg-gray-900 p-4 rounded-lg">
                      <code className="text-purple-400">descargarProcesado(taskId)</code>
                      <p className="text-sm text-gray-300 mt-2">GET /contabilidad/rindegastos/step1/descargar/{'{taskId}'}/ - Descarga archivo procesado (blob)</p>
                    </div>
                  </div>
                </div>
              )}

              {activeSection === 'backend' && (
                <div className="space-y-6">
                  <h2 className="text-3xl font-bold mb-4">🔧 Backend - Análisis Completo (814 líneas)</h2>
                  
                  <div className="bg-blue-900/30 border border-blue-700 p-4 rounded-lg mb-6">
                    <p className="text-blue-200 text-sm">
                      <strong>Archivos analizados:</strong> views/rindegastos.py (231 líneas) + task_rindegastos.py (583 líneas)
                    </p>
                  </div>

                  <div className="space-y-6">
                    <div className="bg-gray-900 p-6 rounded-lg">
                      <h3 className="text-xl font-semibold mb-4 text-purple-400">🏗️ Arquitectura del Sistema</h3>
                      <div className="bg-gray-800 p-4 rounded text-center font-mono text-sm mb-4">
                        Usuario → Frontend → API View → Celery Task → Redis → Descarga Excel
                      </div>
                      <div className="space-y-3 text-gray-300">
                        <div className="flex items-start gap-3">
                          <span className="text-green-400 mt-1">✓</span>
                          <div>
                            <p className="font-semibold">View (procesar_step1_rindegastos)</p>
                            <p className="text-sm text-gray-400">Valida parámetros y encola task en Celery</p>
                          </div>
                        </div>
                        <div className="flex items-start gap-3">
                          <span className="text-green-400 mt-1">✓</span>
                          <div>
                            <p className="font-semibold">Task (rg_procesar_step1_task)</p>
                            <p className="text-sm text-gray-400">Procesa archivo y guarda en Redis (TTL 300s)</p>
                          </div>
                        </div>
                        <div className="flex items-start gap-3">
                          <span className="text-green-400 mt-1">✓</span>
                          <div>
                            <p className="font-semibold">Polling Frontend</p>
                            <p className="text-sm text-gray-400">Consulta estado cada 3 segundos</p>
                          </div>
                        </div>
                      </div>
                    </div>

                    <div className="bg-gray-900 p-6 rounded-lg">
                      <h3 className="text-xl font-semibold mb-4 text-purple-400">📋 Paso a Paso del Procesamiento</h3>
                      
                      <div className="space-y-4">
                        <details className="bg-gray-800 p-4 rounded-lg">
                          <summary className="cursor-pointer font-semibold text-purple-300">Paso 1: Validación inicial</summary>
                          <p className="text-sm text-gray-400 mt-2">Parámetros contables obligatorios: iva, proveedores, gasto_default</p>
                        </details>

                        <details className="bg-gray-800 p-4 rounded-lg">
                          <summary className="cursor-pointer font-semibold text-purple-300">Paso 2: Lectura del Excel</summary>
                          <ul className="list-disc list-inside space-y-1 text-sm text-gray-400 mt-2">
                            <li>Lee headers (fila 1)</li>
                            <li>Detecta columnas: Tipo Doc, Monto Exento, Folio, RUT Proveedor, Fecha Docto, Monto Neto</li>
                            <li>Detecta rango de CC entre "Nombre cuenta" y "Fecha aprobacion"</li>
                          </ul>
                        </details>

                        <details className="bg-gray-800 p-4 rounded-lg">
                          <summary className="cursor-pointer font-semibold text-purple-300">Paso 3: Agrupación de filas</summary>
                          <ul className="list-disc list-inside space-y-1 text-sm text-gray-400 mt-2">
                            <li>Lee desde fila 2 (asume headers en fila 1)</li>
                            <li>Cuenta CC válidos: valores != 0 o strings no vacíos</li>
                            <li>Agrupa por: "{'{'}tipo_doc{'}'} con {'{'}cc_count{'}'}CC"</li>
                          </ul>
                        </details>

                        <details className="bg-gray-800 p-4 rounded-lg" open>
                          <summary className="cursor-pointer font-semibold text-purple-300">Paso 4: Lógica por Tipo de Documento</summary>
                          <div className="mt-3 overflow-x-auto">
                            <table className="w-full text-sm">
                              <thead className="bg-gray-700">
                                <tr>
                                  <th className="px-3 py-2 text-left">Tipo</th>
                                  <th className="px-3 py-2 text-left">Descripción</th>
                                  <th className="px-3 py-2 text-left">Filas generadas</th>
                                </tr>
                              </thead>
                              <tbody className="divide-y divide-gray-700">
                                <tr>
                                  <td className="px-3 py-2">33, 64</td>
                                  <td className="px-3 py-2">Factura Afecta</td>
                                  <td className="px-3 py-2">IVA + Proveedor + Gastos</td>
                                </tr>
                                <tr>
                                  <td className="px-3 py-2">34</td>
                                  <td className="px-3 py-2">Factura Exenta</td>
                                  <td className="px-3 py-2">Proveedor + Gastos (sin IVA)</td>
                                </tr>
                                <tr>
                                  <td className="px-3 py-2">COMO</td>
                                  <td className="px-3 py-2">Similar a 34</td>
                                  <td className="px-3 py-2">Sin Monto Detalle</td>
                                </tr>
                                <tr>
                                  <td className="px-3 py-2">61</td>
                                  <td className="px-3 py-2">Nota de Crédito</td>
                                  <td className="px-3 py-2">Invertido tipo 33</td>
                                </tr>
                                <tr className="bg-red-900/30">
                                  <td className="px-3 py-2 text-red-400">Otros</td>
                                  <td className="px-3 py-2 text-red-400">No soportado</td>
                                  <td className="px-3 py-2 text-red-400">Hoja vacía ⚠️</td>
                                </tr>
                              </tbody>
                            </table>
                          </div>
                        </details>

                        <details className="bg-gray-800 p-4 rounded-lg">
                          <summary className="cursor-pointer font-semibold text-purple-300">Paso 5: Cálculos de montos</summary>
                          <ul className="list-disc list-inside space-y-1 text-sm text-gray-400 mt-2">
                            <li><strong>Monto Neto:</strong> Desde columna "monto neto"</li>
                            <li><strong>IVA:</strong> Usa "iva recuperable" si existe, sino 19% del neto (truncado)</li>
                            <li><strong>Gastos por CC:</strong> (porcentaje / 100) × base_calculo</li>
                          </ul>
                        </details>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {activeSection === 'flujo' && (
                <div className="space-y-6">
                  <h2 className="text-3xl font-bold mb-4">🔍 Análisis: "No leyó una fila del Excel"</h2>
                  
                  <div className="bg-yellow-900/30 border border-yellow-700 p-4 rounded-lg mb-6">
                    <p className="text-yellow-200 text-sm">
                      Si una fila no aparece en el resultado, puede deberse a una de estas 7 causas:
                    </p>
                  </div>

                  <div className="space-y-4">
                    <details className="bg-gray-900 p-4 rounded-lg">
                      <summary className="cursor-pointer font-semibold">1. Fila vacía o con valores nulos</summary>
                      <pre className="bg-gray-800 p-3 rounded mt-2 text-sm text-green-400">{`if not row or not any(row):
    continue`}</pre>
                      <p className="text-sm text-gray-400 mt-2">✅ Verificar: ¿La fila tiene algún valor?</p>
                    </details>

                    <details className="bg-gray-900 p-4 rounded-lg">
                      <summary className="cursor-pointer font-semibold">2. Fila antes de headers (row {'<'} 2)</summary>
                      <p className="text-sm text-gray-400 mt-2">✅ Verificar: ¿Headers están en fila 1? Si están en fila 2 o 3, se pierden las primeras filas</p>
                    </details>

                    <details className="bg-gray-900 p-4 rounded-lg">
                      <summary className="cursor-pointer font-semibold">3. Fila sin Tipo Doc válido</summary>
                      <p className="text-sm text-gray-400 mt-2">Columna "Tipo Doc" vacía se agrupa como "None con XCC"</p>
                    </details>

                    <details className="bg-red-900/30 border border-red-700 p-4 rounded-lg" open>
                      <summary className="cursor-pointer font-semibold text-red-300">4. Tipo de documento no soportado ⚠️ CAUSA MÁS PROBABLE</summary>
                      <pre className="bg-gray-800 p-3 rounded mt-2 text-sm text-red-400">{`if tipo_doc_str in ['33', '64']:
    # ...
elif tipo_doc_str == '34':
    # ...
else:
    pass  # ← HOJA VACÍA`}</pre>
                      <div className="bg-red-950/50 p-3 rounded mt-2 text-sm text-red-200">
                        Si el tipo doc es 35, 39, 46, 52, etc. → se crea hoja pero NO genera movimientos.
                        La fila se cuenta en <code className="bg-gray-800 px-1 rounded">total_filas</code> pero no genera asientos contables.
                      </div>
                      <p className="text-sm text-gray-400 mt-2">✅ Verificar: ¿El tipo de documento está soportado? (33, 34, 61, 64, COMO)</p>
                    </details>

                    <details className="bg-gray-900 p-4 rounded-lg">
                      <summary className="cursor-pointer font-semibold">5. Fila con CC = 0</summary>
                      <p className="text-sm text-gray-400 mt-2">Si todos los CC = 0 → solo genera IVA y Proveedor, no gastos</p>
                    </details>

                    <details className="bg-gray-900 p-4 rounded-lg">
                      <summary className="cursor-pointer font-semibold">6. Error en detección de rango de CC</summary>
                      <p className="text-sm text-gray-400 mt-2">Si no encuentra "Nombre cuenta" y "Fecha aprobacion", usa solo CC conocidos</p>
                    </details>

                    <details className="bg-gray-900 p-4 rounded-lg">
                      <summary className="cursor-pointer font-semibold">7. Truncamiento en debug (no causa pérdida)</summary>
                      <p className="text-sm text-gray-400 mt-2">Solo guarda info de primeras 200 filas en metadata</p>
                    </details>
                  </div>

                  <div className="bg-gray-900 p-6 rounded-lg mt-6">
                    <h3 className="text-xl font-semibold mb-4">📋 Checklist de Debugging</h3>
                    <div className="space-y-2 text-sm text-gray-400">
                      <div className="flex items-start gap-2">
                        <span className="text-green-400 mt-0.5">✓</span>
                        <span>¿La fila está en el Excel original?</span>
                      </div>
                      <div className="flex items-start gap-2">
                        <span className="text-green-400 mt-0.5">✓</span>
                        <span>¿La fila tiene valores en columnas importantes? (Tipo Doc, Monto Neto, CC)</span>
                      </div>
                      <div className="flex items-start gap-2">
                        <span className="text-green-400 mt-0.5">✓</span>
                        <span>¿El "Tipo Doc" es soportado? (33, 34, 61, 64, COMO)</span>
                      </div>
                      <div className="flex items-start gap-2">
                        <span className="text-green-400 mt-0.5">✓</span>
                        <span>Revisar logs de Celery y metadata en Redis</span>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {activeSection === 'problemas' && (
                <div className="space-y-6">
                  <h2 className="text-3xl font-bold mb-4">⚠️ Problemas Potenciales Detectados</h2>

                  <div className="mb-6">
                    <h3 className="text-xl font-semibold text-red-400 mb-4">🔴 Prioridad Alta</h3>
                    
                    <div className="space-y-4">
                      <details className="bg-red-900/20 border border-red-700 p-4 rounded-lg">
                        <summary className="cursor-pointer font-semibold text-red-300">Problema #6: Tipos de documento no contemplados</summary>
                        <div className="mt-3 space-y-2 text-sm text-gray-300">
                          <p><strong>Descripción:</strong> Si aparece un tipo no contemplado (35, 39, 52, etc.), se crea hoja vacía sin avisar</p>
                          <pre className="bg-gray-800 p-3 rounded text-red-400">{`else:
    # Tipos desconocidos: no se generan movimientos
    pass`}</pre>
                          <p><strong>Impacto:</strong> Usuario no sabe que esas filas no fueron procesadas</p>
                        </div>
                      </details>

                      <details className="bg-red-900/20 border border-red-700 p-4 rounded-lg">
                        <summary className="cursor-pointer font-semibold text-red-300">Problema #7: Columna Monto Neto no encontrada</summary>
                        <div className="mt-3 space-y-2 text-sm text-gray-300">
                          <p><strong>Impacto:</strong> Si no existe, todos los cálculos se hacen sobre 0 → Excel de salida con valores incorrectos</p>
                        </div>
                      </details>

                      <details className="bg-red-900/20 border border-red-700 p-4 rounded-lg">
                        <summary className="cursor-pointer font-semibold text-red-300">Problema #8: Porcentajes que no suman 100%</summary>
                        <div className="mt-3 space-y-2 text-sm text-gray-300">
                          <p>No valida que la suma de porcentajes de CC = 100%</p>
                          <ul className="list-disc list-inside">
                            <li>Si suma {'<'} 100%: habrá diferencia en contabilidad</li>
                            <li>Si suma {'>'} 100%: habrá sobregiro</li>
                          </ul>
                        </div>
                      </details>
                    </div>
                  </div>

                  <div>
                    <h3 className="text-xl font-semibold text-yellow-400 mb-4">🟡 Prioridad Media</h3>
                    
                    <div className="space-y-3">
                      <div className="bg-yellow-900/20 border border-yellow-700 p-4 rounded-lg">
                        <p className="font-semibold text-yellow-300">Problema #2: TTL de 5 minutos muy corto</p>
                        <p className="text-sm text-gray-400 mt-1">Si el procesamiento tarda {'>'} 5 minutos, se pierden los resultados</p>
                      </div>

                      <div className="bg-yellow-900/20 border border-yellow-700 p-4 rounded-lg">
                        <p className="font-semibold text-yellow-300">Problema #4: Asume headers siempre en fila 1</p>
                        <p className="text-sm text-gray-400 mt-1">Si hay metadatos arriba, el sistema falla</p>
                      </div>

                      <div className="bg-yellow-900/20 border border-yellow-700 p-4 rounded-lg">
                        <p className="font-semibold text-yellow-300">Problema #1,3: Detección de columnas puede fallar</p>
                        <p className="text-sm text-gray-400 mt-1">Si hay espacios extras o caracteres especiales</p>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {activeSection === 'mejoras' && (
                <div className="space-y-6">
                  <h2 className="text-3xl font-bold mb-4">💡 Recomendaciones de Mejora</h2>

                  <div className="mb-6">
                    <h3 className="text-xl font-semibold text-red-400 mb-4">🔴 Prioridad Alta</h3>
                    
                    <div className="space-y-4">
                      <details className="bg-gray-900 p-4 rounded-lg" open>
                        <summary className="cursor-pointer font-semibold text-green-400">1. Validar columnas críticas al inicio</summary>
                        <p className="text-sm text-gray-400 mt-2 mb-2">Abortar temprano si faltan columnas esenciales:</p>
                        <pre className="bg-gray-800 p-3 rounded text-sm text-green-400">{`if idx_monto_neto is None:
    raise ValueError("No se encontró columna 'Monto Neto' requerida")`}</pre>
                      </details>

                      <details className="bg-gray-900 p-4 rounded-lg">
                        <summary className="cursor-pointer font-semibold text-green-400">2. Reportar tipos de documento no procesados</summary>
                        <pre className="bg-gray-800 p-3 rounded text-sm text-green-400 mt-2">{`tipos_no_soportados = set()
if tipo_doc_str not in ['33', '34', '61', '64', 'COMO']:
    tipos_no_soportados.add(tipo_doc_str)`}</pre>
                        <p className="text-sm text-gray-400 mt-2">Incluir en metadata y mostrar warning en frontend</p>
                      </details>

                      <details className="bg-gray-900 p-4 rounded-lg">
                        <summary className="cursor-pointer font-semibold text-green-400">3. Loggear filas saltadas con razón</summary>
                        <pre className="bg-gray-800 p-3 rounded text-sm text-green-400 mt-2">{`filas_saltadas = []
if not row or not any(row):
    filas_saltadas.append({'fila': row_idx, 'razon': 'fila_vacia'})`}</pre>
                      </details>

                      <details className="bg-gray-900 p-4 rounded-lg">
                        <summary className="cursor-pointer font-semibold text-green-400">4. Validar suma de porcentajes de CC</summary>
                        <pre className="bg-gray-800 p-3 rounded text-sm text-green-400 mt-2">{`suma = sum(_parse_numeric(row[col]) for col in cc_range)
if abs(suma - 100) > 0.01:
    warnings.append(f"Fila {row_idx}: CC suman {suma}%")`}</pre>
                      </details>
                    </div>
                  </div>

                  <div className="mb-6">
                    <h3 className="text-xl font-semibold text-yellow-400 mb-4">🟡 Prioridad Media</h3>
                    
                    <div className="space-y-3">
                      <div className="bg-gray-900 p-4 rounded-lg">
                        <p className="font-semibold text-yellow-300">5. TTL dinámico en Redis</p>
                        <ul className="list-disc list-inside text-sm text-gray-400 mt-2">
                          <li>5 minutos para archivos {'<'} 100 filas</li>
                          <li>30 minutos para archivos {'>'} 1000 filas</li>
                        </ul>
                      </div>

                      <div className="bg-gray-900 p-4 rounded-lg">
                        <p className="font-semibold text-yellow-300">6. Detección dinámica de fila de headers</p>
                        <p className="text-sm text-gray-400 mt-1">Buscar primera fila con "Tipo Doc"</p>
                      </div>

                      <div className="bg-gray-900 p-4 rounded-lg">
                        <p className="font-semibold text-yellow-300">7. Normalización robusta de columnas</p>
                        <p className="text-sm text-gray-400 mt-1">Aplicar unicodedata.normalize() y quitar acentos/espacios</p>
                      </div>
                    </div>
                  </div>

                  <div>
                    <h3 className="text-xl font-semibold text-blue-400 mb-4">🟢 Prioridad Baja</h3>
                    
                    <div className="space-y-3">
                      <div className="bg-gray-900 p-4 rounded-lg">
                        <p className="font-semibold text-blue-300">8. Progreso en tiempo real</p>
                        <p className="text-sm text-gray-400 mt-1">Mostrar "Procesando... 45/100 filas"</p>
                      </div>

                      <div className="bg-gray-900 p-4 rounded-lg">
                        <p className="font-semibold text-blue-300">9. Validación de formato de cuentas</p>
                        <p className="text-sm text-gray-400 mt-1">Verificar formato (1191001 o 1191-001)</p>
                      </div>

                      <div className="bg-gray-900 p-4 rounded-lg">
                        <p className="font-semibold text-blue-300">10. Tests unitarios</p>
                        <p className="text-sm text-gray-400 mt-1">Crear Excels de prueba con casos edge</p>
                      </div>
                    </div>
                  </div>

                  <div className="bg-green-900/30 border border-green-700 p-6 rounded-lg mt-6">
                    <h3 className="text-lg font-semibold mb-2 text-green-300">🎯 Conclusión</h3>
                    <p className="text-sm text-gray-300 mb-2">
                      El sistema está <strong>bien diseñado</strong> con validación robusta, procesamiento asíncrono escalable, 
                      fallbacks razonables y cálculos correctos según normativa chilena.
                    </p>
                    <p className="text-sm text-gray-300">
                      Las mejoras sugeridas se enfocan en mejor manejo de errores, validaciones más estrictas, 
                      y mayor transparencia para el usuario sobre el procesamiento.
                    </p>
                  </div>
                </div>
              )}

              {activeSection === 'security' && (
                <div className="space-y-6">
                  <h2 className="text-3xl font-bold mb-4">🔒 Validación de Acceso</h2>
                  
                  <div className="bg-gray-900 p-6 rounded-lg">
                    <h3 className="text-xl font-semibold mb-3 text-purple-400">Flujo de Validación</h3>
                    <ol className="space-y-3 text-gray-300 list-decimal list-inside">
                      <li>Lee usuario de localStorage</li>
                      <li>Valida que usuario.areas contenga 'Contabilidad'</li>
                      <li>Maneja formato string y objeto con normalización</li>
                      <li>Si no tiene acceso → Pantalla "Acceso Denegado"</li>
                      <li>Si tiene acceso → Muestra herramienta completa</li>
                    </ol>
                  </div>

                  <pre className="bg-gray-900 p-6 rounded-lg text-green-400 text-sm">
{`const acceso = validarAccesoContabilidad(usuario);
if (!acceso) {
  // Mostrar acceso denegado
  return;
}
// Cargar herramienta...`}
                  </pre>
                </div>
              )}

              {activeSection === 'usage' && (
                <div className="space-y-6">
                  <h2 className="text-3xl font-bold mb-4">💡 Uso del Módulo</h2>
                  
                  <pre className="bg-gray-900 p-6 rounded-lg text-green-400 text-sm">
{`// En App.jsx o herramientas de contabilidad
import { CapturaGastosRouter } from './modules/contabilidad/captura-gastos';

<Route path="/menu/tools/captura-gastos/*" element={<CapturaGastosRouter />} />`}
                  </pre>

                  <div className="bg-yellow-900/30 border border-yellow-700 p-4 rounded-lg">
                    <p className="text-yellow-200 text-sm">
                      <strong>Nota:</strong> El módulo valida automáticamente el acceso al área de Contabilidad y maneja toda la lógica de carga y procesamiento de archivos.
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

export default CapturaGastosModuleDocs;
