ARG PYTHON_IMAGE=python:3.12-slim-bookworm
FROM ${PYTHON_IMAGE}
RUN apt-get update && apt-get install -y --no-install-recommends g++ libseccomp2 && rm -rf /var/lib/apt/lists/*
RUN apt-get update && apt-get install -y --no-install-recommends libboost-dev && rm -rf /var/lib/apt/lists/*
ENV PYTHONUNBUFFERED=1 PYTHONUTF8=1 PYTHONDONTWRITEBYTECODE=1
COPY compile.py run.py load.py /sandbox/
RUN chmod -R 555 /sandbox && mkdir /work && chmod 755 /work
WORKDIR /work
CMD ["sleep", "600"]
