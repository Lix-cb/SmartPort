import { useState } from "react";
import { useNavigate } from "react-router-dom";

const API_URL = "http://localhost:5000";

export default function AdminLogin() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleLogin = async () => {
    setLoading(true);
    setError("");

    try {
      const response = await fetch(`${API_URL}/api/admin/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" }
      });

      const data = await response.json();

      if (response.ok && data.status === "ok") {
        // Guardar info del admin
        localStorage.setItem("admin_id", data.admin.id);
        localStorage.setItem("admin_nombre", data.admin.nombre);
        navigate("/admin-panel");
      } else {
        setError(data.error || "Acceso denegado");
      }
    } catch (err) {
      setError("Error de conexión con el servidor");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container">
      <img src="/GAP_logo.jpg" alt="Logo" className="logo" />
      <h2 className="title">Acceso Administrador</h2>
      <p style={{ marginBottom: "30px", fontSize: "16px" }}>
        Acerque su tarjeta RFID al lector
      </p>
      
      {error && (
        <div style={{ color: "red", marginBottom: "20px", fontWeight: "bold" }}>
          {error}
        </div>
      )}
      
      <button 
        className="button" 
        onClick={handleLogin}
        disabled={loading}
      >
        {loading ? "Verificando..." : "Escanear RFID Admin"}
      </button>
      
      <button 
        className="button" 
        onClick={() => navigate("/")}
        style={{ marginTop: "20px", backgroundColor: "#6c757d" }}
      >
        ← Volver
      </button>
    </div>
  );
}
