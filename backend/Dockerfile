FROM python:3.12-slim

RUN useradd -m sandboxuser
USER sandboxuser

WORKDIR /home/sandboxuser

CMD ["python", "solution.py"]
