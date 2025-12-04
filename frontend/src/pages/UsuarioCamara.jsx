import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";

const API_URL = import.meta. env.VITE_API_URL || "http://localhost:5000";

export default function UsuarioCamara() {
  const navigate = useNavigate();
  const videoRef = useRef(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [exito, setExito] = useState(false);
  const [idPasajero, setIdPasajero] = useState(null);
  const [nombrePasajero, setNombrePasajero] = useState("");
  const [vueloPasajero, setVueloPasajero] = useState("");
  const [similitud, setSimilitud] = useState(null);
  const [cameraPreviewAvailable, setCameraPreviewAvailable] = useState(false);
  const [countdown, setCountdown] = useState(3);
  const [showCountdown, setShowCountdown] = useState(false);

  useEffect(() => {
    const id = localStorage.getItem("usuario_id_pasajero");
    const nombre = localStorage.getItem("usuario_nombre");
    const vuelo = localStorage.getItem("usuario_vuelo");

    if (! id) {
      alert("Sesión expirada. Por favor, escanee su RFID nuevamente");
      navigate("/usuario-acceso");
      return;
    }

    setIdPasajero(id);
    setNombrePasajero(nombre);
    setVueloPasajero(vuelo);

    // Iniciar preview de cámara (opcional)
    initCameraPreview();

    return () => {
      if (videoRef.current && videoRef.current.srcObject) {
        videoRef.current. srcObject. getTracks().forEach(track => track.stop());
      }
    };
  }, [navigate]);

  const initCameraPreview = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        video: { 
          width: { ideal: 640 },
          height: { ideal: 480 }
        } 
      });

      if (videoRef.current) {
        videoRef.current. srcObject = stream;
        
        videoRef.current.onloadedmetadata = () => {
          videoRef.current.play();
          setCameraPreviewAvailable(true);
          console.log("[OK] Preview de cámara disponible");
        };
      }
    } catch (err) {
      console.warn("[INFO] Preview de cámara no disponible:", err);
      setCameraPreviewAvailable(false);
    }
  };

  const handleCapturar = async () => {
    setError("");
    setShowCountdown(true);
    setCountdown(3);

    // Cuenta regresiva 3, 2, 1
    for (let i = 3; i > 0; i--) {
      setCountdown(i);
      await new Promise(resolve => setTimeout(resolve, 1000));
    }

    setShowCountdown(false);
    setLoading(true);

    try {
      console.log("[INFO] Capturando y verificando rostro...");
      console.log("[DEBUG] ID Pasajero:", idPasajero);
      
      // PASO 2: Verificar rostro con el backend
      const response = await fetch(`${API_URL}/api/usuario/verificar-rostro`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          id_pasajero: parseInt(idPasajero)
        })
      });

      const data = await response.json();

      // ===== CASO 1: Biometría coincide → ÉXITO =====
      if (response.ok && data.status === "ok" && data.acceso === "concedido") {
        console.log("[OK] ✓✓✓ Acceso concedido - Estado cambiado a ABORDADO");
        
        // Detener preview
        if (videoRef.current && videoRef.current.srcObject) {
          videoRef.current. srcObject.getTracks().forEach(track => track.stop());
        }
        
        setSimilitud(data.similitud);
        setExito(true);
        
      // ===== CASO 2: Biometría NO coincide → ERROR =====
      } else if (data.error === "Biometria no coincide") {
        console.error("[ERROR] Biometría no coincide");
        setError("Los datos biométricos no coinciden.  Intente nuevamente.");
        setLoading(false);
        
      // ===== CASO 3: No detectó rostro → ERROR =====
      } else if (data.error === "No se detectó rostro") {
        console.error("[ERROR] No se detectó rostro");
        setError("No se detectó ningún rostro.  Por favor, mire directamente a la cámara.");
        setLoading(false);
        
      // ===== CASO 4: Otro error =====
      } else {
        console.error("[ERROR]", data.error);
        setError(data.error || "Error en la verificación");
        setLoading(false);
      }

    } catch (err) {
      console.error("[ERROR] Error de conexión:", err);
      setError("Error de conexión con el servidor");
      setLoading(false);
    }
  };

  const handleFinalizar = () => {
    // Limpiar localStorage
    localStorage.removeItem("usuario_id_pasajero");
    localStorage.removeItem("usuario_nombre");
    localStorage. removeItem("usuario_vuelo");
    
    navigate("/");
  };

  // PANTALLA DE ÉXITO
  if (exito) {
    return (
      <div className="container">
        <img src="/GAP_logo.jpg" alt="Logo GAP" className="logo" />
        <h2 className="title" style={{ color: "#28a745" }}>✓ Acceso Concedido</h2>
        
        <div style={{
          backgroundColor: "#d4edda",
          border: "3px solid #28a745",
          borderRadius: "12px",
          padding: "40px",
          marginBottom: "25px",
          textAlign: "center"
        }}>
          <div style={{ fontSize: "120px", marginBottom: "20px" }}>✓</div>
          
          <p style={{ 
            fontSize: "28px", 
            fontWeight: "bold",
            color: "#155724",
            marginBottom: "30px"
          }}>
            Bienvenido, {nombrePasajero}
          </p>
          
          <div style={{ 
            backgroundColor: "#fff",
            padding: "20px",
            borderRadius: "8px",
            marginBottom: "20px"
          }}>
            <p style={{ margin: "5px 0", fontSize: "18px", color: "#333" }}>
              <strong>Vuelo:</strong> {vueloPasajero}
            </p>
            {similitud && (
              <p style={{ margin: "5px 0", fontSize: "16px", color: "#666" }}>
                <strong>Coincidencia biométrica:</strong> {similitud}%
              </p>
            )}
          </div>

          <p style={{ fontSize: "16px", color: "#155724", marginTop: "20px" }}>
            Su acceso ha sido registrado.  ¡Buen viaje!
          </p>
        </div>

        <button 
          className="button" 
          onClick={handleFinalizar}
          style={{
            background: "linear-gradient(135deg, #28a745 0%, #20c997 100%)",
            fontSize: "18px",
            padding: "16px"
          }}
        >
          ✓ Finalizar
        </button>
      </div>
    );
  }

  // PANTALLA DE CAPTURA
  return (
    <div className="container">
      <img src="/GAP_logo.jpg" alt="Logo GAP" className="logo" />
      <h2 className="title" style={{ color: "#007bff" }}>📷 Verificación Facial</h2>
      
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
        marginBottom: "20px", 
        color: "#666",
        fontSize: "15px",
        textAlign: "center",
        lineHeight: "1. 6"
      }}>
        Paso 2 de 2: Mire directamente a la cámara para verificación biométrica
      </p>

      {/* Preview de cámara o placeholder */}
      <div style={{
        backgroundColor: "#000",
        borderRadius: "12px",
        overflow: "hidden",
        marginBottom: "20px",
        position: "relative",
        minHeight: "300px",
        display: "flex",
        alignItems: "center",
        justifyContent: "center"
      }}>
        {cameraPreviewAvailable ?  (
          <>
            <video 
              ref={videoRef} 
              autoPlay 
              playsInline
              style={{
                width: "100%",
                maxWidth: "640px",
                display: "block"
              }}
            />
            {showCountdown && (
              <div style={{
                position: "absolute",
                top: "50%",
                left: "50%",
                transform: "translate(-50%, -50%)",
                fontSize: "120px",
                fontWeight: "bold",
                color: "#fff",
                textShadow: "0 0 20px rgba(0,0,0,0.8)",
                animation: "pulse 1s ease-in-out"
              }}>
                {countdown}
              </div>
            )}
          </>
        ) : (
          <div style={{ textAlign: "center", padding: "40px" }}>
            <div style={{ fontSize: "80px", marginBottom: "20px" }}>📷</div>
            <p style={{ color: "#fff", fontSize: "16px" }}>
              Preview no disponible
            </p>
            <small style={{ color: "#ccc" }}>
              La cámara del servidor se usará para la verificación
            </small>
          </div>
        )}
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
          fontWeight: "500"
        }}>
          ⚠️ {error}
        </div>
      )}

      <button 
        className="button" 
        onClick={handleCapturar}
        disabled={loading || showCountdown}
        style={{
          background: loading || showCountdown 
            ? "#ccc" 
            : "linear-gradient(135deg, #007bff 0%, #0056b3 100%)",
          fontSize: "18px",
          padding: "16px",
          marginBottom: "15px",
          cursor: loading || showCountdown ? "not-allowed" : "pointer"
        }}
      >
        {loading ?  "Verificando..." : showCountdown ? `Preparando...  ${countdown}` : "📸 Verificar Rostro"}
      </button>

      {loading && (
        <p style={{
          textAlign: "center",
          color: "#666",
          fontSize: "14px",
          marginBottom: "15px"
        }}>
          Capturando y verificando biometría...  Esto puede tardar hasta 15 segundos
        </p>
      )}

      <button 
        className="button" 
        onClick={() => navigate("/usuario-acceso")}
        disabled={loading || showCountdown}
        style={{ 
          backgroundColor: "#6c757d",
          fontSize: "16px",
          padding: "14px"
        }}
      >
        ← Volver
      </button>

      <style>{`
        @keyframes pulse {
          0%, 100% { transform: translate(-50%, -50%) scale(1); opacity: 1; }
          50% { transform: translate(-50%, -50%) scale(1.2); opacity: 0.8; }
        }
      `}</style>
    </div>
  );
}
