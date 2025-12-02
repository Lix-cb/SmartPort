import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

const logo = "/GAP_logo.jpg"; // 👈 IMPORTACIÓN CORRECTA DESDE /public

export default function Camara() {
  const videoRef = useRef(null);
  const navigate = useNavigate();
  const [finalizado, setFinalizado] = useState(false);

  useEffect(() => {
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
      }
    }

    startCamera();
  }, []);

  function handleFinalizar() {
    setFinalizado(true);
  }

  function volverInicio() {
    navigate("/");
  }

  return (
    <div className="camera-container">
      {!finalizado ? (
        <>
          <img src={logo} alt="logo" className="logo" />
          <h2 className="title">Confirmación de identidad</h2>

          <div className="camera-frame">
            <video ref={videoRef} autoPlay className="camera-video" />
          </div>

          <button className="button" onClick={handleFinalizar}>
            Finalizar
          </button>
        </>
      ) : (
        <div className="confirmation-box">
          <img src={logo} alt="logo" className="logo-small" />

          <h2 className="confirm-title">¡Identidad confirmada!</h2>
          <p className="confirm-text">
            Has sido verificado exitosamente. Puedes pasar a la zona de
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
