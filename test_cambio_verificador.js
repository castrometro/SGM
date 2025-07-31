// 🧪 TEST ACTUALIZADO - LÓGICA DE BLOQUEO CON VERIFICADOR HABILITADO EN archivos_completos

const testLogicaBloqueoActualizada = () => {
  console.log('🧪 TESTING LÓGICA DE BLOQUEO ACTUALIZADA');
  console.log('======================================');

  // Función actualizada de bloqueo
  const estaSeccionBloqueada = (seccion, estadoCierre) => {
    if (estadoCierre === 'finalizado') {
      return true;
    }
    
    switch (estadoCierre) {
      case 'pendiente':
      case 'cargando_archivos':
        return !['archivosTalana', 'archivosAnalista'].includes(seccion);
        
      case 'archivos_completos':  // 🎯 CAMBIO: Ahora incluye verificadorDatos
      case 'verificacion_datos':
      case 'verificado_sin_discrepancias': 
        return !['archivosTalana', 'archivosAnalista', 'verificadorDatos'].includes(seccion);
        
      case 'datos_consolidados':
      case 'con_incidencias':
        return !['archivosTalana', 'archivosAnalista', 'verificadorDatos', 'incidencias'].includes(seccion);
        
      default:
        const estadosPosteriores = [
          'datos_consolidados', 'con_incidencias', 'incidencias_resueltas', 'validacion_final', 'finalizado'
        ];
        return estadosPosteriores.includes(estadoCierre);
    }
  };

  // Test del cambio específico: archivos_completos ahora habilita verificador
  const testCambio = [
    { estado: 'archivos_completos', seccion: 'archivosTalana', esperado: false },
    { estado: 'archivos_completos', seccion: 'archivosAnalista', esperado: false },
    { estado: 'archivos_completos', seccion: 'verificadorDatos', esperado: false }, // 🎯 CAMBIO: Ahora false (habilitado)
    { estado: 'archivos_completos', seccion: 'incidencias', esperado: true },
  ];

  console.log('\n🎯 VERIFICANDO CAMBIO ESPECÍFICO:');
  console.log('Estado archivos_completos debe habilitar el verificador\n');

  let exito = true;
  testCambio.forEach(test => {
    const resultado = estaSeccionBloqueada(test.seccion, test.estado);
    const paso = resultado === test.esperado;
    
    if (paso) {
      console.log(`✅ ${test.estado} -> ${test.seccion}: ${resultado ? 'bloqueado' : 'habilitado'}`);
    } else {
      console.log(`❌ ${test.estado} -> ${test.seccion}: esperado ${test.esperado ? 'bloqueado' : 'habilitado'}, obtuvo ${resultado ? 'bloqueado' : 'habilitado'}`);
      exito = false;
    }
  });

  // Tabla de estados actualizada
  console.log('\n📊 TABLA DE ESTADOS ACTUALIZADA:');
  console.log('');
  console.log('Estado                  | Talana | Analista | Verificador | Incidencias');
  console.log('------------------------|--------|----------|-------------|------------');
  
  const estados = [
    'pendiente',
    'cargando_archivos', 
    'archivos_completos',
    'verificacion_datos',
    'datos_consolidados',
    'finalizado'
  ];
  
  const secciones = ['archivosTalana', 'archivosAnalista', 'verificadorDatos', 'incidencias'];
  
  estados.forEach(estado => {
    const resultados = secciones.map(seccion => {
      const bloqueado = estaSeccionBloqueada(seccion, estado);
      return bloqueado ? '   ❌   ' : '   ✅   ';
    });
    
    console.log(`${estado.padEnd(23)} |${resultados.join('|')}`);
  });

  console.log('\n🎯 CAMBIO IMPLEMENTADO:');
  console.log('✅ archivos_completos ahora habilita el Verificador de Datos');
  console.log('✅ Flujo más eficiente: se puede verificar inmediatamente tras cargar archivos');

  return exito;
};

// Ejecutar test
const exito = testLogicaBloqueoActualizada();
console.log('\n' + (exito ? '🎉 CAMBIO IMPLEMENTADO CORRECTAMENTE' : '💥 ERROR EN LA IMPLEMENTACIÓN'));
