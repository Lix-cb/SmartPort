import { useState } from "react";
import { useNavigate } from "react-router-dom";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:5000";

export default function AdminRegistro() {
  const navigate = useNavigate();
  const [nombre, setNombre] = useState("");
  const [vuelo, setVuelo] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // CAMBIO 5: Limitar a 4 caracteres
  const handleVueloChange = (e) => {
    const value = e.target.value;
    // Solo aceptar números y limitar a 4 caracteres
    if (value === "" || (/^\d+$/.test(value) && value.length <= 4)) {
      setVuelo(value);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    if (!nombre. trim() || !vuelo.trim()) {
      setError("Complete todos los campos");
      return;
    }

    // Validar que el vuelo tenga máximo 4 dígitos
    if (vuelo.length > 4) {
      setError("El número de vuelo debe tener máximo 4 dígitos");
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
        localStorage.setItem("id_pasajero", data.pasajero. id_pasajero);
        localStorage.setItem("nombre_pasajero", data.pasajero. nombre);
        localStorage.setItem("numero_vuelo", data.pasajero.numero_vuelo);
        navigate("/admin-rfid");
      } else {
        setError(data.error || "Error al crear pasajero");
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
      <img src="/GAP_logo.jpg" alt="Logo GAP" className="logo" />
      <h2 className="title">👤 Registrar Pasajero</h2>
      
      <p style={{ 
        marginBottom: "25px", 
        fontSize: "15px", 
        color: "#666",
        lineHeight: "1.6"
      }}>
        Ingrese los datos del pasajero para iniciar el registro
      </p>

      {error && (
        <div style={{ 
          backgroundColor: "#f8d7da",
          border: "2px solid #f5c6cb",
          borderRadius: "10px",
          padding: "15px",
          marginBottom: "20px",
          color: "#721c24",
          fontSize: "15px",
          fontWeight: "500",
          animation: "shake 0.5s"
        }}>
          ⚠️ {error}
        </div>
      )}
      
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          placeholder="Nombre completo del pasajero"
          className="input"
          value={nombre}
          onChange={(e) => setNombre(e.target.value)}
          disabled={loading}
          style={{
            fontSize: "16px",
            padding: "14px",
            marginBottom: "15px"
          }}
          autoFocus
        />
        <input
          type="text"
          placeholder="Número de vuelo (máx. 4 dígitos)"
          className="input"
          value={vuelo}
          onChange={handleVueloChange}
          disabled={loading}
          maxLength={4}
          style={{
            fontSize: "16px",
            padding: "14px",
            marginBottom: "20px"
          }}
        />
        <button 
          className="button" 
          type="submit" 
          disabled={loading}
          style={{
            background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
            fontSize: "16px",
            padding: "14px",
            marginBottom: "12px"
          }}
        >
          {loading ? (
            <>
              <span style={{
                display: "inline-block",
                width: "16px",
                height: "16px",
                border: "2px solid rgba(255,255,255,0.3)",
                borderTop: "2px solid white",
                borderRadius: "50%",
                marginRight: "8px",
                animation: "spin 0.8s linear infinite",
                verticalAlign: "middle"
              }}></span>
              Creando...
            </>
          ) : "➡️ Continuar"}
        </button>
      </form>
      
      <button 
        className="button" 
        onClick={() => navigate("/admin-panel")}
        disabled={loading}
        style={{ 
          backgroundColor: "#6c757d",
          fontSize: "16px",
          padding: "14px"
        }}
      >
        ← Volver
      </button>

      <style>{`
        @keyframes shake {
          0%, 100% { transform: translateX(0); }
          25% { transform: translateX(-10px); }
          75% { transform: translateX(10px); }
        }
        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}
