import { useState } from "react";
import { useNavigate } from "react-router-dom";

const API_URL = import.meta.env. VITE_API_URL || "http://localhost:5000";

export default function UsuarioAcceso() {
  const navigate = useNavigate();
  const [estado, setEstado] = useState("esperando"); // esperando | escaneandoRFID | capturandoRostro | exito | error
  const [loading, setLoading] = useState(false);
  const [mensaje, setMensaje] = useState("");
  const [pasajeroInfo, setPasajeroInfo] = useState(null);
  const [similitud, setSimilitud] = useState(null);
  const [paso, setPaso] = useState(1); // 1=RFID, 2=Rostro

  const handleVerificar = async () => {
    setLoading(true);
    setEstado("escaneandoRFID");
    setPaso(1);
    setMensaje("Acerque su tarjeta RFID.. .");

    // Simular paso 1: Escaneo RFID (2 segundos)
    setTimeout(() => {
      setEstado("capturandoRostro");
      setPaso(2);
      setMensaje("Mire a la cámara...");
    }, 2000);

    try {
      const response = await fetch(`${API_URL}/api/usuario/verificar-acceso`, {
        method: "POST",
        headers: { "Content-Type": "application/json" }
      });

      const data = await response.json();

      if (response.ok && data.status === "ok" && data.acceso === "concedido") {
        setEstado("exito");
        setPasajeroInfo(data.pasajero);
        setSimilitud(data.similitud);
        setMensaje(`Bienvenido ${data.pasajero.nombre}`);
        
        setTimeout(() => {
          setEstado("esperando");
          setMensaje("");
          setPasajeroInfo(null);
          setSimilitud(null);
          setPaso(1);
        }, 6000);
      } else {
        setEstado("error");
        setMensaje(data. error || "Acceso denegado");
        
        setTimeout(() => {
          setEstado("esperando");
          setMensaje("");
          setPaso(1);
        }, 4000);
      }
    } catch (err) {
      setEstado("error");
      setMensaje("Error de conexión con el servidor");
      console.error(err);
      
      setTimeout(() => {
        setEstado("esperando");
        setMensaje("");
        setPaso(1);
      }, 4000);
    } finally {
      setLoading(false);
    }
  };

  // Estado: Escaneando RFID
  if (estado === "escaneandoRFID") {
    return (
      <div className="container">
        <img src="/GAP_logo.jpg" alt="Logo GAP" className="logo" />
        <h2 className="title" style={{ color: "#007bff" }}>Paso 1/2: Escaneo RFID</h2>
        
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
          
          <p style={{ fontSize: "20px", color: "#0056b3", marginBottom: "10px", fontWeight: "600" }}>
            {mensaje}
          </p>
          <p style={{ fontSize: "14px", color: "#666" }}>
            Esperando lectura de tarjeta...
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

  // Estado: Capturando rostro
  if (estado === "capturandoRostro") {
    return (
      <div className="container">
        <img src="/GAP_logo.jpg" alt="Logo GAP" className="logo" />
        <h2 className="title" style={{ color: "#007bff" }}>Paso 2/2: Reconocimiento Facial</h2>
        
        <div style={{
          backgroundColor: "#fff3cd",
          border: "2px solid #ffc107",
          borderRadius: "12px",
          padding: "40px",
          marginBottom: "25px",
          textAlign: "center"
        }}>
          <div style={{
            width: "100px",
            height: "100px",
            border: "8px solid #ffc107",
            borderTop: "8px solid transparent",
            borderRadius: "50%",
            margin: "0 auto 30px",
            animation: "spin 1.2s linear infinite"
          }}></div>
          
          <div style={{ fontSize: "60px", marginBottom: "20px" }}>📸</div>
          
          <p style={{ fontSize: "20px", color: "#856404", marginBottom: "10px", fontWeight: "600" }}>
            {mensaje}
          </p>
          <p style={{ fontSize: "14px", color: "#666" }}>
            Mantenga su rostro visible frente a la cámara
          </p>
          <p style={{ fontSize: "13px", color: "#999", marginTop: "10px" }}>
            Analizando biometría...
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

  // Estado: Éxito
  if (estado === "exito" && pasajeroInfo) {
    return (
      <div className="container">
        <img src="/GAP_logo.jpg" alt="Logo GAP" className="logo" />
        
        <div style={{
          backgroundColor: "#d4edda",
          border: "3px solid #c3e6cb",
          borderRadius: "16px",
          padding: "40px",
          marginBottom: "25px",
          textAlign: "center",
          animation: "scaleIn 0.5s ease-out"
        }}>
          <div style={{ fontSize: "80px", marginBottom: "20px", animation: "bounce 1s" }}>
            ✅
          </div>
          <h2 style={{ 
            color: "#155724", 
            marginBottom: "20px", 
            fontSize: "28px",
            fontWeight: "700"
          }}>
            ¡Acceso Concedido!
          </h2>
          <p style={{ 
            fontSize: "22px", 
            color: "#155724", 
            marginBottom: "25px",
            fontWeight: "600"
          }}>
            Bienvenido, <strong>{pasajeroInfo.nombre}</strong>
          </p>
          
          <div style={{
            backgroundColor: "#fff",
            borderRadius: "12px",
            padding: "20px",
            marginTop: "25px",
            textAlign: "left",
            boxShadow: "0 2px 8px rgba(0,0,0,0.1)"
          }}>
            <div style={{ marginBottom: "12px" }}>
              <p style={{ margin: 0, fontSize: "14px", color: "#666", marginBottom: "4px" }}>
                Vuelo:
              </p>
              <p style={{ margin: 0, fontSize: "20px", fontWeight: "bold", color: "#333" }}>
                ✈️ {pasajeroInfo.vuelo}
              </p>
            </div>
            
            <div style={{ marginBottom: "12px" }}>
              <p style={{ margin: 0, fontSize: "14px", color: "#666", marginBottom: "4px" }}>
                Destino:
              </p>
              <p style={{ margin: 0, fontSize: "20px", fontWeight: "bold", color: "#333" }}>
                🌍 {pasajeroInfo. destino}
              </p>
            </div>
            
            {similitud && (
              <div style={{
                backgroundColor: "#f8f9fa",
                padding: "10px",
                borderRadius: "8px",
                marginTop: "15px"
              }}>
                <p style={{ margin: 0, fontSize: "13px", color: "#666" }}>
                  Coincidencia biométrica:
                </p>
                <p style={{ margin: "4px 0 0 0", fontSize: "18px", fontWeight: "bold", color: "#28a745" }}>
                  {similitud}%
                </p>
              </div>
            )}
          </div>

          <p style={{ fontSize: "15px", color: "#155724", marginTop: "25px", fontWeight: "500" }}>
            ¡Buen viaje!  🎉
          </p>
        </div>

        <style>{`
          @keyframes scaleIn {
            from { transform: scale(0.8); opacity: 0; }
            to { transform: scale(1); opacity: 1; }
          }
          @keyframes bounce {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-20px); }
          }
        `}</style>
      </div>
    );
  }

  // Estado: Error
  if (estado === "error") {
    return (
      <div className="container">
        <img src="/GAP_logo.jpg" alt="Logo GAP" className="logo" />
        
        <div style={{
          backgroundColor: "#f8d7da",
          border: "3px solid #f5c6cb",
          borderRadius: "16px",
          padding: "40px",
          marginBottom: "25px",
          textAlign: "center",
          animation: "shake 0.5s"
        }}>
          <div style={{ fontSize: "80px", marginBottom: "20px" }}>
            ❌
          </div>
          <h2 style={{ color: "#721c24", marginBottom: "15px", fontSize: "26px", fontWeight: "700" }}>
            Acceso Denegado
          </h2>
          <p style={{ fontSize: "16px", color: "#721c24", lineHeight: "1.6" }}>
            {mensaje}
          </p>
        </div>

        <style>{`
          @keyframes shake {
            0%, 100% { transform: translateX(0); }
            25% { transform: translateX(-15px); }
            75% { transform: translateX(15px); }
          }
        `}</style>
      </div>
    );
  }

  // Estado: Esperando (inicial)
  return (
    <div className="container">
      <img src="/GAP_logo.jpg" alt="Logo GAP" className="logo" />
      <h2 className="title">✈️ Control de Acceso</h2>
      
      <p style={{ 
        marginBottom: "35px", 
        fontSize: "16px", 
        color: "#666",
        lineHeight: "1.6"
      }}>
        Escanee su RFID y mire a la cámara para verificación biométrica
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
            <div style={{ fontSize: "48px", marginBottom: "10px" }}>📱</div>
            <p style={{ fontSize: "14px", color: "#666", margin: 0 }}>
              Paso 1: Tarjeta RFID
            </p>
          </div>
          <div style={{ fontSize: "30px", color: "#dee2e6", display: "flex", alignItems: "center" }}>
            →
          </div>
          <div style={{ textAlign: "center" }}>
            <div style={{ fontSize: "48px", marginBottom: "10px" }}>📸</div>
            <p style={{ fontSize: "14px", color: "#666", margin: 0 }}>
              Paso 2: Reconocimiento facial
            </p>
          </div>
        </div>
      </div>
      
      <button 
        className="button" 
        onClick={handleVerificar}
        disabled={loading}
        style={{
          background: "linear-gradient(135deg, #28a745 0%, #20c997 100%)",
          fontSize: "18px",
          padding: "16px",
          marginBottom: "15px"
        }}
      >
        🚀 Iniciar Verificación
      </button>

      <button 
        className="button" 
        onClick={() => navigate("/")}
        style={{ backgroundColor: "#6c757d", fontSize: "16px", padding: "14px" }}
      >
        ← Volver
      </button>
    </div>
  );
}
