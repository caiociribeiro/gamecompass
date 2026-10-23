FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /workspace

COPY requirements.txt /tmp/requirements-data.txt
RUN python -m pip install --no-cache-dir -r /tmp/requirements-data.txt

COPY . ./scripts

CMD ["python", "scripts/check_neo4j.py"]
