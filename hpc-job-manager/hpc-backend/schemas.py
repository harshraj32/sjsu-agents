from pydantic import BaseModel

class HPCJobRequest(BaseModel):
    username: str
    password: str
    use_gpu: bool
    cpu_time: str
    num_nodes: int
    num_tasks: int

class HPCJobResponse(BaseModel):
    status: str
    jupyter_url: str
