import { useState } from "react";
import { useNavigate } from "react-router-dom";

const API_URL = "http://localhost:5000";

export default function BuscarVuelo() {
  const [nombre, setNombre] = useState("");
  const [vuelo, setVuelo] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");

    if (nombre.trim() === "" || vuelo.trim() === "") {
      setError("Por favor ingresa tu nombre y número de vuelo.");
      return;
    }

    setLoading(true);

    try {
      const response = await fetch(`${API_URL}/api/buscar-pasajero`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          nombre: nombre,
          numero_vuelo: parseInt(vuelo),
        }),
      });

      const data = await response.json();

      if (response.ok && data.status === "ok") {
        // Guardar datos del pasajero en localStorage
        localStorage.setItem("id_pasajero", data.id_pasajero);
        localStorage.setItem("nombre_pasajero", data.nombre_normalizado);
        localStorage.setItem("numero_vuelo", data.numero_vuelo);
        localStorage.setItem("destino", data.destino);

        // Ir a la siguiente página
        navigate("/rfid");
      } else {
        setError(data.msg || "No se encontró el pasajero");
      }
    } catch (err) {
      setError("Error de conexión con el servidor");
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="container">
      <img src="/GAP_logo.jpg" alt="Logo aeropuerto" className="logo" />

      <h2 className="title">Buscar vuelo</h2>

      {error && <div style={{ color: "red", marginBottom: "10px" }}>{error}</div>}

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
          type="text"
          placeholder="Número de vuelo"
          className="input"
          value={vuelo}
          onChange={(e) => setVuelo(e.target.value)}
          disabled={loading}
        />

        <button className="button" type="submit" disabled={loading}>
          {loading ?  "Buscando..." : "Continuar"}
        </button>
      </form>
    </div>
  );
}
