import { useState } from "react";
import { useNavigate } from "react-router-dom";

export default function BuscarVuelo() {
  const [nombre, setNombre] = useState("");
  const [vuelo, setVuelo] = useState("");
  const navigate = useNavigate();

  function handleSubmit(e) {
    e.preventDefault();

    if (nombre.trim() === "" || vuelo.trim() === "") {
      alert("Por favor ingresa tu nombre y número de vuelo.");
      return;
    }

    navigate("/rfid");
  }

  return (
    <div className="container">
      {/* LOGO */}
      <img src="/GAP_logo.jpg" alt="Logo aeropuerto" className="logo" />

      <h2 className="title">Buscar vuelo</h2>

      <form onSubmit={handleSubmit}>
        <input
          type="text"
          placeholder="Nombre completo"
          className="input"
          value={nombre}
          onChange={(e) => setNombre(e.target.value)}
        />

        <input
          type="text"
          placeholder="Número de vuelo"
          className="input"
          value={vuelo}
          onChange={(e) => setVuelo(e.target.value)}
        />

        <button className="button" type="submit">
          Continuar
        </button>
      </form>
    </div>
  );
}
