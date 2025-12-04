import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

const API_URL = import. meta.env.VITE_API_URL || "http://localhost:5000";

export default function UsuarioAcceso() {
  const navigate = useNavigate();
  const [estado, setEstado] = useState("esperando");
  const [loading, setLoading] = useState(false);
  const [mensaje, setMensaje] = useState("");
  const [pasajeroInfo, setPasajeroInfo] = useState(null);
  const [similitud, setSimilitud] = useState(null);
  const [paso, setPaso] = useState(1);
  const [rfidValido, setRfidValido] = useState(false);
  const [idPasajeroTemp, setIdPasajeroTemp] = useState(null);

  const handleVerificar = async () => {
    setLoading(true);
    setEstado("escaneandoRFID");
    setPaso(1);
    setRfidValido(false);
    setIdPasajeroTemp(null);
    setMensaje("Acerque su tarjeta RFID.. .");

    try {
      // PASO 1: VALIDAR RFID
      const response1 = await fetch(`${API_URL}/api/usuario/validar-rfid`, {
        method: "POST",
        headers: { "Content-Type": "application/json" }
      });

      const data1 = await response1.json();

      // VALIDACIÓN 1: RFID no registrado
      if (response1.status === 404 && data1.error === "RFID no registrado") {
        setEstado("error");
        setMensaje("Tarjeta RFID no registrada en el sistema");
        setRfidValido(false);
        
        setTimeout(() => {
          setEstado("esperando");
          setMensaje("");
          setPaso(1);
        }, 4000);
        setLoading(false);
        return;
      }

      // VALIDACIÓN 2: Ya completó proceso
      if (response1.status === 403 && data1.error === "Ya completó el proceso de abordaje") {
        setEstado("error");
        setMensaje(`Ya completó el proceso de abordaje (Estado: ${data1.estado_actual})`);
        setRfidValido(false);
        
        setTimeout(() => {
          setEstado("esperando");
          setMensaje("");
          setPaso(1);
        }, 4000);
        setLoading(false);
        return;
      }

      // VALIDACIÓN 3: Pasajero sin biometría
      if (data1.error === "Pasajero sin biometria registrada") {
        setEstado("error");
        setMensaje("Complete su registro biométrico en el mostrador");
        setRfidValido(false);
        
        setTimeout(() => {
          setEstado("esperando");
          setMensaje("");
          setPaso(1);
        }, 4000);
        setLoading(false);
        return;
      }

      // RFID VÁLIDO
      if (response1.ok && data1. status === "ok") {
        setRfidValido(true);
        setIdPasajeroTemp(data1.pasajero.id_pasajero);
        setPasajeroInfo(data1.pasajero);
        
        setEstado("esperandoCamara");
        setPaso(2);
        setMensaje("Por favor, mire a la cámara...");

        await new Promise(resolve => setTimeout(resolve, 3000));

        // PASO 2: VERIFICAR ROSTRO
        setEstado("capturandoRostro");
        setMensaje("Capturando rostro...");

        const response2 = await fetch(`${API_URL}/api/usuario/verificar-rostro`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ id_pasajero: data1.pasajero.id_pasajero })
        });

        const data2 = await response2.json();

        if (response2.ok && data2.status === "ok" && data2.acceso === "concedido") {
          setEstado("exito");
          setPasajeroInfo(data2.pasajero);
          setSimilitud(data2.similitud);
          setMensaje(`Bienvenido ${data2.pasajero.nombre}`);
          
          setTimeout(() => {
            setEstado("esperando");
            setMensaje("");
            setPasajeroInfo(null);
            setSimilitud(null);
            setPaso(1);
            setRfidValido(false);
            setIdPasajeroTemp(null);
          }, 6000);
          
        } else if (data2. error === "Biometria no coincide") {
          setEstado("error");
          setMensaje("Los datos biométricos no coinciden");
          
          setTimeout(() => {
            setEstado("esperando");
            setMensaje("");
            setPaso(1);
            setRfidValido(false);
            setIdPasajeroTemp(null);
          }, 4000);
          
        } else if (data2.error === "No se detectó rostro") {
          setEstado("errorGeneral");
          setMensaje("No se detectó ningún rostro.  Por favor, intente nuevamente");
          
          setTimeout(() => {
            setEstado("esperando");
            setMensaje("");
            setPaso(1);
            setRfidValido(false);
            setIdPasajeroTemp(null);
          }, 4000);
          
        } else {
          setEstado("errorGeneral");
          setMensaje("Error en la verificación. Por favor, intente nuevamente");
          
          setTimeout(() => {
            setEstado("esperando");
            setMensaje("");
            setPaso(1);
            setRfidValido(false);
            setIdPasajeroTemp(null);
          }, 4000);
        }
      } else {
        setEstado("error");
        setMensaje(data1.error || "Error en la verificación");
        
        setTimeout(() => {
          setEstado("esperando");
          setMensaje("");
          setPaso(1);
          setRfidValido(false);
          setIdPasajeroTemp(null);
        }, 4000);
      }

    } catch (err) {
      setEstado("errorGeneral");
      setMensaje("Error de conexión. Por favor, intente nuevamente");
      console.error(err);
      
      setTimeout(() => {
        setEstado("esperando");
        setMensaje("");
        setPaso(1);
        setRfidValido(false);
        setIdPasajeroTemp(null);
      }, 4000);
    } finally {
      setLoading(false);
    }
  };

  // ESTADO: Escaneando RFID
  if (estado === "escaneandoRFID") {
    return (
      <div className="container">
        <img src="/GAP_logo.jpg" alt="Logo GAP" className="logo" />
        <h2 className="title" style={{ color: "#007bff" }}>Paso 1/2: Escaneo RFID</h2>
        
        <div style={{
          backgroundColor: "#e7f3ff",
          border: "2px solid #b3d9ff",
          borderRadius: "12px",
          padding: "40px",
          marginBottom: "25px",
          textAlign: "center"
        }}>
          <div style={{
            width: "100px",
            height: "100px",
            border: "8px solid #007bff",
            borderTop: "8px solid transparent",
            borderRadius: "50%",
            margin: "0 auto 30px",
            animation: "spin 1. 2s linear infinite"
          }}></div>
          
          <div style={{ fontSize: "60px", marginBottom: "20px" }}>📱</div>
          
          <p style={{ 
            fontSize: "18px", 
            fontWeight: "bold",
            color: "#007bff",
            margin: 0
          }}>
            {mensaje}
          </p>
        </div>

        <style>{`
          @keyframes spin {
            to { transform: rotate(360deg); }
          }
        `}</style>
      </div>
    );
  }

  // ESTADO: Esperando Cámara
  if (estado === "esperandoCamara") {
    return (
      <div className="container">
        <img src="/GAP_logo.jpg" alt="Logo GAP" className="logo" />
        <h2 className="title" style={{ color: "#ff8c00" }}>Paso 2/2: Preparando cámara</h2>
        
        <div style={{
          backgroundColor: "#fff3e0",
          border: "2px solid #ffb74d",
          borderRadius: "12px",
          padding: "40px",
          marginBottom: "25px",
          textAlign: "center"
        }}>
          <div style={{ fontSize: "80px", marginBottom: "20px" }}>📷</div>
          
          <p style={{ 
            fontSize: "18px", 
            fontWeight: "bold",
            color: "#ff8c00",
            margin: 0
          }}>
            {mensaje}
          </p>
        </div>
      </div>
    );
  }

  // ESTADO: Capturando Rostro
  if (estado === "capturandoRostro") {
    return (
      <div className="container">
        <img src="/GAP_logo.jpg" alt="Logo GAP" className="logo" />
        <h2 className="title" style={{ color: "#007bff" }}>Paso 2/2: Verificación Facial</h2>
        
        <div style={{
          backgroundColor: "#e7f3ff",
          border: "2px solid #b3d9ff",
          borderRadius: "12px",
          padding: "40px",
          marginBottom: "25px",
          textAlign: "center"
        }}>
          <div style={{
            width: "100px",
            height: "100px",
            border: "8px solid #007bff",
            borderTop: "8px solid transparent",
            borderRadius: "50%",
            margin: "0 auto 30px",
            animation: "spin 1.2s linear infinite"
          }}></div>
          
          <div style={{ fontSize: "60px", marginBottom: "20px" }}>📷</div>
          
          <p style={{ 
            fontSize: "18px", 
            fontWeight: "bold",
            color: "#007bff",
            margin: 0
          }}>
            {mensaje}
          </p>
        </div>

        <style>{`
          @keyframes spin {
            to { transform: rotate(360deg); }
          }
        `}</style>
      </div>
    );
  }

  // ESTADO: Éxito
  if (estado === "exito") {
    return (
      <div className="container">
        <img src="/GAP_logo.jpg" alt="Logo GAP" className="logo" />
        <h2 className="title" style={{ color: "#28a745" }}>✓ Acceso Concedido</h2>
        
        <div style={{
          backgroundColor: "#d4edda",
          border: "3px solid #28a745",
          borderRadius: "12px",
          padding: "40px",
          marginBottom: "25px",
          textAlign: "center"
        }}>
          <div style={{ fontSize: "100px", marginBottom: "20px" }}>✓</div>
          
          <p style={{ 
            fontSize: "24px", 
            fontWeight: "bold",
            color: "#155724",
            marginBottom: "20px"
          }}>
            {mensaje}
          </p>
          
          {pasajeroInfo && (
            <div style={{ marginTop: "20px", fontSize: "16px", color: "#155724" }}>
              <p><strong>Vuelo:</strong> {pasajeroInfo.vuelo}</p>
              <p><strong>Destino:</strong> {pasajeroInfo.destino}</p>
              {similitud && <p><strong>Coincidencia:</strong> {similitud}%</p>}
            </div>
          )}
        </div>
      </div>
    );
  }

  // ESTADO: Error
  if (estado === "error") {
    return (
      <div className="container">
        <img src="/GAP_logo.jpg" alt="Logo GAP" className="logo" />
        <h2 className="title" style={{ color: "#dc3545" }}>✗ Acceso Denegado</h2>
        
        <div style={{
          backgroundColor: "#f8d7da",
          border: "3px solid #dc3545",
          borderRadius: "12px",
          padding: "40px",
          marginBottom: "25px",
          textAlign: "center"
        }}>
          <div style={{ fontSize: "100px", marginBottom: "20px" }}>✗</div>
          
          <p style={{ 
            fontSize: "20px", 
            fontWeight: "bold",
            color: "#721c24",
            margin: 0
          }}>
            {mensaje}
          </p>
        </div>
      </div>
    );
  }

  // ESTADO: Error General
  if (estado === "errorGeneral") {
    return (
      <div className="container">
        <img src="/GAP_logo.jpg" alt="Logo GAP" className="logo" />
        <h2 className="title" style={{ color: "#ffc107" }}>⚠ Advertencia</h2>
        
        <div style={{
          backgroundColor: "#fff3cd",
          border: "3px solid #ffc107",
          borderRadius: "12px",
          padding: "40px",
          marginBottom: "25px",
          textAlign: "center"
        }}>
          <div style={{ fontSize: "100px", marginBottom: "20px" }}>⚠</div>
          
          <p style={{ 
            fontSize: "20px", 
            fontWeight: "bold",
            color: "#856404",
            margin: 0
          }}>
            {mensaje}
          </p>
        </div>
      </div>
    );
  }

  // ESTADO: Esperando (default)
  return (
    <div className="container">
      <img src="/GAP_logo. jpg" alt="Logo GAP" className="logo" />
      <h1 className="title">🛂 Control de Acceso</h1>
      
      <p style={{ 
        marginBottom: "30px", 
        color: "#666",
        fontSize: "16px",
        textAlign: "center",
        lineHeight: "1.6"
      }}>
        Escanee su RFID y mire a la cámara para verificación biométrica
      </p>

      <div style={{
        backgroundColor: "#f8f9fa",
        border: "2px dashed #dee2e6",
        borderRadius: "12px",
        padding: "30px 20px",
        marginBottom: "30px"
      }}>
        <div style={{ display: "flex", justifyContent: "center", gap: "40px", flexWrap: "wrap" }}>
          <div style={{ textAlign: "center" }}>
            <div style={{ fontSize: "48px", marginBottom: "10px" }}>📱</div>
            <p style={{ fontSize: "14px", color: "#666", margin: 0 }}>
              Paso 1: Tarjeta RFID
            </p>
          </div>
          <div style={{ fontSize: "30px", color: "#dee2e6", display: "flex", alignItems: "center" }}>
            →
          </div>
          <div style={{ textAlign: "center" }}>
            <div style={{ fontSize: "48px", marginBottom: "10px" }}>📷</div>
            <p style={{ fontSize: "14px", color: "#666", margin: 0 }}>
              Paso 2: Reconocimiento Facial
            </p>
          </div>
        </div>
      </div>

      <button 
        className="button" 
        onClick={handleVerificar}
        disabled={loading}
        style={{
          background: loading ? "#ccc" : "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
          cursor: loading ? "not-allowed" : "pointer"
        }}
      >
        {loading ? "Procesando..." : "Iniciar Verificación"}
      </button>
      
      <button 
        className="button" 
        onClick={() => navigate("/")}
        style={{ 
          backgroundColor: "#6c757d",
          marginTop: "15px"
        }}
      >
        ← Volver
      </button>
    </div>
  );
}
