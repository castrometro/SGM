// src/modules/shared/auth/api/auth.api.js
import api from "../../../../api/config";
import { API_ENDPOINTS, ERROR_MESSAGES, HTTP_STATUS } from '../constants/auth.constants';

/**
 * Realiza el login de un usuario
 * @param {string} correo - Email corporativo del usuario
 * @param {string} password - Contraseña del usuario
 * @returns {Promise<Object>} Objeto con access y refresh tokens
 * @throws {Error} Si las credenciales son incorrectas o hay error de conexión
 */
export const loginUsuario = async (correo, password) => {
  const response = await api.post(API_ENDPOINTS.LOGIN, {
    correo_bdo: correo,
    password,
  });
  return response.data;
};

/**
 * Obtiene los datos del usuario autenticado
 * @returns {Promise<Object>} Datos del usuario
 * @throws {Error} Si el token es inválido o expiró
 */
export const obtenerUsuario = async () => {
  const response = await api.get(API_ENDPOINTS.ME);
  return response.data;
};

/**
 * Refresca el access token usando el refresh token
 * @param {string} refreshToken - Refresh token del usuario
 * @returns {Promise<Object>} Nuevo access token
 * @throws {Error} Si el refresh token es inválido
 */
export const refreshToken = async (refreshToken) => {
  const response = await api.post(API_ENDPOINTS.REFRESH, {
    refresh: refreshToken,
  });
  return response.data;
};

/**
 * Parsea un error de la API y retorna un mensaje amigable
 * @param {Error} error - Error de Axios
 * @returns {string} Mensaje de error formateado
 */
export const parseError = (error) => {
  if (error.response) {
    const { status, data } = error.response;
    
    switch (status) {
      case HTTP_STATUS.UNAUTHORIZED:
        return ERROR_MESSAGES.UNAUTHORIZED;
      case HTTP_STATUS.FORBIDDEN:
        return ERROR_MESSAGES.FORBIDDEN;
      case HTTP_STATUS.SERVER_ERROR:
      default:
        if (status >= HTTP_STATUS.SERVER_ERROR) {
          return ERROR_MESSAGES.SERVER_ERROR;
        }
        return data?.detail || ERROR_MESSAGES.LOGIN_FAILED;
    }
  } else if (error.request) {
    return ERROR_MESSAGES.NETWORK_ERROR;
  }
  
  return ERROR_MESSAGES.LOGIN_FAILED;
};

/**
 * Logout del usuario (limpieza de sesión en frontend)
 * Nota: Django usa tokens JWT sin estado, no hay endpoint de logout
 */
export const logout = () => {
  // El logout se maneja limpiando el localStorage
  // No hay endpoint en el backend ya que JWT es stateless
  return Promise.resolve();
};
