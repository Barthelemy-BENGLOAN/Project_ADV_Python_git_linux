#!/bin/bash

# URL de l'API
URL="https://www.boursedirect.fr/api/instrument/intraday/XPAR/PX1/EUR"

# Faire une requête GET avec des en-têtes HTTP pour simuler un navigateur
response=$(curl -s -H "User-Agent: Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:129.0) Gecko/20100101 Firefox/129.0" $URL)

# Vérifier si la requête est réussie
if [[ $? -ne 0 ]]; then
  echo "Erreur de connexion à l'API"
  exit 1
fi

# Sauvegarder le JSON brut dans un fichier pour vérification
echo "$response" > raw_data.json

# Vérifier si le serveur retourne une erreur 403
if [[ "$response" == *"403 Forbidden"* ]]; then
  echo "Erreur 403 : Accès interdit à l'API. Vérifiez les permissions ou les en-têtes de la requête."
  exit 1
fi

# Extraire uniquement les données OpenPrice, ClosePrice, High, Low en utilisant Regex
# Crée un fichier CSV avec les titres "Date, OpenPrice, ClosePrice, High, Low"
echo "Date, OpenPrice, ClosePrice, High, Low" > data_output.csv

# Utiliser regex pour extraire les informations de la réponse JSON
# On va d'abord chercher toutes les entrées dans "current" en capturant la date, open price, close price, high et low
echo "$response" | grep -oP '"Date":\s*\K[0-9]+' | while read -r date; do
    # Pour chaque Date, on extrait OpenPrice, ClosePrice, High, et Low qui suivent dans le JSON
    openPrice=$(echo "$response" | grep -oP "(\"Date\":\s*$date,.*?\"OpenPrice\":\s*\K[0-9.]+)")
    closePrice=$(echo "$response" | grep -oP "(\"Date\":\s*$date,.*?\"ClosePrice\":\s*\K[0-9.]+)")
    highPrice=$(echo "$response" | grep -oP "(\"Date\":\s*$date,.*?\"High\":\s*\K[0-9.]+)")
    lowPrice=$(echo "$response" | grep -oP "(\"Date\":\s*$date,.*?\"Low\":\s*\K[0-9.]+)")
    
    # Formater la date en format lisible
    formattedDate=$(date -d @$((date / 1000)) +"%Y-%m-%d %H:%M:%S")

    # Vérifier si les valeurs extraites sont valides
    if [[ -n "$openPrice" && -n "$closePrice" && -n "$highPrice" && -n "$lowPrice" ]]; then
        # Ajouter les données extraites dans le fichier CSV
        echo "$formattedDate, $openPrice, $closePrice, $highPrice, $lowPrice" >> data_output.csv
    fi
done

echo "Les données ont été enregistrées dans data_output.csv."
