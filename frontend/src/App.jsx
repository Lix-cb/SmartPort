import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import BuscarVuelo from "./pages/BuscarVuelo.jsx";
import RFID from "./pages/RFID.jsx";

export default function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<BuscarVuelo />} />
        <Route path="/rfid" element={<RFID />} />
      </Routes>
    </Router>
  );
}