import axios from "axios";

const API_URL = "http://localhost:8000";  // Adjust based on your backend

export interface JobRequest {
  username: string;
  password: string;
  use_gpu: boolean;
  cpu_time: string;
  num_nodes: number;
  num_tasks: number;
}

export interface JobResponse {
  status: string;
  jupyter_url: string;
}

export const startHPCJob = async (jobData: JobRequest) => {
  const response = await axios.post<JobResponse>(`${API_URL}/start_job`, jobData);
  return response.data;
};

export const fetchRunningJobs = async (username: string) => {
  const response = await axios.get(`${API_URL}/running_jobs/${username}`);
  return response.data;
};

export const cancelJob = async (jobId: string, username: string, password: string) => {
  const response = await axios.delete(`${API_URL}/cancel_job/${jobId}`, {
    params: { username, password },
  });
  return response.data;
};

export const getRunningJobs = async (username: string) => {
    const response = await fetch(`${API_URL}/running_jobs/${username}`);
    return response.json();
  };
  
  export const deleteJob = async (username: string, jobId: string) => {
    await fetch(`${API_URL}/delete_job`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, job_id: jobId }),
    });
  };