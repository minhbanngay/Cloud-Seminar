FROM python:3.11-slim
WORKDIR /app
COPY worker.py /app/worker.py
ENV PYTHONUNBUFFERED=1
ENTRYPOINT ["python3", "/app/worker.py"]
