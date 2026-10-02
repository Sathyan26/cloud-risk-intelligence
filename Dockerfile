FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ backend/
COPY data_pipeline/ data_pipeline/
COPY ml/ ml/
COPY sql/ sql/

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
