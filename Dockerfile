FROM python:3.12-slim

# 1. Installer dépendances système utiles
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libmagic1 \
    libpq-dev \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 2. Créer un dossier pour l'app
WORKDIR /app

# 3. Copier et installer les dépendances Python
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# 4. Copier le reste de l'application
COPY . .

# 5. Exposer le port (optionnel, utile pour docs)
EXPOSE 8080

# 6. Commande de démarrage (Cloud Run friendly)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "2"]
