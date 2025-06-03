import LoginForm from "../components/LoginForm";
import Header_login from "../components/Header_login";
import { useNavigate } from "react-router-dom";
import { loginUsuario, obtenerUsuario } from "../api/auth";
import { useEffect } from "react";
const Login = () => {
  const navigate = useNavigate();
  useEffect(() => {
    const validarSesion = async () => {
      const token = localStorage.getItem("token");
      if (!token) return; // sin token, mostrar login

      try {
        const usuario = await obtenerUsuario();
        localStorage.setItem("usuario", JSON.stringify(usuario));
        navigate("/menu");
      } catch (error) {
        console.warn("Token inválido o expirado, debe iniciar sesión");
        localStorage.removeItem("token");
        localStorage.removeItem("usuario");
      }
    };

    validarSesion();
  }, []);
  const handleLogin = async (correo, password) => {
    try {
      const result = await loginUsuario(correo, password);
      localStorage.setItem("token", result.access);

      const usuario = await obtenerUsuario();
      localStorage.setItem("usuario", JSON.stringify(usuario));

      navigate("/menu");
    } catch (error) {
      console.error("Login error:", error);
      alert("Credenciales incorrectas o error de servidor.");
    }
  };

  return (
    <div className="flex flex-col w-full h-screen overflow-hidden bg-gray-900 text-gray-100">
      <div className="fixed inset-0 z-0">
        <div className="absolute inset-0 bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 opacity-80" />
        <div className="absolute inset-0 backdrop-blur-sm" />
      </div>

      <div className="relative z-10 flex flex-col h-full">
        <Header_login />
        <div className="flex flex-grow items-center justify-center">
          <LoginForm onLogin={handleLogin} />
        </div>
      </div>
    </div>
  );
};

export default Login;

// src/pages/Login.jsx