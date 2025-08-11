import { useNavigate } from "react-router-dom";
import { useMemo } from "react";
import { useToolsOptions } from "./useToolsOptions";

/**
 * Hook para manejar acciones de herramientas
 * Ahora utiliza el nuevo sistema dinámico
 * @deprecated - Usar useToolsOptions para funcionalidad completa
 */
export const useToolActions = () => {
  const navigate = useNavigate();
  
  // Obtener usuario del localStorage
  const usuario = JSON.parse(localStorage.getItem("usuario"));
  
  // Usar el nuevo hook dinámico
  const { sections, executeAction } = useToolsOptions(usuario);

  return {
    sections,
    executeAction
  };
};
