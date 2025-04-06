#!/bin/bash

# Configuration
LOG_FILE="scraping.log"
DATA_DIR="$(dirname "$0")"
BASE_URL="https://www.boursedirect.fr/api/instrument/history/XPAR/PX1/EUR"

# Fonction de logging
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Création du dossier de données si nécessaire
mkdir -p "$DATA_DIR"

# Vérification de la connexion internet
if ! ping -c 1 8.8.8.8 &> /dev/null; then
    log "ERREUR: Pas de connexion internet"
    exit 1
fi

# Calcul des dates
END_DATE=$(date +%s%N | cut -b1-13)
START_DATE=$(date -j -f "%Y-%m-%d" "2000-01-01" "+%s%N" | cut -b1-13)

# GET request avec HTTP headers pour simuler un navigateur
log "Tentative de connexion à l'API..."
response=$(curl -s -H "User-Agent: Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:129.0) Gecko/20100101 Firefox/129.0" \
    "$BASE_URL?start=$START_DATE&end=$END_DATE&period=1d")

if [[ $? -ne 0 ]]; then
    log "ERREUR: Échec de la connexion à l'API"
    exit 1
fi

if [[ "$response" == *"403 Forbidden"* ]]; then
    log "ERREUR: Accès interdit à l'API"
    exit 1
fi

# Sauvegarde des données brutes
log "Sauvegarde des données brutes..."
echo "$response" > "$DATA_DIR/raw_data.json"

# Vérification du format JSON
if ! jq empty "$DATA_DIR/raw_data.json" 2>/dev/null; then
    log "ERREUR: Les données reçues ne sont pas au format JSON valide"
    exit 1
fi

# Créer le fichier CSV avec les en-têtes
echo "Date,OpenPrice,ClosePrice,High,Low" > "$DATA_DIR/data_history.csv"

# Traiter les données JSON et les convertir en CSV
cat "$DATA_DIR/raw_data.json" | jq -r '.current[] | select(.Date != null and .OpenPrice != null) | [.Date, .OpenPrice, .ClosePrice, .High, .Low] | @csv' > "$DATA_DIR/temp.csv"

# Formater les dates et écrire dans le fichier final
while IFS=, read -r timestamp open close high low; do
    # Convertir le timestamp en date lisible
    date=$(date -r "${timestamp}" "+%Y-%m-%d")
    echo "$date,$open,$close,$high,$low" >> "$DATA_DIR/data_history.csv"
done < "$DATA_DIR/temp.csv"

# Supprimer le fichier temporaire
rm "$DATA_DIR/temp.csv"

# Compter le nombre de lignes de données
data_lines=$(wc -l < "$DATA_DIR/data_history.csv")
data_lines=$((data_lines - 1))  # Soustraire la ligne d'en-tête
log "Nombre de lignes de données: \t$data_lines"

# Vérification finale
if [[ -s "$DATA_DIR/data_history.csv" ]]; then
    log "SUCCÈS: Données sauvegardées avec succès"
else
    log "ERREUR: Aucune donnée n'a été extraite"
    exit 1
fi
