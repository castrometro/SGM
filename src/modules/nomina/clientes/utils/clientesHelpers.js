// src/modules/nomina/clientes/utils/clientesHelpers.js
import { TIPO_USUARIO } from '../constants/clientes.constants';

/**
 * 🛠️ Utilidades para el módulo de Clientes de Nómina
 */

/**
 * Determina el área activa del usuario
 */
export const determinarAreaActiva = (userData) => {
  if (userData.area_activa) {
    return userData.area_activa;
  }
  
  if (userData.areas && userData.areas.length > 0) {
    return userData.areas[0].nombre || userData.areas[0];
  }
  
  return null;
};

/**
 * Determina qué API de clientes llamar según el tipo de usuario
 */
export const determinarEndpointClientes = (tipoUsuario) => {
  switch (tipoUsuario) {
    case TIPO_USUARIO.GERENTE:
      return 'clientesPorArea'; // Gerentes ven todos los clientes de sus áreas
    case TIPO_USUARIO.ANALISTA:
      return 'clientesAsignados'; // Analistas solo ven sus asignados
    case TIPO_USUARIO.SUPERVISOR:
      return 'clientesPorArea'; // Supervisores ven el área que supervisan
    default:
      return 'clientesPorArea';
  }
};

/**
 * Filtra clientes por nombre o RUT
 */
export const filtrarClientes = (clientes, filtro) => {
  if (!filtro) return clientes;
  
  const filtroLower = filtro.toLowerCase();
  return clientes.filter((cliente) =>
    cliente.nombre.toLowerCase().includes(filtroLower) ||
    cliente.rut.toLowerCase().includes(filtroLower)
  );
};

/**
 * Genera información de debug para troubleshooting
 */
export const generarInfoDebug = (usuario, areaActiva, clientes, filtro, clientesFiltrados) => {
  return `
=== DEBUG: Carga de Clientes de Nómina ===
Usuario: ${usuario?.nombre} ${usuario?.apellido}
Tipo: ${usuario?.tipo_usuario}
Área Activa: ${areaActiva}
Áreas del Usuario: ${usuario?.areas?.map(a => a.nombre || a).join(', ') || 'N/A'}

Total Clientes Cargados: ${clientes.length}
Clientes Después del Filtro: ${clientesFiltrados.length}
Filtro Actual: "${filtro}"

ENDPOINT USADO:
${usuario?.tipo_usuario === TIPO_USUARIO.GERENTE ? "📊 /clientes-por-area/ (Gerente - clientes de sus áreas)" :
  usuario?.tipo_usuario === TIPO_USUARIO.ANALISTA ? "👤 /clientes/asignados/ (Analista - solo asignados)" :
  usuario?.tipo_usuario === TIPO_USUARIO.SUPERVISOR ? "👁️ /clientes-por-area/ (Supervisor - área supervisada)" :
  "🔧 /clientes-por-area/ (Por defecto)"
}

CLIENTES ENCONTRADOS:
${clientes.slice(0, 5).map((c, i) => 
  `${i + 1}. ${c.nombre} (${c.rut}) - Áreas: ${c.areas_efectivas?.map(a => a.nombre).join(', ') || 'Sin áreas'}`
).join('\n')}
${clientes.length > 5 ? `... y ${clientes.length - 5} más` : ''}
=====================================`;
};

/**
 * Obtiene el mensaje apropiado cuando no hay clientes
 */
export const getMensajeSinClientes = (tipoUsuario, areaActiva) => {
  if (tipoUsuario === TIPO_USUARIO.ANALISTA) {
    return 'No tienes clientes asignados. Contacta a tu supervisor.';
  }
  return `No hay clientes registrados para el área "${areaActiva}".`;
};
