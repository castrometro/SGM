import { useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';

/**
 * Hook personalizado para manejar la navegación del navegador cuando un modal está abierto
 * Previene la navegación hacia atrás no deseada y mantiene al usuario en el contexto correcto
 * 
 * @param {boolean} isModalOpen - Estado del modal (abierto/cerrado)
 * @param {function} onModalClose - Función para cerrar el modal
 * @param {object} options - Opciones adicionales
 * @param {boolean} options.preventNavigation - Si true, previene navegación completamente (default: true)
 * @param {function} options.onNavigationAttempt - Callback cuando se intenta navegar
 */
export const useModalHistoryBlock = (isModalOpen, onModalClose, options = {}) => {
  const navigate = useNavigate();
  const location = useLocation();
  const originalLocation = useRef(null);
  const hasAddedHistoryEntry = useRef(false);
  
  const {
    preventNavigation = true,
    onNavigationAttempt,
  } = options;

  useEffect(() => {
    if (isModalOpen) {
      // Guardar la ubicación original
      originalLocation.current = location;
      
      // Agregar una entrada temporal al historial para interceptar el botón "atrás"
      if (!hasAddedHistoryEntry.current) {
        window.history.pushState(
          { modalOpen: true, timestamp: Date.now() },
          '',
          location.pathname + location.search + '#modal-open'
        );
        hasAddedHistoryEntry.current = true;
      }

      // Manejar el evento popstate (botón atrás/adelante del navegador)
      const handlePopState = (event) => {
        console.log('🔄 Navegación detectada en modal:', { 
          modalOpen: isModalOpen, 
          state: event.state 
        });

        if (onNavigationAttempt) {
          onNavigationAttempt(event);
        }

        if (preventNavigation) {
          // Prevenir la navegación cerrando el modal apropiadamente
          event.preventDefault();
          
          // Cerrar el modal
          if (onModalClose) {
            onModalClose();
          }
          
          // Restaurar la ubicación original sin el hash del modal
          if (originalLocation.current) {
            const cleanPath = originalLocation.current.pathname + originalLocation.current.search;
            window.history.replaceState(null, '', cleanPath);
          }
        }
      };

      // Agregar listener para popstate
      window.addEventListener('popstate', handlePopState);

      // Manejar el evento beforeunload para casos de recarga/cierre de pestaña
      const handleBeforeUnload = (event) => {
        if (isModalOpen) {
          event.preventDefault();
          event.returnValue = '¿Estás seguro de que quieres salir? Los cambios no guardados se perderán.';
          return event.returnValue;
        }
      };

      window.addEventListener('beforeunload', handleBeforeUnload);

      // Cleanup function
      return () => {
        window.removeEventListener('popstate', handlePopState);
        window.removeEventListener('beforeunload', handleBeforeUnload);
      };
    } else {
      // Modal cerrado: limpiar estado
      if (hasAddedHistoryEntry.current) {
        // Remover la entrada temporal del historial si está presente
        if (window.location.hash === '#modal-open') {
          const cleanPath = location.pathname + location.search;
          window.history.replaceState(null, '', cleanPath);
        }
        hasAddedHistoryEntry.current = false;
      }
      originalLocation.current = null;
    }
  }, [isModalOpen, onModalClose, preventNavigation, onNavigationAttempt, location, navigate]);

  // Función de utilidad para cerrar el modal de forma programática
  const closeModal = () => {
    if (onModalClose) {
      onModalClose();
    }
    
    // Limpiar el estado del historial
    if (hasAddedHistoryEntry.current && window.location.hash === '#modal-open') {
      const cleanPath = location.pathname + location.search;
      window.history.replaceState(null, '', cleanPath);
      hasAddedHistoryEntry.current = false;
    }
  };

  return {
    closeModal,
    isBlocking: isModalOpen && preventNavigation,
  };
};

export default useModalHistoryBlock;