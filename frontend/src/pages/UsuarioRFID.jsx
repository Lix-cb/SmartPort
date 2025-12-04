import { useState } from "react";
import { useNavigate } from "react-router-dom";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:5000";

export default function UsuarioRFID() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleScan = async () => {
    setLoading(true);
    setError("");

    try {
      console.log("[INFO] Validando RFID de usuario...");
      
      // PASO 1: Validar que el RFID existe en BD
      const response = await fetch(`${API_URL}/api/usuario/validar-rfid`, {
        method: "POST",
        headers: { "Content-Type": "application/json" }
      });

      const data = await response.json();
      console.log("[DEBUG] Respuesta del servidor:", data);

      // ===== VALIDACIÓN 1: RFID no registrado =====
      if (response.status === 404 && data.error === "RFID no registrado") {
        setError("Tarjeta RFID no registrada en el sistema");
        setLoading(false);
        return;
      }

      // ===== VALIDACIÓN 2: Ya completó proceso =====
      if (response. status === 403 && data. error === "Ya completó el proceso de abordaje") {
        setError(`Ya completó el proceso de abordaje (Estado: ${data.estado_actual})`);
        setLoading(false);
        return;
      }

      // ===== VALIDACIÓN 3: Sin biometría =====
      if (data.error === "Pasajero sin biometria registrada") {
        setError("Complete su registro biométrico en el mostrador");
        setLoading(false);
        return;
      }

      // ===== SI TODO OK: Guardar datos y continuar =====
      if (response.ok && data.status === "ok") {
        console.log("[OK] RFID válido - Continuando a verificación facial");
        
        // ✅ Guardar datos del pasajero en localStorage (SIN destino)
        localStorage. setItem("usuario_id_pasajero", data.pasajero.id_pasajero);
        localStorage.setItem("usuario_nombre", data.pasajero.nombre);
        localStorage.setItem("usuario_vuelo", data.pasajero.vuelo);
        
        // Navegar a la página de cámara
        navigate("/usuario-camara");
      } else {
        setError(data.error || "Error en la verificación");
        setLoading(false);
      }

    } catch (err) {
      console.error("[ERROR] Error de conexión:", err);
      setError("Error de conexión con el servidor");
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="container">
        <img src="/GAP_logo.jpg" alt="Logo GAP" className="logo" />
        <h2 className="title" style={{ color: "#007bff" }}>Validando RFID...</h2>
        
        <div style={{
          backgroundColor: "#e7f3ff",
          border: "2px solid #b3d9ff",
          borderRadius: "12px",
          padding: "40px",
          marginBottom: "25px",
          textAlign: "center"
        }}>
          <div style={{
            width: "100px",
            height: "100px",
            border: "8px solid #007bff",
            borderTop: "8px solid transparent",
            borderRadius: "50%",
            margin: "0 auto 30px",
            animation: "spin 1. 2s linear infinite"
          }}></div>
          
          <div style={{ fontSize: "60px", marginBottom: "20px" }}>📱</div>
          
          <p style={{ 
            fontSize: "18px", 
            fontWeight: "bold",
            color: "#007bff",
            margin: 0
          }}>
            Acerque su tarjeta RFID... 
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
      <h1 className="title">🛂 Control de Acceso</h1>
      
      <p style={{ 
        marginBottom: "30px", 
        color: "#666",
        fontSize: "16px",
        textAlign: "center",
        lineHeight: "1.6"
      }}>
        Paso 1 de 2: Escanee su tarjeta RFID para continuar
      </p>

      <div style={{
        backgroundColor: "#f8f9fa",
        border: "2px dashed #dee2e6",
        borderRadius: "12px",
        padding: "30px 20px",
        marginBottom: "30px"
      }}>
        <div style={{ display: "flex", justifyContent: "center", gap: "40px", flexWrap: "wrap" }}>
          <div style={{ textAlign: "center" }}>
            <div style={{ fontSize: "64px", marginBottom: "10px" }}>📱</div>
            <p style={{ fontSize: "16px", color: "#007bff", fontWeight: "bold", margin: 0 }}>
              Paso 1: Tarjeta RFID
            </p>
          </div>
          <div style={{ fontSize: "30px", color: "#dee2e6", display: "flex", alignItems: "center" }}>
            →
          </div>
          <div style={{ textAlign: "center", opacity: 0.4 }}>
            <div style={{ fontSize: "64px", marginBottom: "10px" }}>📷</div>
            <p style={{ fontSize: "16px", color: "#666", margin: 0 }}>
              Paso 2: Reconocimiento Facial
            </p>
          </div>
        </div>
      </div>

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
          background: loading ? "#ccc" : "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
          fontSize: "18px",
          padding: "16px",
          marginBottom: "15px",
          cursor: loading ? "not-allowed" : "pointer"
        }}
      >
        📱 Escanear RFID
      </button>
      
      <button 
        className="button" 
        onClick={() => navigate("/")}
        disabled={loading}
        style={{ 
          backgroundColor: "#6c757d",
          fontSize: "16px",
          padding: "14px"
        }}
      >
        ← Volver al Inicio
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
