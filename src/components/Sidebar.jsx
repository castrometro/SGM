import {
    BarChart2,
    FolderOpen,
    Settings,
    Users,
    LayoutDashboard,
    Wrench,
    ClipboardCheck,
  } from "lucide-react";
  import { useState } from "react";
  import { AnimatePresence, motion } from "framer-motion";
  import { Link, useLocation } from "react-router-dom";
  
  // Obtenemos el usuario desde localStorage (o contexto si preferís más adelante)
  const getSidebarItemsByRol = (tipo_usuario) => {
    const items = [];
  
    if (tipo_usuario === "analista") {
      items.push(
        { name: "Dashboard", icon: LayoutDashboard, color: "#6366f1", href: "/menu" },
        { name: "Clientes", icon: FolderOpen, color: "#10B981", href: "/menu/clientes" },
        { name: "Herramientas", icon: Wrench, color: "#F59E0B", href: "/menu/tools" }
      );
    }
  
    if (tipo_usuario === "senior") {
      items.push(
        { name: "Dashboard", icon: LayoutDashboard, color: "#6366f1", href: "/menu" },
        { name: "Clientes", icon: FolderOpen, color: "#10B981", href: "/menu/clientes" },
        { name: "Validaciones", icon: ClipboardCheck, color: "#3B82F6", href: "/menu/validaciones" }
      );
    }
  
    if (tipo_usuario === "gerente") {
      items.push(
        { name: "Dashboard", icon: LayoutDashboard, color: "#6366f1", href: "/menu" },
        { name: "Clientes", icon: FolderOpen, color: "#10B981", href: "/menu/clientes" },
        { name: "Usuarios", icon: Users, color: "#EC4899", href: "/menu/usuarios" },
        { name: "Comparador", icon: BarChart2, color: "#F59E0B", href: "/menu/comparacion" },
        { name: "Incidencias", icon: Settings, color: "#6EE7B7", href: "/menu/incidencias" }
      );
    }
  
    return items;
  };
  
  const Sidebar = () => {
    const [isSidebarOpen, setIsSidebarOpen] = useState(true);
    const { pathname } = useLocation();
    const usuario = JSON.parse(localStorage.getItem("usuario"));
    const SIDEBAR_ITEMS = getSidebarItemsByRol(usuario?.tipo_usuario || "");
  
    return (
      <motion.div
        className={`relative z-10 transition-all duration-300 ease-in-out flex-shrink-0 ${
          isSidebarOpen ? "w-64" : "w-20"
        }`}
        animate={{ width: isSidebarOpen ? 256 : 80 }}
      >
        <div className="h-full bg-gray-800 bg-opacity-50 backdrop-blur-md p-4 flex flex-col border-r border-gray-700">
          <motion.button
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
            className="p-2 rounded-full hover:bg-gray-700 transition-colors max-w-fit"
          >
            <Settings size={24} />
          </motion.button>
  
          <nav className="mt-8 flex-grow">
            {SIDEBAR_ITEMS.map((item) => (
              <Link key={item.href} to={item.href}>
                <motion.div
                  className={`flex items-center p-4 text-sm font-medium rounded-lg hover:bg-gray-700 transition-colors mb-2 ${
                    pathname === item.href ? "bg-gray-700" : ""
                  }`}
                >
                  <item.icon size={20} style={{ color: item.color, minWidth: "20px" }} />
                  <AnimatePresence>
                    {isSidebarOpen && (
                      <motion.span
                        className="ml-4 whitespace-nowrap"
                        initial={{ opacity: 0, width: 0 }}
                        animate={{ opacity: 1, width: "auto" }}
                        exit={{ opacity: 0, width: 0 }}
                        transition={{ duration: 0.2, delay: 0.3 }}
                      >
                        {item.name}
                      </motion.span>
                    )}
                  </AnimatePresence>
                </motion.div>
              </Link>
            ))}
          </nav>
        </div>
      </motion.div>
    );
  };
  
  export default Sidebar;
  