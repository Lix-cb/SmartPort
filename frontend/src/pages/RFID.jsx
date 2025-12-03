import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import "../app.css";

const API_URL = "http://localhost:5000";

export default function RFID() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [idPasajero, setIdPasajero] = useState(null);
  const [nombrePasajero, setNombrePasajero] = useState("");

  useEffect(() => {
    // Recuperar datos del pasajero
    const id = localStorage.getItem("id_pasajero");
    const nombre = localStorage.getItem("nombre_pasajero");

    if (! id) {
      alert("No hay pasajero seleccionado");
      navigate("/");
      return;
    }

    setIdPasajero(id);
    setNombrePasajero(nombre);
  }, [navigate]);

  const handleScan = async () => {
    setLoading(true);
    setError("");

    try {
      const response = await fetch(`${API_URL}/api/registrar-rfid`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON. stringify({
          id_pasajero: parseInt(idPasajero),
        }),
      });

      const data = await response.json();

      if (response.ok && data. status === "ok") {
        // Guardar el RFID
        localStorage.setItem("rfid_uid", data.rfid_uid);
        
        // Ir a cámara
        navigate("/camara");
      } else {
        setError(data.error || "Error al registrar RFID");
      }
    } catch (err) {
      setError("Error de conexión con el servidor");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container">
      <h1 className="title">Escaneo de RFID</h1>
      
      {nombrePasajero && (
        <p style={{ marginBottom: "20px", fontSize: "18px" }}>
          Pasajero: <strong>{nombrePasajero}</strong>
        </p>
      )}

      {error && <div style={{ color: "red", marginBottom: "10px" }}>{error}</div>}

      <button 
        className="button" 
        onClick={handleScan}
        disabled={loading}
      >
        {loading ? "Escaneando..." : "Escanear tarjeta RFID"}
      </button>
    </div>
  );
}
