#!/bin/bash

# CAC40 API URL
URL="https://www.boursedirect.fr/api/instrument/intraday/XPAR/PX1/EUR"
# GET request with HTTP headers to simulate a browser
response=$(curl -s -H "User-Agent: Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:129.0) Gecko/20100101 Firefox/129.0" $URL)

if [[ $? -ne 0 ]]; then
  echo "API connection error"
  exit 1
fi

if [[ "$response" == *"403 Forbidden"* ]]; then
  echo "Erreur 403 : Accès interdit à l'API. Vérifiez les permissions ou les en-têtes de la requête."
  exit 1
fi
# Save raw json to file for verification
echo "$response" > raw_data.json

# Extraction using Regex and csv file creation
echo "Date, OpenPrice, ClosePrice, High, Low" > data_output.csv

echo "$response" | grep -oP '"Date":\s*\K[0-9]+' | while read -r date; do
    openPrice=$(echo "$response" | grep -oP "(\"Date\":\s*$date,.*?\"OpenPrice\":\s*\K[0-9.]+)")
    closePrice=$(echo "$response" | grep -oP "(\"Date\":\s*$date,.*?\"ClosePrice\":\s*\K[0-9.]+)")
    highPrice=$(echo "$response" | grep -oP "(\"Date\":\s*$date,.*?\"High\":\s*\K[0-9.]+)")
    lowPrice=$(echo "$response" | grep -oP "(\"Date\":\s*$date,.*?\"Low\":\s*\K[0-9.]+)")
    
    # Convert timestamp to readable date format
    formattedDate=$(date -d @$date +"%Y-%m-%d %H:%M:%S")

    # On récupère l'heure au format HHMM, par ex. 1730
    hourCheck=$(date -d @"$date" +%H%M)

    # Vérifier si l'heure est <= 17h30 (1730)
    if [ "$hourCheck" -le "1730" ]; then
        # On n’écrit la ligne que si toutes les valeurs sont valides ET l’heure est <= 17:30
        if [[ -n "$openPrice" && -n "$closePrice" && -n "$highPrice" && -n "$lowPrice" ]]; then
            echo "$formattedDate, $openPrice, $closePrice, $highPrice, $lowPrice" >> data_output.csv
        fi
    fi
done

echo "The data have been saved in data_output.csv"
