// src/modules/auth/constants/auth.constants.js

/**
 * Claves de almacenamiento en localStorage
 */
export const STORAGE_KEYS = {
  TOKEN: 'token',
  REFRESH_TOKEN: 'refreshToken',
  USUARIO: 'usuario',
  REMEMBER: 'recordarSesion',
};

/**
 * Mensajes de error para validaciones y autenticación
 */
export const ERROR_MESSAGES = {
  // Validaciones de email
  EMAIL_REQUIRED: 'El correo es requerido',
  EMAIL_INVALID: 'Formato de correo inválido',
  EMAIL_NOT_BDO: 'Debe usar un correo @bdo.cl',
  
  // Validaciones de contraseña
  PASSWORD_REQUIRED: 'La contraseña es requerida',
  PASSWORD_TOO_SHORT: 'Mínimo 6 caracteres',
  
  // Errores de autenticación
  LOGIN_FAILED: 'Credenciales incorrectas. Verifique su correo y contraseña.',
  UNAUTHORIZED: 'Correo o contraseña incorrectos.',
  FORBIDDEN: 'Acceso denegado. Contacte al administrador.',
  SERVER_ERROR: 'Error del servidor. Intente nuevamente más tarde.',
  NETWORK_ERROR: 'No se pudo conectar con el servidor. Verifique su conexión.',
};

/**
 * Reglas de validación
 */
export const VALIDATION_RULES = {
  EMAIL_REGEX: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
  BDO_DOMAIN: '@bdo.cl',
  MIN_PASSWORD_LENGTH: 6,
};

/**
 * Endpoints de la API de autenticación
 */
export const API_ENDPOINTS = {
  LOGIN: '/token/',
  REFRESH: '/token/refresh/',
  ME: '/usuarios/me/',
};

/**
 * Códigos de estado HTTP
 */
export const HTTP_STATUS = {
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  SERVER_ERROR: 500,
};
