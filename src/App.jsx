import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Login from "./pages/Login";
import MenuUsuario from "./pages/MenuUsuario/index";
import PrivateRoute from "./components/PrivateRoute";
import Layout from "./components/Layout";
import Clientes from "./pages/Clientes/index";
import ClienteDetalle from "./pages/ClienteDetalle/index";
import PaginaClasificacion from "./pages/PaginaClasificacion";
import ClasificacionCierre from "./pages/ClasificacionCierre";
import HistorialCierresPage from "./pages/HistorialCierresPage/index";
import CrearCierre from "./pages/CrearCierre/index";
import CierreDetalle from "./pages/CierreDetalle/index"; // Feature folder pattern - área específica
import AnalisisLibro from "./pages/AnalisisLibro";
import MovimientosCuenta from "./pages/MovimientosCuenta";
import InformesAnalistas from "./pages/InformesAnalistas";
import Dashboard from "./pages/Dashboard";
import CapturaMasivaGastos from "./pages/CapturaMasivaGastos/index";
import GestionAnalistas from "./components/Gerente/GestionAnalistas";
import DashboardGerente from "./pages/DashboardGerente";
import VistaGerencial from "./pages/VistaGerencial";
import Tools from "./pages/Tools/index";
import MisAnalistas from "./pages/MisAnalistas";
import PayrollDashboard from "./pages/PayrollDashboard/index";

// Importar componentes de Gerente
import LogsActividad from "./components/Gerente/LogsActividad";
import EstadosCierres from "./components/Gerente/EstadosCierres";
import CacheRedis from "./components/Gerente/CacheRedis";
import AdminSistema from "./components/Gerente/AdminSistema";

function App() {
  return (
    <Router>
      <Routes>
        {/* ------------------ PÚBLICAS ------------------ */}
        <Route path="/" element={<Login />} />

        {/* ------------------ PROTEGIDAS / LAYOUT ------------------ */}
        <Route
          path="/menu"
          element={
            <PrivateRoute>
              <Layout />
            </PrivateRoute>
          }
        >

          {/* ----------- ÁREA: GENERAL / USUARIO ------------- */}
          <Route index element={<MenuUsuario />} />

          {/* ----------- ÁREA: CLIENTES ------------- */}
          <Route path="clientes" element={<Clientes />} />
          <Route path="clientes/:id" element={<ClienteDetalle />} />
          <Route path="clientes/:clienteId/clasificacion" element={<PaginaClasificacion />} />
          <Route path="clientes/:clienteId/cierres" element={<HistorialCierresPage />} />
          <Route path="clientes/:clienteId/crear-cierre" element={<CrearCierre />} />
          
          {/* ----------- ÁREA: PAYROLL CLIENTES ------------- */}
          <Route path="clientes/:clienteId/cierres-payroll" element={<HistorialCierresPage />} />
          <Route path="clientes/:clienteId/crear-cierre-payroll" element={<CrearCierre />} />
          <Route path="clientes/:clienteId/cierres-payroll/:cierreId" element={<div className="text-white p-8">Detalle Cierre Payroll - En desarrollo</div>} />

          {/* ----------- ÁREA: CONTABILIDAD ------------- */}
          <Route path="cierres/:cierreId" element={<CierreDetalle />} />
          <Route path="cierres/:cierreId/libro" element={<AnalisisLibro />} />
          <Route path="cierres/:cierreId/clasificacion" element={<ClasificacionCierre />} />
          <Route
            path="cierres/:cierreId/cuentas/:cuentaId"
            element={<MovimientosCuenta />}
          />

          {/* ----------- ÁREA: GESTIÓN DE ANALISTAS ------------- */}
          <Route path="analistas" element={<GestionAnalistas />} />
          
          {/* ----------- ÁREA: MIS ANALISTAS (SUPERVISOR) ------------- */}
          <Route path="mis-analistas" element={<MisAnalistas />} />

          {/* ----------- ÁREA: DASHBOARD GERENTE ------------- */}
          <Route path="dashboard-gerente" element={<DashboardGerente />} />
          
          {/* ----------- ÁREA: VISTA GERENCIAL ------------- */}
          <Route path="vista-gerencial" element={<VistaGerencial />} />

          {/* ----------- ÁREA: GERENTE - FUNCIONES AVANZADAS ------------- */}
          <Route path="gerente/logs-actividad" element={<LogsActividad />} />
          <Route path="gerente/estados-cierres" element={<EstadosCierres />} />
          <Route path="gerente/cache-redis" element={<CacheRedis />} />
          <Route path="gerente/admin-sistema" element={<AdminSistema />} />

          {/* ----------- ÁREA: ANALYTICS DE PERFORMANCE ------------- */}
          <Route path="analytics" element={<Dashboard />} />
          
          {/* ----------- ÁREA: HERRAMIENTAS ------------- */}
          <Route path="tools" element={<Tools />} />
          <Route path="tools/captura-masiva-gastos" element={<CapturaMasivaGastos />} />

          {/* ----------- ÁREA: PAYROLL ------------- */}
          <Route path="payroll/dashboard" element={<PayrollDashboard />} />
          <Route path="payroll/supervision" element={<div className="text-white p-8">Supervisión Nóminas - En desarrollo</div>} />
          <Route path="payroll/reportes" element={<div className="text-white p-8">Reportes de Nómina - En desarrollo</div>} />
          <Route path="payroll/empleados/gestion" element={<div className="text-white p-8">Gestión Avanzada de Empleados - En desarrollo</div>} />
          <Route path="payroll/cierres" element={<div className="text-white p-8">Cierres de Nómina - En desarrollo</div>} />
          <Route path="payroll/configuracion" element={<div className="text-white p-8">Configuración Payroll - En desarrollo</div>} />
          <Route path="payroll/analytics" element={<div className="text-white p-8">Analytics Payroll - En desarrollo</div>} />
          <Route path="payroll/logs" element={<div className="text-white p-8">Logs Payroll - En desarrollo</div>} />

          {/* ----------- 404 / OTRAS ------------- */}
          <Route path="*" element={<h1 className="text-white">404 - Página no encontrada</h1>} />

        </Route>
      </Routes>
    </Router>
  );
}

export default App;
