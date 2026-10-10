ARG PYTHON_IMAGE=python:3.12-slim-bookworm
FROM ${PYTHON_IMAGE}
ENV PYTHONUNBUFFERED=1 PYTHONUTF8=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
COPY worker/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY worker/sandbox.py worker/checkers.py ./
COPY problem-packs/ ./
CMD ["python","build.py"]
