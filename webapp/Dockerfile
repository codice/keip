FROM python:3.11-slim

LABEL org.opencontainers.image.source=https://github.com/codice/keip

RUN groupadd --system --gid 999 appgroup && useradd --system --uid 999 --gid appgroup appuser

WORKDIR /code/webapp

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chown -R appuser:appgroup /code
ENV PYTHONDONTWRITEBYTECODE=1
USER 999

ENTRYPOINT ["python", "-m", "uvicorn", "webapp.app:app", "--host", "0.0.0.0", "--port", "7080", "--app-dir", "/code"]
