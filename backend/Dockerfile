FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends \
    libpq5 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libpangoft2-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libcairo2 \
    libffi8 \
    libmagic1 \
    shared-mime-info \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# --forwarded-allow-ips liste les sauts de confiance qui précèdent ce
# service pour qu'Uvicorn résolve la vraie IP visiteur depuis
# X-Forwarded-For plutôt que celle du conteneur frontend :
#   - 172.16.0.0/12 (réseaux Docker)
#   - 192.168.1.23 (IP LAN du ThinkStation, d'où le Nginx hôte se reconnecte)
# Sans cette liste, le throttle de connexion (slowapi) est soit partagé par
# tout le monde, soit contournable en forgeant l'en-tête — gotcha corrigé sur
# ForfaitFlow/Recueil/Regula Flow/Firewall Analyzer, répliqué ici dès le départ.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "172.16.0.0/12,192.168.1.23"]
