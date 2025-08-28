import MovimientosCuenta from "./pages/MovimientosCuenta";
import InformesAnalistas from "./pages/InformesAnalistas";
import Dashboard from "./pages/Dashboard";
import CapturaMasivaGastos from "./pages/CapturaMasivaGastos/index";
import GestionAnalistas from "./components/Gerente/GestionAnalistas";
import DashboardGerente from "./pages/DashboardGerente";
import VistaGerencial from "./pages/VistaGerencial";
--
          
          {/* ----------- ÁREA: HERRAMIENTAS ------------- */}
          <Route path="tools" element={<Tools />} />
          <Route path="tools/captura-masiva-gastos" element={<CapturaMasivaGastos />} />

          {/* ----------- ÁREA: PAYROLL ------------- */}
          <Route path="payroll/dashboard" element={<PayrollDashboard />} />
