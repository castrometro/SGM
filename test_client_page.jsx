import React from 'react';
import { BrowserRouter } from 'react-router-dom';
import Clientes from './src/pages/Clientes';

function TestClientPage() {
  // Mock user data with payroll area
  const mockUser = {
    area: 'payroll'
  };

  return (
    <BrowserRouter>
      <div style={{ padding: '20px' }}>
        <h1>Test Página de Clientes</h1>
        <Clientes />
      </div>
    </BrowserRouter>
  );
}

export default TestClientPage;
