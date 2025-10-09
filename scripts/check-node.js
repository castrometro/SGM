#!/usr/bin/env node

/**
 * Script de verificación de seguridad para CVE-2024-3566
 * Verifica que Node.js esté en una versión segura, especialmente en Windows
 */

import semver from 'semver';
import os from 'os';
import { createRequire } from 'module';

const require = createRequire(import.meta.url);

const MINIMUM_NODE_VERSION = '20.19.5';
const CVE_VULNERABLE_RANGES = [
  // Rangos conocidos vulnerables a CVE-2024-3566
  '>=18.0.0 <18.20.5',  
  '>=20.0.0 <20.18.0',
  '>=22.0.0 <22.9.0'
];

function checkNodeVersion() {
  const currentVersion = process.version.substring(1); // Remove 'v' prefix
  const isWindows = os.platform() === 'win32';
  
  console.log(`🔍 Verificando Node.js v${currentVersion} en ${os.platform()}`);
  
  // Verificar si está en rango vulnerable
  const isVulnerable = CVE_VULNERABLE_RANGES.some(range => 
    semver.satisfies(currentVersion, range)
  );
  
  if (isVulnerable) {
    console.error(`❌ VULNERABILIDAD DETECTADA: CVE-2024-3566`);
    console.error(`   Node.js v${currentVersion} es vulnerable a command injection en Windows`);
    console.error(`   Actualiza a Node.js v${MINIMUM_NODE_VERSION} o superior`);
    
    if (isWindows) {
      console.error(`\n🔧 Para actualizar en Windows:`);
      console.error(`   1. Descarga desde: https://nodejs.org/`);
      console.error(`   2. O usa: winget install OpenJS.NodeJS`);
      console.error(`   3. O usa: choco upgrade nodejs`);
    }
    
    process.exit(1);
  }
  
  // Verificar versión mínima
  if (!semver.gte(currentVersion, MINIMUM_NODE_VERSION)) {
    console.error(`❌ Node.js v${currentVersion} es menor que la versión mínima requerida v${MINIMUM_NODE_VERSION}`);
    process.exit(1);
  }
  
  console.log(`✅ Node.js v${currentVersion} es seguro`);
  
  // Advertencia específica para Windows
  if (isWindows && semver.lt(currentVersion, '22.9.0')) {
    console.warn(`⚠️  RECOMENDACIÓN: En Windows, considera actualizar a Node.js v22.9.0+ para máxima seguridad`);
  }
}

// Solo ejecutar si es llamado directamente
if (import.meta.url === `file://${process.argv[1]}`) {
  try {
    checkNodeVersion();
  } catch (error) {
    console.error(`❌ Error verificando versión de Node.js:`, error.message);
    process.exit(1);
  }
}

export { checkNodeVersion };