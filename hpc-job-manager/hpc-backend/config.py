from dotenv import load_dotenv
import os

load_dotenv()

HPC_HOST = os.getenv("HPC_HOST", "coe-hpc1.sjsu.edu")
