from fastapi import FastAPI, Depends, HTTPException
from schemas import HPCJobRequest, HPCJobResponse
from services import HPCSessionManager, HPCJobMonitor
from fastapi.middleware.cors import CORSMiddleware
from models import JobCancelRequest, JobRequest
app = FastAPI()
# Store active monitoring sessions
active_monitors = {}
# Allow frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this to your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/start_job", response_model=HPCJobResponse)
async def start_hpc_job(job_request: HPCJobRequest):
    print("Received request:", job_request.dict())  # Debugging log
    session_manager = HPCSessionManager(**job_request.dict())
    success, jupyter_url = session_manager.start()
    
    if not success:
        raise HTTPException(status_code=500, detail="HPC job execution failed")
    
    return {"status": "Job started", "jupyter_url": jupyter_url}

@app.get("/running_jobs/{username}")
async def get_running_jobs(username: str):
    if username not in active_monitors:
        raise HTTPException(status_code=404, detail="No monitoring session found for this user")

    jobs = active_monitors[username].get_current_jobs()
    return {"jobs": jobs}

@app.delete("/cancel_job/{job_id}")
async def cancel_job(job_id: str, username: str, password: str):
    success = HPCSessionManager.cancel_job(job_id, username, password)
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to cancel job")
    
    return {"status": "Job canceled successfully"}





@app.post("/start_monitoring")
def start_monitoring(request: JobRequest):
    if request.username in active_monitors:
        return {"message": "Monitoring already active for this user"}

    monitor = HPCJobMonitor(request.username, request.password)
    active_monitors[request.username] = monitor
    monitor.start_monitoring(lambda jobs: print(f"Updated jobs for {request.username}"))

    return {"message": "Monitoring started"}

@app.get("/running_jobs/{username}")
def get_running_jobs(username: str):
    if username not in active_monitors:
        raise HTTPException(status_code=404, detail="No monitoring session found for this user")
    
    jobs = active_monitors[username].get_current_jobs()
    return {"jobs": jobs}

@app.delete("/delete_job")
def delete_job(request: JobCancelRequest):
    if request.username not in active_monitors:
        raise HTTPException(status_code=404, detail="No monitoring session found for this user")
    
    success = active_monitors[request.username].cancel_job(request.job_id)
    
    if success:
        return {"message": "Job deleted successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to delete job")