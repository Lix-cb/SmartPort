import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import "./app.css";

const API_URL = import.meta.env. VITE_API_URL || "http://localhost:5000";

function AdminCamara() {
  const navigate = useNavigate();
  const videoRef = useRef(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [exito, setExito] = useState(false);
  const [idPasajero, setIdPasajero] = useState(null);
  const [nombrePasajero, setNombrePasajero] = useState("");
  const [cameraPreviewAvailable, setCameraPreviewAvailable] = useState(false);

  useEffect(() => {
    const id = localStorage.getItem("id_pasajero");
    const nombre = localStorage.getItem("nombre_pasajero");

    if (! id) {
      alert("No hay pasajero seleccionado");
      navigate("/admin-panel");
      return;
    }

    setIdPasajero(id);
    setNombrePasajero(nombre);

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
        videoRef.current.srcObject = stream;
        
        videoRef.current.onloadedmetadata = () => {
          videoRef.current.play();
          setCameraPreviewAvailable(true);
          console.log("[OK] Preview de cámara disponible");
        };
      }
    } catch (err) {
      console.warn("[INFO] Preview de cámara no disponible (normal en red remota):", err);
      setCameraPreviewAvailable(false);
      // NO es un error crítico - el backend usa su propia cámara
    }
  };

  const handleCapturar = async () => {
    setLoading(true);
    setError("");

    try {
      console.log("[INFO] Enviando petición de captura al backend...");
      
      const response = await fetch(`${API_URL}/api/admin/registrar-rostro`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          id_pasajero: parseInt(idPasajero)
        })
      });

      const data = await response.json();

      if (response.ok && data.status === "ok") {
        console.log("[OK] Rostro registrado correctamente");
        
        // Detener preview si existe
        if (videoRef.current && videoRef. current.srcObject) {
          videoRef.current.srcObject. getTracks().forEach(track => track.stop());
        }
        
        setExito(true);
      } else {
        console.error("[ERROR]", data.error);
        setError(data.error || "Error al capturar rostro");
      }
    } catch (err) {
      console.error("[ERROR] Error de conexión:", err);
      setError("Error de conexión con el servidor");
    } finally {
      setLoading(false);
    }
  };

  const handleFinalizar = () => {
    localStorage.removeItem("id_pasajero");
    localStorage.removeItem("nombre_pasajero");
    localStorage.removeItem("numero_vuelo");
    localStorage.removeItem("rfid_uid");
    
    navigate("/admin-panel");
  };

  if (exito) {
    return (
      <div className="container">
        <img src="/GAP_logo.jpg" alt="Logo" className="logo" />
        <h2 className="title" style={{ color: "#28a745" }}>✓ Registro Completo</h2>
        <p style={{ fontSize: "18px", marginBottom: "30px" }}>
          El pasajero <strong>{nombrePasajero}</strong> ha sido registrado exitosamente. 
        </p>
        <button className="button" onClick={handleFinalizar}>
          Finalizar
        </button>
      </div>
    );
  }

  return (
    <div className="container">
      <img src="/GAP_logo.jpg" alt="Logo" className="logo" />
      <h2 className="title">Capturar Rostro</h2>
      
      <p style={{ marginBottom: "20px", fontSize: "16px" }}>
        Pasajero: <strong>{nombrePasajero}</strong>
      </p>

      <p style={{ marginBottom: "20px", color: "#666" }}>
        Mire directamente a la cámara
      </p>

      {/* Preview (opcional - solo si el navegador tiene permisos) */}
      {cameraPreviewAvailable ?  (
        <div style={{ marginBottom: "20px" }}>
          <video 
            ref={videoRef} 
            autoPlay 
            playsInline
            style={{
              width: "100%",
              maxWidth: "640px",
              border: "2px solid #ddd",
              borderRadius: "8px"
            }}
          />
          <p style={{ color: "#28a745", marginTop: "10px", fontSize: "14px" }}>
            ✓ Preview de cámara activo
          </p>
        </div>
      ) : (
        <div style={{
          width: "100%",
          maxWidth: "640px",
          height: "480px",
          backgroundColor: "#f0f0f0",
          border: "2px dashed #ccc",
          borderRadius: "8px",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          marginBottom: "20px",
          flexDirection: "column",
          padding: "20px"
        }}>
          <p style={{ color: "#666", textAlign: "center" }}>
            📷 Preview no disponible<br/>
            <small>(La cámara del servidor se usará para el registro)</small>
          </p>
        </div>
      )}

      {error && (
        <div style={{ 
          color: "red", 
          marginBottom: "15px",
          padding: "10px",
          backgroundColor: "#ffe6e6",
          borderRadius: "4px"
        }}>
          {error}
        </div>
      )}

      <button 
        className="button" 
        onClick={handleCapturar}
        disabled={loading}
        style={{ marginBottom: "15px" }}
      >
        {loading ? "⏳ Capturando rostro..." : "📸 Capturar Rostro"}
      </button>

      {loading && (
        <p style={{ color: "#007bff", fontSize: "14px" }}>
          Procesando... esto puede tardar hasta 10 segundos
        </p>
      )}

      <button 
        className="button" 
        onClick={() => navigate("/admin-panel")}
        style={{ backgroundColor: "#6c757d" }}
      >
        Cancelar
      </button>
    </div>
  );
}

export default AdminCamara;
