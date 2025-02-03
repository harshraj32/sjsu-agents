import { useEffect, useState } from "react";
import { fetchRunningJobs, cancelJob } from "../api";

interface Job {
  "Job ID": string;
  Name: string;
  State: string;
}

interface JobListProps {
  username: string;
  password: string;
}

const JobList: React.FC<JobListProps> = ({ username, password }) => {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadJobs() {
      const data = await fetchRunningJobs(username);
      setJobs(data);
      setLoading(false);
    }
    loadJobs();
  }, [username]);

  const handleCancel = async (jobId: string) => {
    await cancelJob(jobId, username, password);
    setJobs(jobs.filter((job) => job["Job ID"] !== jobId));
  };

  if (loading) return <p>Loading jobs...</p>;

  return (
    <div>
      <h3>Running Jobs</h3>
      {jobs.length === 0 ? <p>No active jobs.</p> : jobs.map((job) => (
        <div key={job["Job ID"]}>
          <p>{job.Name} - {job.State}</p>
          <button onClick={() => handleCancel(job["Job ID"])}>Cancel</button>
        </div>
      ))}
    </div>
  );
};

export default JobList;
