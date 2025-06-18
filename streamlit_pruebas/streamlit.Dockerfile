FROM python:3.11-slim

WORKDIR /app

# Copiar el requirements.txt desde el contexto raíz (por eso el build context es .)
COPY ./requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

CMD ["bash", "-c", "streamlit run app.py --server.port=$PORT --server.address=0.0.0.0"]
