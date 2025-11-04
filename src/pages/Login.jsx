import LoginForm from "../components/LoginForm";
import Header_login from "../components/Header_login";
import { useNavigate } from "react-router-dom";
import { loginUsuario, obtenerUsuario } from "../api/auth";
import { useEffect, useState } from "react";

const Login = () => {
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isCheckingSession, setIsCheckingSession] = useState(true);

  useEffect(() => {
    const validarSesion = async () => {
      const token = localStorage.getItem("token");
      if (!token) {
        setIsCheckingSession(false);
        return;
      }

      try {
        const usuario = await obtenerUsuario();
        localStorage.setItem("usuario", JSON.stringify(usuario));
        navigate("/menu");
      } catch (error) {
        console.warn("Token inválido o expirado, debe iniciar sesión");
        localStorage.removeItem("token");
        localStorage.removeItem("usuario");
        setIsCheckingSession(false);
      }
    };

    validarSesion();
  }, [navigate]);

  const handleLogin = async (correo, password, recordar) => {
    setIsLoading(true);
    setError(null);

    try {
      const result = await loginUsuario(correo, password);
      localStorage.setItem("token", result.access);

      // Guardar refresh token si existe
      if (result.refresh) {
        localStorage.setItem("refreshToken", result.refresh);
      }

      // Si el usuario marcó "recordar", guardar preferencia
      if (recordar) {
        localStorage.setItem("recordarSesion", "true");
      }

      const usuario = await obtenerUsuario();
      localStorage.setItem("usuario", JSON.stringify(usuario));

      // Pequeño delay para mejor UX
      setTimeout(() => {
        navigate("/menu");
      }, 300);
    } catch (error) {
      console.error("Login error:", error);
      
      // Mensajes de error más específicos
      let errorMessage = "Credenciales incorrectas. Verifique su correo y contraseña.";
      
      if (error.response) {
        if (error.response.status === 401) {
          errorMessage = "Correo o contraseña incorrectos.";
        } else if (error.response.status === 403) {
          errorMessage = "Acceso denegado. Contacte al administrador.";
        } else if (error.response.status >= 500) {
          errorMessage = "Error del servidor. Intente nuevamente más tarde.";
        } else if (error.response.data?.detail) {
          errorMessage = error.response.data.detail;
        }
      } else if (error.request) {
        errorMessage = "No se pudo conectar con el servidor. Verifique su conexión.";
      }
      
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  // Mostrar loading mientras valida sesión existente
  if (isCheckingSession) {
    return (
      <div className="flex items-center justify-center h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 border-red-600"></div>
          <p className="text-white mt-4 text-lg">Verificando sesión...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col w-full min-h-screen overflow-auto bg-gray-900 text-gray-100">
      {/* Background con gradiente animado */}
      <div className="fixed inset-0 z-0 overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 opacity-90" />
        <div className="absolute inset-0 backdrop-blur-sm" />
        
        {/* Elementos decorativos */}
        <div className="absolute top-20 left-10 w-72 h-72 bg-red-600 rounded-full mix-blend-multiply filter blur-3xl opacity-10 animate-blob"></div>
        <div className="absolute top-40 right-10 w-72 h-72 bg-blue-600 rounded-full mix-blend-multiply filter blur-3xl opacity-10 animate-blob animation-delay-2000"></div>
        <div className="absolute -bottom-8 left-20 w-72 h-72 bg-purple-600 rounded-full mix-blend-multiply filter blur-3xl opacity-10 animate-blob animation-delay-4000"></div>
      </div>

      {/* Contenido */}
      <div className="relative z-10 flex flex-col min-h-screen">
        <Header_login />
        
        <div className="flex flex-grow items-center justify-center px-4 py-8 sm:py-12">
          <LoginForm 
            onLogin={handleLogin} 
            isLoading={isLoading}
            error={error}
          />
        </div>

        {/* Footer */}
        <footer className="relative z-10 py-4 sm:py-6 text-center text-gray-400 text-xs sm:text-sm">
          <p>© {new Date().getFullYear()} BDO Chile. Todos los derechos reservados.</p>
          <p className="mt-1">Sistema de Gestión SGM - Contabilidad & Nómina</p>
        </footer>
      </div>
    </div>
  );
};

export default Login;

// src/pages/Login.jsx