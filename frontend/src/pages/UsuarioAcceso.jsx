import { useState } from "react";
import { useNavigate } from "react-router-dom";

const API_URL = "http://localhost:5000";

export default function UsuarioAcceso() {
  const navigate = useNavigate();
  const [estado, setEstado] = useState("esperando");
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
        setEstado("exito");
        setPasajeroInfo(data.pasajero);
        setMensaje(`Bienvenido ${data.pasajero.nombre}`);
        
        setTimeout(() => {
          setEstado("esperando");
          setMensaje("");
          setPasajeroInfo(null);
        }, 5000);
      } else {
        setEstado("error");
        setMensaje(data. error || "Acceso denegado");
        
        setTimeout(() => {
          setEstado("esperando");
          setMensaje("");
        }, 3000);
      }
    } catch (err) {
      setEstado("error");
      setMensaje("Error de conexion");
      console.error(err);
      
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
            Escanee su RFID y mire a la camara para verificacion
          </p>
          <button 
            className="button" 
            onClick={handleVerificar}
            disabled={loading}
          >
            Iniciar Verificacion
          </button>
        </>
      )}
      
      {estado === "verificando" && (
        <>
          <h2 className="title">Verificando... </h2>
          <p style={{ fontSize: "18px", color: "#666" }}>{mensaje}</p>
          <div className="spinner" style={{ margin: "30px auto" }}>Procesando...</div>
        </>
      )}
      
      {estado === "exito" && pasajeroInfo && (
        <>
          <h2 className="title" style={{ color: "#28a745" }}>
            {mensaje}
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
          </div>
          <p style={{ marginTop: "20px", color: "#666" }}>
            Verifique su puerta de embarque en las pantallas del aeropuerto. 
          </p>
        </>
      )}
      
      {estado === "error" && (
        <>
          <h2 className="title" style={{ color: "#dc3545" }}>
            Acceso Denegado
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
        Volver
      </button>
    </div>
  );
}
