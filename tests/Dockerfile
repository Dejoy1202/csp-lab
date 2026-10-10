ARG PYTHON_IMAGE=python:3.12-slim-bookworm
FROM ${PYTHON_IMAGE}
ENV PYTHONUNBUFFERED=1 PYTHONUTF8=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
COPY tests/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY tests/e2e.py ./
COPY tests/originals_smoke.py ./
COPY tests/test_scoring.py ./tests/
COPY worker/scoring.py ./worker/
COPY problem-packs/202403/reference/ ./reference/
CMD ["python", "e2e.py"]
