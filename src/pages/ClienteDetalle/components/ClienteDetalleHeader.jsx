import React from 'react';
import { getAreaColor } from '../../../constants/areaColors';
import { MESSAGES } from '../config/clienteDetalleConfig';

const ClienteDetalleHeader = ({ areaActiva, areaConfig }) => {
  return (
    <div className="flex items-center gap-4 mb-4">
      <h1 className="text-2xl font-bold">{MESSAGES.pageTitle}</h1>
      {areaActiva && (
        <span className={`px-3 py-1 rounded-full text-white text-sm font-semibold ${getAreaColor(areaActiva)}`}>
          {areaConfig?.title || areaActiva}
        </span>
      )}
    </div>
  );
};

export default ClienteDetalleHeader;
