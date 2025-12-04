import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";

const API_URL = import.meta. env.VITE_API_URL || "http://localhost:5000";

export default function AdminRFID() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [idPasajero, setIdPasajero] = useState(null);
  const [nombrePasajero, setNombrePasajero] = useState("");

  useEffect(() => {
    const id = localStorage.getItem("id_pasajero");
    const nombre = localStorage.getItem("nombre_pasajero");

    if (!id) {
      alert("No hay pasajero seleccionado");
      navigate("/admin-panel");
      return;
    }

    setIdPasajero(id);
    setNombrePasajero(nombre);
  }, [navigate]);

  const handleScan = async () => {
    setLoading(true);
    setError("");

    try {
      const response = await fetch(`${API_URL}/api/admin/registrar-rfid`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          id_pasajero: parseInt(idPasajero)
        })
      });

      const data = await response.json();

      if (response.ok && data.status === "ok") {
        localStorage.setItem("rfid_uid", data.rfid_uid);
        navigate("/admin-camara");
      } else {
        setError(data.error || "Error al registrar RFID");
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
            Pasajero: <strong>{nombrePasajero}</strong>
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

  return (
    <div className="container">
      <img src="/GAP_logo.jpg" alt="Logo GAP" className="logo" />
      <h1 className="title">📱 Registrar RFID</h1>
      
      <div style={{
        backgroundColor: "#f8f9fa",
        border: "2px solid #dee2e6",
        borderRadius: "12px",
        padding: "20px",
        marginBottom: "25px"
      }}>
        <p style={{ margin: 0, fontSize: "15px", color: "#666" }}>
          Pasajero:
        </p>
        <p style={{ 
          margin: "5px 0 0 0", 
          fontSize: "20px", 
          fontWeight: "bold",
          color: "#333"
        }}>
          {nombrePasajero}
        </p>
      </div>

      <p style={{ 
        marginBottom: "30px", 
        color: "#666",
        fontSize: "15px",
        lineHeight: "1.6"
      }}>
        Acerque la tarjeta RFID del pasajero al lector para continuar
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
        onClick={handleScan}
        disabled={loading}
        style={{
          background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
          fontSize: "16px",
          padding: "14px",
          marginBottom: "12px"
        }}
      >
        📱 Escanear RFID
      </button>
      
      <button 
        className="button" 
        onClick={() => navigate("/admin-panel")}
        disabled={loading}
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
