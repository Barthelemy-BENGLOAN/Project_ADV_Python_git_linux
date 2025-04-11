FROM python:3.11-slim

# Installer jq et les dépendances pour curl
RUN apt-get update && apt-get install -y \
    curl \
    jq \
    cron \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copier les fichiers requis
COPY . .

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Rendre les scripts exécutables
RUN chmod +x scrape_intraday.sh
RUN chmod +x scrape_history.sh

# Configurer cron
COPY cron_intraday.txt /etc/cron.d/cron_intraday
RUN chmod 0644 /etc/cron.d/cron_intraday
RUN crontab /etc/cron.d/cron_intraday

# Démarrer cron et l'application
CMD service cron start && python dashboard.py

# Exposer le port
EXPOSE 8050 