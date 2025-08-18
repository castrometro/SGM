import React from 'react';
import { BrowserRouter } from 'react-router-dom';
import ClienteDetalle from './src/pages/ClienteDetalle';

function TestClienteDetalle() {
  return (
    <BrowserRouter>
      <div style={{ padding: '20px', backgroundColor: '#1f2937', minHeight: '100vh' }}>
        <h1 style={{ color: 'white', marginBottom: '20px' }}>Test Cliente Detalle</h1>
        
        {/* Simular diferentes rutas para testing */}
        <div style={{ marginBottom: '20px' }}>
          <p style={{ color: '#9ca3af', fontSize: '14px' }}>
            Para probar, navegar a: /menu/clientes/[ID] donde ID es un cliente válido
          </p>
          <p style={{ color: '#9ca3af', fontSize: '14px' }}>
            El componente detectará automáticamente si el usuario es de Contabilidad o Payroll
          </p>
        </div>
        
        <ClienteDetalle />
      </div>
    </BrowserRouter>
  );
}

export default TestClienteDetalle;
