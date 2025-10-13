# Imagen base con Python y utilidades básicas
FROM python:3.13-slim

# Instalar dependencias del sistema necesarias para Tesseract, Pillow y audio
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    libsm6 \
    libxext6 \
    libgl1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Establecer directorio de trabajo
WORKDIR /app

# Copiar archivos del proyecto
COPY . /app

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Exponer el puerto Flask
EXPOSE 10000

# Comando para ejecutar el bot
CMD ["python", "main.py"]
