import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:5000";

export default function UsuarioAcceso() {
  const navigate = useNavigate();
  const [estado, setEstado] = useState("esperando"); // esperando | escaneandoRFID | esperandoCamara | capturandoRostro | exito | error | errorGeneral
  const [loading, setLoading] = useState(false);
  const [mensaje, setMensaje] = useState("");
  const [pasajeroInfo, setPasajeroInfo] = useState(null);
  const [similitud, setSimilitud] = useState(null);
  const [paso, setPaso] = useState(1); // 1=RFID, 2=Rostro
  const [rfidValido, setRfidValido] = useState(false);
  const [idPasajeroTemp, setIdPasajeroTemp] = useState(null); // Para guardar ID entre pasos

  const handleVerificar = async () => {
    setLoading(true);
    setEstado("escaneandoRFID");
    setPaso(1);
    setRfidValido(false);
    setIdPasajeroTemp(null);
    setMensaje("Acerque su tarjeta RFID.. .");

    try {
      // ============================================
      // PASO 1: VALIDAR RFID (SIN CAPTURAR ROSTRO)
      // ============================================
      const response1 = await fetch(`${API_URL}/api/usuario/validar-rfid`, {
        method: "POST",
        headers: { "Content-Type": "application/json" }
      });

      const data1 = await response1.json();

      // ===== VALIDACIÓN 1: RFID no registrado =====
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

      // ===== VALIDACIÓN 2: Ya completó proceso (ABORDADO/COMPLETO) =====
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

      // ===== VALIDACIÓN 3: Pasajero sin biometría =====
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

      // ===== SI LLEGÓ AQUÍ: RFID VÁLIDO =====
      if (response1.ok && data1.status === "ok") {
        setRfidValido(true);
        setIdPasajeroTemp(data1.pasajero.id_pasajero);
        setPasajeroInfo(data1. pasajero);
        
        // MOSTRAR MENSAJE "MIRE A LA CÁMARA" (ESTADO AMARILLO/NARANJA)
        setEstado("esperandoCamara");
        setPaso(2);
        setMensaje("Por favor, mire a la cámara...");

        // ============================================
        // ESPERAR 3 SEGUNDOS ANTES DE CAPTURAR ROSTRO
        // ============================================
        await new Promise(resolve => setTimeout(resolve, 3000));

        // ============================================
        // PASO 2: VERIFICAR ROSTRO
        // ============================================
        setEstado("capturandoRostro");
        setMensaje("Capturando rostro...");

        const response2 = await fetch(`${API_URL}/api/usuario/verificar-rostro`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ id_pasajero: data1.pasajero.id_pasajero })
        });

        const data2 = await response2.json();

        // ===== EVALUAR RESULTADO DE VERIFICACIÓN BIOMÉTRICA =====
        if (response2.ok && data2. status === "ok" && data2.acceso === "concedido") {
          // ✅ ÉXITO: Biometría coincide - AHORA SÍ SE CAMBIÓ A ABORDADO
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
          
        } else if (data2.error === "Biometria no coincide") {
          // ❌ ERROR: Biometría no coincide - NO SE CAMBIÓ EL ESTADO
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
          // ⚠️ ERROR: No detectó rostro - NO SE CAMBIÓ EL ESTADO
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
          // ⚠️ ERROR GENERAL - NO SE CAMBIÓ EL ESTADO
          setEstado("errorGeneral");
          setMensaje("Error en la verificación.  Por favor, intente nuevamente");
          
          setTimeout(() => {
            setEstado("esperando");
            setMensaje("");
            setPaso(1);
            setRfidValido(false);
            setIdPasajeroTemp(null);
          }, 4000);
        }
      } else {
        // Error en validación de RFID
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
      // ERROR DE CONEXIÓN
      setEstado("errorGeneral");
      setMensaje("Error de conexión.  Por favor, intente nuevamente");
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

  // ========================================
  // ESTADO: Escaneando RFID
  // ========================================
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

  // ========================================
  // ESTADO: Esperando Cámara (NUEVO)
  // ========================================
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
            
