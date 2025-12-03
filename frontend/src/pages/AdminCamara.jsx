import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";

const API_URL = "http://localhost:5000";

export default function AdminCamara() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [exito, setExito] = useState(false);
  const [idPasajero, setIdPasajero] = useState(null);
  const [nombrePasajero, setNombrePasajero] = useState("");
  const [cameraReady, setCameraReady] = useState(false);
  const videoRef = useRef(null);

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

    // Inicializar camara para preview
    initCamera();

    return () => {
      // Limpiar stream al desmontar
      if (videoRef.current && videoRef.current.srcObject) {
        videoRef.current.srcObject. getTracks().forEach(track => track.stop());
      }
    };
  }, [navigate]);

  const initCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        video: { 
          width: { ideal: 640 },
          height: { ideal: 480 }
        } 
      });

      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        
        // Esperar a que el video este listo
        videoRef.current.onloadedmetadata = () => {
          videoRef.current.play();
          setCameraReady(true);
          console.log("[OK] Camara inicializada y mostrando video");
        };
      }
    } catch (err) {
      console.error("[ERROR] No se pudo acceder a la camara:", err);
      setError("No se pudo acceder a la camara.  Verifica los permisos.");
      setCameraReady(false);
    }
  };

  const handleCapturar = async () => {
    if (!cameraReady) {
      setError("Esperando a que la camara este lista...");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const response = await fetch(`${API_URL}/api/admin/registrar-rostro`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          id_pasajero: parseInt(idPasajero)
        })
      });

      const data = await response.json();

      if (response.ok && data.status === "ok") {
        // Detener camara
        if (videoRef. current && videoRef.current.srcObject) {
          videoRef. current.srcObject.getTracks(). forEach(track => track.stop());
        }
        setExito(true);
      } else {
        setError(data.error || "Error al capturar rostro");
      }
    } catch (err) {
      setError("Error de conexion");
      console.error(err);
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
        <h2 className="title" style={{ color: "#28a745" }}>Registro Completo</h2>
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
      <h1 className="title">Capturar Rostro</h1>
      {nombrePasajero && (
        <p style={{ marginBottom: "20px", fontSize: "18px" }}>
          Pasajero: <strong>{nombrePasajero}</strong>
        </p>
      )}
      <p style={{ marginBottom: "20px", color: "#666" }}>
        Mire directamente a la camara
      </p>

      {/* Preview de camara */}
      <div className="camera-frame">
        {!cameraReady && (
          <div className="camera-loading">Inicializando camara...</div>
        )}
        <video 
          ref={videoRef}
          className="camera-video"
          autoPlay
          playsInline
          muted
        />
      </div>
      
      {error && (
        <div style={{ color: "red", marginBottom: "15px" }}>{error}</div>
      )}
      
      <button 
        className="button" 
        onClick={handleCapturar}
        disabled={loading || !cameraReady}
      >
        {loading ? "Capturando..." : "Capturar Rostro"}
      </button>
      
      <button 
        className="button" 
        onClick={() => navigate("/admin-panel")}
        style={{ marginTop: "10px", backgroundColor: "#6c757d" }}
      >
        Volver
      </button>
    </div>
  );
}
