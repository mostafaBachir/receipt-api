FROM python:3.12.9-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Dépendances système
RUN apt-get update && apt-get install -y gcc libffi-dev curl && apt-get clean

# Créer un utilisateur non-root
RUN useradd -m appuser

# Dossier de travail
WORKDIR /app

# Copier d’abord les requirements et installer les dépendances Python
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copier tout le reste
COPY . .

# Créer le dossier uploads avec les bons droits pour appuser
RUN mkdir -p /app/uploads && chown -R appuser:appuser /app/uploads

# Changer d’utilisateur (sécurité)
USER appuser

# Exposer le port pour FastAPI
EXPOSE 8000

# Démarrage du serveur Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
