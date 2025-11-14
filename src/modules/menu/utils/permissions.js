// src/modules/menu/utils/permissions.js
import { USER_ROLES } from '../constants/menu.constants';

/**
 * Obtiene las áreas asociadas a un usuario
 * @param {object} usuario
 * @returns {Array}
 */
export const getUserAreas = (usuario) => usuario?.areas ?? [];

/**
 * Verifica si el usuario tiene el rol indicado
 * @param {object} usuario
 * @param {string} role
 * @returns {boolean}
 */
export const isRole = (usuario, role) => usuario?.tipo_usuario === role;

/**
 * Verifica si el usuario es gerente
 * @param {object} usuario
 * @returns {boolean}
 */
export const isGerente = (usuario) => isRole(usuario, USER_ROLES.GERENTE);

/**
 * Verifica si el usuario pertenece a un área específica
 * @param {object} usuario
 * @param {string} areaName
 * @returns {boolean}
 */
export const hasArea = (usuario, areaName) =>
  getUserAreas(usuario).some((area) => area?.nombre === areaName);

/**
 * Verifica si el usuario pertenece a alguna de las áreas provistas
 * @param {object} usuario
 * @param {string[]} areaNames
 * @returns {boolean}
 */
export const hasAnyArea = (usuario, areaNames = []) =>
  areaNames.some((name) => hasArea(usuario, name));
