import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

const logo = "/GAP_logo.jpg";
const API_URL = "http://localhost:5000";

export default function Camara() {
  const videoRef = useRef(null);
  const navigate = useNavigate();
  const [finalizado, setFinalizado] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [idPasajero, setIdPasajero] = useState(null);

  useEffect(() => {
    // Recuperar datos del pasajero
    const id = localStorage. getItem("id_pasajero");

    if (!id) {
      alert("No hay pasajero seleccionado");
      navigate("/");
      return;
    }

    setIdPasajero(id);

    async function startCamera() {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: true,
        });
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
        }
      } catch (error) {
        console.error("Error al acceder a la cámara:", error);
        setError("No se pudo acceder a la cámara");
      }
    }

    startCamera();
  }, [navigate]);

  async function handleFinalizar() {
    setLoading(true);
    setError("");

    try {
      const response = await fetch(`${API_URL}/api/registrar-rostro`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON. stringify({
          id_pasajero: parseInt(idPasajero),
        }),
      });

      const data = await response. json();

      if (response. ok && data.status === "ok") {
        // Detener la cámara
        if (videoRef.current && videoRef.current.srcObject) {
          videoRef.current. srcObject. getTracks().forEach(track => track.stop());
        }
        
        setFinalizado(true);
      } else {
        setError(data.error || "Error al registrar rostro");
      }
    } catch (err) {
      setError("Error de conexión con el servidor");
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  function volverInicio() {
    // Limpiar localStorage
    localStorage.removeItem("id_pasajero");
    localStorage.removeItem("nombre_pasajero");
    localStorage.removeItem("numero_vuelo");
    localStorage. removeItem("destino");
    localStorage.removeItem("rfid_uid");
    
    navigate("/");
  }

  return (
    <div className="camera-container">
      {! finalizado ?  (
        <>
          <img src={logo} alt="logo" className="logo" />
          <h2 className="title">Confirmación de identidad</h2>

          {error && <div style={{ color: "red", marginBottom: "10px" }}>{error}</div>}

          <div className="camera-frame">
            <video ref={videoRef} autoPlay className="camera-video" />
          </div>

          <button 
            className="button" 
            onClick={handleFinalizar}
            disabled={loading}
          >
            {loading ? "Procesando..." : "Finalizar"}
          </button>
        </>
      ) : (
        <div className="confirmation-box">
          <img src={logo} alt="logo" className="logo-small" />

          <h2 className="confirm-title">¡Identidad confirmada!</h2>
          <p className="confirm-text">
            Has sido verificado exitosamente.  Puedes pasar a la zona de
            seguridad.
          </p>

          <button className="button" onClick={volverInicio}>
            Volver al inicio
          </button>
        </div>
      )}
    </div>
  );
}
