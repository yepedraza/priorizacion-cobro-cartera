# Imagen del servicio del score de pago tardío (B).
# Se construye desde la raíz del repo; app/Dockerfile.dockerignore deja entrar solo el servicio y
# el modelo, así que datos_crudos/ nunca llega a la imagen:
#   docker build -f app/Dockerfile -t score-b .
FROM python:3.14.5-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 CARPETA_MODELOS=/srv/modelos
WORKDIR /srv

COPY app/requirements.txt app/requirements.txt
RUN pip install --no-cache-dir -r app/requirements.txt

COPY src/cartera/ src/cartera/
COPY app/servicio.py app/demo.html app/
COPY modelos/modelo_B.joblib modelos/modelo_B.json modelos/segmentacion_A.joblib modelos/segmentacion_A.json modelos/

RUN useradd --no-create-home servicio
USER servicio

EXPOSE 8000
CMD ["uvicorn", "app.servicio:app", "--host", "0.0.0.0", "--port", "8000"]
