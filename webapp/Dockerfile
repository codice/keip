FROM python:3.11-slim

LABEL org.opencontainers.image.source=https://github.com/codice/keip

RUN groupadd --system appgroup && useradd --system --gid appgroup appuser

WORKDIR /code/webapp

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chown -R appuser:appgroup /code
ENV PYTHONDONTWRITEBYTECODE=1
USER appuser

ENTRYPOINT ["python", "-m", "uvicorn", "webapp.app:app", "--host", "0.0.0.0", "--port", "7080", "--app-dir", "/code"]
