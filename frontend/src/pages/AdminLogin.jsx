import { useState } from "react";
import { useNavigate } from "react-router-dom";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:5000";

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
        localStorage.setItem("admin_id", data.admin. id);
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

  if (loading) {
    return (
      <div className="container">
        <img src="/GAP_logo.jpg" alt="Logo GAP" className="logo" />
        <h2 className="title" style={{ color: "#667eea" }}>Escaneando RFID...</h2>
        
        <div style={{
          backgroundColor: "#e7f3ff",
          border: "2px solid #b3d9ff",
          borderRadius: "12px",
          padding: "40px",
          marginBottom: "25px",
          textAlign: "center"
        }}>
          <div style={{
            width: "80px",
            height: "80px",
            border: "6px solid #667eea",
            borderTop: "6px solid transparent",
            borderRadius: "50%",
            margin: "0 auto 25px",
            animation: "spin 1s linear infinite"
          }}></div>
          
          <p style={{ fontSize: "18px", color: "#0056b3", marginBottom: "15px" }}>
            <strong>Acerque su tarjeta RFID</strong>
          </p>
          <p style={{ fontSize: "16px", color: "#666" }}>
            📱 Esperando lectura del administrador...
          </p>
        </div>

        <style>{`
          @keyframes spin {
            to { transform: rotate(360deg); }
          }
        `}</style>
      </div>
    );
  }

  return (
    <div className="container">
      <img src="/GAP_logo.jpg" alt="Logo GAP" className="logo" />
      <h2 className="title">🔐 Acceso Administrador</h2>
      <p style={{ 
        marginBottom: "30px", 
        fontSize: "16px",
        color: "#666",
        lineHeight: "1.6"
      }}>
        Identifíquese con su tarjeta RFID de administrador
      </p>
      
      {error && (
        <div style={{ 
          backgroundColor: "#f8d7da",
          border: "2px solid #f5c6cb",
          borderRadius: "10px",
          padding: "15px",
          marginBottom: "20px",
          color: "#721c24",
          fontSize: "15px",
          fontWeight: "500",
          animation: "shake 0.5s"
        }}>
          ⚠️ {error}
        </div>
      )}
      
      <button 
        className="button" 
        onClick={handleLogin}
        disabled={loading}
        style={{
          background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
          fontSize: "16px",
          padding: "14px",
          marginBottom: "12px"
        }}
      >
        📱 Escanear RFID Admin
      </button>
      
      <button 
        className="button" 
        onClick={() => navigate("/")}
        style={{ 
          backgroundColor: "#6c757d",
          fontSize: "16px",
          padding: "14px"
        }}
      >
        ← Volver
      </button>

      <style>{`
        @keyframes shake {
          0%, 100% { transform: translateX(0); }
          25% { transform: translateX(-10px); }
          75% { transform: translateX(10px); }
        }
      `}</style>
    </div>
  );
}
