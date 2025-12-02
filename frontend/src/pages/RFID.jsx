import { useNavigate } from "react-router-dom";
import "../App.css";

export default function RFID() {
  const navigate = useNavigate();

  const handleScan = () => {
    alert("RFID escaneado correctamente");
    navigate("/camara");
  };

  return (
    <div className="container">
      <h1 className="title">Escaneo de RFID</h1>

      <button className="button" onClick={handleScan}>
        Escanear tarjeta RFID
      </button>
    </div>
  );
}
