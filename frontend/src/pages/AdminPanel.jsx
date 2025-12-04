import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

export default function AdminPanel() {
  const navigate = useNavigate();
  const [adminNombre, setAdminNombre] = useState("");

  useEffect(() => {
    const nombre = localStorage.getItem("admin_nombre");
    if (! nombre) {
      navigate("/admin-login");
      return;
    }
    setAdminNombre(nombre);
  }, [navigate]);

  const handleRegistrarPasajero = () => {
    navigate("/admin-registro");
  };

  const handleRegistrarAdmin = () => {
    navigate("/admin-registrar-admin");
  };

  const handleDashboard = () => {
    navigate("/dashboard-pesos");
  };

  const handleSalir = () => {
    localStorage.removeItem("admin_id");
    localStorage.removeItem("admin_nombre");
    navigate("/");
  };

  return (
    <div className="container">
      <img src="/GAP_logo.jpg" alt="Logo GAP" className="logo" />
      <h2 className="title">Panel de Administrador</h2>
      <p style={{ marginBottom: "30px", fontSize: "16px", color: "#666" }}>
        Bienvenido, <strong>{adminNombre}</strong>
      </p>
      
      <button 
        className="button" 
        onClick={handleRegistrarPasajero}
        style={{ 
          marginBottom: "15px",
          background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
        }}
      >
        👤 Registrar Pasajero
      </button>
      
      <button 
        className="button" 
        onClick={handleRegistrarAdmin}
        style={{ 
          marginBottom: "15px", 
          backgroundColor: "#17a2b8" 
        }}
      >
        🔑 Registrar Nuevo Admin
      </button>
      
      <button 
        className="button" 
        onClick={handleDashboard}
        style={{ 
          marginBottom: "15px", 
          background: "linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%)"
        }}
      >
        📊 Dashboard de Pesos
      </button>
      
      <button 
        className="button" 
        onClick={handleSalir}
        style={{ backgroundColor: "#6c757d" }}
      >
        ← Salir
      </button>
    </div>
  );
}
