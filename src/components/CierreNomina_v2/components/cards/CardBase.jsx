import React from 'react';
import { Loader2, CheckCircle, AlertTriangle, Clock, Upload } from 'lucide-react';

/**
 * Componente base para todas las tarjetas del sistema de nómina
 * Proporciona estructura y estilos consistentes
 */
const CardBase = ({
  title,
  estado = 'pendiente',
  loading = false,
  error = null,
  disabled = false,
  children,
  actions,
  className = '',
  icon: IconComponent,
  // Props específicas para el componente que no deben llegar al DOM
  isDisabled,
  status,
  description,
  buttons,
  additionalInfo,
  ...domProps
}) => {
  
  // Configuración de estados
  const estadoConfig = {
    pendiente: {
      color: 'border-gray-600 bg-gray-800/50',
      textColor: 'text-gray-300',
      icon: Clock,
      bgIcon: 'bg-gray-600',
      label: 'Pendiente'
    },
    subiendo: {
      color: 'border-blue-500 bg-blue-900/20',
      textColor: 'text-blue-300',
      icon: Upload,
      bgIcon: 'bg-blue-600',
      label: 'Subiendo'
    },
    procesando: {
      color: 'border-yellow-500 bg-yellow-900/20',
      textColor: 'text-yellow-300',
      icon: Loader2,
      bgIcon: 'bg-yellow-600',
      label: 'Procesando'
    },
    procesado: {
      color: 'border-green-500 bg-green-900/20',
      textColor: 'text-green-300',
      icon: CheckCircle,
      bgIcon: 'bg-green-600',
      label: 'Procesado'
    },
    error: {
      color: 'border-red-500 bg-red-900/20',
      textColor: 'text-red-300',
      icon: AlertTriangle,
      bgIcon: 'bg-red-600',
      label: 'Error'
    }
  };

  // Determinar la configuración efectiva basada en las props recibidas
  const estadoEfectivo = status || estado;
  const disabledEfectivo = isDisabled !== undefined ? isDisabled : disabled;
  
  const config = estadoConfig[estadoEfectivo] || estadoConfig.pendiente;
  const IconToShow = IconComponent || config.icon;

  return (
    <div 
      className={`
        relative rounded-lg border backdrop-blur-sm transition-all duration-200
        ${config.color}
        ${disabledEfectivo ? 'opacity-60 cursor-not-allowed' : 'hover:shadow-lg'}
        ${className}
      `}
      {...domProps}
    >
      {/* Header de la tarjeta */}
      <div className="p-4 border-b border-gray-700/50">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {/* Icono de estado */}
            <div className={`
              flex items-center justify-center w-10 h-10 rounded-lg
              ${disabled ? 'bg-gray-600' : config.bgIcon}
            `}>
              <IconToShow 
                size={20} 
                className={`
                  text-white
                  ${estado === 'procesando' ? 'animate-spin' : ''}
                `} 
              />
            </div>
            
            {/* Título y descripción */}
            <div>
              <h3 className={`
                font-semibold
                ${disabledEfectivo ? 'text-gray-400' : 'text-white'}
              `}>
                {title}
                {disabledEfectivo && (
                  <span className="ml-2 text-sm font-normal text-gray-500">
                    (Bloqueado)
                  </span>
                )}
              </h3>
              <p className={`text-sm ${config.textColor}`}>
                {loading ? 'Cargando...' : (description || config.label)}
              </p>
            </div>
          </div>

          {/* Loading spinner si está cargando */}
          {loading && (
            <Loader2 className="animate-spin text-blue-400" size={20} />
          )}
        </div>

        {/* Mostrar error si existe */}
        {error && (
          <div className="mt-3 p-2 bg-red-900/30 border border-red-700/50 rounded text-red-300 text-sm">
            <div className="flex items-center gap-2">
              <AlertTriangle size={16} />
              <span>Error: {error.message || error}</span>
            </div>
          </div>
        )}
      </div>

      {/* Contenido principal */}
      <div className="p-4">
        {children}
        
        {/* Información adicional */}
        {additionalInfo && additionalInfo.length > 0 && (
          <div className="mt-3 space-y-1">
            {additionalInfo.map((info, index) => (
              <p key={index} className="text-sm text-gray-400">
                {info}
              </p>
            ))}
          </div>
        )}
      </div>

      {/* Botones de acción */}
      {buttons && buttons.length > 0 && (
        <div className="px-4 pb-4 border-t border-gray-700/50 bg-gray-800/30">
          <div className="pt-4 flex gap-2 flex-wrap">
            {buttons.map((button, index) => {
              const ButtonIcon = button.icon;
              return (
                <button
                  key={index}
                  onClick={button.onClick}
                  disabled={button.disabled || disabledEfectivo}
                  className={`
                    flex items-center gap-2 px-4 py-2 rounded-lg font-medium text-sm
                    transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed
                    ${button.variant === 'primary' 
                      ? 'bg-blue-600 hover:bg-blue-700 text-white' 
                      : button.variant === 'danger'
                      ? 'bg-red-600 hover:bg-red-700 text-white'
                      : 'bg-gray-600 hover:bg-gray-700 text-gray-200'
                    }
                  `}
                >
                  {button.loading ? (
                    <Loader2 className="animate-spin" size={16} />
                  ) : (
                    ButtonIcon && <ButtonIcon size={16} />
                  )}
                  {button.text}
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Acciones legacy (por compatibilidad) */}
      {actions && (
        <div className="px-4 pb-4 border-t border-gray-700/50 bg-gray-800/30">
          <div className="pt-4">
            {actions}
          </div>
        </div>
      )}

      {/* Overlay para disabled */}
      {disabledEfectivo && (
        <div className="absolute inset-0 bg-gray-900/50 rounded-lg pointer-events-none" />
      )}
    </div>
  );
};

export default CardBase;
