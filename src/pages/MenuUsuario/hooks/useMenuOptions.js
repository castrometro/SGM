import { useMemo } from 'react';
import { MENU_CONFIG } from '../config/menuConfig';

/**
 * Hook personalizado para generar las opciones de menú
 * basado en el tipo de usuario y sus áreas asignadas
 */
export const useMenuOptions = (usuario) => {
  return useMemo(() => {
    if (!usuario || !usuario.tipo_usuario) {
      return [];
    }

    const config = MENU_CONFIG[usuario.tipo_usuario];
    if (!config) {
      console.warn(`Configuración no encontrada para tipo de usuario: ${usuario.tipo_usuario}`);
      return [];
    }

    // Empezar con las opciones base del tipo de usuario
    let opciones = [...config.base];

    // Agregar opciones específicas por área (solo para gerentes por ahora)
    if (usuario.tipo_usuario === 'gerente' && usuario.areas?.length > 0) {
      const areas = usuario.areas || [];
      
      areas.forEach(area => {
        const areaOpciones = config.areas[area.nombre] || [];
        opciones = [...opciones, ...areaOpciones];
      });
    }

    return opciones;
  }, [usuario]);
};

/**
 * Hook para obtener información sobre las áreas del usuario
 */
export const useUserAreas = (usuario) => {
  return useMemo(() => {
    const areas = usuario?.areas || [];
    return {
      areas,
      tieneContabilidad: areas.some(area => area.nombre === "Contabilidad"),
      tienePayroll: areas.some(area => area.nombre === "Payroll"),
      // Futuras áreas
      tieneTax: areas.some(area => area.nombre === "Tax"),
    };
  }, [usuario]);
};
