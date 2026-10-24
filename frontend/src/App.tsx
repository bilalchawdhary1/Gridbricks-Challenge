import {useEffect, useState} from "react";
import "./App.css";
import {checkApiHealth} from "./api";

function App() {
  const [status, setStatus] = useState("Checking...");

  useEffect(() => {
    checkApiHealth()
      .then(data => setStatus(data.status))
      .catch(() => setStatus("Backend disconnected"));
  }, []);

  return (
    <div className='App'>
      <h1>Gridbricks Challenge</h1>
      <p>Backend status: {status}</p>
    </div>
  );
}

export default App;
