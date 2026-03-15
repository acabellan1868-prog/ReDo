FROM python:3.12-slim

# Instalar nmap (necesario para python-nmap)
RUN apt-get update && \
    apt-get install -y --no-install-recommends nmap && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instalar dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar codigo y frontend
COPY app/ app/
COPY static/ static/

# Puerto de la aplicacion
EXPOSE 8081

# Arrancar uvicorn
CMD ["uvicorn", "app.principal:app", "--host", "0.0.0.0", "--port", "8081"]
