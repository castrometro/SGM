import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Login from "./pages/Login";
import MenuUsuario from "./pages/MenuUsuario";
import PrivateRoute from "./components/PrivateRoute";
import Layout from "./components/Layout";
import Clientes from "./pages/Clientes";
import ClienteDetalle from "./pages/ClienteDetalle";
import PaginaClasificacion from "./pages/PaginaClasificacion";
import HistorialCierresPage from "./pages/HistorialCierresPage";
import CrearCierre from "./pages/CrearCierre";
import CierreDetalle from "./pages/CierreDetalle"; // Asegúrate de importar la página de detalle del cierre
import CierreDetalleNomina from "./pages/CierreDetalleNomina";
import AnalisisCuentas from "./pages/AnalisisCuentas";

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

          {/* ----------- ÁREA: CONTABILIDAD ------------- */}
          <Route path="cierres/:cierreId" element={<CierreDetalle />} />
          <Route path="cierres/:cierreId/analisis" element={<AnalisisCuentas />} />

          {/* ----------- ÁREA: NÓMINA ------------- */}
          <Route path="nomina/cierres/:cierreId" element={<CierreDetalleNomina />} />

          {/* ----------- 404 / OTRAS ------------- */}
          <Route path="*" element={<h1 className="text-white">404 - Página no encontrada</h1>} />

        </Route>
      </Routes>
    </Router>
  );
}

export default App;
