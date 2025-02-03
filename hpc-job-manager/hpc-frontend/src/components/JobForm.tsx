import React, { useState } from "react";

const JobForm: React.FC = () => {
    const [username, setUsername] = useState<string>("");
    const [password, setPassword] = useState<string>("");
    const [use_gpu, setUseGPU] = useState<boolean>(false);
    const [cpu_time, setCpuTime] = useState<string>("01:00:00");
    const [num_nodes, setNumNodes] = useState<number>(1);
    const [num_tasks, setNumTasks] = useState<number>(1);
    const [status, setStatus] = useState<string>("");
    const [jupyterURL, setJupyterURL] = useState<string>("");

    const handleSubmit = async (event: React.FormEvent) => {
        event.preventDefault();
        setStatus("🔗 Connecting to HPC and requesting a node...");

        const requestData = {
            username,
            password,
            use_gpu,
            cpu_time,
            num_nodes,
            num_tasks
            
        };

        console.log("Sending request:", requestData); // Debugging log

        try {
            const response = await fetch("http://127.0.0.1:8000/start_job", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(requestData),
            });

            const data = await response.json();
            if (response.ok) {
                setJupyterURL(data.jupyter_url);
                setStatus("✅ Jupyter Notebook launched!");
            } else {
                console.error("Server Error:", data);
                setStatus("❌ HPC Job Failed.");
            }
        } catch (error) {
            console.error("Request Error:", error);
            setStatus("❌ Network error.");
        }
    };

    return (
        <div>
            <h1>Submit Job to HPC</h1>
            <form onSubmit={handleSubmit}>
                <label>
                    Username:
                    <input
                        type="text"
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                    />
                </label>
                <br />
                <label>
                    Password:
                    <input
                        type="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                    />
                </label>
                <br />
                <label>
                    Use GPU:
                    <input
                        type="checkbox"
                        checked={use_gpu}
                        onChange={(e) => setUseGPU(e.target.checked)}
                    />
                </label>
                <br />
                <label>
                    Number of Nodes:
                    <input
                        type="number"
                        value={num_nodes}
                        onChange={(e) => setNumNodes(Number(e.target.value))}
                    />
                </label>
                <br />
                <label>
                    Number of Tasks:
                    <input
                        type="number"
                        value={num_tasks}
                        onChange={(e) => setNumTasks(Number(e.target.value))}
                    />
                </label>
                <br />
                <label>
                    CPU Time (in hh:mm:ss):
                    <input
                        type="text"
                        value={cpu_time}
                        onChange={(e) => setCpuTime(e.target.value)}
                    />
                </label>
                <br />
                <button type="submit">Submit Job</button>
            </form>
            <p>{status}</p>
            {jupyterURL && <p>Access your Jupyter Notebook at: <a href={jupyterURL} target="_blank" rel="noopener noreferrer">{jupyterURL}</a></p>}
        </div>
    );
};

export default JobForm;
