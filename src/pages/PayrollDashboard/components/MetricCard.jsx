import React from 'react';
import { DASHBOARD_CARDS } from '../config/dashboardConfig';

const MetricCard = ({ cardKey, data, userType }) => {
  const config = DASHBOARD_CARDS[cardKey];
  const IconComponent = config.icon;
  const cardData = data[cardKey] || {};

  const formatValue = (value, type = 'number') => {
    if (type === 'currency') {
      return new Intl.NumberFormat('es-CL', {
        style: 'currency',
        currency: 'CLP',
        minimumFractionDigits: 0
      }).format(value);
    }
    if (type === 'percentage') {
      return `${value}%`;
    }
    return new Intl.NumberFormat('es-CL').format(value);
  };

  const getMainValue = () => {
    switch (cardKey) {
      case 'empleados':
        return formatValue(cardData.activos || 0);
      case 'nominasEnProceso':
        return formatValue(cardData.total || 0);
      case 'nominasAprobadas':
        return formatValue(cardData.total || 0);
      case 'costoMensual':
        return formatValue(cardData.total || 0, 'currency');
      case 'alertas':
        return formatValue(cardData.total || 0);
      case 'reportes':
        return formatValue(cardData.total || 0);
      default:
        return '0';
    }
  };

  const getSubValue = () => {
    switch (cardKey) {
      case 'empleados':
        return `${cardData.inactivos || 0} inactivos`;
      case 'nominasEnProceso':
        return `${cardData.pendientes || 0} pendientes`;
      case 'nominasAprobadas':
        return `Este mes: ${cardData.esteMes || 0}`;
      case 'costoMensual':
        return `Descuentos: ${formatValue(cardData.descuentos || 0, 'currency')}`;
      case 'alertas':
        return `${cardData.criticas || 0} críticas`;
      case 'reportes':
        return `${cardData.pendientes || 0} pendientes`;
      default:
        return '';
    }
  };

  const getTrend = () => {
    const trend = cardData.trend;
    if (!trend) return null;

    const isPositive = trend.startsWith('+');
    const isNeutral = trend === '0' || trend === '+0' || trend === '-0';

    return (
      <span className={`text-xs font-medium ${
        isNeutral ? 'text-gray-400' :
        isPositive ? 'text-green-400' : 'text-red-400'
      }`}>
        {trend}
      </span>
    );
  };

  return (
    <div className={`${config.bgColor} ${config.borderColor} border rounded-lg p-6 transition-all duration-200 hover:scale-105`}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-lg bg-gray-800/50`}>
            <IconComponent 
              size={24} 
              style={{ color: config.color }}
            />
          </div>
          <h3 className="text-white font-semibold text-sm">
            {config.title}
          </h3>
        </div>
        {getTrend()}
      </div>
      
      <div className="space-y-1">
        <div className="text-2xl font-bold text-white">
          {getMainValue()}
        </div>
        <div className="text-sm text-gray-400">
          {getSubValue()}
        </div>
      </div>
    </div>
  );
};

export default MetricCard;
