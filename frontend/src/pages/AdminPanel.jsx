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
    const nombre = prompt("Ingrese el nombre del nuevo administrador:");
    if (! nombre) return;

    registrarNuevoAdmin(nombre);
  };

  const registrarNuevoAdmin = async (nombre) => {
    try {
      const response = await fetch("http://localhost:5000/api/admin/registrar-admin", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ nombre })
      });

      const data = await response.json();

      if (response.ok && data.status === "ok") {
        alert(`✅ ${data.mensaje}\nRFID: ${data.rfid_uid}`);
      } else {
        alert(`❌ Error: ${data.error}`);
      }
    } catch (err) {
      alert("❌ Error de conexión");
      console.error(err);
    }
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
