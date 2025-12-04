import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import "./AdminCamara.css";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:5000";

function AdminCamara() {
  const navigate = useNavigate();
  const videoRef = useRef(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [exito, setExito] = useState(false);
  const [idPasajero, setIdPasajero] = useState(null);
  const [nombrePasajero, setNombrePasajero] = useState("");
  const [rfidTemp, setRfidTemp] = useState("");
  const [cameraPreviewAvailable, setCameraPreviewAvailable] = useState(false);

  useEffect(() => {
    const id = localStorage.getItem("id_pasajero");
    const nombre = localStorage.getItem("nombre_pasajero");
    const rfid = localStorage.getItem("temp_rfid");

    if (!id || !rfid) {
      alert("Datos incompletos. Reiniciando proceso...");
      navigate("/admin-panel");
      return;
    }

    setIdPasajero(id);
    setNombrePasajero(nombre);
    setRfidTemp(rfid);

    // INTENTAR inicializar preview (opcional - no bloquea el registro)
    initCameraPreview();

    return () => {
      // Limpiar stream al desmontar
      if (videoRef.current && videoRef.current.srcObject) {
        videoRef.current.srcObject. getTracks().forEach(track => track.stop());
      }
    };
  }, [navigate]);

  const initCameraPreview = async () => {
    try {
      const stream = await navigator. mediaDevices.getUserMedia({ 
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
      console.warn("[INFO] Preview de cámara no disponible (normal en red remota):", err);
      setCameraPreviewAvailable(false);
    }
  };

  const handleCapturar = async () => {
    setLoading(true);
    setError("");

    try {
      console.log("[INFO] Enviando RFID + captura de rostro al backend...");
      console.log("[DEBUG] ID Pasajero:", idPasajero);
      console.log("[DEBUG] RFID Temporal:", rfidTemp);
      
      const response = await fetch(`${API_URL}/api/admin/completar-registro`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          id_pasajero: parseInt(idPasajero),
          rfid_uid: rfidTemp
        })
      });

      const data = await response.json();

      if (response.ok && data.status === "ok") {
        console.log("[OK] ✓✓✓ Registro completado exitosamente");
        
        // Detener preview si existe
        if (videoRef.current && videoRef.current.srcObject) {
          videoRef.current.srcObject.getTracks().forEach(track => track.stop());
        }
        
        setExito(true);
      } else {
        console.error("[ERROR]", data.error);
        setError(data.error || "Error al completar registro");
      }
    } catch (err) {
      console. error("[ERROR] Error de conexión:", err);
      setError("Error de conexión con el servidor");
    } finally {
      setLoading(false);
    }
  };

  const handleFinalizar = () => {
    // Limpiar TODO el localStorage
    localStorage.removeItem("id_pasajero");
    localStorage.removeItem("nombre_pasajero");
    localStorage.removeItem("numero_vuelo");
    localStorage.removeItem("temp_rfid");
    
    navigate("/admin-panel");
  };

  if (exito) {
    return (
      <div className="container success-container">
        <img src="/GAP_logo.jpg" alt="Logo GAP" className="logo" />
        <h2 className="success-title">
          <span className="success-icon">✅</span>
          Registro Completo
        </h2>
        <p className="success-message">
          El pasajero <strong>{nombrePasajero}</strong> ha sido registrado exitosamente con todos sus datos biométricos.
        </p>
        <div style={{
          backgroundColor: "#f8f9fa",
          padding: "15px",
          borderRadius: "8px",
          marginTop: "20px",
          marginBottom: "25px"
        }}>
          <p style={{ margin: 0, color: "#666", fontSize: "14px" }}>RFID Registrado:</p>
          <p style={{ 
            margin: "5px 0 0 0", 
            fontFamily: "monospace", 
            fontSize: "16px",
            fontWeight: "bold",
            color: "#333"
          }}>
            {rfidTemp}
          </p>
        </div>
        <button className="button button-primary" onClick={handleFinalizar}>
          ✓ Finalizar
        </button>
      </div>
    );
  }

  return (
    <div className="container">
      <img src="/GAP_logo.jpg" alt="Logo GAP" className="logo" />
      <h2 className="title">Capturar Rostro</h2>
      
      <div className="pasajero-info">
        <p>Pasajero: <strong>{nombrePasajero}</strong></p>
      </div>

      <p className="instrucciones">
        Último paso: Mire directamente a la cámara para capturar su rostro
      </p>

      {/* Preview de cámara o placeholder */}
      <div className="camera-container">
        {cameraPreviewAvailable ? (
          <>
            <div className="camera-preview">
              <video 
                ref={videoRef} 
                autoPlay 
                playsInline
              />
            </div>
            <div className="preview-status">
              Preview de cámara activo
            </div>
          </>
        ) : (
          <div className="camera-placeholder">
            <div className="camera-placeholder-icon">📷</div>
            <div className="camera-placeholder-text">
              <p>Preview no disponible</p>
              <small>(La cámara del servidor se usará para el registro)</small>
            </div>
          </div>
        )}
      </div>

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      <button 
        className="button button-primary" 
        onClick={handleCapturar}
        disabled={loading}
      >
        {loading && <span className="spinner"></span>}
        {loading ? "Capturando y guardando..." : "📸 Capturar Rostro y Finalizar"}
      </button>

      {loading && (
        <p className="loading-text">
          Capturando rostro y guardando en base de datos...  Esto puede tardar hasta 15 segundos
        </p>
      )}

      <button 
        className="button button-secondary" 
        onClick={() => navigate("/admin-panel")}
        disabled={loading}
      >
        Cancelar
      </button>
    </div>
  );
}

export default AdminCamara;
