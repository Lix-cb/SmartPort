import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";

const API_URL = "http://localhost:5000";

export default function AdminRFID() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [idPasajero, setIdPasajero] = useState(null);
  const [nombrePasajero, setNombrePasajero] = useState("");

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
  }, [navigate]);

  const handleScan = async () => {
    setLoading(true);
    setError("");

    try {
      const response = await fetch(`${API_URL}/api/admin/registrar-rfid`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          id_pasajero: parseInt(idPasajero)
        })
      });

      const data = await response.json();

      if (response.ok && data.status === "ok") {
        localStorage.setItem("rfid_uid", data.rfid_uid);
        navigate("/admin-camara");
      } else {
        setError(data.error || "Error al registrar RFID");
      }
    } catch (err) {
      setError("Error de conexión");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container">
      <h1 className="title">Registrar RFID</h1>
      {nombrePasajero && (
        <p style={{ marginBottom: "20px", fontSize: "18px" }}>
          Pasajero: <strong>{nombrePasajero}</strong>
        </p>
      )}
      <p style={{ marginBottom: "30px", color: "#666" }}>
        Acerque la tarjeta RFID del pasajero al lector
      </p>
      
      {error && (
        <div style={{ color: "red", marginBottom: "15px" }}>{error}</div>
      )}
      
      <button 
        className="button" 
        onClick={handleScan}
        disabled={loading}
      >
        {loading ? "Escaneando..." : "Escanear RFID"}
      </button>
      
      <button 
        className="button" 
        onClick={() => navigate("/admin-panel")}
        style={{ marginTop: "10px", backgroundColor: "#6c757d" }}
      >
        ← Volver
      </button>
    </div>
  );
}
