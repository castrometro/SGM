// src/modules/auth/utils/validators.js
import { VALIDATION_RULES, ERROR_MESSAGES } from '../constants/auth.constants';

/**
 * Valida el formato y dominio de un email
 * @param {string} email - Email a validar
 * @returns {string} Mensaje de error o string vacío si es válido
 */
export const validateEmail = (email) => {
  if (!email) {
    return ERROR_MESSAGES.EMAIL_REQUIRED;
  }
  
  if (!VALIDATION_RULES.EMAIL_REGEX.test(email)) {
    return ERROR_MESSAGES.EMAIL_INVALID;
  }
  
  if (!email.endsWith(VALIDATION_RULES.BDO_DOMAIN)) {
    return ERROR_MESSAGES.EMAIL_NOT_BDO;
  }
  
  return '';
};

/**
 * Valida la longitud de una contraseña
 * @param {string} password - Contraseña a validar
 * @returns {string} Mensaje de error o string vacío si es válida
 */
export const validatePassword = (password) => {
  if (!password) {
    return ERROR_MESSAGES.PASSWORD_REQUIRED;
  }
  
  if (password.length < VALIDATION_RULES.MIN_PASSWORD_LENGTH) {
    return ERROR_MESSAGES.PASSWORD_TOO_SHORT;
  }
  
  return '';
};

/**
 * Verifica si un email es del dominio BDO
 * @param {string} email - Email a verificar
 * @returns {boolean} True si es email de BDO
 */
export const validateBDOEmail = (email) => {
  return email.endsWith(VALIDATION_RULES.BDO_DOMAIN);
};

/**
 * Valida un formulario de login completo
 * @param {string} correo - Email del usuario
 * @param {string} password - Contraseña del usuario
 * @returns {Object} Objeto con errores { correo: string, password: string }
 */
export const validateLoginForm = (correo, password) => {
  return {
    correo: validateEmail(correo),
    password: validatePassword(password),
  };
};

/**
 * Verifica si un formulario tiene errores
 * @param {Object} errors - Objeto de errores
 * @returns {boolean} True si existe algún error
 */
export const hasErrors = (errors) => {
  return Object.values(errors).some(error => error !== '');
};
