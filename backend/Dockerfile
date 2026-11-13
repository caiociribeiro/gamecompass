FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY tests ./tests

EXPOSE 8000

# O uvicorn lê WEB_CONCURRENCY como número de processos. O cálculo das recomendações é CPU em
# Python: com 1 processo os pedidos simultâneos disputam o mesmo núcleo (veja backend/perf/).
ENV WEB_CONCURRENCY=4

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
