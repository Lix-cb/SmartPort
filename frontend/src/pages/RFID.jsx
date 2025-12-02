import { useState, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import "../App.css";

export default function RFID() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [mensaje, setMensaje] = useState("");
  const [success, setSuccess] = useState(false);
  
  const navigate = useNavigate();
  const location = useLocation();

  const { id_pasajero, nombre, vuelo, destino } = location.state || {};

  // Si no hay datos del pasajero, redirigir al inicio
  useEffect(() => {
    if (!id_pasajero) {
      navigate("/");
    }
  }, [id_pasajero, navigate]);

  const iniciarRegistro = async () => {
    setLoading(true);
    setError("");
    setMensaje("📡 Acerca tu tarjeta RFID al lector...");

    try {
      const res = await fetch("http://localhost:5000/api/registrar-persona", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          id_pasajero: id_pasajero,
        }),
      });

      const data = await res.json();

      if (res.ok) {
        setSuccess(true);
        setMensaje("✅ ¡Check-in completado exitosamente!");
        
        // Redirigir al inicio después de 3 segundos
        setTimeout(() => {
          navigate("/", { replace: true });
        }, 3000);
      } else {
        setError(data.error || "❌ Error en el registro. Intenta nuevamente.");
        setLoading(false);
      }
    } catch (err) {
      console.error("Error:", err);
      setError("❌ Error de conexión con el servidor");
      setLoading(false);
    }
  };

  return (
    <div className="container">
      <div className="logo">{success ? "✅" : "🎫"}</div>
      
      <h1 className="title">
        {success ? "Check-in Completado" : "Registro de Pasajero"}
      </h1>
      
      <div style={{
        background: "#f0f8ff",
        padding: "20px",
        borderRadius: "12px",
        marginBottom: "25px",
        border: "2px solid #4b9ce2"
      }}>
        <p style={{ fontSize: "18px", fontWeight: "600", marginBottom: "8px", color: "#333" }}>
          {nombre}
        </p>
        <p style={{ fontSize: "15px", color: "#666", marginBottom: "4px" }}>
          ✈️ Vuelo {vuelo}
        </p>
        <p style={{ fontSize: "14px", color: "#888" }}>
          📍 Destino: {destino}
        </p>
      </div>

      {!success && !loading && (
        <div style={{
          background: "#fff3cd",
          padding: "20px",
          borderRadius: "12px",
          marginBottom: "25px",
          border: "2px dashed #ffc107"
        }}>
          <p style={{ fontSize: "16px", fontWeight: "600", marginBottom: "12px", textAlign: "center" }}>
            📋 Proceso de Check-in
          </p>
          <ol style={{ 
            textAlign: "left", 
            paddingLeft: "20px", 
            fontSize: "14px",
            lineHeight: "1.8"
          }}>
            <li>📡 Escaneo de tarjeta RFID</li>
            <li>📸 Captura de rostro facial</li>
            <li>✅ Validación completa</li>
          </ol>
        </div>
      )}

      {error && (
        <div style={{
          background: "#fee",
          color: "#c33",
          padding: "15px",
          borderRadius: "10px",
          marginBottom: "20px",
          fontSize: "14px",
          fontWeight: "500"
        }}>
          {error}
        </div>
      )}

      {mensaje && (
        <div style={{
          background: success ? "#d4edda" : "#cce5ff",
          color: success ? "#155724" : "#004085",
          padding: "15px",
          borderRadius: "10px",
          marginBottom: "20px",
          fontSize: "15px",
          fontWeight: "600",
          animation: loading && !success ? "pulse 1.5s infinite" : "none"
        }}>
          {mensaje}
        </div>
      )}

      {!success && (
        <>
          <button
            className="btn primary"
            onClick={iniciarRegistro}
            disabled={loading}
            style={{
              fontSize: "16px",
              padding: "14px"
            }}
          >
            {loading ? "🔄 Procesando..." : "Iniciar Check-in →"}
          </button>

          <button
            className="btn secondary"
            onClick={() => navigate("/")}
            disabled={loading}
            style={{ marginTop: "12px" }}
          >
            ← Cancelar
          </button>
        </>
      )}

      {success && (
        <div style={{
          marginTop: "20px",
          fontSize: "14px",
          color: "#666"
        }}>
          Redirigiendo al inicio...
        </div>
      )}

      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.6; }
        }
      `}</style>
    </div>
  );
}