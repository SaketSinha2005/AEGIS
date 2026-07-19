from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from generator import generate_code
from executor import execute_code

app = FastAPI(title="Code Executor")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ExecuteRequest(BaseModel):
    problem: str


class ExecuteResponse(BaseModel):
    generated_code: str
    stdout: str
    stderr: str
    exit_code: int


@app.post("/execute", response_model=ExecuteResponse)
def execute(request: ExecuteRequest):

    try:

        result = generate_code(request.problem)

        code = result["generated_code"]

        execution = execute_code(code)

        return ExecuteResponse(
            generated_code=code,
            stdout=execution["stdout"],
            stderr=execution["stderr"],
            exit_code=execution["exit_code"],
        )

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )