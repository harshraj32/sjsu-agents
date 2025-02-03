import { useEffect, useState } from "react";
import { useUser } from '../contexts/UserContext';

// Ensure Job interface matches backend response
interface Job {
  job_id: string;
  name: string;
  status: string;
  partition: string;
  user: string;
  time: string;
  nodes: string;
  nodelist: string;
}

const MonitorJobs = () => {
  const { user } = useUser();  // Get the full user object from context
  const username = user?.username || '';
  const [jobs, setJobs] = useState<Job[]>([]); // Ensure correct typing
  const [loading, setLoading] = useState<boolean>(false); // Track loading state
  const [error, setError] = useState<string | null>(null); // Track errors

  const fetchJobs = async () => {
    if (!username) {
      setError("Username is required to fetch jobs.");
      return;
    }
  
    setLoading(true);
    setError(null); // Clear any previous errors
  
    try {
      const response = await fetch(`/api/jobs?username=${encodeURIComponent(username)}`);


  
      // Check if the response is HTML (usually occurs on error pages)
      const contentType = response.headers.get("content-type");
      if (contentType && contentType.includes("text/html")) {
        const html = await response.text();
        setError(`Unexpected HTML response: ${html}`);
        return;
      }
  
      if (!response.ok) {
        throw new Error("Failed to fetch jobs");
      }
  
      const data = await response.json();
      setJobs(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error occurred");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJobs();
  }, [username]); // Refetch jobs when username changes

  if (loading) {
    return <div>Loading jobs...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  return (
    <div>
      <h1>Monitor Jobs</h1>
      {jobs.length > 0 ? (
        <table>
          <thead>
            <tr>
              <th>Job ID</th>
              <th>Name</th>
              <th>Status</th>
              <th>Partition</th>
              <th>Time</th>
              <th>Nodes</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {jobs.map((job) => (
              <tr key={job.job_id}>
                <td>{job.job_id}</td>
                <td>{job.name}</td>
                <td>{job.status}</td>
                <td>{job.partition}</td>
                <td>{job.time}</td>
                <td>{job.nodes}</td>
                <td>
                  <button onClick={() => console.log(`Delete job: ${job.job_id}`)}>
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <div>No jobs found.</div>
      )}
    </div>
  );
};

export default MonitorJobs;
