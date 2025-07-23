const fs = require('fs');

// Leer el archivo
const filePath = '/root/SGM/src/components/TarjetasCierreNomina/VerificadorDatosSection.jsx';
let content = fs.readFileSync(filePath, 'utf8');

// Reemplazar la sección completa
const oldSection = `  return (
    <section className="space-y-6">
      {disabled ? (
        /* SECCIÓN BLOQUEADA - Solo Consolidación */
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="flex items-center justify-center w-10 h-10 bg-gray-600 rounded-lg">
                <Lock size={20} className="text-white" />
              </div>
              <div>
                <h2 className="text-xl font-semibold text-gray-400">
                  Verificación de Datos
                  <span className="ml-2 text-sm font-normal text-gray-500">
                    (Bloqueado - Datos Consolidados)
                  </span>
                </h2>
                <p className="text-gray-500 text-sm">
                  La verificación está bloqueada porque los datos ya han sido consolidados
                </p>
              </div>
            </div>
            <span className="text-sm font-medium text-gray-500">Bloqueado</span>
          </div>
          
          {/* Botón de Re-Consolidación */}
          <div className="mt-6 pt-6 border-t border-gray-700">
            <div className="bg-blue-900/30 border border-blue-700 rounded-lg p-4">
              <div className="flex items-start gap-4">
                <div className="flex-shrink-0">
                  <CheckCircle className="w-6 h-6 text-blue-400 mt-1" />
                </div>
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-blue-300 mb-2">
                    ¿Necesitas actualizar los datos consolidados?
                  </h3>
                  <div className="text-gray-300 text-sm space-y-2 mb-4">
                    <p>
                      • Si has subido <strong>nuevos archivos</strong> después de la consolidación
                    </p>
                    <p>
                      • Si necesitas <strong>corregir datos</strong> y volver a procesar
                    </p>
                    <p>
                      • Para <strong>actualizar</strong> la información consolidada con cambios recientes
                    </p>
                  </div>
                  <div className="flex items-center gap-3">
                    {puedeConsolidarDatos() ? (
                      <button
                        onClick={() => {
                          console.log('🔵 Click en botón Actualizar Consolidación');
                          console.log('🔧 Abriendo modal de consolidación...');
                          setMostrarModalConsolidacion(true);
                          console.log('✅ Estado modal actualizado a true');
                        }}
                        disabled={consolidando}
                        className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
                      >
                        {consolidando ? (
                          <>
                            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                            {taskIdConsolidacion ? 'Procesando datos...' : 'Iniciando...'}
                          </>
                        ) : (
                          <>
                            <RefreshCw className="w-4 h-4 mr-2" />
                            Actualizar Consolidación
                          </>
                        )}
                      </button>
                    ) : (
                      <div className="text-gray-400 text-sm">
                        <p>No es posible re-consolidar en este momento.</p>
                        <p>Asegúrate de que todos los archivos estén procesados.</p>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      ) : (
        /* SECCIÓN NORMAL - Verificación + Consolidación */
        <>
          <div
            className="flex items-center justify-between cursor-pointer hover:bg-gray-800/50 p-3 -m-3 rounded-lg transition-colors"
            onClick={() => setExpandido(!expandido)}
          >
            <div className="flex items-center gap-3">
              <div className="flex items-center justify-center w-10 h-10 bg-orange-600 rounded-lg">
                <ShieldCheck size={20} className="text-white" />
              </div>
              <div>
                <h2 className="text-xl font-semibold text-white">
                  Verificación de Datos
                </h2>
                <div className="flex items-center gap-2 text-sm">
                  <p className="text-gray-400">
                    Verificación de consistencia entre Libro de Remuneraciones y Novedades
                  </p>
                  {estadoDiscrepancias && (
                    <span className={\`\${obtenerColorEstado()} font-medium\`}>
                      • {estadoDiscrepancias.total_discrepancias || 0} discrepancias
                      {estadoDiscrepancias.total_discrepancias === 0 && estadoDiscrepancias.verificacion_completada && (
                        <span className="ml-2 text-green-300">✅ Verificación exitosa</span>
                      )}
                    </span>
                  )}
                </div>
              </div>
            </div>
            <div className="flex items-center gap-3">
              {estadoDiscrepancias && estadoDiscrepancias.total_discrepancias > 0 && (
                <div className="flex items-center gap-2 text-sm">
                  <span className="text-white">
                    {estadoDiscrepancias.total_discrepancias}
                  </span>
                  <span className={obtenerColorEstado()}>
                    {obtenerTextoEstado()}
                  </span>
                </div>
              )}
              {expandido ? (
                <ChevronDown size={20} className="text-gray-400" />
              ) : (
                <ChevronRight size={20} className="text-gray-400" />
              )}
            </div>
          </div>
          
          {expandido && (`;

const newSection = `  return (
    <section className="space-y-6">
      {/* Header de la sección - unificado para disabled y no disabled */}
      <div 
        className={\`flex items-center justify-between p-3 -m-3 rounded-lg transition-colors \${
          disabled 
            ? 'opacity-60 cursor-not-allowed' 
            : 'cursor-pointer hover:bg-gray-800/50'
        }\`}
        onClick={() => !disabled && setExpandido(!expandido)}
      >
        <div className="flex items-center gap-3">
          <div className={\`flex items-center justify-center w-10 h-10 rounded-lg \${
            disabled ? 'bg-gray-600' : 'bg-orange-600'
          }\`}>
            {disabled ? (
              <Lock size={20} className="text-white" />
            ) : (
              <ShieldCheck size={20} className="text-white" />
            )}
          </div>
          <div>
            <h2 className={\`text-xl font-semibold \${disabled ? 'text-gray-400' : 'text-white'}\`}>
              Verificación de Datos
              {disabled && (
                <span className="ml-2 text-sm font-normal text-gray-500">
                  (Bloqueado - Datos Consolidados)
                </span>
              )}
            </h2>
            <div className="flex items-center gap-2 text-sm">
              <p className={disabled ? 'text-gray-500' : 'text-gray-400'}>
                {disabled 
                  ? 'La verificación está bloqueada porque los datos ya han sido consolidados'
                  : 'Verificación de consistencia entre Libro de Remuneraciones y Novedades'
                }
              </p>
              {!disabled && estadoDiscrepancias && (
                <span className={\`\${obtenerColorEstado()} font-medium\`}>
                  • {estadoDiscrepancias.total_discrepancias || 0} discrepancias
                  {estadoDiscrepancias.total_discrepancias === 0 && estadoDiscrepancias.verificacion_completada && (
                    <span className="ml-2 text-green-300">✅ Verificación exitosa</span>
                  )}
                </span>
              )}
            </div>
          </div>
        </div>
        
        <div className="flex items-center gap-3">
          {!expandido && !disabled && estadoDiscrepancias && estadoDiscrepancias.total_discrepancias > 0 && (
            <div className="flex items-center gap-2 text-sm">
              <span className="text-white">
                {estadoDiscrepancias.total_discrepancias}
              </span>
              <span className={obtenerColorEstado()}>
                {obtenerTextoEstado()}
              </span>
            </div>
          )}
          {disabled ? (
            <span className="text-sm font-medium text-gray-500">Bloqueado</span>
          ) : (
            expandido ? (
              <ChevronDown size={20} className="text-gray-400" />
            ) : (
              <ChevronRight size={20} className="text-gray-400" />
            )
          )}
        </div>
      </div>
      
      {/* Contenido de la sección - solo se muestra cuando está expandido y no disabled */}
      {expandido && !disabled && (`;

// Hacer el reemplazo
const newContent = content.replace(oldSection, newSection);

// Escribir el archivo
fs.writeFileSync(filePath, newContent);

console.log('✅ Archivo actualizado exitosamente');
