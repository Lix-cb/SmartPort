import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

const API_URL = import.meta. env.VITE_API_URL || "http://localhost:5000";

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

  const handleSalir = () => {
    localStorage.removeItem("admin_id");
    localStorage.removeItem("admin_nombre");
    navigate("/");
  };

  return (
    <div className="container">
      <img src="/GAP_logo.jpg" alt="Logo" className="logo" />
      <h2 className="title">Panel de Administrador</h2>
      <p style={{ marginBottom: "30px", fontSize: "16px", color: "#666" }}>
        Bienvenido, <strong>{adminNombre}</strong>
      </p>
      
      <button 
        className="button" 
        onClick={handleRegistrarPasajero}
        style={{ marginBottom: "15px" }}
      >
        👤 Registrar Pasajero
      </button>
      
      <button 
        className="button" 
        onClick={handleRegistrarAdmin}
        style={{ marginBottom: "15px", backgroundColor: "#17a2b8" }}
      >
        🔑 Registrar Nuevo Admin
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
