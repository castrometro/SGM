FROM python:3.12

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Si necesitas instalar otros paquetes del sistema (ej: build-essential, libpq-dev, etc), descomenta:
# RUN apt-get update && apt-get install -y build-essential libpq-dev

# Entrypoint/cmd lo maneja docker-compose
