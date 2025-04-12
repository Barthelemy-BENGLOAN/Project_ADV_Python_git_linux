#!/bin/bash

# CAC40 API URL
URL="https://www.boursedirect.fr/api/instrument/intraday/XPAR/PX1/EUR"
# GET request with HTTP headers to simulate a browser
response=$(curl -s -H "User-Agent: Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:129.0) Gecko/20100101 Firefox/129.0" $URL)

if [[ $? -ne 0 ]]; then
  echo "API connection error"  # Check if the request was successful
  exit 1
fi

if [[ "$response" == *"403 Forbidden"* ]]; then  # Check if the server returns a 403 error
  echo "Erreur 403 : Accès interdit à l'API. Vérifiez les permissions ou les en-têtes de la requête."
  exit 1
fi

# Save raw JSON to file for verification
echo "$response" > raw_data.json

# Extraction using jq instead of regex for better compatibility
echo "Date, OpenPrice, ClosePrice, High, Low" > data_output.csv

# Check if jq is installed
if ! command -v jq &> /dev/null; then
    echo "jq is required but not installed. Installing it now..."
    sudo apt-get update
    sudo apt-get install -y jq
    if ! command -v jq &> /dev/null; then
        echo "jq installation failed. Please install jq manually."
        exit 1
    fi
fi

# Use jq to extract and format the data (works on both Linux and macOS)
jq -r '.current[] | select(.Date != null and .OpenPrice != null) | [.Date, .OpenPrice, .ClosePrice, .High, .Low] | @csv' raw_data.json > temp_data.csv

# Process the data
while IFS=, read -r date openPrice closePrice highPrice lowPrice; do
    # Remove quotes if present
    date=${date//\"/}
    openPrice=${openPrice//\"/}
    closePrice=${closePrice//\"/}
    highPrice=${highPrice//\"/}
    lowPrice=${lowPrice//\"/}
    
    # Format date (for Linux)
    formattedDate=$(date -d "@$date" +"%Y-%m-%d %H:%M:%S")
    
    # Get hour in HHMM format
    hourCheck=$(date -d "@$date" +%H%M)
    
    # Only include data before or at 17:30
    if [ "$hourCheck" -le "1730" ]; then
        echo "$formattedDate, $openPrice, $closePrice, $highPrice, $lowPrice" >> data_output.csv
    fi
done < temp_data.csv

# Clean up temp file
rm temp_data.csv

echo "The data has been saved in data_output.csv"
