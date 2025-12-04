import { useNavigate } from "react-router-dom";

export default function Inicio() {
  const navigate = useNavigate();

  return (
    <div className="container" style={{ animation: "fadeIn 0.5s ease-in" }}>
      <img src="/GAP_logo.jpg" alt="Logo GAP" className="logo" />
      <h1 className="title" style={{ fontSize: "32px", marginBottom: "15px" }}>
        SmartPort v2.0
      </h1>
      <p style={{ 
        marginBottom: "45px", 
        fontSize: "17px", 
        color: "#666",
        lineHeight: "1.6"
      }}>
        Sistema de control de acceso inteligente<br/>
        <small style={{ fontSize: "14px", color: "#999" }}>
          Identificación biométrica y RFID
        </small>
      </p>
      
      <button 
        className="button" 
        onClick={() => navigate("/admin-login")}
        style={{ 
          marginBottom: "18px",
          background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
          border: "none",
          boxShadow: "0 4px 15px rgba(102, 126, 234, 0.4)",
          transition: "all 0.3s ease"
        }}
      >
        🔐 Modo Administrador
      </button>
      
      <button 
        className="button" 
        onClick={() => navigate("/usuario-acceso")}
        style={{ 
          background: "linear-gradient(135deg, #28a745 0%, #20c997 100%)",
          border: "none",
          boxShadow: "0 4px 15px rgba(40, 167, 69, 0.4)",
          transition: "all 0.3s ease"
        }}
      >
        ✈️ Verificación de Acceso
      </button>

      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(-20px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  );
}
