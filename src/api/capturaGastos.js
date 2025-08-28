// src/api/capturaGastos.js

const API_BASE_URL = 'http://172.17.11.18:8000/api';

export const subirArchivoGastos = async (archivo, mapeoCC = {}) => {
  const formData = new FormData();
  formData.append('archivo', archivo);
  
  // Agregar mapeo de centros de costos
  if (mapeoCC) {
    formData.append('mapeo_cc', JSON.stringify(mapeoCC));
  }

  const token = localStorage.getItem('token');
  
  const response = await fetch(`${API_BASE_URL}/captura-masiva-gastos/`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.error || 'Error subiendo archivo');
  }

  return await response.json();
};

export const consultarEstadoGastos = async (taskId) => {
  const token = localStorage.getItem('token');
  
  const response = await fetch(`${API_BASE_URL}/estado-captura-gastos/${taskId}/`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.error || 'Error consultando estado');
  }

  return await response.json();
};

export const descargarResultadoGastos = async (taskId) => {
  const token = localStorage.getItem('token');
  
  const response = await fetch(`${API_BASE_URL}/descargar-resultado-gastos/${taskId}/`, {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.error || 'Error descargando archivo');
  }

  // Obtener el blob del archivo
  const blob = await response.blob();
  
  // Crear URL para descarga
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `gastos_procesados_${taskId}.xlsx`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
  
  return true;
};

export const leerHeadersExcel = async (archivo) => {
  const formData = new FormData();
  formData.append('archivo', archivo);

  const token = localStorage.getItem('token');
  
  const response = await fetch(`${API_BASE_URL}/gastos/leer-headers/`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.error || 'Error leyendo headers del Excel');
  }

  return await response.json();
};
