import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import BuscarVuelo from "./pages/BuscarVuelo.jsx";
import RFID from "./pages/RFID.jsx";
import Camara from "./pages/Camara.jsx";

export default function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<BuscarVuelo />} />
        <Route path="/rfid" element={<RFID />} />
        <Route path="/camara" element={<Camara />} />
      </Routes>
    </Router>
  );
}
