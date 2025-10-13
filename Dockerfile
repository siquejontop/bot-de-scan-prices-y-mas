# Imagen base con Python
FROM python:3.13-slim

# Instala dependencias del sistema, incluyendo Tesseract
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    && rm -rf /var/lib/apt/lists/*

# Copia los archivos del repositorio
WORKDIR /app
COPY . /app

# Instala dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Expone el puerto de Flask (ajústalo si usas otro)
EXPOSE 10000

# Comando para ejecutar el bot
CMD ["python", "main.py"]
