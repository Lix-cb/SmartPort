import { useState } from "react";
import { useNavigate } from "react-router-dom";
import "../App.css";

export default function BuscarVuelo() {
  const [nombre, setNombre] = useState("");
  const [vuelo, setVuelo] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const navigate = useNavigate();

  // Validación: solo 4 dígitos en número de vuelo
  const handleVueloChange = (e) => {
    const value = e.target.value;
    // Solo permitir números y máximo 4 dígitos
    if (/^\d{0,4}$/.test(value)) {
      setVuelo(value);
      setError("");
    }
  };

  const buscarPasajero = async () => {
    // Validaciones
    if (!nombre.trim()) {
      setError("⚠️ Por favor ingresa tu nombre completo");
      return;
    }

    if (!vuelo || vuelo.length !== 4) {
      setError("⚠️ El número de vuelo debe tener 4 dígitos");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const res = await fetch("http://localhost:5000/api/buscar-pasajero", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          nombre: nombre.trim(),
          numero_vuelo: parseInt(vuelo),
        }),
      });

      const data = await res.json();

      if (res.ok) {
        // Pasajero encontrado → ir a RFID
        navigate("/rfid", {
          state: {
            id_pasajero: data.id_pasajero,
            nombre: data.nombre_normalizado,
            vuelo: data.numero_vuelo,
            destino: data.destino,
          },
        });
      } else {
        // No encontrado
        setError(
          data.msg || 
          "❌ No se encontró tu reservación. Verifica tu nombre y número de vuelo."
        );
      }
    } catch (err) {
      console.error("Error:", err);
      setError("❌ Error de conexión. Intenta nuevamente.");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    buscarPasajero();
  };

  return (
    <div className="container">
      <div className="logo">✈️</div>
      
      <h1 className="title">Check-in Aeropuerto</h1>
      <p style={{ marginBottom: "30px", color: "#666" }}>
        Ingresa tus datos para comenzar
      </p>

      <form onSubmit={handleSubmit}>
        <input
          type="text"
          className="input"
          placeholder="Nombre completo"
          value={nombre}
          onChange={(e) => {
            setNombre(e.target.value);
            setError("");
          }}
          disabled={loading}
        />

        <input
          type="text"
          className="input"
          placeholder="Número de vuelo (4 dígitos)"
          value={vuelo}
          onChange={handleVueloChange}
          maxLength={4}
          disabled={loading}
        />

        {error && (
          <div
            style={{
              background: "#fee",
              color: "#c33",
              padding: "12px",
              borderRadius: "8px",
              marginBottom: "15px",
              fontSize: "14px",
            }}
          >
            {error}
          </div>
        )}

        <button 
          type="submit" 
          className="btn primary" 
          disabled={loading}
        >
          {loading ? "🔍 Buscando..." : "Continuar →"}
        </button>
      </form>

      <p style={{ marginTop: "30px", fontSize: "13px", color: "#999" }}>
        Sistema Aeropuerto Smart v1.0
      </p>
    </div>
  );
}