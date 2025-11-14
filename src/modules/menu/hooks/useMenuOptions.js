// src/modules/menu/hooks/useMenuOptions.js
import { useMemo } from 'react';
import {
  AREA_NAMES,
  MENU_CARD_DEFAULTS,
  MENU_OPTION_KEYS,
  USER_ROLES,
} from '../constants/menu.constants';
import {
  BASE_MENU_OPTIONS,
  ROLE_OPTION_KEYS,
  GERENTE_AREA_OPTION_KEYS,
  CONTABILIDAD_SHARED_KEYS,
} from '../data/menu-options.map';
import { hasArea, isGerente } from '../utils/permissions';

const buildOption = (key, role) => {
  const option = BASE_MENU_OPTIONS[key];
  if (!option) {
    return null;
  }

  if (key === MENU_OPTION_KEYS.CLIENTES) {
    if (role === USER_ROLES.GERENTE) {
      return {
        ...option,
        descripcion: 'Visión general de todos los clientes',
      };
    }

    if (role === USER_ROLES.SUPERVISOR) {
      return {
        ...option,
        descripcion: 'Ver y validar clientes asignados',
      };
    }
  }

  if (key === MENU_OPTION_KEYS.HERRAMIENTAS && role === USER_ROLES.GERENTE) {
    return {
      ...option,
      descripcion: 'Utilidades del sistema',
    };
  }

  return option;
};

/**
 * Construye la lista de opciones disponibles para el usuario del menú
 * @param {object} usuario
 * @returns {Array}
 */
const useMenuOptions = (usuario) =>
  useMemo(() => {
    if (!usuario?.tipo_usuario) {
      return [];
    }

    const role = usuario.tipo_usuario;
    const baseKeys = ROLE_OPTION_KEYS[role] ?? [];
    const optionKeys = [...baseKeys];

    if (isGerente(usuario)) {
      const areas = usuario.areas ?? [];
      areas.forEach((area) => {
        const extraKeys = GERENTE_AREA_OPTION_KEYS[area?.nombre];
        if (extraKeys) {
          optionKeys.push(...extraKeys);
        }
      });
    } else if (hasArea(usuario, AREA_NAMES.CONTABILIDAD)) {
      optionKeys.push(...CONTABILIDAD_SHARED_KEYS);
    }

    const uniqueOptions = [];
    const seen = new Set();

    optionKeys.forEach((key, index) => {
      if (!seen.has(key)) {
        seen.add(key);
        const option = buildOption(key, role);
        if (option) {
          uniqueOptions.push({
            ...option,
            key,
            animationDelay: `${index * MENU_CARD_DEFAULTS.animationDelayStep}ms`,
            initialOpacity: MENU_CARD_DEFAULTS.opacity,
          });
        }
      }
    });

    return uniqueOptions;
  }, [usuario]);

export default useMenuOptions;
