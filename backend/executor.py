import subprocess
import tempfile
import uuid
from pathlib import Path
from fastapi import HTTPException


def execute_code(code: str):
    with tempfile.TemporaryDirectory() as tmpdir:

        solution_path = Path(tmpdir) / "solution.py"
        solution_path.write_text(code)

        container_name = f"sandbox-{uuid.uuid4().hex[:12]}"

        try:
            process = subprocess.run(
                [
                    "docker",
                    "run",
                    "--rm",
                    "--name",
                    container_name,
                    "--network",
                    "none",
                    "--cpus",
                    "0.5",
                    "--memory",
                    "256m",
                    "-v",
                    f"{tmpdir}:/home/sandboxuser",
                    "img-backend",
                ],
                capture_output=True,
                text=True,
                timeout=15,
                stdin=subprocess.DEVNULL,
            )

            return {
                "stdout": process.stdout,
                "stderr": process.stderr,
                "exit_code": process.returncode,
            }

        except subprocess.TimeoutExpired:

            subprocess.run(
                ["docker", "kill", container_name],
                capture_output=True,
                timeout=5,
            )

            raise HTTPException(
                status_code=408,
                detail="Execution timed out.",
            )