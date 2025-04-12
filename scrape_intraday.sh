#!/bin/bash

# URL de l'API pour les données du CAC40
URL="https://www.boursedirect.fr/api/instrument/intraday/XPAR/PX1/EUR"

# Requête GET avec en-têtes HTTP pour simuler un navigateur
response=$(curl -s -H "User-Agent: Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:129.0) Gecko/20100101 Firefox/129.0" $URL)

# Vérification si la requête a échoué
if [[ $? -ne 0 ]]; then
  echo "Erreur de connexion à l'API"  # Vérifie si la requête a réussi
  exit 1
fi

# Vérification du code d'erreur HTTP 403
if [[ "$response" == *"403 Forbidden"* ]]; then
  echo "Erreur 403 : Accès interdit à l'API. Vérifiez les permissions ou les en-têtes de la requête."
  exit 1
fi

# Sauvegarde des données brutes pour vérification
echo "$response" > raw_data.json

# Création du fichier CSV de sortie
echo "Date, OpenPrice, ClosePrice, High, Low" > data_output.csv

# Extraction des données avec Regex et écriture dans le CSV
echo "$response" | grep -oP '"Date":\s*\K[0-9]+' | while read -r date; do
    # Extraction des différentes valeurs
    openPrice=$(echo "$response" | grep -oP "(\"Date\":\s*$date,.*?\"OpenPrice\":\s*\K[0-9.]+)")
    closePrice=$(echo "$response" | grep -oP "(\"Date\":\s*$date,.*?\"ClosePrice\":\s*\K[0-9.]+)")
    highPrice=$(echo "$response" | grep -oP "(\"Date\":\s*$date,.*?\"High\":\s*\K[0-9.]+)")
    lowPrice=$(echo "$response" | grep -oP "(\"Date\":\s*$date,.*?\"Low\":\s*\K[0-9.]+)")

    # Formatage de la date en un format lisible
    formattedDate=$(date -d @$date +"%Y-%m-%d %H:%M:%S")

    # Récupération de l'heure au format HHMM
    hourCheck=$(date -d @"$date" +%H%M)

    # Exclure toutes les heures >= 17h30 (1730) du CSV
    if [ "$hourCheck" -lt "1730" ]; then
        # On écrit la ligne dans le CSV si toutes les valeurs sont présentes et valides
        if [[ -n "$openPrice" && -n "$closePrice" && -n "$highPrice" && -n "$lowPrice" ]]; then
            echo "$formattedDate, $openPrice, $closePrice, $highPrice, $lowPrice" >> data_output.csv
        fi
    fi
done

echo "Les données ont été enregistrées dans data_output.csv"
