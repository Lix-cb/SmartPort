import { useState } from "react";
import { useNavigate } from "react-router-dom";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:5000";

export default function AdminRegistrarAdmin() {
  const navigate = useNavigate();
  const [nombre, setNombre] = useState("");
  const [loading, setLoading] = useState(false);
  const [escaneando, setEscaneando] = useState(false);
  const [error, setError] = useState("");
  const [exito, setExito] = useState(false);
  const [rfidRegistrado, setRfidRegistrado] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (!nombre.trim()) {
      setError("El nombre es requerido");
      return;
    }

    setEscaneando(true);
    setLoading(true);

    try {
      console.log("[INFO] Registrando nuevo admin:", nombre);

      const response = await fetch(`${API_URL}/api/admin/registrar-admin`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ nombre: nombre.trim() })
      });

      const data = await response. json();

      if (response. ok && data.status === "ok") {
        console.log("[OK] Admin registrado exitosamente");
        setRfidRegistrado(data.rfid_uid);
        setExito(true);
      } else {
        console.error("[ERROR]", data.error);
        setError(data.error || "Error al registrar administrador");
      }
    } catch (err) {
      console.error("[ERROR] Error de conexión:", err);
      setError("Error de conexión con el servidor");
    } finally {
      setLoading(false);
      setEscaneando(false);
    }
  };

  const handleVolver = () => {
    navigate("/admin-panel");
  };

  // Pantalla de éxito
  if (exito) {
    return (
      <div className="container">
        <img src="/GAP_logo.jpg" alt="Logo" className="logo" />
        
        <div style={{
          backgroundColor: "#d4edda",
          border: "2px solid #c3e6cb",
          borderRadius: "12px",
          padding: "30px",
          marginBottom: "25px",
          textAlign: "center"
        }}>
          <div style={{ fontSize: "64px", marginBottom: "15px" }}>✅</div>
          <h2 style={{ color: "#155724", marginBottom: "15px", fontSize: "28px" }}>
            Administrador Registrado
          </h2>
          <p style={{ fontSize: "18px", color: "#155724", marginBottom: "10px" }}>
            <strong>{nombre. toUpperCase()}</strong>
          </p>
          <div style={{
            backgroundColor: "#f8f9fa",
            padding: "15px",
            borderRadius: "8px",
            marginTop: "20px"
          }}>
            <p style={{ margin: 0, color: "#666", fontSize: "14px" }}>RFID Asignado:</p>
            <p style={{ 
              margin: "5px 0 0 0", 
              fontFamily: "monospace", 
              fontSize: "18px",
              fontWeight: "bold",
              color: "#333"
            }}>
              {rfidRegistrado}
            </p>
          </div>
        </div>

        <button 
          className="button" 
          onClick={handleVolver}
          style={{ 
            backgroundColor: "#28a745",
            fontSize: "16px",
            padding: "14px"
          }}
        >
          ✓ Finalizar
        </button>
      </div>
    );
  }

  // Pantalla de escaneo
  if (escaneando) {
    return (
      <div className="container">
        <img src="/GAP_logo.jpg" alt="Logo" className="logo" />
        <h2 className="title" style={{ color: "#007bff" }}>Escaneando RFID...</h2>
        
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
            border: "6px solid #007bff",
            borderTop: "6px solid transparent",
            borderRadius: "50%",
            margin: "0 auto 25px",
            animation: "spin 1s linear infinite"
          }}></div>
          
          <p style={{ fontSize: "18px", color: "#0056b3", marginBottom: "15px" }}>
            Administrador: <strong>{nombre.toUpperCase()}</strong>
          </p>
          
          <p style={{ fontSize: "16px", color: "#666" }}>
            📱 Acerque la tarjeta RFID al lector
          </p>
          <p style={{ fontSize: "14px", color: "#999", marginTop: "10px" }}>
            Esperando lectura...
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

  // Formulario inicial
  return (
    <div className="container">
      <img src="/GAP_logo.jpg" alt="Logo" className="logo" />
      <h2 className="title">🔑 Registrar Nuevo Administrador</h2>
      
      <p style={{ 
        marginBottom: "25px", 
        fontSize: "15px", 
        color: "#666",
        lineHeight: "1.6"
      }}>
        Ingrese el nombre del administrador y luego escanee su tarjeta RFID
      </p>

      {error && (
        <div style={{ 
          backgroundColor: "#f8d7da",
          border: "2px solid #f5c6cb",
          borderRadius: "8px",
          padding: "12px",
          marginBottom: "20px",
          color: "#721c24",
          fontSize: "15px",
          fontWeight: "500"
        }}>
          ⚠️ {error}
        </div>
      )}
      
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          placeholder="Nombre completo del administrador"
          className="input"
          value={nombre}
          onChange={(e) => setNombre(e.target.value)}
          disabled={loading}
          style={{
            fontSize: "16px",
            padding: "14px",
            marginBottom: "20px"
          }}
          autoFocus
        />
        
        <button 
          className="button" 
          type="submit" 
          disabled={loading || !nombre.trim()}
          style={{
            backgroundColor: "#17a2b8",
            fontSize: "16px",
            padding: "14px",
            marginBottom: "12px"
          }}
        >
          {loading ? "Procesando..." : "📱 Continuar a Escaneo RFID"}
        </button>
      </form>
      
      <button 
        className="button" 
        onClick={handleVolver}
        disabled={loading}
        style={{ 
          backgroundColor: "#6c757d",
          fontSize: "16px",
          padding: "14px"
        }}
      >
        ← Cancelar
      </button>
    </div>
  );
}
