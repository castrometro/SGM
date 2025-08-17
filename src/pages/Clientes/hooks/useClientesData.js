import { useState, useEffect } from 'react';
import { obtenerUsuario } from '../../../api/auth';
import { getUserConfig, MESSAGES } from '../config/clientesConfig';

export const useClientesData = () => {
  const [clientes, setClientes] = useState([]);
  const [filtro, setFiltro] = useState("");
  const [usuario, setUsuario] = useState(null);
  const [areaActiva, setAreaActiva] = useState(null);
  const [tipoModulo, setTipoModulo] = useState(null);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const cargarDatos = async () => {
      setCargando(true);
      setError("");
      try {
        const userData = await obtenerUsuario();
        setUsuario(userData);

        // Determinar área activa - misma lógica que el original
        let area = null;
        if (userData.area_activa) {
          area = userData.area_activa;
        } else if (userData.areas && userData.areas.length > 0) {
          area = userData.areas[0].nombre || userData.areas[0];
        } else {
          setError(MESSAGES.noArea);
          setCargando(false);
          return;
        }
        setAreaActiva(area);
        localStorage.setItem("area_activa", area);

        // Obtener configuración y API según tipo de usuario Y área activa
        const userConfig = getUserConfig(userData.tipo_usuario, area);
        const data = await userConfig.apiFunction();
        
        console.log('=== DEBUG: Clientes cargados ===');
        console.log('Tipo usuario:', userData.tipo_usuario);
        console.log('Área activa:', area);
        console.log('Módulo:', userConfig.tipoModulo);
        console.log('Total clientes:', data.length);
        console.log('Endpoint usado:', userConfig.endpoint);
        console.log('Estructura primer cliente:', data[0]);
        console.log('===============================');
        
        setClientes(data);
        setTipoModulo(userConfig.tipoModulo);
      } catch (err) {
        setError(MESSAGES.error);
        console.error("Error al cargar usuario/clientes:", err);
      }
      setCargando(false);
    };

    cargarDatos();
  }, []);

  // Filtrado de clientes - misma lógica que el original
  const clientesFiltrados = clientes.filter((cliente) =>
    cliente.nombre.toLowerCase().includes(filtro.toLowerCase()) ||
    cliente.rut.toLowerCase().includes(filtro.toLowerCase())
  );

  return {
    clientes,
    clientesFiltrados,
    filtro,
    setFiltro,
    usuario,
    areaActiva,
    tipoModulo,
    cargando,
    error
  };
};
