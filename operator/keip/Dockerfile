FROM python:3.11.5-slim

LABEL org.opencontainers.image.source=https://github.com/codice/keip

WORKDIR /code/keip

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENTRYPOINT ["python", "-m", "uvicorn", "keip.app:app", "--host", "0.0.0.0", "--port", "7080", "--app-dir", "/code"]
