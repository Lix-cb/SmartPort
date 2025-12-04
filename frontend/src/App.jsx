import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Inicio from "./pages/Inicio.jsx";
import AdminLogin from "./pages/AdminLogin.jsx";
import AdminPanel from "./pages/AdminPanel.jsx";
import AdminRegistro from "./pages/AdminRegistro.jsx";
import AdminRFID from "./pages/AdminRFID.jsx";
import AdminCamara from "./pages/AdminCamara.jsx";
import UsuarioAcceso from "./pages/UsuarioAcceso.jsx";
import AdminRegistrarAdmin from "./pages/AdminRegistrarAdmin";

export default function App() {
  return (
    <Router>
      <Routes>
        {/* Pantalla inicial */}
        <Route path="/" element={<Inicio />} />
        
        {/* Flujo Administrador */}
        <Route path="/admin-login" element={<AdminLogin />} />
        <Route path="/admin-panel" element={<AdminPanel />} />
        <Route path="/admin-registro" element={<AdminRegistro />} />
        <Route path="/admin-rfid" element={<AdminRFID />} />
        <Route path="/admin-camara" element={<AdminCamara />} />
        <Route path="/admin-registrar-admin" element={<AdminRegistrarAdmin />} />
        
        {/* Flujo Usuario */}
        <Route path="/usuario-acceso" element={<UsuarioAcceso />} />
      </Routes>
    </Router>
  );
}
