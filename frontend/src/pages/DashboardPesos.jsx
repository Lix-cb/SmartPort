import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import "./DashboardPesos.css";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:5000";

export default function DashboardPesos() {
  const navigate = useNavigate();
  const [pesos, setPesos] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [autoRefresh, setAutoRefresh] = useState(true);

  const fetchDatos = async () => {
    try {
      const response = await fetch(`${API_URL}/api/admin/dashboard-pesos? limite=50`);
      const data = await response.json();

      if (response.ok && data.status === "ok") {
        setPesos(data.pesos);
        setStats(data.estadisticas);
        setError("");
      } else {
        setError(data.error || "Error al cargar datos");
      }
    } catch (err) {
      console.error(err);
      setError("Error de conexión con el servidor");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Cargar datos iniciales
    fetchDatos();

    // Auto-refresh cada 5 segundos si está activado
    let interval;
    if (autoRefresh) {
      interval = setInterval(() => {
        fetchDatos();
      }, 5000);
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [autoRefresh]);

  const getEstadoColor = (estado) => {
    switch (estado) {
      case "SOBREPESO":
        return "#dc3545";
      case "ADVERTENCIA":
        return "#ffc107";
      default:
        return "#28a745";
    }
  };

  const getEstadoIcon = (estado) => {
    switch (estado) {
      case "SOBREPESO":
        return "⚠️";
      case "ADVERTENCIA":
        return "⚡";
      default:
        return "✅";
    }
  };

  if (loading) {
    return (
      <div className="dashboard-container">
        <img src="/GAP_logo.jpg" alt="Logo GAP" className="logo" />
        <h2 className="title">📊 Cargando Dashboard...</h2>
        <div className="spinner-large"></div>
      </div>
    );
  }

  return (
    <div className="dashboard-container">
      <img src="/GAP_logo.jpg" alt="Logo GAP" className="logo" />
      
      <div className="dashboard-header">
        <h2 className="title">📊 Dashboard de Pesos</h2>
        <div className="auto-refresh">
          <label>
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e. target.checked)}
            />
            <span style={{ marginLeft: "8px" }}>Actualización automática (5s)</span>
          </label>
        </div>
      </div>

      {error && (
        <div className="error-banner">
          ⚠️ {error}
        </div>
      )}

      {/* ESTADÍSTICAS */}
      {stats && (
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-icon">📦</div>
            <div className="stat-value">{stats. total_hoy}</div>
            <div className="stat-label">Pesajes Hoy</div>
          </div>

          <div className="stat-card">
            <div className="stat-icon">📊</div>
            <div className="stat-value">{stats. promedio} kg</div>
            <div className="stat-label">Promedio</div>
          </div>

          <div className="stat-card">
            <div className="stat-icon">⬆️</div>
            <div className="stat-value">{stats.maximo} kg</div>
            <div className="stat-label">Máximo</div>
          </div>

          <div className="stat-card">
            <div className="stat-icon">⬇️</div>
            <div className="stat-value">{stats.minimo} kg</div>
            <div className="stat-label">Mínimo</div>
          </div>

          <div className="stat-card alert">
            <div className="stat-icon">⚠️</div>
            <div className="stat-value">{stats.sobrepesos}</div>
            <div className="stat-label">Sobrepesos</div>
          </div>
        </div>
      )}

      {/* TABLA DE PESOS */}
      <div className="table-container">
        <div className="table-header">
          <h3>Últimos 50 Registros</h3>
          <button 
            className="btn-refresh" 
            onClick={fetchDatos}
          >
            🔄 Actualizar
          </button>
        </div>

        {pesos.length === 0 ?  (
          <div className="empty-state">
            <div className="empty-icon">📭</div>
            <p>No hay registros de pesos todavía</p>
          </div>
        ) : (
          <div className="table-scroll">
            <table className="pesos-table">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Peso (kg)</th>
                  <th>Estado</th>
                  <th>Fecha y Hora</th>
                </tr>
              </thead>
              <tbody>
                {pesos.map((peso) => (
                  <tr key={peso.id_peso}>
                    <td>{peso.id_peso}</td>
                    <td className="peso-value">
                      <strong>{peso.peso_kg}</strong> kg
                    </td>
                    <td>
                      <span 
                        className="badge"
                        style={{ backgroundColor: getEstadoColor(peso.estado) }}
                      >
                        {getEstadoIcon(peso.estado)} {peso.estado}
                      </span>
                    </td>
                    <td className="fecha">
                      {new Date(peso.fecha_hora).toLocaleString('es-MX')}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <button 
        className="button button-secondary" 
        onClick={() => navigate("/admin-panel")}
        style={{ marginTop: "25px" }}
      >
        ← Volver al Panel
      </button>
    </div>
  );
}
