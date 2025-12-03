import { useNavigate } from "react-router-dom";

export default function Inicio() {
  const navigate = useNavigate();

  return (
    <div className="container">
      <img src="/GAP_logo.jpg" alt="Logo aeropuerto" className="logo" />
      <h1 className="title">SmartPort v2.0</h1>
      <p style={{ marginBottom: "40px", fontSize: "18px", color: "#666" }}>
        Sistema de control de acceso inteligente
      </p>
      
      <button 
        className="button" 
        onClick={() => navigate("/admin-login")}
        style={{ marginBottom: "20px" }}
      >
        Modo Administrador
      </button>
      
      <button 
        className="button" 
        onClick={() => navigate("/usuario-acceso")}
      >
        Verificacion de Acceso
      </button>
    </div>
  );
}
