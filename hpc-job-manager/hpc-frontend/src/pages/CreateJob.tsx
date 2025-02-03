import { useState } from "react";
import { useUser } from '../contexts/UserContext';

const CreateJob = () => {
  const setUsername = useUser(); 
  const [password, setPassword] = useState("");
  const [use_gpu, setUseGPU] = useState(false);
  const [num_nodes, setNumNodes] = useState(1);
  const [num_tasks, setNumTasks] = useState(1);
  const [cpu_time, setCpuTime] = useState("01:00:00");
  const [status, setStatus] = useState("");
  const [jupyterURL, setJupyterURL] = useState("");
  const [localUsername, setLocalUsername] = useState(""); // Local state

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLocalUsername(localUsername); // Store username in context
    setStatus("🔗 Connecting to HPC...");

    const requestData = { username: localUsername, password, use_gpu, num_nodes, num_tasks, cpu_time };

    try {
      const response = await fetch("http://127.0.0.1:8000/start_job", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestData),
      });

      const data = await response.json();
      if (response.ok) {
        setJupyterURL(data.jupyter_url);
        setStatus("✅ Jupyter Notebook launched!");
      } else {
        setStatus("❌ HPC Job Failed.");
      }
    } catch (error) {
      setStatus("❌ Network error.");
    }
  };

  return (
    <div className="max-w-lg mx-auto bg-white p-6 shadow-md rounded-md">
      <h2 className="text-2xl font-bold text-center mb-4">Launch Jupyter Notebook</h2>
      <form onSubmit={handleSubmit} className="space-y-4">
        <input className="w-full p-2 border rounded" type="text" placeholder="Username" value={localUsername} onChange={(e) => setLocalUsername(e.target.value)} />
        <input className="w-full p-2 border rounded" type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} />
        <label className="flex items-center space-x-2">
          <input type="checkbox" checked={use_gpu} onChange={(e) => setUseGPU(e.target.checked)} />
          <span>Use GPU</span>
        </label>
        <input className="w-full p-2 border rounded" type="number" min="1" value={num_nodes} onChange={(e) => setNumNodes(Number(e.target.value))} placeholder="Number of Nodes" />
        <input className="w-full p-2 border rounded" type="number" min="1" value={num_tasks} onChange={(e) => setNumTasks(Number(e.target.value))} placeholder="Number of Tasks" />
        <input className="w-full p-2 border rounded" type="text" value={cpu_time} onChange={(e) => setCpuTime(e.target.value)} placeholder="CPU Time (hh:mm:ss)" />
        <button className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700">Launch</button>
      </form>
      <p className="mt-4">{status}</p>
      {jupyterURL && <a className="block text-blue-600 underline mt-2" href={jupyterURL} target="_blank">Open Jupyter Notebook</a>}
    </div>
  );
};

export default CreateJob;
