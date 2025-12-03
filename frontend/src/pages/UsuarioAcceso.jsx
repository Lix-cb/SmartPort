import { useState } from "react";
import { useNavigate } from "react-router-dom";

const API_URL = "http://localhost:5000";

export default function UsuarioAcceso() {
  const navigate = useNavigate();
  const [estado, setEstado] = useState("esperando"); // esperando, verificando, exito, error
  const [loading, setLoading] = useState(false);
  const [mensaje, setMensaje] = useState("");
  const [pasajeroInfo, setPasajeroInfo] = useState(null);

  const handleVerificar = async () => {
    setLoading(true);
    setEstado("verificando");
    setMensaje("Acerque su tarjeta RFID.. .");

    try {
      const response = await fetch(`${API_URL}/api/usuario/verificar-acceso`, {
        method: "POST",
        headers: { "Content-Type": "application/json" }
      });

      const data = await response.json();

      if (response.ok && data.status === "ok" && data.acceso === "concedido") {
        // ACCESO CONCEDIDO
        setEstado("exito");
        setPasajeroInfo(data.pasajero);
        setMensaje(`¡Bienvenido ${data.pasajero.nombre}!`);
        
        // Volver al inicio después de 5 segundos
        setTimeout(() => {
          setEstado("esperando");
          setMensaje("");
          setPasajeroInfo(null);
        }, 5000);
      } else {
        // ACCESO DENEGADO
        setEstado("error");
        setMensaje(data.error || "Acceso denegado");
        
        // Volver al inicio después de 3 segundos
        setTimeout(() => {
          setEstado("esperando");
          setMensaje("");
        }, 3000);
      }
    } catch (err) {
      setEstado("error");
      setMensaje("Error de conexión");
      console. error(err);
      
      setTimeout(() => {
        setEstado("esperando");
        setMensaje("");
      }, 3000);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container">
      <img src="/GAP_logo.jpg" alt="Logo" className="logo" />
      
      {estado === "esperando" && (
        <>
          <h2 className="title">Control de Acceso</h2>
          <p style={{ marginBottom: "30px", fontSize: "16px", color: "#666" }}>
            Escanee su RFID y mire a la cámara para acceder
          </p>
          <button 
            className="button" 
            onClick={handleVerificar}
            disabled={loading}
          >
            Iniciar Verificación
          </button>
        </>
      )}
      
      {estado === "verificando" && (
        <>
          <h2 className="title">Verificando... </h2>
          <p style={{ fontSize: "18px", color: "#666" }}>{mensaje}</p>
          <div className="spinner" style={{ margin: "30px auto" }}>⏳</div>
        </>
      )}
      
      {estado === "exito" && pasajeroInfo && (
        <>
          <h2 className="title" style={{ color: "#28a745" }}>
            ✅ {mensaje}
          </h2>
          <div style={{ 
            backgroundColor: "#d4edda", 
            border: "1px solid #c3e6cb",
            borderRadius: "8px",
            padding: "20px",
            marginTop: "20px",
            textAlign: "left"
          }}>
            <p><strong>Vuelo:</strong> {pasajeroInfo.vuelo}</p>
            <p><strong>Destino:</strong> {pasajeroInfo.destino}</p>
            <p><strong>Puerta:</strong> {pasajeroInfo.puerta}</p>
          </div>
          <p style={{ marginTop: "20px", color: "#666" }}>
            Puede abordar su vuelo.  Buen viaje ✈️
          </p>
        </>
      )}
      
      {estado === "error" && (
        <>
          <h2 className="title" style={{ color: "#dc3545" }}>
            ❌ Acceso Denegado
          </h2>
          <p style={{ fontSize: "18px", color: "#dc3545", marginTop: "20px" }}>
            {mensaje}
          </p>
        </>
      )}
      
      <button 
        className="button" 
        onClick={() => navigate("/")}
        style={{ 
          position: "fixed", 
          bottom: "20px", 
          right: "20px",
          backgroundColor: "#6c757d",
          width: "auto",
          padding: "10px 20px"
        }}
      >
        ← Volver
      </button>
    </div>
  );
}
