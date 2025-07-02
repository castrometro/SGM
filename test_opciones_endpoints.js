/**
 * Test simple para verificar que los endpoints de opciones funcionen
 * Ejecutar en la consola del navegador para debuggear
 */

const testOpcionesEndpoints = async (clienteId = 1, setId = 1) => {
  console.log('🧪 === TEST DE ENDPOINTS DE OPCIONES ===');
  console.log(`📋 Cliente ID: ${clienteId}, Set ID: ${setId}`);
  
  try {
    // 1. Test endpoint normal de opciones
    console.log('\n1️⃣ Probando endpoint normal...');
    const normalRes = await fetch(`/api/contabilidad/sets/${setId}/opciones/`);
    console.log(`Status: ${normalRes.status} ${normalRes.statusText}`);
    
    if (normalRes.ok) {
      const normalData = await normalRes.json();
      console.log(`✅ Opciones normales: ${normalData.length} items`);
      console.log('Ejemplo:', normalData.slice(0, 2));
    } else {
      console.log('❌ Error en endpoint normal:', await normalRes.text());
    }
    
    // 2. Test endpoint bilingüe ES
    console.log('\n2️⃣ Probando endpoint bilingüe ES...');
    const bilingueEsRes = await fetch(`/api/contabilidad/clasificacion/opciones-bilingues/${setId}/?idioma=es&cliente_id=${clienteId}`);
    console.log(`Status: ${bilingueEsRes.status} ${bilingueEsRes.statusText}`);
    
    if (bilingueEsRes.ok) {
      const bilingueEsData = await bilingueEsRes.json();
      console.log(`✅ Opciones bilingües ES: ${bilingueEsData.length} items`);
      console.log('Ejemplo:', bilingueEsData.slice(0, 2));
    } else {
      console.log('❌ Error en endpoint bilingüe ES:', await bilingueEsRes.text());
    }
    
    // 3. Test endpoint bilingüe EN
    console.log('\n3️⃣ Probando endpoint bilingüe EN...');
    const bilingueEnRes = await fetch(`/api/contabilidad/clasificacion/opciones-bilingues/${setId}/?idioma=en&cliente_id=${clienteId}`);
    console.log(`Status: ${bilingueEnRes.status} ${bilingueEnRes.statusText}`);
    
    if (bilingueEnRes.ok) {
      const bilingueEnData = await bilingueEnRes.json();
      console.log(`✅ Opciones bilingües EN: ${bilingueEnData.length} items`);
      console.log('Ejemplo:', bilingueEnData.slice(0, 2));
    } else {
      console.log('❌ Error en endpoint bilingüe EN:', await bilingueEnRes.text());
    }
    
    // 4. Test endpoint de sets
    console.log('\n4️⃣ Probando endpoint de sets...');
    const setsRes = await fetch(`/api/contabilidad/sets/cliente/${clienteId}/`);
    console.log(`Status: ${setsRes.status} ${setsRes.statusText}`);
    
    if (setsRes.ok) {
      const setsData = await setsRes.json();
      console.log(`✅ Sets del cliente: ${setsData.length} items`);
      console.log('Sets disponibles:', setsData.map(s => `${s.id}: ${s.nombre}`));
    } else {
      console.log('❌ Error en endpoint de sets:', await setsRes.text());
    }
    
  } catch (error) {
    console.error('❌ Error general en test:', error);
  }
  
  console.log('\n🏁 === FIN DEL TEST ===');
};

// Para ejecutar el test, usar:
// testOpcionesEndpoints(1, 1); // Reemplazar con IDs reales

console.log('💡 Test creado. Para ejecutar, usar: testOpcionesEndpoints(clienteId, setId)');
