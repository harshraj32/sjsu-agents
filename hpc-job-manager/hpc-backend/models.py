from pydantic import BaseModel

class HPCJob(BaseModel):
    username: str
    password: str
    use_gpu: bool
    cpu_time: str
    num_nodes: int
    num_tasks: int
    jupyter_url: str = None


class JobRequest(BaseModel):
    username: str
    password: str

class JobCancelRequest(BaseModel):
    username: str
    job_id: str