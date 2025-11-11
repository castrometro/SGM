// src/modules/auth/utils/storage.js
import { STORAGE_KEYS } from '../constants/auth.constants';

/**
 * Guarda los datos de autenticación en localStorage
 * @param {Object} authData - Datos de autenticación del backend { access, refresh }
 * @param {boolean} recordar - Si el usuario marcó "recordar sesión"
 */
export const saveAuthData = (authData, recordar = false) => {
  localStorage.setItem(STORAGE_KEYS.TOKEN, authData.access);
  
  if (authData.refresh) {
    localStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, authData.refresh);
  }
  
  if (recordar) {
    localStorage.setItem(STORAGE_KEYS.REMEMBER, 'true');
  }
};

/**
 * Guarda los datos del usuario en localStorage
 * @param {Object} usuario - Datos del usuario autenticado
 */
export const saveUsuario = (usuario) => {
  localStorage.setItem(STORAGE_KEYS.USUARIO, JSON.stringify(usuario));
};

/**
 * Obtiene el token de acceso desde localStorage
 * @returns {string|null} Token JWT o null si no existe
 */
export const getToken = () => {
  return localStorage.getItem(STORAGE_KEYS.TOKEN);
};

/**
 * Obtiene el refresh token desde localStorage
 * @returns {string|null} Refresh token o null si no existe
 */
export const getRefreshToken = () => {
  return localStorage.getItem(STORAGE_KEYS.REFRESH_TOKEN);
};

/**
 * Obtiene los datos del usuario desde localStorage
 * @returns {Object|null} Objeto con datos del usuario o null
 */
export const getUsuario = () => {
  const usuario = localStorage.getItem(STORAGE_KEYS.USUARIO);
  return usuario ? JSON.parse(usuario) : null;
};

/**
 * Verifica si existe una sesión válida (tiene token)
 * @returns {boolean} True si existe token
 */
export const hasValidSession = () => {
  return !!getToken();
};

/**
 * Verifica si el usuario marcó "recordar sesión"
 * @returns {boolean} True si marcó recordar
 */
export const shouldRemember = () => {
  return localStorage.getItem(STORAGE_KEYS.REMEMBER) === 'true';
};

/**
 * Limpia todos los datos de autenticación del localStorage
 */
export const clearAuthData = () => {
  localStorage.removeItem(STORAGE_KEYS.TOKEN);
  localStorage.removeItem(STORAGE_KEYS.REFRESH_TOKEN);
  localStorage.removeItem(STORAGE_KEYS.USUARIO);
  localStorage.removeItem(STORAGE_KEYS.REMEMBER);
};

/**
 * Obtiene todos los datos de autenticación
 * @returns {Object} Objeto con token, refreshToken y usuario
 */
export const getAllAuthData = () => {
  return {
    token: getToken(),
    refreshToken: getRefreshToken(),
    usuario: getUsuario(),
    remember: shouldRemember(),
  };
};
