// src/modules/menu/hooks/useUserContext.js
import { useMemo } from 'react';
import * as userStorage from '../utils/user-storage';

/**
 * Hook para obtener información del usuario autenticado
 */
const useUserContext = () => {
  const usuario = useMemo(() => userStorage.getUsuario(), []);
  const token = useMemo(() => userStorage.getToken(), []);

  return {
    usuario,
    token,
    isAuthenticated: Boolean(token && usuario),
    hasSession: userStorage.hasValidSession(),
  };
};

export default useUserContext;
