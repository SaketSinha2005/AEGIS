from fastapi import FastAPI, HTTPException
from generator import generate_code
from pydantic import BaseModel
import tempfile
from pathlib import Path
import subprocess

app = FastAPI(title="Code Executor")

class ExecuteRequest(BaseModel):
    problem: str


class ExecuteResponse(BaseModel):
    generated_code: str
    stdout: str
    stderr: str
    exit_code: int


@app.post("/execute")
def execute(request: ExecuteRequest):

    try:
        problem = request.problem

        result = generate_code(problem)
        code = result["generated_code"]

        with tempfile.TemporaryDirectory() as tmpdir:
            solution_path = Path(tmpdir) / "solution.py"
            solution_path.write_text(code)


            process = subprocess.run(
                [
                    "docker",
                    "run",
                    "--rm",
                    "--network", "none",
                    "--cpus", "0.5",
                    "--memory", "256m",
                    "-v", f"{tmpdir}:/home/sandboxuser",
                    "img-backend"
                ],
                capture_output=True,
                text=True,
                timeout=15
            )

            return ExecuteResponse(
                generated_code=code,
                stdout=process.stdout,
                stderr=process.stderr,
                exit_code=process.returncode
            )
        

    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=408,
            detail="Execution timed out."
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )