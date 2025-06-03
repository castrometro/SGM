// src/hooks/useAuth.js
export const useAuth = () => {
  const token = localStorage.getItem("token");
  const usuario = JSON.parse(localStorage.getItem("usuario") || "null");
  return { token, usuario };
};
