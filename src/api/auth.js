// src/api/auth.js
import api from "./config";

export const loginUsuario = async (correo, password) => {
  const response = await api.post("/token/", {
    correo_bdo: correo,
    password,
  });
  console.log("Login response:", response.data);
  return response.data;
};

export const obtenerUsuario = async () => {
  const response = await api.get("/usuarios/me/");
  return response.data;
};
