import React from 'react';
import { getUserConfig } from '../config/clientesConfig';

const DebugButton = ({ usuario, areaActiva, clientes, clientesFiltrados, filtro }) => {
  const handleDebugClick = () => {
    const userConfig = getUserConfig(usuario?.tipo_usuario);
    
    const debugInfo = `
=== DEBUG: Carga de Clientes por Área ===
Usuario: ${usuario?.nombre} ${usuario?.apellido}
Tipo: ${usuario?.tipo_usuario}
Área Activa: ${areaActiva}
Áreas del Usuario: ${usuario?.areas?.map(a => a.nombre || a).join(', ') || 'N/A'}

Total Clientes Cargados: ${clientes.length}
Clientes Después del Filtro: ${clientesFiltrados.length}
Filtro Actual: "${filtro}"

ENDPOINT USADO:
${userConfig.endpoint}

CLIENTES ENCONTRADOS:
${clientes.slice(0, 5).map((c, i) => 
  `${i + 1}. ${c.nombre} (${c.rut}) - Áreas: ${c.areas_efectivas?.map(a => a.nombre).join(', ') || 'Sin áreas'}`
).join('\n')}
${clientes.length > 5 ? `... y ${clientes.length - 5} más` : ''}
=====================================`;
    alert(debugInfo);
  };

  return (
    <button
      onClick={handleDebugClick}
      className="ml-2 text-xs text-blue-400 hover:text-blue-300 underline"
    >
      🔍 Debug
    </button>
  );
};

export default DebugButton;
