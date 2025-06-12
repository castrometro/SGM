// src/api/areas.js
import api from "./config";

export const obtenerAreas = async () => {
  const res = await api.get('/areas/');
  return res.data;
};

export const crearArea = async (areaData) => {
  const res = await api.post('/areas/', areaData);
  return res.data;
};

export const actualizarArea = async (areaId, areaData) => {
  const res = await api.put(`/areas/${areaId}/`, areaData);
  return res.data;
};

export const eliminarArea = async (areaId) => {
  const res = await api.delete(`/areas/${areaId}/`);
  return res.data;
};
