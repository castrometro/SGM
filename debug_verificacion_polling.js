/**
 * Script de depuración para el problema de actualización del componente VerificacionControl
 * 
 * Ejecuta este script en la consola del navegador para verificar:
 * 1. Si el polling se está ejecutando
 * 2. Si las llamadas a la API están funcionando
 * 3. Si los callbacks se están ejecutando correctamente
 */

console.clear();
console.log('🔍 SCRIPT DE DEPURACIÓN - VERIFICACION POLLING');
console.log('===============================================');

// Verificar si hay polling activos
const checkPollingIntervals = () => {
  console.log('\n📡 VERIFICANDO INTERVALS ACTIVOS:');
  
  // En React Dev Tools, buscar intervalos activos
  const intervalCount = setInterval(() => {}, 1000);
  clearInterval(intervalCount);
  console.log(`🔍 Último interval ID creado: ${intervalCount}`);
  
  // Esto nos da una idea de cuántos intervals podrían estar corriendo
  console.log('💡 TIP: Revisa React DevTools > Profiler para ver re-renders');
};

// Verificar estado del cierre en localStorage o sessionStorage
const checkCierreState = () => {
  console.log('\n📊 VERIFICANDO ESTADO DEL CIERRE:');
  
  // Buscar datos del cierre en el DOM
  const cierreElements = document.querySelectorAll('[data-testid*="cierre"], [class*="cierre"]');
  console.log(`🔍 Elementos relacionados con cierre encontrados: ${cierreElements.length}`);
  
  // Buscar texto que indique el estado del cierre
  const textContent = document.body.textContent;
  const estadosEncontrados = textContent.match(/(creado|archivos_pendientes|archivos_completos|verificacion_datos|con_discrepancias|sin_discrepancias|verificado_sin_discrepancias|datos_consolidados)/g);
  if (estadosEncontrados) {
    console.log('🎯 Estados de cierre encontrados en la página:', [...new Set(estadosEncontrados)]);
  }
};

// Verificar llamadas de API en Network
const checkNetworkCalls = () => {
  console.log('\n🌐 MONITOREO DE LLAMADAS API:');
  console.log('Abre las DevTools > Network y filtra por:');
  console.log('• XHR/Fetch');
  console.log('• Busca llamadas a /nomina/');
  console.log('• Especialmente: obtenerEstadoDiscrepanciasCierre');
  console.log('• Y: actualizarEstadoCierreNomina');
  
  // Interceptar fetch para logging
  const originalFetch = window.fetch;
  window.fetch = function(...args) {
    const url = args[0];
    if (typeof url === 'string' && url.includes('/nomina/')) {
      console.log('📡 API Call detectada:', url);
    }
    return originalFetch.apply(this, args);
  };
  
  console.log('✅ Interceptor de API activado - verás logs de llamadas /nomina/');
};

// Verificar logs del componente
const checkComponentLogs = () => {
  console.log('\n📝 LOGS A BUSCAR EN CONSOLA:');
  console.log('🔍 Busca estos mensajes:');
  console.log('• [VerificacionControl] useEffect polling');
  console.log('• [VerificacionControl] Polling automático #X');
  console.log('• [cargarEstadoDiscrepancias] Iniciando carga');
  console.log('• [actualizarEstadoCierre] Iniciando actualización');
  console.log('• [CierreProgresoNomina] Actualizando cierre desde verificador');
  
  console.log('\n🚨 ERRORES COMUNES A VERIFICAR:');
  console.log('• "No hay callback onCierreActualizado disponible"');
  console.log('• "No hay ID de cierre disponible"');
  console.log('• "Error en polling automático"');
};

// Función para forzar re-render del componente
const forceReRender = () => {
  console.log('\n🔄 FORZANDO RE-RENDER:');
  console.log('Ejecuta esto en la consola si quieres forzar una actualización:');
  console.log('window.location.reload(); // Recarga completa');
  console.log('// O busca el botón de actualizar estado y haz clic');
};

// Verificar si el estado del cierre cambió recientemente
const checkRecentStateChanges = () => {
  console.log('\n⏰ VERIFICANDO CAMBIOS RECIENTES:');
  
  // Buscar timestamps o indicadores de última actualización
  const badges = document.querySelectorAll('.badge, [class*="badge"], [class*="status"]');
  badges.forEach((badge, index) => {
    console.log(`🏷️ Badge ${index}:`, badge.textContent.trim());
  });
  
  console.log('\n💡 PASOS PARA VERIFICAR:');
  console.log('1. ¿Ves el spinner de "generando" o "procesando"?');
  console.log('2. ¿El estado en el header cambió?');
  console.log('3. ¿Hay números de discrepancias visibles?');
  console.log('4. ¿Los botones están habilitados/deshabilitados correctamente?');
};

// Ejecutar todas las verificaciones
const runAllChecks = () => {
  checkPollingIntervals();
  checkCierreState();
  checkNetworkCalls();
  checkComponentLogs();
  forceReRender();
  checkRecentStateChanges();
  
  console.log('\n🎯 RESUMEN DE DEPURACIÓN:');
  console.log('1. Revisa la consola durante los próximos 10 segundos');
  console.log('2. Observa si aparecen logs de polling cada 3 segundos');
  console.log('3. Verifica en Network si hay llamadas API');
  console.log('4. Si no ves actividad, el polling podría estar detenido');
  
  // Programar una verificación en 10 segundos
  setTimeout(() => {
    console.log('\n⏰ VERIFICACIÓN DESPUÉS DE 10 SEGUNDOS:');
    console.log('¿Viste algún log de polling en los últimos 10 segundos?');
    console.log('Si NO: El polling no está funcionando');
    console.log('Si SÍ: El polling funciona, revisar por qué no actualiza el estado');
  }, 10000);
};

// Ejecutar automáticamente al cargar el script
runAllChecks();

// Exportar funciones para uso manual
window.debugVerificacion = {
  checkPolling: checkPollingIntervals,
  checkState: checkCierreState,
  checkNetwork: checkNetworkCalls,
  checkLogs: checkComponentLogs,
  forceReRender: forceReRender,
  runAll: runAllChecks
};

console.log('\n🛠️ FUNCIONES DISPONIBLES:');
console.log('• debugVerificacion.checkPolling() - Verificar polling');
console.log('• debugVerificacion.checkState() - Verificar estado');
console.log('• debugVerificacion.checkNetwork() - Monitor API');
console.log('• debugVerificacion.runAll() - Ejecutar todo');
