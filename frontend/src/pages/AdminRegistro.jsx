import { useState } from "react";
import { useNavigate } from "react-router-dom";

const API_URL = "http://localhost:5000";

export default function AdminRegistro() {
  const navigate = useNavigate();
  const [nombre, setNombre] = useState("");
  const [vuelo, setVuelo] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (!nombre. trim() || !vuelo.trim()) {
      setError("Complete todos los campos");
      return;
    }

    setLoading(true);

    try {
      const response = await fetch(`${API_URL}/api/admin/crear-pasajero`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          nombre: nombre,
          numero_vuelo: parseInt(vuelo)
        })
      });

      const data = await response.json();

      if (response.ok && data.status === "ok") {
        // Guardar ID del pasajero
        localStorage. setItem("id_pasajero", data.pasajero.id_pasajero);
        localStorage.setItem("nombre_pasajero", data.pasajero. nombre);
        localStorage.setItem("numero_vuelo", data.pasajero.numero_vuelo);
        
        // Ir a registrar RFID
        navigate("/admin-rfid");
      } else {
        setError(data.error || "Error al crear pasajero");
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
      <img src="/GAP_logo.jpg" alt="Logo" className="logo" />
      <h2 className="title">Registrar Pasajero</h2>
      
      {error && (
        <div style={{ color: "red", marginBottom: "15px" }}>{error}</div>
      )}
      
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          placeholder="Nombre completo"
          className="input"
          value={nombre}
          onChange={(e) => setNombre(e.target. value)}
          disabled={loading}
        />
        <input
          type="number"
          placeholder="Número de vuelo"
          className="input"
          value={vuelo}
          onChange={(e) => setVuelo(e.target.value)}
          disabled={loading}
        />
        <button className="button" type="submit" disabled={loading}>
          {loading ? "Creando..." : "Continuar"}
        </button>
      </form>
      
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
