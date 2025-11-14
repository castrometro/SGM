// src/modules/menu/utils/user-storage.js

/**
 * Claves usadas en localStorage (duplicadas de la implementación legacy)
 */
const STORAGE_KEYS = {
  TOKEN: 'token',
  USUARIO: 'usuario',
};

/**
 * Obtiene el token del usuario autenticado
 * @returns {string|null}
 */
export const getToken = () => localStorage.getItem(STORAGE_KEYS.TOKEN);

/**
 * Obtiene el objeto usuario guardado en localStorage
 * @returns {object|null}
 */
export const getUsuario = () => {
  const raw = localStorage.getItem(STORAGE_KEYS.USUARIO);
  try {
    return raw ? JSON.parse(raw) : null;
  } catch (error) {
    console.warn('[menu][user-storage] Error al parsear usuario', error);
    return null;
  }
};

/**
 * Verifica si existe una sesión válida
 * @returns {boolean}
 */
export const hasValidSession = () => Boolean(getToken());
