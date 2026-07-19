from fastapi import FastAPI
from generator import generate_code
from pydantic import BaseModel
import tempfile
from pathlib import Path
import subprocess
import sys

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

    problem = request.problem

    result = generate_code(problem)
    code = result["generated_code"]

    with tempfile.TemporaryDirectory() as tmpdir:
        solution_path = Path(tmpdir) / "solution.py"
        solution_path.write_text(code)
        print(solution_path)


        process = subprocess.run(
            [sys.executable, str(solution_path)],
            capture_output=True,
            text=True,
            timeout=10
        )

        return ExecuteResponse(
            generated_code=code,
            stdout=process.stdout,
            stderr=process.stderr,
            exit_code=process.returncode
        )